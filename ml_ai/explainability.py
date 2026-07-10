"""
ml_ai/explainability.py — SHAP Explainability Engine
======================================================
Every prediction in AMR-Nexus MUST be explainable — this is NON-NEGOTIABLE.

This module wraps SHAP (SHapley Additive exPlanations) to provide:
    1. Per-anomaly feature attribution (which features drove the score)
    2. Human-readable explanations in plain language
    3. Force plot data for dashboard rendering
    4. Monthly model monitoring SHAP summaries
    5. Feature name mapping: technical → clinician-friendly labels

Design:
    - TreeExplainer for XGBoost (exact, fast — O(TLD²))
    - KernelExplainer fallback for any model (approximate, slower)
    - Graceful degradation when SHAP is not installed
    - Background dataset management via k-means summarization
    - Designed for unreliable, low-resource East African infrastructure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from ml_ai.config import get_ml_config

# ---------------------------------------------------------------------------
# Conditional SHAP import — graceful degradation
# ---------------------------------------------------------------------------

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

# ---------------------------------------------------------------------------
# KENYA_COUNTIES import — self-contained fallback
# ---------------------------------------------------------------------------

try:
    from ml_ai.feature_engineering import KENYA_COUNTIES
except ImportError:
    # Fallback: all 47 Kenyan counties keyed by 3-digit code
    KENYA_COUNTIES: dict[str, str] = {
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


# ============================================================================
# FEATURE NAME MAPPING — Technical → Clinician-Friendly
# ============================================================================

FEATURE_NAME_MAP: dict[str, str] = {
    # Resistance rates
    "resistance_rate": "Current resistance rate",
    "resistance_rate_rolling_3m": "3-month average resistance rate",
    "resistance_rate_rolling_6m": "6-month average resistance rate",
    "resistance_rate_rolling_12m": "12-month average resistance rate",
    # Counts
    "total_tests": "Total tests performed",
    "resistant_count": "Resistant isolate count",
    # MDR
    "mdr_prevalence_county": "County MDR prevalence",
    "mdr_count": "MDR case count",
    "total_records": "Total surveillance records",
    # Reporting lag
    "reporting_lag_mean": "Average reporting delay (days)",
    "reporting_lag_median": "Median reporting delay (days)",
    "reporting_lag_p95": "95th percentile reporting delay (days)",
    # Seasonal
    "month_of_year": "Month of year",
    "quarter": "Quarter",
    "month_sin": "Seasonal cycle (sin)",
    "month_cos": "Seasonal cycle (cos)",
    # Cross-sector (One Health)
    "resistance_rate_human_sector": "Human sector resistance rate",
    "resistance_rate_animal_sector": "Animal sector resistance rate",
    "resistance_rate_environment_sector": "Environmental sector resistance rate",
    # Geographic
    "neighbor_resistance_mean": "Neighboring counties avg resistance",
    "neighbor_county_count": "Number of neighboring counties with data",
    # Rate of change
    "resistance_rate_delta_1m": "Month-over-month resistance change",
    "resistance_rate_pct_change_1m": "Month-over-month % change",
    # Prescribing-pressure proxy (aggregated from per-record
    # prior_antibiotic_exposure; NOT true pharmacy dispensing volume —
    # see _generate_plain_language docstring for the caveat).
    "prior_antibiotic_exposure_rate": "Recent antibiotic exposure rate",
}


# ============================================================================
# EXPLANATION DATA CLASSES
# ============================================================================


@dataclass
class FeatureContribution:
    """A single feature's contribution to the prediction.

    Attributes:
        feature_name: Technical column name (e.g. ``resistance_rate``).
        display_name: Human-readable label shown to clinicians.
        shap_value: SHAP contribution value for this feature.
        feature_value: Actual value of the feature for the explained row.
        context: Plain-language string giving context,
                 e.g. ``"Resistance rate: 78%, 6-month baseline: 45%"``.
    """

    feature_name: str
    display_name: str
    shap_value: float
    feature_value: float
    context: str


@dataclass
class AnomalyExplanation:
    """Complete explanation for a single anomaly.

    Attributes:
        anomaly_id: Unique identifier of the anomaly being explained.
        top_features: Ordered list of the most impactful features.
        plain_language_summary: Full English narrative of the anomaly.
        force_plot_data: Serialisable dict for SHAP force-plot rendering.
        base_value: Expected model output (population mean prediction).
        predicted_value: Model's predicted value for this instance.
    """

    anomaly_id: str
    top_features: list[FeatureContribution]
    plain_language_summary: str
    force_plot_data: dict[str, Any]
    base_value: float
    predicted_value: float


# ============================================================================
# EXPLAINABILITY ENGINE
# ============================================================================


class ExplainabilityEngine:
    """SHAP-based explainability for all AMR-Nexus predictions.

    Uses ``TreeExplainer`` for XGBoost models (O(TLD²) exact Shapley
    values) and falls back to ``KernelExplainer`` for any other sklearn-
    compatible model (sampling-based approximation).

    When SHAP is not installed the engine degrades gracefully and
    produces explanations based on raw feature-value ranking — every
    prediction still gets an explanation.

    Attributes:
        model: The trained ML model to explain.
        tree_explainer: SHAP TreeExplainer instance (or ``None``).
        kernel_explainer: SHAP KernelExplainer fallback (or ``None``).
        background_data: Reference samples for KernelExplainer.
        feature_columns: Ordered list of feature column names.
        feature_name_map: Technical → human-readable column mapping.
    """

    # ------------------------------------------------------------------ #
    # INITIALISATION                                                       #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        model: Any = None,
        background_data: pd.DataFrame | np.ndarray | None = None,
        feature_columns: list[str] | None = None,
    ) -> None:
        """Initialise the explainability engine.

        Args:
            model: A trained ML model (XGBoost, sklearn, etc.).
                   If ``None``, SHAP values will not be computed until
                   a model is provided via a later call.
            background_data: Reference dataset used by KernelExplainer
                             for Shapley value approximation.  Not
                             required for TreeExplainer.
            feature_columns: Ordered list of feature column names that
                             the model was trained on.  If ``None``,
                             numeric columns are inferred at explain
                             time.
        """
        self.model = model
        self.tree_explainer: Any = None
        self.kernel_explainer: Any = None
        self.background_data = background_data
        self.feature_columns: list[str] = feature_columns or []
        self.feature_name_map: dict[str, str] = FEATURE_NAME_MAP.copy()

        if model is not None and HAS_SHAP:
            self._init_explainer(model, background_data)

    # ------------------------------------------------------------------ #
    # EXPLAINER BOOTSTRAPPING                                              #
    # ------------------------------------------------------------------ #

    def _init_explainer(
        self,
        model: Any,
        background_data: pd.DataFrame | np.ndarray | None,
    ) -> None:
        """Initialise the appropriate SHAP explainer.

        Strategy:
            1. Try ``TreeExplainer`` first — works natively with
               XGBoost, LightGBM, CatBoost, and scikit-learn tree
               ensembles.
            2. On failure, fall back to ``KernelExplainer`` which
               requires a background (reference) dataset and is
               model-agnostic but slower.

        Args:
            model: Trained model instance.
            background_data: Reference dataset (required only for
                             KernelExplainer fallback).
        """
        try:
            self.tree_explainer = shap.TreeExplainer(model)
            logger.info("TreeExplainer initialised successfully.")
        except Exception:
            logger.info(
                "TreeExplainer failed; attempting KernelExplainer fallback."
            )
            if background_data is not None:
                bg = self._prepare_background(background_data)
                try:
                    predict_fn = (
                        model.predict_proba
                        if hasattr(model, "predict_proba")
                        else model.predict
                    )
                    self.kernel_explainer = shap.KernelExplainer(predict_fn, bg)
                    logger.info("KernelExplainer initialised successfully.")
                except Exception as exc:
                    logger.error(
                        "Both TreeExplainer and KernelExplainer failed: %s",
                        exc,
                    )
            else:
                logger.warning(
                    "No background data supplied; KernelExplainer cannot "
                    "be initialised.  Explanations will use fallback mode."
                )

    def _prepare_background(
        self, data: pd.DataFrame | np.ndarray
    ) -> np.ndarray:
        """Prepare a background dataset for KernelExplainer.

        Uses k-means summarisation (via ``shap.kmeans``) to reduce a
        large training set to a representative subset.  Falls back to
        random sampling if k-means fails.

        Args:
            data: Full training data (DataFrame or ndarray).

        Returns:
            Reduced background dataset as a numpy array (or shap
            ``DenseData`` object).
        """
        max_samples: int = _cfg.explainability.shap_background_samples

        if isinstance(data, pd.DataFrame):
            data = data.values

        if len(data) <= max_samples:
            return data

        # Prefer shap.kmeans for a statistically representative summary
        if HAS_SHAP:
            try:
                return shap.kmeans(data, max_samples)
            except Exception:
                logger.warning(
                    "shap.kmeans failed; falling back to random sampling."
                )

        indices = np.random.choice(len(data), max_samples, replace=False)
        return data[indices]

    # ================================================================== #
    # PER-ANOMALY EXPLANATION                                              #
    # ================================================================== #

    def explain_anomaly(
        self,
        anomaly_result: Any,
        feature_df: pd.DataFrame,
        row_index: int = 0,
    ) -> dict[str, Any]:
        """Generate a full SHAP explanation for a single anomaly.

        This is the primary public method.  It returns a dict that is
        directly serialisable to JSON and suitable for API responses and
        dashboard rendering.

        Args:
            anomaly_result: An anomaly result object / dataclass with
                            attributes such as ``score``, ``pathogen``,
                            ``drug_class``, ``county``,
                            ``resistance_rate``, ``baseline_rate``.
            feature_df: Feature DataFrame containing the anomaly row.
            row_index: Row index within *feature_df* for this anomaly.

        Returns:
            Dict with keys:
                - ``top_features`` — Top contributing features (list).
                - ``force_plot_data`` — Data for SHAP force plot.
                - ``plain_language_summary`` — English explanation.
                - ``base_value`` — Expected model output.
                - ``predicted_value`` — Model's prediction for this row.
        """
        if not HAS_SHAP or (
            self.tree_explainer is None and self.kernel_explainer is None
        ):
            return self._fallback_explanation(
                anomaly_result, feature_df, row_index
            )

        feature_cols = self.feature_columns or [
            c
            for c in feature_df.select_dtypes(include=[np.number]).columns
            if c not in {"year_month"}
        ]

        try:
            X = feature_df[feature_cols].values.astype(np.float64)
        except (KeyError, ValueError) as exc:
            logger.warning(
                "Feature extraction failed (%s); using fallback.", exc
            )
            return self._fallback_explanation(
                anomaly_result, feature_df, row_index
            )

        instance = X[row_index : row_index + 1]

        # Compute SHAP values
        shap_values = self._compute_shap_values(instance)
        if shap_values is None:
            return self._fallback_explanation(
                anomaly_result, feature_df, row_index
            )

        # Handle multi-output (binary classifier → take class-1 values).
        # Some SHAP versions return a list of per-class arrays; others
        # return a single 3D array shaped (n_samples, n_features, n_classes).
        if isinstance(shap_values, list):
            shap_vals = (
                shap_values[1][0]
                if len(shap_values) > 1
                else shap_values[0][0]
            )
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # (n_samples, n_features, n_classes) — take positive class, row 0
            shap_vals = shap_values[0, :, 1]
        elif shap_values.ndim > 1:
            shap_vals = shap_values[0]
        else:
            shap_vals = shap_values

        base_value = self._get_base_value()

        # Build ordered feature contributions
        contributions = self._build_contributions(
            shap_vals, feature_cols, instance[0], feature_df.iloc[row_index]
        )

        # Sort by absolute SHAP value and take the top N
        top_n: int = _cfg.explainability.top_features_count
        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)
        top_contributions = contributions[:top_n]

        # Generate plain-language summary
        summary = self._generate_plain_language(
            anomaly_result, top_contributions, feature_df.iloc[row_index]
        )

        # Assemble force-plot payload
        predicted_value = float(
            anomaly_result.score
            if hasattr(anomaly_result, "score")
            else 0.0
        )
        force_data: dict[str, Any] = {
            "base_value": float(base_value),
            "predicted_value": predicted_value,
            "features": [
                {
                    "name": c.display_name,
                    "value": round(c.feature_value, 4),
                    "shap_value": round(c.shap_value, 4),
                    "direction": (
                        "positive" if c.shap_value > 0 else "negative"
                    ),
                }
                for c in contributions
            ],
        }

        return {
            "top_features": [
                {
                    "feature": c.display_name,
                    "value": round(c.feature_value, 4),
                    "contribution": round(c.shap_value, 4),
                    "context": c.context,
                }
                for c in top_contributions
            ],
            "force_plot_data": force_data,
            "plain_language_summary": summary,
            "base_value": float(base_value),
            "predicted_value": predicted_value,
        }

    # ------------------------------------------------------------------ #
    # SHAP COMPUTATION HELPERS                                             #
    # ------------------------------------------------------------------ #

    def _compute_shap_values(
        self, instance: np.ndarray
    ) -> np.ndarray | list | None:
        """Compute SHAP values using the best available explainer.

        Args:
            instance: A 2-D array of shape ``(1, n_features)``.

        Returns:
            SHAP values array, a list of arrays (multi-class), or
            ``None`` if computation fails.
        """
        try:
            if self.tree_explainer is not None:
                return self.tree_explainer.shap_values(instance)
            if self.kernel_explainer is not None:
                return self.kernel_explainer.shap_values(
                    instance, nsamples=100
                )
        except Exception as exc:
            logger.warning("SHAP value computation failed: %s", exc)
        return None

    def _get_base_value(self) -> float:
        """Retrieve the SHAP base value (expected model output).

        The base value represents the average prediction over the
        background dataset; individual SHAP values are additive
        departures from this baseline.

        Returns:
            Base value as a float.  Defaults to ``0.5`` if unavailable.
        """
        try:
            explainer = self.tree_explainer or self.kernel_explainer
            if explainer is not None:
                bv = explainer.expected_value
                if isinstance(bv, (list, np.ndarray)):
                    return (
                        float(bv[1]) if len(bv) > 1 else float(bv[0])
                    )
                return float(bv)
        except Exception:
            logger.debug("Could not retrieve SHAP base value; using 0.5.")
        return 0.5

    # ------------------------------------------------------------------ #
    # CONTRIBUTION BUILDING                                                #
    # ------------------------------------------------------------------ #

    def _build_contributions(
        self,
        shap_vals: np.ndarray,
        feature_cols: list[str],
        feature_values: np.ndarray,
        row: pd.Series,
    ) -> list[FeatureContribution]:
        """Build a list of ``FeatureContribution`` from SHAP values.

        Args:
            shap_vals: 1-D array of SHAP values (one per feature).
            feature_cols: Ordered feature column names.
            feature_values: 1-D array of raw feature values.
            row: Full pandas row (may contain extra metadata columns
                 used for context generation).

        Returns:
            List of ``FeatureContribution`` objects.
        """
        contributions: list[FeatureContribution] = []

        for i, col in enumerate(feature_cols):
            if i >= len(shap_vals):
                break

            display_name = self.feature_name_map.get(
                col, col.replace("_", " ").title()
            )
            feat_val = float(feature_values[i])
            shap_val = float(shap_vals[i])

            context = self._generate_feature_context(col, feat_val, row)

            contributions.append(
                FeatureContribution(
                    feature_name=col,
                    display_name=display_name,
                    shap_value=shap_val,
                    feature_value=feat_val,
                    context=context,
                )
            )

        return contributions

    # ------------------------------------------------------------------ #
    # CONTEXT & LANGUAGE GENERATION                                        #
    # ------------------------------------------------------------------ #

    def _generate_feature_context(
        self, col: str, value: float, row: pd.Series
    ) -> str:
        """Generate a human-readable context string for a feature.

        Depending on the feature type this produces strings like:
            - ``"Resistance rate: 78%, 6-month baseline: 45%"``
            - ``"Reporting delay: 12.3 days"``
            - ``"Count: 423"``

        Args:
            col: Technical column name.
            value: Feature value for the row being explained.
            row: Full pandas row for cross-referencing related columns.

        Returns:
            Context string suitable for clinician-facing display.
        """
        # Resistance rate (but not deltas / pct changes)
        if "resistance_rate" in col and "delta" not in col and "pct" not in col:
            baseline_col = "resistance_rate_rolling_6m"
            baseline = (
                float(row.get(baseline_col, 0))
                if baseline_col in row.index
                else 0.0
            )
            return (
                f"Resistance rate: {value:.0%}, "
                f"6-month baseline: {baseline:.0%}"
            )

        if "mdr_prevalence" in col:
            return f"MDR prevalence: {value:.1%}"

        if "reporting_lag" in col:
            return f"Reporting delay: {value:.1f} days"

        if "delta" in col or "pct_change" in col:
            direction = "increase" if value > 0 else "decrease"
            return f"Month-over-month {direction}: {abs(value):.1%}"

        if "neighbor_resistance" in col:
            return f"Neighboring county average: {value:.0%}"

        if col == "prior_antibiotic_exposure_rate":
            return f"Recent antibiotic exposure rate: {value:.0%}"

        if col in {
            "total_tests",
            "resistant_count",
            "mdr_count",
            "total_records",
        }:
            return f"Count: {int(value)}"

        if col in {"month_of_year", "quarter"}:
            return f"Value: {int(value)}"

        if col in {"month_sin", "month_cos"}:
            return f"Seasonal component: {value:.4f}"

        return f"Value: {value:.4f}"

    def _generate_plain_language(
        self,
        anomaly_result: Any,
        top_contributions: list[FeatureContribution],
        row: pd.Series,
    ) -> str:
        """Generate a full plain-language summary of an anomaly.

        Example output::

            "Flagged because Ciprofloxacin resistance in E. coli rose
             to 78% in Kiambu county, 33% above the 6-month baseline,
             coinciding with elevated recent antibiotic exposure (61%).
             Key drivers: Current resistance rate (↑), Month-over-month
             resistance change (↑), Neighboring counties avg
             resistance (↑)."

        Trend-direction fix (2026-07):
            The opening clause used to hardcode "rose to {rate}%"
            regardless of whether the rate had actually increased. When
            ``current_rate`` was roughly equal to (or even below)
            ``baseline_rate``, this produced self-contradictory output
            like "rose to 100%... 0% below the 6-month baseline." The
            opening verb is now derived from the same ``diff`` used for
            the baseline clause, so the two can never disagree:
                - meaningful rise  (diff >  0.5 pts) -> "rose to"
                - meaningful drop  (diff < -0.5 pts) -> "fell to"
                - negligible change                  -> "remained at"
                - no baseline available               -> "was recorded at"

        Concept-note alignment note (corroborating-signal clause):
            The original concept note's example sentence ("...with
            concurrent high carbapenem prescription volumes") implies
            real pharmacy/dispensing data. This dataset does not contain
            that — the closest honest signal actually collected is the
            per-record ``prior_antibiotic_exposure`` flag. Aggregated per
            pathogen+drug+county bucket into
            ``prior_antibiotic_exposure_rate`` (a proxy for prescribing
            pressure, NOT a measurement of it), this clause reads that
            column from the feature row if present. The column does not
            exist yet — ``ml_ai/feature_engineering.py`` still needs a
            groupby-mean of ``prior_antibiotic_exposure`` per
            pathogen+drug+county(+month) bucket to populate it. Until
            that upstream work is done, this clause silently omits
            itself (see ``row.index`` check below) — no fabricated
            numbers, and it "lights up" automatically the moment that
            feature is added upstream.

        Args:
            anomaly_result: Anomaly result object with metadata attrs.
            top_contributions: Top-N feature contributions by |SHAP|.
            row: Full feature row for the anomaly.

        Returns:
            Human-readable summary string.
        """
        pathogen = getattr(anomaly_result, "pathogen", "Unknown pathogen")
        drug_class = getattr(anomaly_result, "drug_class", "Unknown drug")
        county_code = getattr(anomaly_result, "county", "Unknown")
        sub_county = getattr(anomaly_result, "sub_county", "")

        current_rate = getattr(anomaly_result, "resistance_rate", 0.0)
        baseline_rate = getattr(anomaly_result, "baseline_rate", 0.0)

        county_name = KENYA_COUNTIES.get(county_code, county_code)
        # sub_county is a genuine data gap for this source dataset, not just a
        # missing value — suppress "Unknown" (and blank) rather than printing
        # "Unknown, Kisumu".
        has_sub_county = bool(sub_county) and sub_county.strip().lower() not in ("", "unknown")
        location = (
            f"{sub_county}, {county_name}" if has_sub_county else county_name
        )

        # Direction-aware opening clause + baseline comparison. Both derive
        # from the same `diff`, so they can never contradict each other.
        if baseline_rate > 0:
            diff = current_rate - baseline_rate
            if diff > 0.005:       # meaningful rise (>0.5 pts)
                trend_verb, baseline_clause = "rose to", f", {diff:.0%} above the 6-month baseline"
            elif diff < -0.005:    # meaningful drop
                trend_verb, baseline_clause = "fell to", f", {abs(diff):.0%} below the 6-month baseline"
            else:                  # no meaningful change from baseline
                trend_verb, baseline_clause = "remained at", ""
        else:
            trend_verb, baseline_clause = "was recorded at", ""

        parts = [
            f"Flagged because {drug_class} resistance in {pathogen} "
            f"{trend_verb} {current_rate:.0%} in {location}{baseline_clause}"
        ]

        # Corroborating signal — honest proxy for prescribing pressure.
        # Only fires when the upstream feature actually exists in the row;
        # silently omitted otherwise (see docstring above for the caveat
        # on why this is a proxy, not a fabricated "prescription volume").
        exposure_col = "prior_antibiotic_exposure_rate"
        if exposure_col in row.index:
            exposure_rate = row.get(exposure_col)
            try:
                exposure_rate = float(exposure_rate)
            except (TypeError, ValueError):
                exposure_rate = None
            if (
                exposure_rate is not None
                and not pd.isna(exposure_rate)
                and exposure_rate >= 0.5
            ):
                parts.append(
                    f", coinciding with elevated recent antibiotic exposure "
                    f"({exposure_rate:.0%})"
                )

        # Key drivers
        #if top_contributions:
        #   parts.append(". Key drivers: ")
        #    factor_strs: list[str] = []
        #   for contrib in top_contributions:
        #       arrow = "↑" if contrib.shap_value > 0 else "↓"
        #       factor_strs.append(f"{contrib.display_name} ({arrow})")
        #   parts.append(", ".join(factor_strs))

        return "".join(parts) + "."

    # ================================================================== #
    # FALLBACK EXPLANATION (NO SHAP)                                       #
    # ================================================================== #

    def _fallback_explanation(
        self,
        anomaly_result: Any,
        feature_df: pd.DataFrame,
        row_index: int,
    ) -> dict[str, Any]:
        """Generate a feature-importance explanation when SHAP is unavailable.

        Falls back to ranking features by their absolute normalised
        value — this guarantees that every anomaly still ships with an
        explanation even when the SHAP library is missing or fails.

        Args:
            anomaly_result: Anomaly result object with metadata attrs.
            feature_df: Feature DataFrame containing the anomaly row.
            row_index: Row index within *feature_df*.

        Returns:
            Dict with the same schema as ``explain_anomaly``.
        """
        logger.info(
            "Using fallback (non-SHAP) explanation for row %d.", row_index
        )

        row = feature_df.iloc[row_index]
        feature_cols = [
            c
            for c in feature_df.select_dtypes(include=[np.number]).columns
            if c not in {"year_month"}
        ]

        # Rank by absolute value (a rough proxy for importance)
        values: dict[str, float] = {
            col: abs(float(row.get(col, 0))) for col in feature_cols
        }
        sorted_features = sorted(
            values.items(), key=lambda x: x[1], reverse=True
        )[: _cfg.explainability.top_features_count]

        top_features: list[dict[str, Any]] = []
        for col, val in sorted_features:
            display = self.feature_name_map.get(
                col, col.replace("_", " ").title()
            )
            raw_val = float(row.get(col, 0))
            context = self._generate_feature_context(col, raw_val, row)
            top_features.append(
                {
                    "feature": display,
                    "value": round(raw_val, 4),
                    "contribution": round(val, 4),
                    "context": context,
                }
            )

        pathogen = getattr(anomaly_result, "pathogen", "Unknown")
        drug_class = getattr(anomaly_result, "drug_class", "Unknown")
        county_code = getattr(anomaly_result, "county", "")
        county_name = KENYA_COUNTIES.get(county_code, county_code)
        current_rate = getattr(anomaly_result, "resistance_rate", 0.0)
        predicted_value = float(getattr(anomaly_result, "score", 0.0))

        summary = (
            f"Anomaly detected: {drug_class} resistance in {pathogen} "
            f"at {current_rate:.0%} in {county_name}. "
            f"Top factors: {', '.join(f['feature'] for f in top_features)}."
        )

        return {
            "top_features": top_features,
            "force_plot_data": {
                "base_value": 0.5,
                "predicted_value": predicted_value,
                "features": top_features,
            },
            "plain_language_summary": summary,
            "base_value": 0.5,
            "predicted_value": predicted_value,
        }

    # ================================================================== #
    # MODEL MONITORING — GLOBAL SHAP SUMMARY                               #
    # ================================================================== #

    def generate_shap_summary(
        self,
        model: Any,
        feature_df: pd.DataFrame,
    ) -> dict[str, Any]:
        """Generate a global SHAP summary for model monitoring.

        Computes mean |SHAP| values across a sample of the dataset to
        quantify global feature importance.  Useful for drift detection,
        monthly reports, and audit trails.

        Args:
            model: Trained model (XGBoost, sklearn, etc.).
            feature_df: Feature DataFrame (all available records).

        Returns:
            Dict containing:
                - ``generated_at``: ISO timestamp.
                - ``n_samples``: Number of samples evaluated.
                - ``n_features``: Number of features.
                - ``feature_importance``: Ranked list of dicts with
                  ``feature``, ``display_name``, ``mean_abs_shap``,
                  ``rank``.
                - ``top_feature``: Display name of the most important
                  feature.
        """
        if not HAS_SHAP:
            logger.warning(
                "SHAP is not installed; cannot generate SHAP summary."
            )
            return {"error": "SHAP not installed", "feature_importance": []}

        feature_cols = self.feature_columns or [
            c
            for c in feature_df.select_dtypes(include=[np.number]).columns
            if c not in {"year_month"}
        ]

        try:
            X = feature_df[feature_cols].values.astype(np.float64)
        except (KeyError, ValueError) as exc:
            logger.error("Feature extraction for SHAP summary failed: %s", exc)
            return {"error": str(exc), "feature_importance": []}

        # Cap the number of samples for performance on low-resource infra
        max_samples = min(len(X), 500)
        if len(X) > max_samples:
            indices = np.random.choice(len(X), max_samples, replace=False)
            X = X[indices]

        # Initialise a fresh explainer for the provided model
        try:
            explainer = shap.TreeExplainer(model)
            logger.info("SHAP summary: using TreeExplainer.")
        except Exception:
            logger.info("SHAP summary: falling back to KernelExplainer.")
            bg = self._prepare_background(X)
            predict_fn = (
                model.predict_proba
                if hasattr(model, "predict_proba")
                else model.predict
            )
            try:
                explainer = shap.KernelExplainer(predict_fn, bg)
            except Exception as exc:
                logger.error("KernelExplainer init failed for summary: %s", exc)
                return {"error": str(exc), "feature_importance": []}

        try:
            shap_values = explainer.shap_values(X)
        except Exception as exc:
            logger.error("SHAP summary computation failed: %s", exc)
            return {"error": str(exc), "feature_importance": []}

        # Handle multi-class output (take class-1 for binary)
        if isinstance(shap_values, list):
            sv = (
                shap_values[1]
                if len(shap_values) > 1
                else shap_values[0]
            )
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # (n_samples, n_features, n_classes) — take positive class
            sv = shap_values[:, :, 1]
        else:
            sv = shap_values

        # Mean |SHAP| per feature
        mean_abs_shap = np.abs(sv).mean(axis=0)

        importance: list[dict[str, Any]] = []
        for i, col in enumerate(feature_cols):
            if i >= len(mean_abs_shap):
                break
            display = self.feature_name_map.get(
                col, col.replace("_", " ").title()
            )
            importance.append(
                {
                    "feature": col,
                    "display_name": display,
                    "mean_abs_shap": round(float(mean_abs_shap[i]), 6),
                    "rank": 0,  # assigned below after sorting
                }
            )

        # Sort descending by importance and assign ranks
        importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        for rank, item in enumerate(importance, 1):
            item["rank"] = rank

        max_display: int = _cfg.explainability.shap_max_display
        top_feature = importance[0]["display_name"] if importance else "N/A"

        summary: dict[str, Any] = {
            "generated_at": pd.Timestamp.now().isoformat(),
            "n_samples": max_samples,
            "n_features": len(feature_cols),
            "feature_importance": importance[:max_display],
            "top_feature": top_feature,
        }

        logger.info(
            "SHAP summary generated — top feature: %s, %d features ranked.",
            top_feature,
            len(importance),
        )
        return summary

    # ================================================================== #
    # FEATURE NAME MANAGEMENT                                              #
    # ================================================================== #

    def add_feature_mapping(self, technical: str, display: str) -> None:
        """Add or update a feature name mapping at runtime.

        Args:
            technical: Technical column name (e.g. ``"mic_value"``).
            display: Human-readable label (e.g. ``"MIC value (µg/mL)"``).
        """
        self.feature_name_map[technical] = display
        logger.debug(
            "Feature mapping added/updated: %s → %s", technical, display
        )

    def get_display_name(self, technical: str) -> str:
        """Look up the clinician-friendly display name for a feature.

        If no explicit mapping exists, the column name is title-cased
        with underscores replaced by spaces.

        Args:
            technical: Technical column name.

        Returns:
            Human-readable display name.
        """
        return self.feature_name_map.get(
            technical, technical.replace("_", " ").title()
        )