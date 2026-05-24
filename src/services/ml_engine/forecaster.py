"""
services/ml_engine/forecaster.py — Component B: Time-Series Trajectory Forecasting

Uses Facebook Prophet to project 24-month antimicrobial resistance trends
by county and pathogen combination. Invoked on-demand via the intelligence API
to avoid blocking ingestion performance.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.entities import AMRRecord, SectorEnum

logger = logging.getLogger(__name__)


class AMRForecaster:
    """
    Component B: Facebook Prophet-based resistance trajectory engine.

    Computes monthly resistance event counts from historical AMRRecord data
    and projects forward 24 months (configurable).
    """

    MINIMUM_DATA_POINTS = 2

    def __init__(self):
        # Prophet is imported lazily to keep startup time fast when not used
        pass

    # ── Data Preparation ──────────────────────────────────────────────────────────

    def prepare_time_series(
        self,
        county: str,
        db: Session,
        pathogen: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Queries AMRRecord and aggregates monthly Resistant isolate counts
        into the Prophet-required {ds, y} format.

        Args:
            county: Target county name (exact match, case-insensitive).
            db: Active SQLAlchemy session.
            pathogen: Optional pathogen filter. If None, aggregates all pathogens.
            sector: Optional sector filter ('human', 'animal', 'environment').

        Returns:
            DataFrame with columns ['ds' (datetime), 'y' (int count)].
            Empty DataFrame if fewer than MINIMUM_DATA_POINTS months of data.
        """
        query = (
            db.query(
                func.date_trunc("month", AMRRecord.timestamp).label("month"),
                func.count(AMRRecord.id).label("resistance_count"),
            )
            .filter(AMRRecord.county.ilike(county))
            .filter(AMRRecord.result_value == "Resistant")
        )

        if pathogen:
            query = query.filter(AMRRecord.pathogen_name.ilike(f"%{pathogen}%"))

        if sector:
            try:
                sector_enum = SectorEnum(sector.lower())
                query = query.filter(AMRRecord.sector == sector_enum)
            except ValueError:
                logger.warning("Invalid sector filter '%s' in forecaster — ignoring.", sector)

        query = query.group_by("month").order_by("month")
        results = query.all()

        if not results:
            logger.info("No resistance records found for county='%s', pathogen='%s'.", county, pathogen)
            return pd.DataFrame(columns=["ds", "y"])

        df = pd.DataFrame(
            [(row.month, int(row.resistance_count)) for row in results],
            columns=["ds", "y"],
        )
        df["ds"] = pd.to_datetime(df["ds"])
        return df

    # ── Forecast Generation ───────────────────────────────────────────────────────

    def generate_forecast(
        self,
        county: str,
        db: Session,
        pathogen: Optional[str] = None,
        sector: Optional[str] = None,
        periods: int = 24,
    ) -> Dict[str, Any]:
        """
        Fits a Prophet model on historical resistance data and returns a
        24-month forward projection as a serializable dict.

        Args:
            county: Target county for the forecast.
            db: Active SQLAlchemy session.
            pathogen: Optional pathogen filter.
            sector: Optional sector filter.
            periods: Number of months to forecast (default: 24).

        Returns:
            Dict with keys:
              - county, pathogen, generated_at, periods, historical_points
              - forecast: list of {ds, yhat, yhat_lower, yhat_upper} dicts
            Returns empty forecast list if insufficient data.
        """
        from prophet import Prophet  # Lazy import to avoid startup overhead

        ts_df = self.prepare_time_series(
            county=county, db=db, pathogen=pathogen, sector=sector
        )

        result_base = {
            "county": county,
            "pathogen": pathogen,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "periods": periods,
            "historical_points": len(ts_df),
            "forecast": [],
        }

        if len(ts_df) < self.MINIMUM_DATA_POINTS:
            logger.info(
                "Insufficient data for forecast: %d point(s) for county='%s'. "
                "Minimum %d required.",
                len(ts_df), county, self.MINIMUM_DATA_POINTS,
            )
            return result_base

        # ── Fit Prophet ─────────────────────────────────────────────────────────
        try:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=0.80,      # 80% confidence interval
                changepoint_prior_scale=0.05,
            )
            model.fit(ts_df)

            future = model.make_future_dataframe(periods=periods, freq="MS")
            forecast_df = model.predict(future)

            # ── Serialize (forward-looking periods only) ───────────────────────
            future_forecast = forecast_df.tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            forecast_list = [
                {
                    "ds": row["ds"].strftime("%Y-%m-%d"),
                    "yhat": round(max(0.0, float(row["yhat"])), 3),
                    "yhat_lower": round(max(0.0, float(row["yhat_lower"])), 3),
                    "yhat_upper": round(max(0.0, float(row["yhat_upper"])), 3),
                }
                for _, row in future_forecast.iterrows()
            ]

            result_base["forecast"] = forecast_list
            logger.info(
                "Forecast generated: county='%s', pathogen='%s', %d months, %d historical points.",
                county, pathogen, periods, len(ts_df),
            )

        except Exception as exc:
            logger.error("Prophet forecast failed for county='%s': %s", county, exc)
            # Return empty forecast rather than raising — API handles gracefully

        return result_base
