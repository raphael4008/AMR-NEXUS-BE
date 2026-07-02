"""
services/ml_engine/anomaly_detector.py — Production ML Analysis Pipeline
=========================================================================
Integrates the real ML models from the /ml_ai/ package into Raph & Naomi's
backend service layer. Replaces the stub _invoke_model_stub() with a
calibrated XGBoost + Isolation Forest ensemble with SHAP explainability.

Architecture:
    1. Raw DB records → FeatureEngineer → feature DataFrame
    2. Feature DataFrame → AnomalyDetector → anomaly scores
    3. Anomaly scores → ExplainabilityEngine → SHAP attributions
    4. Results → Alert table commits with feature_importance JSON

Dependencies:
    - ml_ai.feature_engineering.FeatureEngineer
    - ml_ai.anomaly_detection.AnomalyDetector
    - ml_ai.explainability.ExplainabilityEngine
    - ml_ai.experiment_tracking.MLflowTracker
"""

import logging
import os
import sys
from datetime import date, timedelta, timezone, datetime
from pathlib import Path
from typing import List, Optional

import numpy as np
from sqlalchemy.orm import Session

from backend.src.models.entities import AMRRecord, Alert
from backend.src.core.socket import emit_new_anomaly_sync

# ── Ensure ml_ai is importable from the monorepo root ────────────────────────
_project_root = Path(__file__).resolve().parents[4]  # backend/src/services/ml_engine → root
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Lazy ML imports — these are heavy and may not be installed in dev mode
_ml_available = False
FeatureEngineer = None
AnomalyDetector = None
ExplainabilityEngine = None
MLflowTracker = None
get_ml_config = None

try:
    from ml_ai.feature_engineering import FeatureEngineer
    from ml_ai.anomaly_detection import AnomalyDetector
    from ml_ai.explainability import ExplainabilityEngine
    from ml_ai.experiment_tracking import MLflowTracker
    from ml_ai.config import get_ml_config
    _ml_available = True
except ImportError as e:
    logging.getLogger(__name__).warning(
        "ML pipeline packages not fully installed (%s). ML features disabled.", e
    )

logger = logging.getLogger("amr_nexus.ml_engine")

# Provide a default config if ml_ai isn't available
if get_ml_config is not None:
    config = get_ml_config()
else:
    config = None


class AMRAnomalyEngine:
    """
    Production ML analysis pipeline that replaces the original stub.

    Orchestrates:
        1. Feature engineering from raw AMR records
        2. Ensemble anomaly detection (XGBoost + Isolation Forest)
        3. SHAP explainability for every flagged anomaly
        4. MLflow experiment tracking for auditability

    The engine maintains a trained model in memory after first training.
    Models are persisted to disk via joblib and registered in MLflow.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        if _ml_available and FeatureEngineer is not None:
            self.feature_engineer = FeatureEngineer()
            self.tracker = MLflowTracker(experiment_name="amr-nexus-anomaly-detection")
        else:
            self.feature_engineer = None
            self.tracker = None
            logger.warning("ML packages unavailable — AMRAnomalyEngine running in stub mode")

        self.detector: Optional[object] = None
        self.explainer: Optional[object] = None
        self._model_path = model_path or os.environ.get(
            "AMR_MODEL_PATH",
            str(_project_root / "ml_artifacts" / "anomaly_detector_latest.joblib"),
        )

        # Attempt to load a pre-trained model from disk
        if _ml_available:
            self._try_load_model()

    def _try_load_model(self) -> None:
        """Attempt to load a pre-trained model from disk or MLflow registry."""
        model_file = Path(self._model_path)
        if model_file.exists():
            try:
                self.detector = AnomalyDetector.load(model_file)
                # Initialize explainer with the loaded XGBoost model
                if self.detector.xgb_model is not None:
                    self.explainer = ExplainabilityEngine(
                        model=self.detector.xgb_model,
                        feature_columns=self.detector.feature_columns,
                    )
                logger.info(
                    "✅ Loaded pre-trained anomaly detector: %s (version: %s)",
                    self._model_path,
                    getattr(self.detector, "model_version", "unknown"),
                )
            except Exception as exc:
                logger.warning(
                    "⚠️ Failed to load model from %s: %s — will train on first run",
                    self._model_path,
                    exc,
                )
        else:
            logger.info(
                "No pre-trained model at %s — will train on first analysis run",
                self._model_path,
            )

    def _ensure_detector_trained(self, db_session: Session) -> bool:
        """
        Ensure the detector is trained before inference.

        If no model is loaded, trains on the last 12 months of data from the DB.

        Returns:
            True if the detector is ready for inference, False otherwise.
        """
        if self.detector is not None and self.detector.xgb_model is not None:
            return True

        logger.info("Training anomaly detector on historical data...")

        # Fetch last 12 months of records for training
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        training_records = (
            db_session.query(AMRRecord)
            .filter(AMRRecord.timestamp >= cutoff)
            .all()
        )

        if len(training_records) < 100:
            logger.warning(
                "Insufficient training data (%d records). Need at least 100. "
                "Falling back to rule-based scoring.",
                len(training_records),
            )
            return False

        # Convert ORM objects to feature-ready dicts
        records_dicts = [self._orm_to_dict(r) for r in training_records]

        # Build training features
        start_date = (datetime.now(timezone.utc) - timedelta(days=365)).date()
        end_date = date.today()
        feature_df = self.feature_engineer.build_training_features(
            records_dicts, (start_date, end_date)
        )

        if feature_df.empty or len(feature_df) < 50:
            logger.warning("Feature DataFrame too small for training: %d rows", len(feature_df))
            return False

        # Train with MLflow tracking
        self.detector = AnomalyDetector()
        try:
            run = self.tracker.start_run(run_name="auto-train-on-ingest")
            metrics = self.detector.train(feature_df)
            self.tracker.log_params({
                "xgb_weight": self.detector.xgb_weight,
                "threshold": self.detector.threshold,
                "training_records": len(training_records),
                "feature_count": len(self.detector.feature_columns),
            })
            self.tracker.log_metrics({
                "f1": metrics.f1,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "auc_roc": metrics.auc_roc,
            })

            # Save model
            model_dir = Path(self._model_path).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            self.detector.save(model_dir)
            self.tracker.end_run()

            logger.info(
                "✅ Anomaly detector trained — F1: %.4f, AUC-ROC: %.4f",
                metrics.f1,
                metrics.auc_roc,
            )
        except Exception as exc:
            logger.error("Training failed: %s", exc, exc_info=True)
            self.tracker.end_run()
            return False

        # Initialize explainer
        if self.detector.xgb_model is not None:
            self.explainer = ExplainabilityEngine(
                model=self.detector.xgb_model,
                feature_columns=self.detector.feature_columns,
            )

        return True

    def execute_analysis_pipeline(
        self, record_ids: List[int], db_session: Session
    ) -> List[int]:
        """
        Production ML pipeline: feature engineering → anomaly detection →
        SHAP explainability → Alert commit.

        This method replaces the original stub. It is called by Raph's
        background worker in backbone.py after data ingestion.

        Args:
            record_ids: List of AMRRecord IDs to analyze.
            db_session: Active SQLAlchemy session.

        Returns:
            List of generated Alert IDs for downstream LLM processing.
        """
        logger.info("🔬 Starting ML analysis for %d records", len(record_ids))

        records = (
            db_session.query(AMRRecord)
            .filter(AMRRecord.id.in_(record_ids))
            .all()
        )

        if not records:
            logger.warning("No records found for IDs: %s", record_ids)
            return []

        # Filter by data quality threshold
        quality_records = [
            r for r in records
            if r.data_quality_score is not None
            and float(r.data_quality_score) > config.anomaly.data_quality_min
        ]

        if not quality_records:
            logger.info(
                "All %d records below quality threshold (%.2f). Skipping ML.",
                len(records),
                config.anomaly.data_quality_min,
            )
            return []

        # Ensure model is trained
        model_ready = self._ensure_detector_trained(db_session)

        # Convert records to dicts for feature engineering
        records_dicts = [self._orm_to_dict(r) for r in quality_records]

        generated_alert_ids: List[int] = []

        if model_ready and self.detector is not None:
            # ── Real ML Pipeline ──────────────────────────────────────────
            try:
                feature_df = self.feature_engineer.build_inference_features(
                    records_dicts, as_of_date=date.today()
                )

                if feature_df.empty:
                    logger.warning("Feature DataFrame empty — falling back to rule-based")
                    return self._rule_based_fallback(quality_records, db_session)

                # Run ensemble anomaly detection
                results = self.detector.predict(feature_df)

                # Generate SHAP explanations for anomalies
                for i, result in enumerate(results):
                    if not result.is_anomaly:
                        continue

                    # Get SHAP explanation
                    explanation = {}
                    if self.explainer is not None:
                        try:
                            explanation = self.explainer.explain_anomaly(
                                result, feature_df, row_index=i
                            )
                        except Exception as shap_err:
                            logger.warning("SHAP explanation failed: %s", shap_err)

                    # Build feature importance JSON
                    feature_importance = {}
                    if explanation.get("top_features"):
                        feature_importance = {
                            f["feature"]: f["contribution"]
                            for f in explanation["top_features"]
                        }
                    else:
                        feature_importance = {
                            "xgb_score": result.xgb_score,
                            "iforest_score": result.iforest_score,
                        }

                    # Find the original record for this anomaly
                    matching_record = self._find_matching_record(
                        result, quality_records
                    )
                    if matching_record is None:
                        continue

                    # Commit Alert
                    alert = Alert(
                        amr_record_id=matching_record.id,
                        anomaly_score=result.score,
                        hotspot_magnitude=self._compute_hotspot_magnitude(result),
                        feature_importance=feature_importance,
                    )
                    db_session.add(alert)
                    db_session.flush()
                    generated_alert_ids.append(alert.id)

                    logger.info(
                        "🚨 Alert #%d — %s in %s (score: %.3f, county: %s)",
                        alert.id,
                        result.pathogen,
                        result.drug_class,
                        result.score,
                        result.county,
                    )

                    emit_new_anomaly_sync({
                        "message": f"⚠️ Anomaly: {result.pathogen.upper()} in {result.county}",
                        "severity": "high",
                        "record_id": str(matching_record.id),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                db_session.commit()

            except Exception as exc:
                logger.error(
                    "ML pipeline failed: %s — falling back to rule-based",
                    exc,
                    exc_info=True,
                )
                db_session.rollback()
                return self._rule_based_fallback(quality_records, db_session)

        else:
            # ── Rule-Based Fallback ───────────────────────────────────────
            generated_alert_ids = self._rule_based_fallback(
                quality_records, db_session
            )

        logger.info(
            "✅ Analysis complete: %d alerts generated from %d records",
            len(generated_alert_ids),
            len(quality_records),
        )
        return generated_alert_ids

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _orm_to_dict(record: AMRRecord) -> dict:
        """Convert SQLAlchemy AMRRecord to a flat dict for feature engineering."""
        sector_val = ""
        if record.sector:
            sector_val = record.sector.value if hasattr(record.sector, "value") else str(record.sector)

        return {
            "id": record.id,
            "sector": sector_val,
            "pathogen_name": record.pathogen_name or "Unknown",
            "antimicrobial_agent": record.antimicrobial_agent or "Unknown",
            "county": record.county or "Unknown",
            "county_code": record.county or "000",
            "sub_county": record.sub_county or "",
            "facility_type": record.facility_type or "",
            "result_value": record.result_value or "U",
            "mic_value": record.mic_value,
            "timestamp": record.timestamp,
            "sample_collection_date": record.timestamp.date() if record.timestamp else date.today(),
            "data_quality_score": record.data_quality_score or 0.0,
            "ncbi_tax_id": record.ncbi_tax_id,
        }

    @staticmethod
    def _find_matching_record(
        result, quality_records: List[AMRRecord]
    ) -> Optional[AMRRecord]:
        """Match an AnomalyResult back to its source AMRRecord."""
        for r in quality_records:
            if (
                (r.pathogen_name or "").lower() == result.pathogen.lower()
                and (r.county or "") == result.county
            ):
                return r
        # Fallback: return first record if exact match fails
        return quality_records[0] if quality_records else None

    @staticmethod
    def _compute_hotspot_magnitude(result) -> float:
        """
        Compute hotspot magnitude from anomaly result.

        Normalized severity [0, 10]: higher = more severe.
        Uses anomaly score and resistance rate deviation from baseline.
        """
        rate_deviation = abs(result.resistance_rate - result.baseline_rate)
        magnitude = (result.score * 5.0) + (rate_deviation * 5.0)
        return round(min(magnitude, 10.0), 2)

    def _rule_based_fallback(
        self, records: List[AMRRecord], db_session: Session
    ) -> List[int]:
        """
        Simple rule-based anomaly detection when ML models are unavailable.

        Rules:
            - Negative score indicates anomaly (matches original stub behavior)
            - All resistant results with quality > 0.7 flagged
        """
        logger.info("Using rule-based fallback for %d records", len(records))
        generated_alert_ids: List[int] = []

        for record in records:
            # Basic rule: flag resistant results as potential anomalies
            if (
                record.result_value
                and record.result_value.lower() == "resistant"
                and record.data_quality_score is not None
                and float(record.data_quality_score) > 0.7
            ):
                alert = Alert(
                    amr_record_id=record.id,
                    anomaly_score=-0.15,  # Negative = anomaly (original convention)
                    hotspot_magnitude=5.0,
                    feature_importance={
                        "method": "rule_based_fallback",
                        "pathogen": record.pathogen_name,
                        "county": record.county,
                    },
                )
                db_session.add(alert)
                db_session.flush()
                generated_alert_ids.append(alert.id)

                emit_new_anomaly_sync({
                    "message": f"⚠️ Anomaly: {record.pathogen_name.upper()} in {record.county}",
                    "severity": "high",
                    "record_id": str(record.id),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        db_session.commit()
        return generated_alert_ids
