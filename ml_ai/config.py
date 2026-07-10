"""
ml_ai/config.py — ML Pipeline Configuration
==============================================
Central configuration for all ML models, thresholds, and experiment
tracking parameters. All values are tunable per deployment environment.

This module is the SINGLE SOURCE OF TRUTH for hyperparameters,
threshold values, and infrastructure settings used across the
anomaly detection, forecasting, and explainability engines.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AnomalyConfig:
    """Anomaly detection engine configuration."""

    # ── Ensemble weights ──────────────────────────────────────────────
    xgb_weight: float = 0.6
    iforest_weight: float = 0.4

    # ── Thresholds ────────────────────────────────────────────────────
    anomaly_threshold: float = 0.65
    data_quality_min: float = 0.7      # Minimum quality score for ML

    # ── Isolation Forest ──────────────────────────────────────────────
    iforest_contamination: float = 0.05
    iforest_n_estimators: int = 200
    iforest_max_samples: str = "auto"

    # ── XGBoost ───────────────────────────────────────────────────────
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.1
    xgb_n_estimators: int = 200
    xgb_subsample: float = 0.8
    xgb_colsample_bytree: float = 0.8

    # ── Optuna ────────────────────────────────────────────────────────
    optuna_n_trials: int = 50
    optuna_cv_folds: int = 5

    # ── PSI Drift ─────────────────────────────────────────────────────
    drift_psi_threshold: float = 0.2
    drift_psi_n_bins: int = 10


@dataclass(frozen=True)
class ForecastConfig:
    """Forecasting engine configuration."""

    horizon_months: int = 3
    min_series_length: int = 6          # Minimum months for Prophet

    # ── Prophet ───────────────────────────────────────────────────────
    prophet_changepoint_prior: float = 0.05
    prophet_seasonality_mode: str = "additive"
    prophet_yearly_seasonality: bool = True

    # ── Risk Classification Thresholds ────────────────────────────────
    risk_critical_rate: float = 0.80
    risk_critical_delta: float = 0.20   # 20pp increase
    risk_high_rate: float = 0.60
    risk_high_delta: float = 0.10
    risk_medium_rate: float = 0.40
    risk_medium_delta: float = 0.05


@dataclass(frozen=True)
class ExplainabilityConfig:
    """SHAP explainability configuration."""

    shap_background_samples: int = 100
    shap_max_display: int = 20
    top_features_count: int = 3


@dataclass(frozen=True)
class MLflowConfig:
    """MLflow experiment tracking configuration."""

    tracking_uri: str = field(
        default_factory=lambda: os.environ.get(
            "MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"
        )
    )
    experiment_name: str = "amr-nexus-anomaly-detection"
    registered_model_name: str = "amr-nexus-anomaly-detector"
    artifact_location: str = field(
        default_factory=lambda: os.environ.get(
            "MLFLOW_ARTIFACT_ROOT", "mlruns/artifacts"
        )
    )


@dataclass(frozen=True)
class SyntheticConfig:
    """Synthetic data generation configuration."""

    default_n_records: int = 50_000
    genomics_prevalence: float = 0.10   # 10% of isolates get genomic metadata
    genomics_prevalence_min: float = 0.05
    genomics_prevalence_max: float = 0.15
    incomplete_reporting_rate: float = 0.15
    outbreak_probability: float = 0.02  # Per-record outbreak spike probability
    seed: int = 42


@dataclass(frozen=True)
class MLConfig:
    """
    Master ML configuration — aggregates all sub-configs.

    Usage:
        from ml_ai.config import get_ml_config
        cfg = get_ml_config()
        print(cfg.anomaly.anomaly_threshold)
    """

    anomaly: AnomalyConfig = field(default_factory=AnomalyConfig)
    forecast: ForecastConfig = field(default_factory=ForecastConfig)
    explainability: ExplainabilityConfig = field(default_factory=ExplainabilityConfig)
    mlflow: MLflowConfig = field(default_factory=MLflowConfig)
    synthetic: SyntheticConfig = field(default_factory=SyntheticConfig)

    # ── Paths ─────────────────────────────────────────────────────────
    model_artifacts_dir: str = field(
        default_factory=lambda: os.environ.get(
            "ML_ARTIFACTS_DIR", "ml_artifacts"
        )
    )


# ── Singleton accessor ────────────────────────────────────────────────────
_config: MLConfig | None = None


def get_ml_config() -> MLConfig:
    """Return the global ML configuration singleton."""
    global _config
    if _config is None:
        _config = MLConfig()
    return _config
