"""
api/backbone.py — Component A: Data Ingestion Routes

Exposes the primary WHONET ingest endpoint. The pipeline is:
  1. Payload arrives → DataCleaner processes (imputation, quality scoring)
  2. Clean records are persisted to amr_records via SQLAlchemy session
  3. AMRAnomalyEngine is enqueued as a BackgroundTask (non-blocking)
  4. Response returns immediately with counts and queued task status
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.entities import AMRRecord, SectorEnum
from src.schemas.backbone import WhonetIngestResponse, AMRRecordResponse
from src.services.ingestion.cleaner import DataCleaner

logger = logging.getLogger(__name__)
router = APIRouter()
cleaner = DataCleaner(threshold=0.4)


def _run_anomaly_pipeline(record_ids: List[int], db_factory) -> None:
    """
    Background worker: instantiates a fresh DB session and runs the full
    ML anomaly detection pipeline. Isolated from the request thread.
    """
    from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine

    db: Session = db_factory()
    try:
        engine = AMRAnomalyEngine(db=db)
        engine.run_detection_pipeline(record_ids=record_ids)
        db.commit()
    except Exception as exc:
        logger.error("Anomaly pipeline failed for records %s: %s", record_ids, exc)
        db.rollback()
    finally:
        db.close()


@router.post(
    "/backbone/ingest/whonet",
    response_model=WhonetIngestResponse,
    summary="Ingest WHONET isolate records",
    description=(
        "Accepts a batch of raw WHONET-format isolate payloads. Records pass through "
        "the DataCleaner pipeline (imputation, quality scoring), clean records are "
        "persisted to the database, and anomaly detection is queued as a background task."
    ),
)
async def ingest_whonet_data(
    payload: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> WhonetIngestResponse:
    if not payload:
        raise HTTPException(status_code=400, detail="Payload must not be empty.")

    # ── Stage 1: Clean & validate ────────────────────────────────────────────────
    clean_df, failed_records = cleaner.process_dirty_data(payload)

    if clean_df.empty:
        return WhonetIngestResponse(
            status="rejected",
            processed_records=0,
            failed_critical=len(failed_records),
            record_ids=[],
            task_queued=False,
            message="All submitted records failed critical field validation.",
        )

    # ── Stage 2: Persist clean records to DB ────────────────────────────────────
    persisted_ids: List[int] = []
    for _, row in clean_df.iterrows():
        # Resolve sector enum safely
        sector_raw = str(row.get("sector", "human")).lower().split(".")[-1]
        try:
            sector_enum = SectorEnum(sector_raw)
        except ValueError:
            sector_enum = SectorEnum.HUMAN

        record = AMRRecord(
            sector=sector_enum,
            pathogen_name=str(row.get("pathogen_name", "")),
            antimicrobial_agent=str(row.get("antimicrobial_agent", "")),
            county=str(row.get("county", "")),
            sub_county=row.get("sub_county") or None,
            facility_type=row.get("facility_type") or None,
            result_value=str(row.get("result_value", "")),
            mic_value=float(row["mic_value"]) if row.get("mic_value") else None,
            is_synthetic=int(row.get("is_synthetic", 1)),
            data_quality_score=float(row.get("data_quality_score", 1.0)),
            missing_fields=row.get("missing_fields") if isinstance(row.get("missing_fields"), list) else None,
            hl7_fhir_id=row.get("hl7_fhir_id") or None,
            woah_reference=row.get("woah_reference") or None,
        )
        db.add(record)

    db.flush()  # Assign IDs without committing
    persisted_ids = [r.id for r in db.new if isinstance(r, AMRRecord)]
    db.commit()
    db.refresh  # Ensure IDs are populated

    # Re-query to get the committed IDs (flush above captures newly added objects)
    if not persisted_ids:
        # Fallback: query for recently inserted records
        from sqlalchemy import desc
        recent = (
            db.query(AMRRecord)
            .order_by(desc(AMRRecord.id))
            .limit(len(clean_df))
            .all()
        )
        persisted_ids = [r.id for r in recent]

    logger.info("Persisted %d records. IDs: %s", len(persisted_ids), persisted_ids)

    # ── Stage 3: Queue anomaly detection as BackgroundTask ───────────────────────
    from src.models.base import SessionLocal

    if persisted_ids:
        background_tasks.add_task(
            _run_anomaly_pipeline,
            record_ids=persisted_ids,
            db_factory=SessionLocal,
        )

    return WhonetIngestResponse(
        status="success",
        processed_records=len(clean_df),
        failed_critical=len(failed_records),
        record_ids=persisted_ids,
        task_queued=bool(persisted_ids),
        message=(
            f"{len(clean_df)} records ingested and persisted. "
            f"{len(failed_records)} records rejected (missing critical fields). "
            f"Anomaly detection queued for {len(persisted_ids)} records."
        ),
    )


@router.get(
    "/backbone/records",
    response_model=List[AMRRecordResponse],
    summary="List ingested AMR records",
    description="Paginated query of persisted AMR records with optional filters.",
)
async def list_records(
    county: Optional[str] = Query(None, description="Filter by county name"),
    sector: Optional[str] = Query(None, description="Filter by sector: human, animal, environment"),
    pathogen: Optional[str] = Query(None, description="Filter by pathogen name (partial match)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[AMRRecordResponse]:
    query = db.query(AMRRecord)

    if county:
        query = query.filter(AMRRecord.county.ilike(f"%{county}%"))
    if sector:
        try:
            sector_enum = SectorEnum(sector.lower())
            query = query.filter(AMRRecord.sector == sector_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid sector: {sector}")
    if pathogen:
        query = query.filter(AMRRecord.pathogen_name.ilike(f"%{pathogen}%"))

    records = query.order_by(AMRRecord.timestamp.desc()).offset(skip).limit(limit).all()
    return records
