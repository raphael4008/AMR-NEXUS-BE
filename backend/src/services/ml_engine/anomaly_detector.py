# Track: backend/feature-api-name
import uuid
import pandas as pd
from typing import List
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from src.models.entities import AMRRecord, Alert
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
from src.services.notifications.sms_service import NotificationService
from src.core.config import settings

class AMRAnomalyEngine:
    def __init__(self):
        # Feature matrix tracking inputs matching Nicole's data schema
        self.feature_columns = ["data_quality_score", "ncbi_tax_id", "is_synthetic"]

    def preprocess_records(self, records: List[AMRRecord]) -> pd.DataFrame:
        """Transforms structural database rows into numeric feature arrays for ML execution."""
        data_matrix = []
        for r in records:
            data_matrix.append({
                "data_quality_score": float(r.data_quality_score),
                "ncbi_tax_id": r.ncbi_tax_id if r.ncbi_tax_id else 0,
                "is_synthetic": r.is_synthetic
            })
        return pd.DataFrame(data_matrix)

    def execute_analysis_pipeline(self, record_ids: List[uuid.UUID], db_session: Session, bg_tasks: BackgroundTasks):
        """
        Downstream asynchronous worker target.Processes records safely 
        containing the new genomic markers, creates alerts, and chains downstream actions.
        """
        records = db_session.query(AMRRecord).filter(AMRRecord.id.in_(record_ids)).all()
        if not records:
            return

        features_df = self.preprocess_records(records)
        
        # Invoke Gavinta and Jesse's predictive modeling outputs via deterministic stubs for Demo Day
        # FIX: use enumerate() so list_idx is always the Python list position, not the DataFrame index.
        new_alerts = []
        for list_idx, (_, row_data) in enumerate(features_df.iterrows()):
            current_record = records[list_idx]
            
            # Guard: data_quality_score may be None before the DB flushes the column default
            quality_score = float(current_record.data_quality_score or 0.0)

            # Simple demonstration trigger logic for the July 14 demo constraints
            # Supports both single-char SIR ('R') and full-word ('Resistant') result values
            result_val = str(current_record.result_value or "").strip()
            is_resistant = result_val == "R" or result_val.lower() == "resistant"

            if is_resistant and quality_score > 0.7:
                # 1. Instantiate and Save Anomaly Entry to DB
                new_alert = Alert(
                    amr_isolate_record_id=current_record.id,
                    anomaly_score=0.91,
                    hotspot_magnitude=0.88,
                    feature_importance={"county_weight": 0.4, "pathogen_risk_weight": 0.35},
                    status="PENDING"
                )
                db_session.add(new_alert)
                new_alerts.append(new_alert)

        # Single commit for all alerts in this batch
        if new_alerts:
            db_session.commit()
            for new_alert in new_alerts:
                db_session.refresh(new_alert)
                # 2. Chain Component C LLM Generation and Last-Mile SMS into Background Worker Loops
                bg_tasks.add_task(self._process_advisory_and_sms, new_alert.id, db_session)

    async def _process_advisory_and_sms(self, alert_id: uuid.UUID, db_session: Session):
        """Helper to process LLM Generation and outbound messaging without slowing down the server thread."""
        try:
            # Generate adaptive, role-scoped markdown briefs
            advisory_engine = LLMAdvisoryEngine()
            await advisory_engine.trigger_role_guidance(alert_id=alert_id, db_session=db_session)
            
            # Fire automated last-mile sandbox triggers via Africa's Talking
            alert = db_session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return
                
            record = db_session.query(AMRRecord).filter(AMRRecord.id == alert.amr_isolate_record_id).first()
            
            from src.models.entities import SectorEnum
            if record and record.sector == SectorEnum.ANIMAL.value:
                sms_gateway = NotificationService()
                sms_message = f"AMR-Nexus Alert: High resistance for {record.pathogen_name} detected in {record.county} County poultry facilities. Review National Guidelines."
                # Target mock configuration number for the Kiambu vet profile
                await sms_gateway.dispatch_stewardship_trigger(phone="+254700000000", message=sms_message)
                
                alert.status = "NOTIFIED"
                db_session.commit()
        except Exception as e:
            print(f"Background worker execution pipeline exception caught safely: {str(e)}")
