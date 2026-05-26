from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.entities import AMRRecord, SectorEnum
from src.services.ingestion.cleaner import DataCleaner
from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine

router = APIRouter(prefix="/backbone", tags=["Ingestion"])

# Service Instantiation
cleaner = DataCleaner()
anomaly_engine = AMRAnomalyEngine()
advisory_engine = LLMAdvisoryEngine()

def run_downstream_evaluations(record_ids: List[int]):
    """
    Background worker: executes the ML pipeline and generates LLM advisories
    without blocking the incoming HTTP request.
    """
    db: Session = next(get_db())
    try:
        # 1. Handoff to ML Model (Gavinta/Jesse's Domain)
        alert_ids = anomaly_engine.execute_analysis_pipeline(record_ids, db)
        
        # 2. Handoff to LLM engine for newly generated anomalies
        for alert_id in alert_ids:
            advisory_engine.trigger_role_guidance(alert_id, db)
    finally:
        db.close()

@router.post("/ingest/whonet")
async def ingest_whonet_data(
    payload: List[Dict[str, Any]], 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accepts synthetic JSON arrays from Nicole's Data Science pipeline,
    cleans constraints, commits data, and delegates asynchronous ML.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Payload must not be empty.")

    clean_records, rejected_records = cleaner.process_dirty_data(payload)
    
    if not clean_records:
        return {
            "status": "failed",
            "message": "All records were rejected due to critical missing fields.",
            "processed_records": 0,
            "failed_critical": len(rejected_records)
        }

    # Transact ACID compliant models
    db_records = []
    for rec in clean_records:
        # Resolve sector to enum
        sector_str = str(rec.get("sector", "human")).upper()
        try:
            sector_val = SectorEnum[sector_str]
        except KeyError:
            sector_val = SectorEnum.HUMAN

        amr_record = AMRRecord(
            timestamp=datetime.now(timezone.utc),
            sector=sector_val,
            pathogen_name=rec["pathogen_name"],
            antimicrobial_agent=rec["antimicrobial_agent"],
            county=rec["county"],
            sub_county=rec.get("sub_county"),
            facility_type=rec.get("facility_type"),
            result_value=rec["result_value"],
            mic_value=rec.get("mic_value"),
            is_synthetic=rec.get("is_synthetic", 1),
            data_quality_score=rec.get("data_quality_score"),
            missing_fields=rec.get("missing_fields")
        )
        db.add(amr_record)
        db_records.append(amr_record)
        
    db.commit()
    
    # Asynchronous delegation
    record_ids = [r.id for r in db_records]
    background_tasks.add_task(run_downstream_evaluations, record_ids)

    # Return stable JSON REST endpoint response to frontend (Lowell) or pipeline (Nicole)
    return {
        "status": "success",
        "message": "Data ingested and queued for downstream anomaly evaluation.",
        "processed_records": len(clean_records),
        "failed_critical": len(rejected_records)
    }
