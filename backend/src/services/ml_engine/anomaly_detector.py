# Track: backend/feature-api-name
# AMRAnomalyEngine v1.3 — Async ML worker with BackgroundTask chaining.
# Routes downstream LLM advisory and SMS notification correctly via single-role
# target_role parameter to prevent cost overrun.

import uuid
import logging
from typing import List

import pandas as pd
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.models.entities import AMRRecord, Alert
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
from src.services.notifications.sms_service import NotificationService
from src.core.config import settings

logger = logging.getLogger(__name__)


class AMRAnomalyEngine:
    """
    Asynchronous ML worker for AMR anomaly detection.
    Processes record IDs, applies feature matrix logic, creates Alert records,
    and chains downstream LLM advisory + SMS dispatch via FastAPI BackgroundTasks.
    """

    def __init__(self):
        # Feature columns matching Nicole's data schema v1.3
        self.feature_columns = [
            "data_quality_score",
            "ncbi_taxonomy_id",
            "is_synthetic",
        ]

    def preprocess_records(self, records: List[AMRRecord]) -> pd.DataFrame:
        """
        Transforms ORM record objects into a numeric feature array for ML inference.
        Guards against None values from pre-flush DB column defaults.
        """
        data_matrix = []
        for r in records:
            data_matrix.append({
                "data_quality_score": float(r.data_quality_score or 0.0),
                "ncbi_taxonomy_id":   int(r.ncbi_taxonomy_id) if r.ncbi_taxonomy_id else 0,
                "is_synthetic":       int(r.is_synthetic or 1),
            })
        return pd.DataFrame(data_matrix)

    def execute_analysis_pipeline(
        self,
        record_ids: List[uuid.UUID],
        db_session: Session,
        bg_tasks: BackgroundTasks,
    ) -> None:
        """
        Core analysis pipeline:
        1. Fetches AMRRecord objects by primary key batch.
        2. Preprocesses to feature matrix.
        3. Applies deterministic anomaly detection logic (ML-track stub).
        4. Persists Alert records for flagged anomalies.
        5. Enqueues LLM advisory + SMS tasks in BackgroundTasks.

        Args:
            record_ids: List of AMRRecord UUIDs to evaluate.
            db_session: Active SQLAlchemy session.
            bg_tasks:   FastAPI BackgroundTasks instance for async chaining.
        """
        records = db_session.query(AMRRecord).filter(AMRRecord.id.in_(record_ids)).all()
        if not records:
            logger.warning("execute_analysis_pipeline: No records found for given IDs.")
            return

        features_df = self.preprocess_records(records)
        new_alerts: List[Alert] = []

        # FIX: use enumerate() so list_idx is always the Python list position,
        # not the DataFrame index. Prevents index-alignment bugs on filtered DFs.
        for list_idx, (_, row_data) in enumerate(features_df.iterrows()):
            current_record = records[list_idx]

            quality_score = float(current_record.data_quality_score or 0.0)

            # Resistance flag — handles both CHAR(1) 'R' and full-word 'Resistant'
            result_val = str(current_record.sir_result or "").strip()
            is_resistant = result_val.upper() == "R" or result_val.lower() == "resistant"

            # SHAP-stub feature importance (real SHAP integration: ML/AI track)
            shap_contributors = {
                "county_weight":        0.40,
                "pathogen_risk_weight": 0.35,
                "quality_score_weight": round(quality_score * 0.25, 3),
            }

            if is_resistant and quality_score > 0.7:
                new_alert = Alert(
                    amr_isolate_record_id=current_record.id,
                    anomaly_score=0.91,
                    hotspot_magnitude=0.88,
                    feature_importance=shap_contributors,
                    status="PENDING",
                )
                db_session.add(new_alert)
                new_alerts.append((new_alert, current_record))

        if not new_alerts:
            return

        # Single atomic commit for all alerts in this batch
        db_session.commit()

        for new_alert, source_record in new_alerts:
            db_session.refresh(new_alert)

            # Determine role from sector — routes LLM to correct system prompt
            sector_val = str(source_record.sector or "").upper()
            if sector_val == "ANIMAL":
                advisory_role = "County Veterinarian"
            else:
                advisory_role = "National Coordinator"

            # Enqueue advisory + SMS as background tasks (non-blocking)
            bg_tasks.add_task(
                self._process_advisory_and_sms,
                new_alert.id,
                advisory_role,
                db_session,
            )

    async def _process_advisory_and_sms(
        self,
        alert_id: uuid.UUID,
        target_role: str,
        db_session: Session,
    ) -> None:
        """
        Background worker: generates role-specific LLM brief and dispatches
        SMS notification. Runs outside the main request-response cycle.
        """
        try:
            # ── Component C: LLM Advisory Generation ─────────────────────────
            advisory_engine = LLMAdvisoryEngine()
            await advisory_engine.trigger_role_guidance(
                alert_id=alert_id,
                target_role=target_role,
                db_session=db_session,
            )

            # ── Last-Mile SMS Notification (animal sector only) ───────────────
            alert = db_session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return

            record = db_session.query(AMRRecord).filter(
                AMRRecord.id == alert.amr_isolate_record_id
            ).first()

            if record and str(record.sector or "").upper() == "ANIMAL":
                sms_gateway = NotificationService()
                message = (
                    f"AMR-Nexus Alert: High resistance for {record.pathogen_name} "
                    f"detected in {record.county} County poultry facilities. "
                    f"Review National VMD Guidelines immediately."
                )
                await sms_gateway.dispatch_stewardship_trigger(
                    phone="+254700000000",  # Mock config for sandbox testing
                    message=message,
                )
                alert.status = "NOTIFIED"
                db_session.commit()

        except Exception as exc:
            logger.error(
                f"Background pipeline exception for alert={alert_id}, "
                f"role='{target_role}': {exc}"
            )
