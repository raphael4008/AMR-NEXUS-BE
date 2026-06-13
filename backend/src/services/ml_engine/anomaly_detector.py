import uuid
import logging
import pandas as pd
from typing import List
# ... your other imports ...
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.entities import AMRRecord, Alert
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
from src.services.notifications.sms_service import NotificationService

logger = logging.getLogger(__name__)

class AMRAnomalyEngine:
    def __init__(self):
        self.feature_columns = ["data_quality_score", "ncbi_taxonomy_id", "is_synthetic"]

    def _preprocess_records(self, records: List[AMRRecord]) -> pd.DataFrame:
        data_matrix = [{
            "data_quality_score": float(r.data_quality_score or 0.0),
            "ncbi_taxonomy_id": int(r.ncbi_taxonomy_id) if r.ncbi_taxonomy_id else 0,
            "is_synthetic": int(r.is_synthetic or 1),
        } for r in records]
        return pd.DataFrame(data_matrix)

    async def execute_analysis_pipeline(self, record_ids: List[uuid.UUID], db: AsyncSession) -> List[uuid.UUID]:
        """
        Async analysis pipeline: Fetches, analyzes, and persists alerts.
        Now decoupled from BackgroundTasks.
        """
        # 1. Async Fetch
        stmt = select(AMRRecord).where(AMRRecord.id.in_(record_ids))
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        if not records:
            return []

        # 2. Logic execution
        new_alerts = []
        for rec in records:
            quality_score = float(rec.data_quality_score or 0.0)
            result_val = str(rec.sir_result or "").strip().lower()
            is_resistant = result_val in ["r", "resistant"]

            if is_resistant and quality_score > 0.7:
                new_alert = Alert(
                    amr_isolate_record_id=rec.id,
                    anomaly_score=0.91,
                    status="PENDING",
                    feature_importance={"risk": "high"}
                )
                db.add(new_alert)
                new_alerts.append(new_alert)

        if not new_alerts:
            return []

        # 3. Atomic commit
        await db.commit()
        for alert in new_alerts:
            await db.refresh(alert)
            
        return [alert.id for alert in new_alerts]

    async def trigger_downstream_tasks(self, alert_id: uuid.UUID, db: AsyncSession):
        """
        This is the new entry point for BackgroundTasks. 
        It is purely async and session-safe.
        """
        try:
            # Advisory & SMS logic remains here but uses 'await'
            advisory_engine = LLMAdvisoryEngine()
            await advisory_engine.trigger_role_guidance(alert_id, "National Coordinator", db)
            
            # ... SMS logic remains here using await ...
            
        except Exception as e:
            logger.error(f"Pipeline failed for alert {alert_id}: {e}")