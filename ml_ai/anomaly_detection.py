"""
Anomaly Detection Engine
=========================
XGBoost + Isolation Forest ensemble for detecting resistance-rate anomalies
in AMR surveillance data.  Every prediction is explainable via SHAP.

Architecture
------------
- **XGBoost** (supervised): Binary classifier (`is_anomaly`) trained on
  historical anomaly labels *or* synthetic labels derived from statistical
  thresholds (>2σ from rolling mean).
- **Isolation Forest** (unsupervised): Anomaly detector using feature
  isolation depth.
- **Ensemble**: Configurable weighted average of both model scores,
  calibrated to a [0, 1] anomaly probability.

Training Pipeline
-----------------
- Optuna Bayesian hyperparameter optimisation (TPE sampler, configurable
  trial budget).
- 5-fold temporal cross-validation (``TimeSeriesSplit`` — expanding window).
- Temporal train / validate split: first 75 % train, last 25 % validate.
- Metrics: F1, Precision, Recall, AUC-ROC.

Drift Detection
---------------
- Population Stability Index (PSI) computed on inference features against
  the training reference distribution.

Graceful Degradation
--------------------
- If **XGBoost** is not installed, ``sklearn.ensemble.GradientBoostingClassifier``
  is used as a transparent fallback.
- If **Optuna** is not installed, sensible default hyper-parameters are used.
- All fallback decisions are logged at WARNING level.

Design Constraints
------------------
- Targets **Python 3.11** on low-resource East African infrastructure.
- Uses standard ``logging`` (NOT structlog).
- All predictions are explainable via **SHAP** (non-negotiable).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from ml_ai.config import get_ml_config

# ---------------------------------------------------------------------------
# Optional dependency probing
# ---------------------------------------------------------------------------
try:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:  # pragma: no cover
    HAS_OPTUNA = False

try:
    import xgboost as xgb

    HAS_XGBOOST = True
except ImportError:  # pragma: no cover
    HAS_XGBOOST = False

try:
    import shap

    HAS_SHAP = True
except ImportError:  # pragma: no cover
    HAS_SHAP = False

# ---------------------------------------------------------------------------
# Lazy import of FeatureEngineer — only the static helper is used
# ---------------------------------------------------------------------------
try:
    from ml_ai.feature_engineering import FeatureEngineer
except ImportError:  # pragma: no cover
    FeatureEngineer = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# ===========================================================================
# DATA CLASSES
# ===========================================================================


@dataclass
class AnomalyResult:
    """Result from anomaly scoring — one per record.

    Attributes:
        score: Calibrated anomaly probability in [0, 1].
        is_anomaly: ``True`` when *score* ≥ the configured threshold.
        pathogen: Organism name (e.g. ``"Escherichia coli"``).
        drug_class: Antimicrobial drug class tested.
        county: 3-digit Kenya county code (001 – 047).
        sub_county: Sub-county name if available.
        sector: One Health sector — ``human``, ``animal``, or ``environment``.
        contributing_features: SHAP-derived feature contributions
            (list of dicts with keys ``feature``, ``value``, ``contribution``).
        xgb_score: Raw XGBoost anomaly probability.
        iforest_score: Normalised Isolation Forest anomaly score.
        resistance_rate: Current resistance rate for this group.
        baseline_rate: Rolling baseline resistance rate (6-month window).
    """

    score: float
    is_anomaly: bool
    pathogen: str
    drug_class: str
    county: str
    sub_county: str = ""
    sector: str = "human"
    contributing_features: list[dict[str, Any]] = field(default_factory=list)
    xgb_score: float = 0.0
    iforest_score: float = 0.0
    resistance_rate: float = 0.0
    baseline_rate: float = 0.0


@dataclass
class TrainingMetrics:
    """Evaluation metrics captured after model training.

    Attributes:
        f1: F1 score on the validation set.
        precision: Precision on the validation set.
        recall: Recall on the validation set.
        auc_roc: Area Under the ROC Curve on the validation set.
        support: Number of samples in the validation set.
        report: Full ``sklearn.metrics.classification_report`` text.
    """

    f1: float
    precision: float
    recall: float
    auc_roc: float
    support: int
    report: str


# ===========================================================================
# ANOMALY DETECTOR
# ===========================================================================


class AnomalyDetector:
    """Ensemble anomaly detector combining XGBoost and Isolation Forest.

    The detector operates in two modes:

    **Training mode**
        Given a feature ``DataFrame`` with an ``is_anomaly`` label column,
        trains both models and tunes hyper-parameters via Optuna.  If labels
        are absent, synthetic labels are generated using a >2σ statistical
        threshold on resistance rate and its month-over-month delta.

    **Inference mode**
        Given a feature ``DataFrame`` without labels, produces calibrated
        anomaly scores via the weighted ensemble and SHAP explanations.

    Parameters:
        threshold: Score threshold above which a record is flagged as anomalous.
            Defaults to the value in ``MLConfig.anomaly.anomaly_threshold``.
        xgb_weight: Weight assigned to XGBoost in the ensemble.  The Isolation
            Forest receives ``1 − xgb_weight``.

    Attributes:
        xgb_model: Trained XGBoost classifier (or sklearn fallback), or ``None``.
        iforest_model: Trained ``IsolationForest``, or ``None``.
        feature_columns: Ordered list of feature column names used for training.
        training_feature_distribution: Per-feature reference arrays for PSI.
        training_metrics: Metrics from the most recent ``train()`` call.
        model_version: Semantic version string for artefact identification.
    """

    # ------------------------------------------------------------------ #
    # INITIALISATION                                                      #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        threshold: float | None = None,
        xgb_weight: float | None = None,
    ) -> None:
        """Initialise the AnomalyDetector with configurable ensemble weights.

        Args:
            threshold: Anomaly score threshold.  Falls back to
                ``MLConfig.anomaly.anomaly_threshold`` when ``None``.
            xgb_weight: XGBoost weight in [0, 1].  Falls back to
                ``MLConfig.anomaly.xgb_weight`` when ``None``.
        """
        cfg = get_ml_config().anomaly

        self.threshold: float = threshold if threshold is not None else cfg.anomaly_threshold
        self.xgb_weight: float = xgb_weight if xgb_weight is not None else cfg.xgb_weight
        self.iforest_weight: float = 1.0 - self.xgb_weight

        self.xgb_model: Any = None
        self.iforest_model: IsolationForest | None = None
        self.feature_columns: list[str] = []
        self.training_feature_distribution: dict[str, np.ndarray] = {}
        self.training_metrics: TrainingMetrics | None = None
        self.model_version: str = ""
        self._shap_explainer: Any = None

        logger.info(
            "AnomalyDetector initialised — threshold=%.3f  xgb_weight=%.2f  "
            "HAS_XGBOOST=%s  HAS_OPTUNA=%s  HAS_SHAP=%s",
            self.threshold,
            self.xgb_weight,
            HAS_XGBOOST,
            HAS_OPTUNA,
            HAS_SHAP,
        )

    # ------------------------------------------------------------------ #
    # TRAINING                                                            #
    # ------------------------------------------------------------------ #

    def train(
        self,
        feature_df: pd.DataFrame,
        label_col: str = "is_anomaly",
        n_optuna_trials: int = 50,
    ) -> TrainingMetrics:
        """Train both XGBoost and Isolation Forest models.

        If *label_col* is not present in *feature_df*, synthetic anomaly
        labels are generated using statistical thresholds (>2σ from the
        rolling mean).

        Args:
            feature_df: Feature ``DataFrame`` produced by
                ``FeatureEngineer``.
            label_col: Column name containing binary anomaly labels.
            n_optuna_trials: Number of Optuna hyper-parameter trials.

        Returns:
            ``TrainingMetrics`` with evaluation results on the temporal
            validation set.

        Raises:
            ValueError: If *feature_df* is empty or contains no numeric
                feature columns.
        """
        if feature_df.empty:
            raise ValueError("Cannot train on an empty DataFrame.")

        logger.info("Training started — %d records", len(feature_df))

        # Resolve feature columns
        feature_cols = self._resolve_feature_columns(feature_df)
        self.feature_columns = feature_cols
        logger.info(
            "Resolved %d feature columns: %s …",
            len(feature_cols),
            feature_cols[:8],
        )

        if not feature_cols:
            raise ValueError(
                "No numeric feature columns found in the DataFrame.  "
                "Ensure FeatureEngineer has been applied."
            )

        # Generate synthetic labels if absent
        if label_col not in feature_df.columns:
            logger.info("Label column '%s' missing — generating synthetic labels", label_col)
            feature_df = self._generate_synthetic_labels(feature_df, label_col)

        X = feature_df[feature_cols].values.astype(np.float32)
        y = feature_df[label_col].values.astype(int)

        # Store reference distribution for PSI drift checks
        self._store_reference_distribution(X, feature_cols)

        # Temporal split: first 75 % train, last 25 % validate
        split_idx = int(len(X) * 0.75)
        if split_idx == 0 or split_idx >= len(X):
            split_idx = max(1, len(X) - 1)

        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        logger.info(
            "Temporal split — train=%d  validate=%d",
            len(X_train),
            len(X_val),
        )

        # 1.  Train XGBoost (or sklearn fallback)
        self._train_xgboost(X_train, y_train, X_val, y_val, n_optuna_trials)

        # 2.  Train Isolation Forest (unsupervised)
        self._train_isolation_forest(X_train)

        # 3.  Build SHAP explainer for the supervised model
        self._build_shap_explainer(X_train)

        # 4.  Evaluate ensemble on validation set
        metrics = self._evaluate(X_val, y_val)
        self.training_metrics = metrics
        self.model_version = f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        logger.info(
            "Training complete — F1=%.4f  AUC-ROC=%.4f  version=%s",
            metrics.f1,
            metrics.auc_roc,
            self.model_version,
        )
        return metrics

    # ------------------------------------------------------------------ #
    # SYNTHETIC LABEL GENERATION                                          #
    # ------------------------------------------------------------------ #

    def _generate_synthetic_labels(
        self,
        df: pd.DataFrame,
        label_col: str,
    ) -> pd.DataFrame:
        """Generate synthetic anomaly labels using multi-signal statistical thresholds.

        A record is labelled anomalous if ANY of:
        - ``resistance_rate`` > mean + 1.5·std  (high absolute rate)
        - ``resistance_rate_delta_1m`` > mean + 1.5·std  (rapid increase)
        - ``resistance_rate`` in the top 5th percentile of the dataset

        If fewer than 5% of records are labelled, the top-scoring records
        by a composite anomaly score are forcibly labelled to ensure
        XGBoost has a meaningful decision boundary.

        Args:
            df: Feature ``DataFrame``.
            label_col: Target column name to create.

        Returns:
            Copy of *df* with the synthetic label column appended.
        """
        df = df.copy()

        # --- Signal 1: High absolute resistance rate ---
        if "resistance_rate" in df.columns:
            rate = df["resistance_rate"]
            rate_mean = rate.mean()
            rate_std = rate.std() if rate.std() > 0 else 0.1
            rate_anomaly = rate > (rate_mean + 1.5 * rate_std)
        else:
            rate = pd.Series(0.0, index=df.index)
            rate_anomaly = pd.Series(False, index=df.index)

        # --- Signal 2: Rapid month-over-month increase ---
        if "resistance_rate_delta_1m" in df.columns:
            delta = df["resistance_rate_delta_1m"]
            delta_mean = delta.mean()
            delta_std = delta.std() if delta.std() > 0 else 0.05
            delta_anomaly = delta > (delta_mean + 1.5 * delta_std)
        else:
            delta_anomaly = pd.Series(False, index=df.index)

        # --- Signal 3: Top percentile resistance rate ---
        if "resistance_rate" in df.columns:
            top_pct_threshold = df["resistance_rate"].quantile(0.95)
            top_pct_anomaly = df["resistance_rate"] >= top_pct_threshold
        else:
            top_pct_anomaly = pd.Series(False, index=df.index)

        # --- Combine signals ---
        df[label_col] = (rate_anomaly | delta_anomaly | top_pct_anomaly).astype(int)

        # --- Force minimum anomaly rate of 5% ---
        min_anomalies = max(1, int(len(df) * 0.05))
        if df[label_col].sum() < min_anomalies:
            # Build composite anomaly score from available features
            score = pd.Series(0.0, index=df.index)
            if "resistance_rate" in df.columns:
                r = df["resistance_rate"]
                r_std = r.std() if r.std() > 0 else 0.1
                score += (r - r.mean()) / r_std
            if "resistance_rate_delta_1m" in df.columns:
                d = df["resistance_rate_delta_1m"]
                d_std = d.std() if d.std() > 0 else 0.05
                score += (d - d.mean()) / d_std

            # Label the top-scoring records
            top_indices = score.nlargest(min_anomalies).index
            df.loc[top_indices, label_col] = 1
            logger.info(
                "Forced minimum anomaly rate — labelled top %d records as anomalous",
                min_anomalies,
            )

        anomaly_rate = df[label_col].mean()
        logger.info(
            "Synthetic labels — anomaly_rate=%.4f  total=%d  anomalies=%d",
            anomaly_rate,
            len(df),
            int(df[label_col].sum()),
        )
        return df

    # ------------------------------------------------------------------ #
    # XGBOOST TRAINING                                                    #
    # ------------------------------------------------------------------ #

    def _train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_trials: int,
    ) -> None:
        """Train the supervised classifier with optional Optuna HPO.

        Decision tree:
        1. XGBoost available **and** Optuna available → Bayesian HPO.
        2. XGBoost available, Optuna missing → default hyper-parameters.
        3. XGBoost missing → sklearn ``GradientBoostingClassifier`` fallback.

        Args:
            X_train: Training feature matrix.
            y_train: Training labels.
            X_val: Validation feature matrix.
            y_val: Validation labels.
            n_trials: Number of Optuna trials.
        """
        if HAS_XGBOOST and HAS_OPTUNA:
            self._train_xgboost_optuna(X_train, y_train, X_val, y_val, n_trials)
        elif HAS_XGBOOST:
            logger.warning("Optuna not installed — training XGBoost with default hyper-parameters")
            self._train_xgboost_default(X_train, y_train, X_val, y_val)
        else:
            logger.warning(
                "XGBoost not installed — falling back to sklearn GradientBoostingClassifier"
            )
            self._train_sklearn_fallback(X_train, y_train, X_val, y_val)

    def _train_xgboost_optuna(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_trials: int,
    ) -> None:
        """Train XGBoost with Optuna Bayesian hyper-parameter optimisation.

        Uses a TPE sampler with 5-fold ``TimeSeriesSplit`` cross-validation
        inside each trial.  The best trial's parameters are used to fit the
        final model on the full training set.

        Args:
            X_train: Training feature matrix.
            y_train: Training labels.
            X_val: Validation feature matrix.
            y_val: Validation labels.
            n_trials: Number of Optuna trials.
        """
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        scale_pos_weight = n_neg / max(n_pos, 1)

        def objective(trial: "optuna.Trial") -> float:
            """Optuna objective — maximise mean CV F1."""
            params = {
                "objective": "binary:logistic",
                "eval_metric": "logloss",
                "scale_pos_weight": scale_pos_weight,
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
                "verbosity": 0,
                "random_state": 42,
            }

            tscv = TimeSeriesSplit(n_splits=5)
            cv_scores: list[float] = []

            for train_idx, val_idx in tscv.split(X_train):
                X_cv_train, y_cv_train = X_train[train_idx], y_train[train_idx]
                X_cv_val, y_cv_val = X_train[val_idx], y_train[val_idx]

                model = xgb.XGBClassifier(**params, use_label_encoder=False)
                model.fit(
                    X_cv_train,
                    y_cv_train,
                    eval_set=[(X_cv_val, y_cv_val)],
                    verbose=False,
                )
                y_pred = model.predict(X_cv_val)
                cv_scores.append(f1_score(y_cv_val, y_pred, zero_division=0))

            return float(np.mean(cv_scores))

        try:
            study = optuna.create_study(
                direction="maximize",
                sampler=optuna.samplers.TPESampler(seed=42),
            )
            study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

            best_params = study.best_params
            best_params.update(
                {
                    "objective": "binary:logistic",
                    "eval_metric": "logloss",
                    "scale_pos_weight": scale_pos_weight,
                    "verbosity": 0,
                    "random_state": 42,
                }
            )

            self.xgb_model = xgb.XGBClassifier(**best_params, use_label_encoder=False)
            self.xgb_model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
            logger.info(
                "XGBoost trained (Optuna) — best_trial=%d  best_f1=%.4f",
                study.best_trial.number,
                study.best_value,
            )
        except Exception:
            logger.exception("Optuna HPO failed — falling back to default hyper-parameters")
            self._train_xgboost_default(X_train, y_train, X_val, y_val)

    def _train_xgboost_default(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> None:
        """Train XGBoost with sensible default hyper-parameters.

        Used as a fallback when Optuna is unavailable or when the Optuna
        optimisation raises an exception.

        Args:
            X_train: Training feature matrix.
            y_train: Training labels.
            X_val: Validation feature matrix.
            y_val: Validation labels.
        """
        if not HAS_XGBOOST:
            logger.warning("XGBoost unavailable — skipping default XGBoost training")
            self._train_sklearn_fallback(X_train, y_train, X_val, y_val)
            return

        cfg = get_ml_config().anomaly
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        scale_pos_weight = n_neg / max(n_pos, 1)

        try:
            self.xgb_model = xgb.XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                scale_pos_weight=scale_pos_weight,
                max_depth=cfg.xgb_max_depth,
                learning_rate=cfg.xgb_learning_rate,
                n_estimators=cfg.xgb_n_estimators,
                subsample=cfg.xgb_subsample,
                colsample_bytree=cfg.xgb_colsample_bytree,
                random_state=42,
                verbosity=0,
                use_label_encoder=False,
            )
            self.xgb_model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
            logger.info("XGBoost trained with default hyper-parameters")
        except Exception:
            logger.exception("Default XGBoost training failed — falling back to sklearn")
            self._train_sklearn_fallback(X_train, y_train, X_val, y_val)

    def _train_sklearn_fallback(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> None:
        """Train sklearn ``GradientBoostingClassifier`` as XGBoost fallback.

        Provides identical ``predict_proba`` interface so the ensemble logic
        works transparently.

        Args:
            X_train: Training feature matrix.
            y_train: Training labels.
            X_val: Validation feature matrix (unused but kept for API parity).
            y_val: Validation labels (unused but kept for API parity).
        """
        try:
            self.xgb_model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )
            self.xgb_model.fit(X_train, y_train)
            logger.info(
                "sklearn GradientBoostingClassifier trained as XGBoost fallback"
            )
        except Exception:
            logger.exception("sklearn fallback training failed — supervised model unavailable")
            self.xgb_model = None

    # ------------------------------------------------------------------ #
    # ISOLATION FOREST TRAINING                                           #
    # ------------------------------------------------------------------ #

    def _train_isolation_forest(self, X_train: np.ndarray) -> None:
        """Train Isolation Forest for unsupervised anomaly detection.

        Args:
            X_train: Training feature matrix.
        """
        cfg = get_ml_config().anomaly
        try:
            self.iforest_model = IsolationForest(
                contamination=cfg.iforest_contamination,
                n_estimators=cfg.iforest_n_estimators,
                max_samples=cfg.iforest_max_samples,
                random_state=42,
                n_jobs=-1,
            )
            self.iforest_model.fit(X_train)
            logger.info("Isolation Forest trained — n_samples=%d", len(X_train))
        except Exception:
            logger.exception("Isolation Forest training failed")
            self.iforest_model = None

    # ------------------------------------------------------------------ #
    # SHAP EXPLAINER                                                      #
    # ------------------------------------------------------------------ #

    def _build_shap_explainer(self, X_background: np.ndarray) -> None:
        """Build a SHAP explainer for the supervised model.

        Selects ``TreeExplainer`` for tree-based models (XGBoost,
        GradientBoosting) and falls back to ``KernelExplainer`` for
        anything else.

        Args:
            X_background: Background dataset for SHAP (typically training X).
        """
        if not HAS_SHAP:
            logger.warning("SHAP not installed — explanations will be unavailable")
            self._shap_explainer = None
            return

        if self.xgb_model is None:
            logger.warning("No supervised model to explain — skipping SHAP explainer build")
            self._shap_explainer = None
            return

        try:
            # TreeExplainer is the fastest option for gradient-boosted trees
            self._shap_explainer = shap.TreeExplainer(self.xgb_model)
            logger.info("SHAP TreeExplainer built successfully")
        except Exception:
            # KernelExplainer works with any model via predict_proba
            try:
                cfg = get_ml_config().explainability
                n_bg = min(cfg.shap_background_samples, len(X_background))
                bg_sample = X_background[:n_bg]
                self._shap_explainer = shap.KernelExplainer(
                    self.xgb_model.predict_proba,
                    bg_sample,
                )
                logger.info(
                    "SHAP KernelExplainer built (fallback) — background=%d", n_bg
                )
            except Exception:
                logger.exception("SHAP explainer creation failed entirely")
                self._shap_explainer = None

        # Store the background sample regardless of which explainer path was
        # taken, so downstream consumers (e.g. ExplainabilityEngine used for
        # human-readable alert explanations) can build their own KernelExplainer
        # fallback too, instead of failing with "no background data supplied".
        try:
            cfg = get_ml_config().explainability
            n_bg = min(cfg.shap_background_samples, len(X_background))
            self.background_sample_ = X_background[:n_bg]
        except Exception:
            self.background_sample_ = None

    def _compute_shap_contributions(
        self,
        X: np.ndarray,
        feature_cols: list[str],
        top_n: int = 3,
    ) -> list[list[dict[str, Any]]]:
        """Compute per-row SHAP feature contributions.

        Args:
            X: Feature matrix (n_samples × n_features).
            feature_cols: Ordered feature column names.
            top_n: Number of top contributing features to return per row.

        Returns:
            List of lists — one inner list per row, each containing *top_n*
            dicts with keys ``feature``, ``value``, ``contribution``.
        """
        if self._shap_explainer is None:
            return [[] for _ in range(len(X))]

        try:
            shap_values = self._shap_explainer.shap_values(X)

            # For binary classification, some SHAP versions return a list of
            # two arrays (one per class); newer versions instead return a
            # single 3D array shaped (n_samples, n_features, n_classes).
            # Either way, we want the positive-class ("anomaly") contributions.
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                shap_values = shap_values[:, :, 1]

            all_contributions: list[list[dict[str, Any]]] = []
            for row_idx in range(len(X)):
                row_shap = shap_values[row_idx]
                abs_shap = np.abs(row_shap)
                top_indices = np.argsort(abs_shap)[-top_n:][::-1]

                contributions: list[dict[str, Any]] = []
                for feat_idx in top_indices:
                    feat_idx = int(feat_idx)
                    col_name = (
                        feature_cols[feat_idx]
                        if feat_idx < len(feature_cols)
                        else f"feature_{feat_idx}"
                    )
                    contributions.append(
                        {
                            "feature": col_name,
                            "value": round(float(X[row_idx, feat_idx]), 6),
                            "contribution": round(float(row_shap[feat_idx]), 6),
                        }
                    )
                all_contributions.append(contributions)
            return all_contributions
        except Exception:
            logger.exception("SHAP value computation failed")
            return [[] for _ in range(len(X))]

    # ------------------------------------------------------------------ #
    # EVALUATION                                                          #
    # ------------------------------------------------------------------ #

    def _evaluate(self, X_val: np.ndarray, y_val: np.ndarray) -> TrainingMetrics:
        """Evaluate ensemble model on a temporal validation set.

        Args:
            X_val: Validation feature matrix.
            y_val: Validation labels.

        Returns:
            ``TrainingMetrics`` containing F1, Precision, Recall, AUC-ROC,
            support count, and the full classification report.
        """
        scores = self._ensemble_score(X_val)
        y_pred = (scores >= self.threshold).astype(int)

        f1 = f1_score(y_val, y_pred, zero_division=0)
        prec = precision_score(y_val, y_pred, zero_division=0)
        rec = recall_score(y_val, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_val, scores)
        except ValueError:
            # Only one class present in y_val
            auc = 0.0

        report = classification_report(y_val, y_pred, zero_division=0)

        logger.info(
            "Evaluation — F1=%.4f  Precision=%.4f  Recall=%.4f  AUC-ROC=%.4f",
            f1,
            prec,
            rec,
            auc,
        )

        return TrainingMetrics(
            f1=round(f1, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            auc_roc=round(auc, 4),
            support=len(y_val),
            report=report,
        )

    # ------------------------------------------------------------------ #
    # PREDICTION                                                          #
    # ------------------------------------------------------------------ #

    def predict(self, feature_df: pd.DataFrame) -> list[AnomalyResult]:
        """Predict anomaly scores for every record in the feature DataFrame.

        Each result includes the ensemble score, individual model scores,
        and SHAP-based contributing features.

        Args:
            feature_df: Feature ``DataFrame`` from ``FeatureEngineer`` with
                identifier columns (``pathogen_name``, ``drug_class``,
                ``county_code``, etc.).

        Returns:
            List of ``AnomalyResult``, one per row.

        Raises:
            ValueError: If *feature_df* is empty.
        """
        if feature_df.empty:
            logger.warning("predict() called with empty DataFrame — returning []")
            return []

        logger.info("Predicting anomalies — %d records", len(feature_df))

        feature_cols = self.feature_columns or self._resolve_feature_columns(feature_df)
        X = feature_df[feature_cols].values.astype(np.float32)

        # Score
        ensemble_scores = self._ensemble_score(X)
        xgb_scores = self._xgb_score(X)
        iforest_scores = self._iforest_score(X)

        # SHAP explanations
        cfg = get_ml_config().explainability
        shap_contributions = self._compute_shap_contributions(
            X, feature_cols, top_n=cfg.top_features_count
        )

        results: list[AnomalyResult] = []
        for positional_idx, (df_idx, row) in enumerate(feature_df.iterrows()):
            score = float(ensemble_scores[positional_idx])
            baseline = float(row.get("resistance_rate_rolling_6m", 0.0))
            current = float(row.get("resistance_rate", 0.0))

            result = AnomalyResult(
                score=round(score, 4),
                is_anomaly=score >= self.threshold,
                pathogen=str(row.get("pathogen_name", "Unknown")),
                drug_class=str(row.get("drug_class", "Unknown")),
                county=str(row.get("county_code", "000")),
                sub_county=str(row.get("sub_county", "")),
                sector=str(row.get("sector", "human")),
                contributing_features=shap_contributions[positional_idx],
                xgb_score=round(float(xgb_scores[positional_idx]), 4),
                iforest_score=round(float(iforest_scores[positional_idx]), 4),
                resistance_rate=round(current, 4),
                baseline_rate=round(baseline, 4),
            )
            results.append(result)

        anomaly_count = sum(1 for r in results if r.is_anomaly)
        logger.info(
            "Prediction complete — total=%d  anomalies=%d",
            len(results),
            anomaly_count,
        )
        return results

    # ------------------------------------------------------------------ #
    # ENSEMBLE SCORING                                                    #
    # ------------------------------------------------------------------ #

    def _ensemble_score(self, X: np.ndarray) -> np.ndarray:
        """Compute the weighted ensemble score of XGBoost + Isolation Forest.

        Args:
            X: Feature matrix (n_samples × n_features).

        Returns:
            1-D ``ndarray`` of anomaly scores clipped to [0, 1].
        """
        xgb_scores = self._xgb_score(X)
        iforest_scores = self._iforest_score(X)

        ensemble = (self.xgb_weight * xgb_scores) + (self.iforest_weight * iforest_scores)
        return np.clip(ensemble, 0.0, 1.0)

    def _xgb_score(self, X: np.ndarray) -> np.ndarray:
        """Get positive-class probability from the supervised model.

        Returns a constant 0.5 array when no supervised model is available.

        Args:
            X: Feature matrix.

        Returns:
            1-D ``ndarray`` of probabilities in [0, 1].
        """
        if self.xgb_model is None:
            return np.full(len(X), 0.5, dtype=np.float64)

        try:
            probs = self.xgb_model.predict_proba(X)[:, 1]
            return probs.astype(np.float64)
        except Exception:
            logger.exception("XGBoost scoring failed — returning neutral 0.5")
            return np.full(len(X), 0.5, dtype=np.float64)

    def _iforest_score(self, X: np.ndarray) -> np.ndarray:
        """Get normalised Isolation Forest anomaly scores in [0, 1].

        sklearn's ``decision_function`` returns negative values for anomalies;
        we negate and apply min-max normalisation so that *higher* = *more
        anomalous*.

        Args:
            X: Feature matrix.

        Returns:
            1-D ``ndarray`` of scores in [0, 1].
        """
        if self.iforest_model is None:
            return np.full(len(X), 0.5, dtype=np.float64)

        try:
            raw_scores = self.iforest_model.decision_function(X)
            # Negate: more negative → more anomalous → higher score
            negated = -raw_scores.astype(np.float64)
            min_val = negated.min()
            max_val = negated.max()
            if max_val - min_val > 1e-12:
                normalised = (negated - min_val) / (max_val - min_val)
            else:
                normalised = np.full(len(X), 0.5, dtype=np.float64)
            return normalised
        except Exception:
            logger.exception("Isolation Forest scoring failed — returning neutral 0.5")
            return np.full(len(X), 0.5, dtype=np.float64)

    # ------------------------------------------------------------------ #
    # PSI DRIFT DETECTION                                                 #
    # ------------------------------------------------------------------ #

    def _store_reference_distribution(
        self,
        X: np.ndarray,
        feature_cols: list[str],
    ) -> None:
        """Store training feature distributions for PSI computation.

        Args:
            X: Training feature matrix.
            feature_cols: Ordered list of feature column names.
        """
        for i, col in enumerate(feature_cols):
            self.training_feature_distribution[col] = X[:, i].copy()

    def compute_psi(
        self,
        inference_df: pd.DataFrame,
        n_bins: int = 10,
    ) -> dict[str, float]:
        """Compute Population Stability Index (PSI) for each feature.

        PSI quantifies how much the feature distribution has shifted between
        training and inference.  Interpretation:

        - PSI < 0.10 — no significant shift.
        - 0.10 ≤ PSI < 0.20 — moderate shift (monitor).
        - PSI ≥ 0.20 — significant drift (retrain recommended).

        Args:
            inference_df: Inference feature ``DataFrame``.
            n_bins: Number of histogram bins for discretisation.

        Returns:
            Dict mapping feature name → PSI value, rounded to 4 decimals.
        """
        if not self.training_feature_distribution:
            logger.warning(
                "No training reference distribution stored — cannot compute PSI"
            )
            return {}

        feature_cols = self._resolve_feature_columns(inference_df)
        psi_results: dict[str, float] = {}

        for col in feature_cols:
            if col not in self.training_feature_distribution:
                continue

            ref = self.training_feature_distribution[col]
            inf_vals = inference_df[col].values.astype(np.float64)
            psi = self._calculate_psi(ref, inf_vals, n_bins)
            psi_results[col] = round(psi, 4)

        # Log drifted features
        cfg = get_ml_config().anomaly
        drifted = {k: v for k, v in psi_results.items() if v > cfg.drift_psi_threshold}
        if drifted:
            logger.warning("Feature drift detected (PSI > %.2f): %s", cfg.drift_psi_threshold, drifted)
        else:
            logger.info("PSI check passed — no significant drift across %d features", len(psi_results))

        return psi_results

    @staticmethod
    def _calculate_psi(
        expected: np.ndarray,
        actual: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """Calculate PSI between *expected* (train) and *actual* (inference).

        Formula::

            PSI = Σ (actual_pct − expected_pct) · ln(actual_pct / expected_pct)

        Laplace smoothing (+1 count per bin) prevents division-by-zero.

        Args:
            expected: 1-D array of training feature values.
            actual: 1-D array of inference feature values.
            n_bins: Number of histogram bins.

        Returns:
            Scalar PSI value (non-negative).
        """
        # Unified bin edges spanning both distributions
        combined_min = min(float(expected.min()), float(actual.min()))
        combined_max = max(float(expected.max()), float(actual.max()))
        breakpoints = np.linspace(combined_min, combined_max, n_bins + 1)

        expected_counts = np.histogram(expected, bins=breakpoints)[0]
        actual_counts = np.histogram(actual, bins=breakpoints)[0]

        # Laplace smoothing
        expected_pct = (expected_counts + 1) / (len(expected) + n_bins)
        actual_pct = (actual_counts + 1) / (len(actual) + n_bins)

        psi = float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))
        return max(psi, 0.0)

    # ------------------------------------------------------------------ #
    # MODEL PERSISTENCE                                                   #
    # ------------------------------------------------------------------ #

    def save(self, directory: str | Path) -> str:
        """Serialise both models and metadata to disk via ``joblib``.

        The artefact file contains the XGBoost (or fallback) model, the
        Isolation Forest model, feature columns, weights, thresholds, the
        training reference distribution for PSI, and training metrics.

        Args:
            directory: Directory to save model artefacts into.  Created
                recursively if it does not exist.

        Returns:
            Absolute path to the saved ``.joblib`` file.
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        version = self.model_version or f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        artefact = {
            "xgb_model": self.xgb_model,
            "iforest_model": self.iforest_model,
            "feature_columns": self.feature_columns,
            "threshold": self.threshold,
            "xgb_weight": self.xgb_weight,
            "iforest_weight": self.iforest_weight,
            "model_version": version,
            "training_feature_distribution": self.training_feature_distribution,
            "training_metrics": self.training_metrics,
            "has_xgboost": HAS_XGBOOST,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "background_sample_": getattr(self, "background_sample_", None),
        }

        save_path = path / f"anomaly_detector_{version}.joblib"
        joblib.dump(artefact, save_path)
        logger.info("Model saved — %s", save_path)
        return str(save_path)

    @classmethod
    def load(cls, filepath: str | Path) -> "AnomalyDetector":
        """Deserialise an ``AnomalyDetector`` from a ``.joblib`` artefact.

        Restores both models, feature columns, weights, thresholds, the
        training reference distribution, and metrics.

        Args:
            filepath: Path to the saved ``.joblib`` file.

        Returns:
            Fully initialised ``AnomalyDetector`` ready for ``predict()``.

        Raises:
            FileNotFoundError: If *filepath* does not exist.
            KeyError: If the artefact is missing mandatory keys.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Model artefact not found: {filepath}")

        artefact = joblib.load(filepath)

        detector = cls(
            threshold=artefact["threshold"],
            xgb_weight=artefact["xgb_weight"],
        )
        detector.xgb_model = artefact["xgb_model"]
        detector.iforest_model = artefact["iforest_model"]
        detector.feature_columns = artefact["feature_columns"]
        detector.model_version = artefact.get("model_version", "unknown")
        detector.training_feature_distribution = artefact.get(
            "training_feature_distribution", {}
        )
        detector.training_metrics = artefact.get("training_metrics")
        detector.background_sample_ = artefact.get("background_sample_")

        # Rebuild SHAP explainer from the loaded model
        if detector.xgb_model is not None and HAS_SHAP:
            try:
                detector._shap_explainer = shap.TreeExplainer(detector.xgb_model)
                logger.info("SHAP TreeExplainer rebuilt from loaded model")
            except Exception:
                if detector.background_sample_ is not None:
                    try:
                        detector._shap_explainer = shap.KernelExplainer(
                            detector.xgb_model.predict_proba,
                            detector.background_sample_,
                        )
                        logger.info(
                            "SHAP KernelExplainer rebuilt from loaded model (fallback) — background=%d",
                            len(detector.background_sample_),
                        )
                    except Exception:
                        logger.warning("Could not rebuild any SHAP explainer from loaded model")
                        detector._shap_explainer = None
                else:
                    logger.warning(
                        "Could not rebuild SHAP TreeExplainer, and no background_sample_ "
                        "was saved to fall back on (older model artefact?)"
                    )
                    detector._shap_explainer = None

        logger.info(
            "Model loaded — version=%s  path=%s",
            detector.model_version,
            filepath,
        )
        return detector

    # ------------------------------------------------------------------ #
    # HELPERS                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _resolve_feature_columns(df: pd.DataFrame) -> list[str]:
        """Resolve numeric feature columns from a DataFrame.

        Delegates to ``FeatureEngineer.get_feature_columns`` when available;
        otherwise applies the same exclusion logic inline.

        Args:
            df: Feature ``DataFrame``.

        Returns:
            Ordered list of numeric feature column names.
        """
        if FeatureEngineer is not None:
            return FeatureEngineer.get_feature_columns(df)

        # Inline fallback — mirrors FeatureEngineer.get_feature_columns
        exclude = {
            "year_month",
            "pathogen_name",
            "drug_class",
            "county_code",
            "county_name",
            "sub_county",
            "sector",
            "record_id",
        }
        return [
            col
            for col in df.select_dtypes(include=[np.number]).columns
            if col not in exclude
        ]