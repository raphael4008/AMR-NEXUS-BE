# Track: backend/feature-api-name
# API Router v1.3 — Bulk ingestion endpoint mapped to all v1.3 schema columns.
# Route: POST /api/v1/records/bulk/
# Supports asynchronous handling for up to 10,000 records per batch.

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import insert
import asyncio

from src.models.base import get_db
from src.models.entities import AMRRecord, SectorEnum
from src.services.ingestion.cleaner import DataCleaner
from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine
from src.core.security import RoleChecker

router = APIRouter(tags=["Ingestion"])

# ── Service Instantiation ─────────────────────────────────────────────────────
cleaner = DataCleaner()
anomaly_engine = AMRAnomalyEngine()


def run_downstream_evaluations(record_ids: List) -> None:
    """
    Background worker: executes the ML anomaly pipeline without blocking
    the incoming HTTP response. Safely handles async sub-tasks internally.
    """
    db: Session = next(get_db())
    try:
        bg_tasks = BackgroundTasks()
        anomaly_engine.execute_analysis_pipeline(record_ids, db, bg_tasks)

        # Execute enqueued coroutine tasks (advisory + SMS) in a new event loop
        for task in bg_tasks.tasks:
            result = task.func(*task.args, **task.kwargs)
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(result)
                except RuntimeError:
                    asyncio.run(result)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(f"Downstream evaluation error: {exc}")
    finally:
        db.close()


@router.post(
    "/records/bulk/",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk AMR Record Ingestion",
    description=(
        "Accepts JSON arrays of up to 10,000 AMR isolate records from Nicole's "
        "Data Science pipeline. Validates, cleans, and commits records asynchronously, "
        "then delegates anomaly detection and LLM advisory generation as background tasks."
    ),
)
async def bulk_ingest_records(
    payload: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    if not payload:
        raise HTTPException(status_code=400, detail="Payload must not be empty.")
    if len(payload) > 10_000:
        raise HTTPException(
            status_code=400,
            detail=f"Payload exceeds maximum batch size of 10,000 records (got {len(payload)}).",
        )

    # ── Data cleaning + Pydantic validation pass ──────────────────────────────
    clean_records, rejected_records = cleaner.process_dirty_data(payload)

    if not clean_records:
        return {
            "status": "failed",
            "message": "All records were rejected due to critical missing fields or validation errors.",
            "processed_records": 0,
            "failed_critical": len(rejected_records),
        }

    # ── Build bulk-insert mapping with all v1.3 columns ──────────────────────
    mappings = []
    now_utc = datetime.now(timezone.utc)

    for rec in clean_records:
        # Resolve sector to enum string
        sector_str = str(rec.get("sector", "HUMAN")).upper()
        try:
            sector_val = SectorEnum[sector_str].value
        except KeyError:
            sector_val = SectorEnum.HUMAN.value

        # Handle both string and datetime sample_collection_date
        raw_date = rec.get("sample_collection_date", now_utc)
        if isinstance(raw_date, str):
            try:
                raw_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                raw_date = now_utc

        mappings.append({
            # Core identity
            "sample_collection_date": raw_date,
            "sector":                  sector_val,
            # Pathogen taxonomy (Unmapped 1–3)
            "pathogen_name":           rec["pathogen_name"],
            "pathogen_code":           rec.get("pathogen_code"),
            "ncbi_taxonomy_id":        rec.get("ncbi_taxonomy_id"),
            # Antimicrobial profile (Unmapped 4–6)
            "antibiotic_code":         rec.get("antibiotic_code"),
            "antibiotic_name":         rec.get("antibiotic_name") or rec.get("antimicrobial_agent", ""),
            "antibiotic_class":        rec.get("antibiotic_class"),
            # Resistance result (Unmapped 7–8)
            "mic_value":               rec.get("mic_value"),
            "sir_result":              rec.get("sir_result") or rec.get("result_value", ""),
            # Geography (Unmapped 9–10)
            "county":                  rec["county"],
            "sub_county":              rec.get("sub_county"),
            # Dataset-specific indicators
            "latitude":                rec.get("latitude"),
            "longitude":               rec.get("longitude"),
            "specimen_type":           rec.get("specimen_type"),
            "resistance_rate":         rec.get("resistance_rate"),
            "resistance_percent":      rec.get("resistance_percent"),
            "classification":          rec.get("classification"),
            "sample_size":             rec.get("sample_size"),
            "hospitalised":            rec.get("hospitalised"),
            "outcome":                 rec.get("outcome"),
            "reported_by":             rec.get("reported_by"),
            # Data integrity
            "is_synthetic":            rec.get("is_synthetic", 1),
            "data_quality_score":      rec.get("data_quality_score"),
            "missing_fields":          rec.get("missing_fields"),
            "submission_type":         rec.get("submission_type", "SYNTHETIC"),
            # Interoperability
            "hl7_fhir_id":             rec.get("hl7_fhir_id"),
            "woah_reference":          rec.get("woah_reference"),
            # Genomic metadata
            "sequencing_platform":     rec.get("sequencing_platform"),
            "assembly_id":             rec.get("assembly_id"),
            "accession_number":        rec.get("accession_number"),
            "qc_status":               rec.get("qc_status"),
            # GAP-AMR disaggregation — human
            "patient_sex":             rec.get("patient_sex"),
            "patient_age_years":       rec.get("patient_age_years"),
            "admission_type":          rec.get("admission_type"),
            "clinical_indication":     rec.get("clinical_indication"),
            # GAP-AMR disaggregation — animal
            "animal_species":          rec.get("animal_species"),
            "production_system":       rec.get("production_system"),
            # Compliance flags
            "infarm_compliant":        rec.get("infarm_compliant", False),
            "animuse_compliant":       rec.get("animuse_compliant", False),
            "glass_eligible":          rec.get("glass_eligible", False),
            "woah_animal_aware_class": rec.get("woah_animal_aware_class"),
            "antimicrobial_residue_ppm": rec.get("antimicrobial_residue_ppm"),
            # Legacy
            "facility_type":           rec.get("facility_type"),
        })

    # ── Atomic batch insertion with RETURNING for race-condition-free ID retrieval ──
    stmt = insert(AMRRecord).values(mappings).returning(AMRRecord.id)
    result = db.execute(stmt)
    record_ids = [row[0] for row in result]
    db.commit()

    # ── Delegate anomaly detection pipeline as background task ────────────────
    background_tasks.add_task(run_downstream_evaluations, record_ids)

    return {
        "status": "success",
        "message": (
            f"Batch of {len(clean_records)} records ingested and queued for "
            "downstream anomaly evaluation."
        ),
        "processed_records": len(clean_records),
        "failed_critical": len(rejected_records),
        "task_queued": True,
    }


# ── Legacy alias route (v1.2 backward compatibility) ─────────────────────────
@router.post(
    "/backbone/ingest/whonet",
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,  # Hidden from OpenAPI docs — use /records/bulk/ instead
)
async def ingest_whonet_data_legacy(
    payload: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """Legacy route — redirects to bulk_ingest_records logic."""
    return await bulk_ingest_records(payload, background_tasks, db, user)
