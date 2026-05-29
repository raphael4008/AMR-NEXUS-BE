from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import insert

from src.models.base import get_db
from src.models.entities import AMRRecord, SectorEnum
from src.services.ingestion.cleaner import DataCleaner
from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
from src.core.security import RoleChecker

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
        from fastapi import BackgroundTasks
        bg_tasks = BackgroundTasks()
        # 1. Handoff to ML Model (Gavinta/Jesse's Domain)
        anomaly_engine.execute_analysis_pipeline(record_ids, db, bg_tasks)
        
        # 2. Execute any downstream tasks (LLM engine, SMS)
        for task in bg_tasks.tasks:
            task.func(*task.args, **task.kwargs)
    finally:
        db.close()

@router.post("/ingest/whonet", status_code=status.HTTP_202_ACCEPTED)
async def ingest_whonet_data(
    payload: List[Dict[str, Any]], 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(RoleChecker(["National Coordinator", "County Veterinarian"]))
):
    """
    Accepts synthetic JSON arrays from Nicole's Data Science pipeline,
    cleans constraints, commits data, and delegates asynchronous ML.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Payload must not be empty.")
    if len(payload) > 10000:
        raise HTTPException(status_code=400, detail="Payload exceeds maximum size of 10,000 records.")

    clean_records, rejected_records = cleaner.process_dirty_data(payload)
    
    if not clean_records:
        return {
            "status": "failed",
            "message": "All records were rejected due to critical missing fields.",
            "processed_records": 0,
            "failed_critical": len(rejected_records)
        }

    # Transact ACID compliant models using bulk inserts
    mappings = []
    now_utc = datetime.now(timezone.utc)
    for rec in clean_records:
        # Resolve sector to enum
        sector_str = str(rec.get("sector", "human")).upper()
        try:
            sector_val = SectorEnum[sector_str]
        except KeyError:
            sector_val = SectorEnum.HUMAN

        mappings.append({
            "sample_collection_date": rec.get("sample_collection_date", now_utc),
            "sector": sector_val,
            "pathogen_name": rec["pathogen_name"],
            "antimicrobial_agent": rec["antimicrobial_agent"],
            "county": rec["county"],
            "sub_county": rec.get("sub_county"),
            "facility_type": rec.get("facility_type"),
            "result_value": rec["result_value"],
            "mic_value": rec.get("mic_value"),
            "is_synthetic": rec.get("is_synthetic", 1),
            "data_quality_score": rec.get("data_quality_score"),
            "missing_fields": rec.get("missing_fields"),
            "ncbi_tax_id": rec.get("ncbi_tax_id"),
            "sequencing_platform": rec.get("sequencing_platform"),
            "assembly_id": rec.get("assembly_id"),
            "accession_number": rec.get("accession_number"),
            "qc_status": rec.get("qc_status"),
            "patient_sex": rec.get("patient_sex"),
            "patient_age_years": rec.get("patient_age_years"),
            "admission_type": rec.get("admission_type"),
            "animal_species": rec.get("animal_species"),
            "production_system": rec.get("production_system"),
            "infarm_compliant": rec.get("infarm_compliant", False),
            "animuse_compliant": rec.get("animuse_compliant", False),
            "glass_eligible": rec.get("glass_eligible", False),
            "woah_animal_aware_class": rec.get("woah_animal_aware_class"),
            "antimicrobial_residue_ppm": rec.get("antimicrobial_residue_ppm")
        })

    # Ultra-fast atomic batch database insertion using PostgreSQL RETURNING
    stmt = insert(AMRRecord).values(mappings).returning(AMRRecord.id)
    result = db.execute(stmt)

    # Safely retrieve EXACT IDs generated in this transaction without race conditions
    record_ids = [row[0] for row in result]

    db.commit()
    
    # Asynchronous delegation
    background_tasks.add_task(run_downstream_evaluations, record_ids)

    # Return immediate 202 Accepted response
    return {
        "status": "success",
        "message": "Data ingested and queued for downstream anomaly evaluation.",
        "processed_records": len(clean_records),
        "failed_critical": len(rejected_records)
    }
