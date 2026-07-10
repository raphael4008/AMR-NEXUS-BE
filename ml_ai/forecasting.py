"""
Resistance Rate Forecasting Engine
====================================
Prophet-based forecasting for AMR resistance rate trajectories.
Produces configurable-horizon (default 3-month) ahead forecasts with
confidence intervals and risk classification for all pathogen–drug–county
combinations in Kenya's 47 counties.

Architecture
------------
- **Prophet**: Interpretable additive model with yearly seasonality,
  Kenyan public holidays as regressors, quarterly seasonality via Fourier
  terms, optional reporting-lag regressor, and automatic changepoint
  detection.

Risk Classification
-------------------
- **Critical**: Forecast >80 % resistance rate OR >20 pp increase
- **High**: Forecast >60 % OR >10 pp increase
- **Medium**: Forecast >40 % OR >5 pp increase
- **Low**: Otherwise

Graceful Degradation
--------------------
When ``prophet`` is not installed the module falls back to flat-line
forecasts (last-known value projected forward) so that the API surface
never raises ``ImportError`` at import time.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from ml_ai.config import get_ml_config

# ── Guarded Prophet import ────────────────────────────────────────────────
# ── Guarded Prophet import ────────────────────────────────────────────────
import os as _os

try:
    import cmdstanpy as _cmdstanpy

    # Explicitly tell cmdstanpy where CmdStan lives.
    # The CMDSTAN env var is set in docker-compose but cmdstanpy
    # doesn't auto-read it — set_cmdstan_path() must be called first.
    _cmdstan_path = _os.environ.get(
        "CMDSTAN",
        _os.path.expanduser("~/.cmdstan/cmdstan-2.39.0"),
    )
    if _os.path.isdir(_cmdstan_path):
        _cmdstanpy.set_cmdstan_path(_cmdstan_path)

except Exception:
    pass

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    Prophet = None
    HAS_PROPHET = False

# ── Guarded KENYA_COUNTIES import ────────────────────────────────────────
# The canonical dict lives in ml_ai.feature_engineering.  When that module
# has not been created yet (early bootstrapping) we define a local fallback
# so this file remains independently importable.
try:
    from ml_ai.feature_engineering import KENYA_COUNTIES
except ImportError:  # pragma: no cover
    KENYA_COUNTIES: Dict[str, str] = {
        "001": "Mombasa", "002": "Kwale", "003": "Kilifi",
        "004": "Tana River", "005": "Lamu", "006": "Taita-Taveta",
        "007": "Garissa", "008": "Wajir", "009": "Mandera",
        "010": "Marsabit", "011": "Isiolo", "012": "Meru",
        "013": "Tharaka-Nithi", "014": "Embu", "015": "Kitui",
        "016": "Machakos", "017": "Makueni", "018": "Nyandarua",
        "019": "Nyeri", "020": "Kirinyaga", "021": "Murang'a",
        "022": "Kiambu", "023": "Turkana", "024": "West Pokot",
        "025": "Samburu", "026": "Trans-Nzoia", "027": "Uasin Gishu",
        "028": "Elgeyo-Marakwet", "029": "Nandi", "030": "Baringo",
        "031": "Laikipia", "032": "Nakuru", "033": "Narok",
        "034": "Kajiado", "035": "Kericho", "036": "Bomet",
        "037": "Kakamega", "038": "Vihiga", "039": "Bungoma",
        "040": "Busia", "041": "Siaya", "042": "Kisumu",
        "043": "Homa Bay", "044": "Migori", "045": "Kisii",
        "046": "Nyamira", "047": "Nairobi",
    }

logger = logging.getLogger(__name__)
_cfg = get_ml_config()


# ═══════════════════════════════════════════════════════════════════════════
# KENYAN PUBLIC HOLIDAYS — Prophet regressor
# ═══════════════════════════════════════════════════════════════════════════

KENYA_HOLIDAYS = pd.DataFrame(
    {
        "holiday": [
            # ── Fixed-date holidays (2025 & 2026) ────────────────────
            "new_year",        "new_year",
            "labour_day",      "labour_day",
            "madaraka_day",    "madaraka_day",
            "mashujaa_day",    "mashujaa_day",
            "jamhuri_day",     "jamhuri_day",
            "christmas",       "christmas",
            "boxing_day",      "boxing_day",
            # ── Islamic holidays (approximate) ───────────────────────
            "eid_al_fitr",     "eid_al_fitr",
            "eid_al_adha",     "eid_al_adha",
            # ── Christian moveable feasts ─────────────────────────────
            "easter_monday",   "easter_monday",
            "good_friday",     "good_friday",
        ],
        "ds": pd.to_datetime([
            # 2025 fixed
            "2025-01-01", "2026-01-01",  # New Year
            "2025-05-01", "2026-05-01",  # Labour Day
            "2025-06-01", "2026-06-01",  # Madaraka Day
            "2025-10-20", "2026-10-20",  # Mashujaa Day
            "2025-12-12", "2026-12-12",  # Jamhuri Day
            "2025-12-25", "2026-12-25",  # Christmas
            "2025-12-26", "2026-12-26",  # Boxing Day
            # Eid (approximate dates)
            "2025-03-30", "2026-03-20",  # Eid al-Fitr
            "2025-06-07", "2026-05-27",  # Eid al-Adha
            # Easter
            "2025-04-21", "2026-04-06",  # Easter Monday
            "2025-04-18", "2026-04-03",  # Good Friday
        ]),
        "lower_window": 0,
        "upper_window": 1,
    }
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ForecastPoint:
    """Single-month forecast data point.

    Attributes:
        month: Year-month string in ``YYYY-MM`` format.
        predicted_rate: Point estimate of the resistance rate [0, 1].
        lower_ci: Lower bound of the 95 % confidence interval.
        upper_ci: Upper bound of the 95 % confidence interval.
    """

    month: str
    predicted_rate: float
    lower_ci: float
    upper_ci: float


@dataclass
class ForecastResult:
    """Complete forecast output for one pathogen–drug–county combination.

    Attributes:
        pathogen: Pathogen organism name (e.g. ``Escherichia coli``).
        drug_class: Antimicrobial drug class (e.g. ``Carbapenems``).
        county: Kenya county 3-digit code (e.g. ``047``).
        county_name: Human-readable county name.
        sector: One Health sector (``human``, ``animal``, ``environment``).
        forecast_horizon_months: Number of months forecasted.
        predictions: Ordered list of per-month forecast dicts.
        model_used: Identifier of the model that produced the forecast.
        mape: Mean Absolute Percentage Error on the validation set.
        trend_direction: ``increasing``, ``decreasing``, or ``stable``.
        risk_level: ``critical``, ``high``, ``medium``, or ``low``.
    """

    pathogen: str
    drug_class: str
    county: str
    county_name: str
    sector: str
    forecast_horizon_months: int
    predictions: List[Dict[str, Any]]
    model_used: str
    mape: Optional[float]
    trend_direction: str
    risk_level: str


# ═══════════════════════════════════════════════════════════════════════════
# RESISTANCE FORECASTER
# ═══════════════════════════════════════════════════════════════════════════

class ResistanceForecaster:
    """Prophet-based resistance rate forecaster.

    Trains per-(pathogen, drug_class, county_code) Prophet models and
    produces multi-month-ahead forecasts with confidence intervals.  When
    Prophet is unavailable the forecaster returns flat-line fallback
    predictions so that the downstream API never breaks.

    Attributes:
        prophet_models: Dict of fitted Prophet models keyed by series ID.
        prophet_weight: Weight factor reserved for future ensemble use.
        horizon_months: Default forecast horizon.
        model_version: Version tag assigned at training time.
        validation_mape: Per-series validation MAPE values.
    """

    # ------------------------------------------------------------------ #
    # CONSTRUCTION                                                        #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        horizon_months: Optional[int] = None,
        prophet_weight: float = 1.0,
    ) -> None:
        """Initialise the forecaster.

        Args:
            horizon_months: Months to forecast ahead.  Falls back to
                ``ForecastConfig.horizon_months`` (default 3).
            prophet_weight: Weight assigned to Prophet in potential
                future ensembles.  Fixed at 1.0 for the MVP.
        """
        self.horizon_months: int = horizon_months or _cfg.forecast.horizon_months
        self.prophet_weight: float = prophet_weight

        self.prophet_models: Dict[str, Any] = {}
        self.model_version: str = ""
        self.validation_mape: Dict[str, float] = {}

        logger.info(
            "ResistanceForecaster initialised — horizon=%d months, "
            "prophet_available=%s",
            self.horizon_months,
            HAS_PROPHET,
        )

    # ------------------------------------------------------------------ #
    # SERIES KEY                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _series_key(pathogen: str, drug_class: str, county: str) -> str:
        """Generate a unique composite key for a time-series.

        Args:
            pathogen: Pathogen organism name.
            drug_class: Antimicrobial drug class.
            county: Kenya county 3-digit code.

        Returns:
            Pipe-delimited key string.
        """
        return f"{pathogen}|{drug_class}|{county}"

    # ------------------------------------------------------------------ #
    # PROPHET DF PREPARATION                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _prepare_prophet_df(group: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Convert an aggregated group into a Prophet-compatible DataFrame.

        Expects columns ``year_month`` (``pd.Period``) and
        ``resistance_rate`` (float in [0, 1]).  Optionally includes
        ``reporting_lag_mean`` which is renamed to ``reporting_lag``.

        Args:
            group: Subset of the master time-series DataFrame for one
                (pathogen, drug_class, county) combination.

        Returns:
            DataFrame with columns ``ds``, ``y``, and optionally
            ``reporting_lag``, sorted chronologically.  ``None`` when
            required columns are missing.
        """
        required = {"year_month", "resistance_rate"}
        if not required.issubset(group.columns):
            logger.warning(
                "Cannot prepare Prophet DF — missing columns: %s",
                required - set(group.columns),
            )
            return None

        pdf = group.sort_values("year_month").copy()

        # Prophet requires a ``ds`` datetime and ``y`` target column.
        pdf["ds"] = pdf["year_month"].apply(
            lambda p: p.to_timestamp() if hasattr(p, "to_timestamp") else pd.Timestamp(p)
        )
        pdf["y"] = pdf["resistance_rate"].clip(0.0, 1.0)

        keep_cols = ["ds", "y"]

        # Optional reporting-lag regressor.
        if "reporting_lag_mean" in pdf.columns:
            pdf["reporting_lag"] = pdf["reporting_lag_mean"].fillna(0)
            keep_cols.append("reporting_lag")

        return pdf[keep_cols].reset_index(drop=True)

    # ------------------------------------------------------------------ #
    # MAPE HELPER                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_mape(actuals: np.ndarray, predictions: np.ndarray) -> float:
        """Mean Absolute Percentage Error, ignoring zeros in *actuals*.

        Args:
            actuals: Ground-truth values.
            predictions: Model predictions of the same length.

        Returns:
            MAPE as a fraction (e.g. 0.12 for 12 %).
        """
        mask = actuals != 0
        if mask.sum() == 0:
            return 0.0
        return float(
            np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask]))
        )

    # ------------------------------------------------------------------ #
    # TRAINING                                                            #
    # ------------------------------------------------------------------ #

    def train(self, time_series_df: pd.DataFrame) -> Dict[str, float]:
        """Train per-series Prophet models on historical resistance data.

        The method groups ``time_series_df`` by
        ``(pathogen_name, drug_class, county_code)`` and fits a Prophet
        model for each group that contains ≥6 months of data.  A temporal
        validation split (last 3 months) is used to compute MAPE.

        Args:
            time_series_df: Feature DataFrame with at minimum the columns
                ``year_month``, ``pathogen_name``, ``drug_class``,
                ``county_code``, and ``resistance_rate``.

        Returns:
            Dict mapping ``"prophet_avg_mape"`` to the average validation
            MAPE across all trained series.
        """
        logger.info(
            "Forecast training started — %d records", len(time_series_df),
        )

        prophet_mapes = self._train_prophet_models(time_series_df)

        self.model_version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        avg_mape: Optional[float] = None
        if prophet_mapes:
            avg_mape = round(float(np.mean(list(prophet_mapes.values()))), 4)

        metrics: Dict[str, float] = {}
        if avg_mape is not None:
            metrics["prophet_avg_mape"] = avg_mape

        logger.info(
            "Forecast training complete — %d Prophet models, metrics=%s",
            len(self.prophet_models),
            metrics,
        )
        return metrics

    # ------------------------------------------------------------------ #
    # PROPHET MODEL TRAINING (per-series)                                 #
    # ------------------------------------------------------------------ #

    def _train_prophet_models(self, df: pd.DataFrame) -> Dict[str, float]:
        """Fit one Prophet model per unique time-series group.

        Groups the data by ``(pathogen_name, drug_class, county_code)``
        and trains a Prophet model for each group whose length is at
        least ``ForecastConfig.min_series_length`` (default 6).

        Args:
            df: Full feature DataFrame.

        Returns:
            Dict of ``series_key → validation MAPE``.
        """
        if not HAS_PROPHET:
            logger.warning(
                "Prophet is not installed — skipping Prophet training.  "
                "Forecasts will use the flat-line fallback."
            )
            return {}

        mapes: Dict[str, float] = {}
        entity_cols = ["pathogen_name", "drug_class", "county_code"]
        min_len = _cfg.forecast.min_series_length

        for keys, group in df.groupby(entity_cols, observed=True):
            pathogen, drug_class, county = keys
            series_key = self._series_key(pathogen, drug_class, county)

            if len(group) < min_len:
                logger.debug(
                    "Skipping series %s — only %d data points (need %d)",
                    series_key, len(group), min_len,
                )
                continue

            try:
                prophet_df = self._prepare_prophet_df(group)
                if prophet_df is None or len(prophet_df) < min_len:
                    continue

                # Temporal split: last 3 months held out for validation.
                train_df = prophet_df.iloc[:-3]
                val_df = prophet_df.iloc[-3:]

                try:
                    model = Prophet(
                        changepoint_prior_scale=_cfg.forecast.prophet_changepoint_prior,
                        seasonality_mode=_cfg.forecast.prophet_seasonality_mode,
                        yearly_seasonality=_cfg.forecast.prophet_yearly_seasonality,
                        weekly_seasonality=False,
                        daily_seasonality=False,
                        holidays=KENYA_HOLIDAYS,
                    )
                except AttributeError as exc:
                    logger.error(
                        "Prophet init failed for series %s — CmdStan likely not found. "
                        "CMDSTAN env=%s. Error: %s",
                        series_key,
                        _os.environ.get("CMDSTAN", "not set"),
                        exc,
                    )
                    continue

                # Optional reporting-lag regressor.
                if "reporting_lag" in prophet_df.columns:
                    model.add_regressor("reporting_lag")

                # Quarterly seasonality.
                model.add_seasonality(
                    name="quarterly",
                    period=91.25,
                    fourier_order=3,
                )

                model.fit(train_df)
                self.prophet_models[series_key] = model

                # ── Validation ───────────────────────────────────────
                future = model.make_future_dataframe(periods=3, freq="MS")
                if "reporting_lag" in prophet_df.columns:
                    future["reporting_lag"] = prophet_df["reporting_lag"].iloc[-1]

                forecast = model.predict(future)

                if len(val_df) > 0 and len(forecast) >= len(prophet_df):
                    actuals = val_df["y"].values
                    preds = forecast.iloc[-3:]["yhat"].values[: len(actuals)]
                    mape_val = self._compute_mape(actuals, preds)
                    mapes[series_key] = mape_val
                    self.validation_mape[series_key] = mape_val

            except Exception:
                logger.exception(
                    "Prophet training failed for series %s", series_key,
                )

        logger.info(
            "Prophet training complete — %d models fitted", len(self.prophet_models),
        )
        return mapes

    # ------------------------------------------------------------------ #
    # SINGLE-SERIES FORECAST                                              #
    # ------------------------------------------------------------------ #

    def forecast(
        self,
        as_of_date: date,
        pathogen: str,
        drug_class: str,
        county: str,
        horizon_months: Optional[int] = None,
        time_series_df: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        """Generate a forecast for one (pathogen, drug_class, county) tuple.

        If a trained Prophet model exists for the series it is used;
        otherwise a flat-line fallback is returned.

        Args:
            as_of_date: Reference date from which to project forward.
            pathogen: Pathogen organism name.
            drug_class: Antimicrobial drug class.
            county: Kenya county 3-digit code.
            horizon_months: Override the default forecast horizon.
            time_series_df: Historical data (used to derive the last
                known resistance rate for fallback forecasts).

        Returns:
            A fully populated :class:`ForecastResult`.
        """
        horizon = horizon_months or self.horizon_months
        series_key = self._series_key(pathogen, drug_class, county)

        # Attempt Prophet forecast.
        prophet_preds = self._prophet_forecast(series_key, as_of_date, horizon)

        if prophet_preds is not None:
            predictions = prophet_preds
            model_used = "prophet"
        else:
            # Fallback: flat-line projection.
            last_rate = self._last_known_rate(
                time_series_df, pathogen, drug_class, county,
            )
            predictions = self._flat_forecast(as_of_date, horizon, last_rate)
            model_used = "fallback"

        # ── Trend & risk ─────────────────────────────────────────────
        rates = [p["predicted_rate"] for p in predictions]
        current_rate = rates[0] if rates else 0.0
        final_rate = rates[-1] if rates else 0.0

        trend_direction = self._classify_trend(current_rate, final_rate)
        risk_level = self._classify_risk(rates, current_rate)

        mape = self.validation_mape.get(series_key)
        county_name = KENYA_COUNTIES.get(county, county)

        sector = "human"
        if time_series_df is not None and "sector" in time_series_df.columns:
            mask = (
                (time_series_df["pathogen_name"] == pathogen)
                & (time_series_df["drug_class"] == drug_class)
                & (time_series_df["county_code"] == county)
            )
            sector_vals = time_series_df.loc[mask, "sector"]
            if not sector_vals.empty:
                sector = str(sector_vals.mode().iloc[0])

        return ForecastResult(
            pathogen=pathogen,
            drug_class=drug_class,
            county=county,
            county_name=county_name,
            sector=sector,
            forecast_horizon_months=horizon,
            predictions=predictions,
            model_used=model_used,
            mape=mape,
            trend_direction=trend_direction,
            risk_level=risk_level,
        )

    # ------------------------------------------------------------------ #
    # BATCH FORECAST                                                      #
    # ------------------------------------------------------------------ #

    def forecast_all_combinations(
        self,
        time_series_df: pd.DataFrame,
        as_of_date: Optional[date] = None,
    ) -> List[ForecastResult]:
        """Generate forecasts for every pathogen–drug–county combination.

        Args:
            time_series_df: Full feature DataFrame.
            as_of_date: Reference date; defaults to the latest month in
                the data.

        Returns:
            List of :class:`ForecastResult` objects, one per combination.
        """
        if as_of_date is None:
            if "year_month" in time_series_df.columns:
                latest = time_series_df["year_month"].max()
                as_of_date = (
                    latest.to_timestamp().date()
                    if hasattr(latest, "to_timestamp")
                    else date.today()
                )
            else:
                as_of_date = date.today()

        entity_cols = ["pathogen_name", "drug_class", "county_code"]
        results: List[ForecastResult] = []

        for keys, group in time_series_df.groupby(entity_cols, observed=True):
            pathogen, drug_class, county = keys
            try:
                result = self.forecast(
                    as_of_date=as_of_date,
                    pathogen=pathogen,
                    drug_class=drug_class,
                    county=county,
                    time_series_df=group,
                )
                results.append(result)
            except Exception:
                logger.exception(
                    "Forecast failed for %s / %s / %s",
                    pathogen, drug_class, county,
                )

        logger.info("Batch forecasting complete — %d results", len(results))
        return results

    # ------------------------------------------------------------------ #
    # PROPHET FORECAST (internal)                                         #
    # ------------------------------------------------------------------ #

    def _prophet_forecast(
        self,
        series_key: str,
        as_of_date: date,
        horizon: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Run Prophet prediction for one trained series.

        Args:
            series_key: Composite key identifying the trained model.
            as_of_date: Not directly consumed by Prophet but kept for
                API symmetry.
            horizon: Number of months to forecast.

        Returns:
            List of prediction dicts or ``None`` if no model exists.
        """
        if not HAS_PROPHET or series_key not in self.prophet_models:
            return None

        model = self.prophet_models[series_key]
        try:
            future = model.make_future_dataframe(periods=horizon, freq="MS")
            if "reporting_lag" in model.extra_regressors:
                future["reporting_lag"] = 0.0

            forecast = model.predict(future)
            tail = forecast.tail(horizon)

            return [
                {
                    "month": row["ds"].strftime("%Y-%m"),
                    "predicted_rate": float(np.clip(row["yhat"], 0, 1)),
                    "lower_ci": float(np.clip(row["yhat_lower"], 0, 1)),
                    "upper_ci": float(np.clip(row["yhat_upper"], 0, 1)),
                }
                for _, row in tail.iterrows()
            ]
        except Exception:
            logger.exception(
                "Prophet forecast error for series %s", series_key,
            )
            return None

    # ------------------------------------------------------------------ #
    # FLAT-LINE FALLBACK                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _flat_forecast(
        as_of_date: date,
        horizon: int,
        last_rate: float,
    ) -> List[Dict[str, Any]]:
        """Return a flat-line forecast when no trained model is available.

        Projects the *last_rate* unchanged for *horizon* months, with a
        fixed ±5 pp confidence band.

        Args:
            as_of_date: Date from which months are counted.
            horizon: Number of future months.
            last_rate: Last known resistance rate.

        Returns:
            List of prediction dicts.
        """
        base = pd.Timestamp(as_of_date)
        predictions: List[Dict[str, Any]] = []
        for i in range(horizon):
            forecast_ts = base + pd.DateOffset(months=i + 1)
            predictions.append(
                {
                    "month": forecast_ts.strftime("%Y-%m"),
                    "predicted_rate": round(float(np.clip(last_rate, 0, 1)), 4),
                    "lower_ci": round(float(np.clip(last_rate - 0.05, 0, 1)), 4),
                    "upper_ci": round(float(np.clip(last_rate + 0.05, 0, 1)), 4),
                }
            )
        return predictions

    # ------------------------------------------------------------------ #
    # LAST-KNOWN RATE                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _last_known_rate(
        df: Optional[pd.DataFrame],
        pathogen: str,
        drug_class: str,
        county: str,
    ) -> float:
        """Extract the most recent resistance rate from historical data.

        Args:
            df: Historical time-series DataFrame (may be ``None``).
            pathogen: Pathogen organism name.
            drug_class: Antimicrobial drug class.
            county: County code.

        Returns:
            Last resistance rate as a float, or 0.0 if unavailable.
        """
        if df is None or df.empty:
            return 0.0

        required = {"pathogen_name", "drug_class", "county_code", "resistance_rate"}
        if not required.issubset(df.columns):
            return 0.0

        mask = (
            (df["pathogen_name"] == pathogen)
            & (df["drug_class"] == drug_class)
            & (df["county_code"] == county)
        )
        subset = df.loc[mask]
        if subset.empty:
            return 0.0

        if "year_month" in subset.columns:
            subset = subset.sort_values("year_month")

        return float(subset["resistance_rate"].iloc[-1])

    # ------------------------------------------------------------------ #
    # TREND CLASSIFICATION                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _classify_trend(current: float, final: float) -> str:
        """Classify the forecast trajectory direction.

        Uses a ±2 pp dead-band around zero change:
        - **increasing**: final > current + 0.02
        - **decreasing**: final < current − 0.02
        - **stable**: otherwise

        Args:
            current: First forecasted resistance rate.
            final: Last forecasted resistance rate.

        Returns:
            One of ``"increasing"``, ``"decreasing"``, ``"stable"``.
        """
        delta = final - current
        if delta > 0.02:
            return "increasing"
        if delta < -0.02:
            return "decreasing"
        return "stable"

    # ------------------------------------------------------------------ #
    # RISK CLASSIFICATION                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _classify_risk(rates: List[float], current_baseline: float) -> str:
        """Classify the clinical risk implied by the forecast trajectory.

        Thresholds (applied against the *maximum* predicted rate and the
        *maximum* increase relative to ``current_baseline``):

        +-----------+--------+--------------+
        | Level     | Rate   | Δ (pp)       |
        +===========+========+==============+
        | Critical  | >0.80  | >0.20        |
        | High      | >0.60  | >0.10        |
        | Medium    | >0.40  | >0.05        |
        | Low       | else   | else         |
        +-----------+--------+--------------+

        Args:
            rates: Sequence of predicted resistance rates.
            current_baseline: Most recent observed (or first forecasted)
                resistance rate, used to compute deltas.

        Returns:
            One of ``"critical"``, ``"high"``, ``"medium"``, ``"low"``.
        """
        if not rates:
            return "low"

        max_rate = max(rates)
        max_increase = max(r - current_baseline for r in rates)

        if max_rate > _cfg.forecast.risk_critical_rate or max_increase > _cfg.forecast.risk_critical_delta:
            return "critical"
        if max_rate > _cfg.forecast.risk_high_rate or max_increase > _cfg.forecast.risk_high_delta:
            return "high"
        if max_rate > _cfg.forecast.risk_medium_rate or max_increase > _cfg.forecast.risk_medium_delta:
            return "medium"
        return "low"

    # ------------------------------------------------------------------ #
    # MODEL PERSISTENCE — SAVE                                            #
    # ------------------------------------------------------------------ #

    def save(self, directory: Union[str, Path]) -> str:
        """Persist the forecaster state (Prophet models + metadata) to disk.

        Creates a single ``.joblib`` artefact containing:
        - all fitted Prophet models,
        - the ensemble weight,
        - the forecast horizon,
        - the model version tag,
        - per-series validation MAPE scores.

        Args:
            directory: Destination directory.  Created if it does not
                exist.

        Returns:
            Absolute path to the saved artefact file.
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        artefact = {
            "prophet_models": self.prophet_models,
            "prophet_weight": self.prophet_weight,
            "horizon_months": self.horizon_months,
            "model_version": self.model_version,
            "validation_mape": self.validation_mape,
        }

        filename = f"forecaster_{self.model_version}.joblib"
        save_path = path / filename
        joblib.dump(artefact, save_path)

        logger.info("Forecaster saved to %s", save_path)
        return str(save_path)

    # ------------------------------------------------------------------ #
    # MODEL PERSISTENCE — LOAD                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "ResistanceForecaster":
        """Restore a :class:`ResistanceForecaster` from a saved artefact.

        Args:
            filepath: Path to the ``.joblib`` file produced by
                :meth:`save`.

        Returns:
            Fully reconstituted :class:`ResistanceForecaster` instance.

        Raises:
            FileNotFoundError: When *filepath* does not exist.
            joblib.externals.loky.process_executor.TerminatedWorkerError:
                If the artefact file is corrupted.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(
                f"Forecaster artefact not found: {filepath}"
            )

        artefact = joblib.load(filepath)

        forecaster = cls(
            horizon_months=artefact.get("horizon_months", 3),
            prophet_weight=artefact.get("prophet_weight", 1.0),
        )
        forecaster.prophet_models = artefact.get("prophet_models", {})
        forecaster.model_version = artefact.get("model_version", "")
        forecaster.validation_mape = artefact.get("validation_mape", {})

        logger.info("Forecaster loaded from %s", filepath)
        return forecaster


def forecast_trend_weekly(
    db_session,
    pathogen_code: Optional[str] = None,
    county: Optional[str] = None,
    sector: Optional[str] = None,
    antibiotic_class: Optional[str] = None,
    months: int = 6
) -> dict:
    """
    Weekly Prophet forecasting logic extracted from Lowell's backend and adapted for schema v2.0.
    Fits a Prophet model on weekly aggregated resistance rates and returns historical vs forecasted trends.
    """
    from backend.src.models.entities import AMRRecord
    import pandas as pd
    from datetime import datetime, date, timedelta

    # Query the database for records matching the filters
    query = db_session.query(AMRRecord.timestamp, AMRRecord.result_value)
    if pathogen_code:
        query = query.filter(AMRRecord.pathogen_code == pathogen_code)
    if county:
        query = query.filter(AMRRecord.county == county)
    if sector:
        query = query.filter(AMRRecord.sector == sector)
    if antibiotic_class:
        query = query.filter(AMRRecord.antimicrobial_agent == antibiotic_class)

    df = pd.read_sql(query.statement, db_session.bind)
    if df.empty:
        return {"error": "Insufficient data for forecast"}

    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    # Map resistant status to 1, others to 0
    df['mdr_flag'] = (df['result_value'].str.lower() == 'resistant').astype(int)

    # Group by date and aggregate total vs resistant cases
    weekly = df.groupby('date').agg(total=('mdr_flag', 'count'), resistant=('mdr_flag', 'sum')).reset_index()
    weekly['rate'] = weekly['resistant'] / weekly['total']
    
    # Filter dates with at least some minimal cases to prevent noise
    weekly = weekly[weekly['total'] >= 5]
    if len(weekly) < 4:
        # Fallback to lower threshold if data is sparse
        weekly = df.groupby('date').agg(total=('mdr_flag', 'count'), resistant=('mdr_flag', 'sum')).reset_index()
        weekly['rate'] = weekly['resistant'] / weekly['total']
        if len(weekly) < 4:
            return {"error": "Insufficient data points for forecast"}

    prophet_df = weekly[['date', 'rate']].rename(columns={'date': 'ds', 'rate': 'y'})
    
    try:
        from prophet import Prophet
        model = Prophet(interval_width=0.8, seasonality_mode='multiplicative')
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=months * 4, freq='W')
        forecast = model.predict(future)
        
        result = {
            "historical": [{"ds": r['date'].isoformat() if hasattr(r['date'], 'isoformat') else str(r['date']), "y": float(r['rate'])} for _, r in weekly.iterrows()],
            "forecast": [{"ds": r['ds'].date().isoformat() if hasattr(r['ds'], 'date') else str(r['ds']), "yhat": float(r['yhat']), "yhat_lower": float(r['yhat_lower']), "yhat_upper": float(r['yhat_upper'])} for _, r in forecast.iterrows()]
        }
    except Exception as e:
        logger.error("Prophet forecasting failed: %s", e)
        # Graceful flat fallback forecast if Prophet training fails
        last_rate = float(weekly['rate'].iloc[-1]) if not weekly.empty else 0.0
        historical = [{"ds": r['date'].isoformat() if hasattr(r['date'], 'isoformat') else str(r['date']), "y": float(r['rate'])} for _, r in weekly.iterrows()]
        forecast_points = []
        last_date = weekly['date'].iloc[-1] if not weekly.empty else date.today()
        for i in range(months * 4):
            fut_date = last_date + timedelta(weeks=i+1)
            forecast_points.append({
                "ds": fut_date.isoformat() if hasattr(fut_date, 'isoformat') else str(fut_date),
                "yhat": last_rate,
                "yhat_lower": max(0.0, last_rate - 0.1),
                "yhat_upper": min(1.0, last_rate + 0.1)
            })
        result = {
            "historical": historical,
            "forecast": forecast_points
        }
        
    return result

