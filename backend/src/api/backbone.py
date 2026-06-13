"""
api/backbone.py — AMR-Nexus Data Backbone Router

Refactored for production:
  1. Pydantic AMRRecordCreate schema-first validation (replaces raw Dict[str, Any])
  2. ARQ job queue replaces FastAPI BackgroundTasks for ML processing
  3. Typed BulkIngestResponse on the ingest endpoint
  4. Async SQLAlchemy 2.0 insert with scalar IDs
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from src.models.base import get_db
from src.models.entities import AMRRecord
from src.schemas.backbone import AMRRecordCreate, BulkIngestResponse
from src.core.security import RoleChecker

logger = logging.getLogger("amr_nexus.api.backbone")
router = APIRouter(tags=["Data Backbone"])


@router.get("/records", status_code=status.HTTP_200_OK)
async def get_records(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    user=Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """Returns recent AMR isolate records ordered by collection date descending."""
    stmt = (
        select(AMRRecord)
        .order_by(AMRRecord.sample_collection_date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        {
            "record_id": str(r.id),
            "pathogen_code": r.pathogen_name,
            "county": r.county,
            "mdr_flag": r.sir_result == "R",
            "mdr_probability": float(r.resistance_percent) if r.resistance_percent else 0.0,
            "anomaly_detected": False,
            "timestamp": r.sample_collection_date.isoformat() if r.sample_collection_date else None,
            "antibiotic_class": r.antibiotic_name,
            "sector": r.sector,
        }
        for r in records
    ]


@router.post(
    "/records/bulk/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BulkIngestResponse,
    summary="Bulk ingest AMR isolate records",
    description=(
        "Accepts up to 10,000 validated AMR isolate records per batch. "
        "Each record is validated against the AMRRecordCreate schema "
        "(WHO GAP-AMR 2026-2036 compliance). "
        "ML anomaly analysis is dispatched to an async ARQ worker — "
        "the HTTP response returns immediately with 202 Accepted."
    ),
)
async def bulk_ingest_records(
    payload: List[AMRRecordCreate],
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> BulkIngestResponse:
    """
    Schema-first bulk ingest endpoint.

    Pydantic handles all validation upstream:
      - sector enum normalization
      - pathogen name normalization (e.g. 'e. coli' → 'Escherichia coli')
      - SIR result normalization ('resistant' → 'R')
      - GAP-AMR sector disaggregation rules enforcement
      - Field range validation (lat/lon, mic_value >= 0, etc.)

    Invalid records are rejected with HTTP 422 before touching the database.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Payload is empty.")
    if len(payload) > 10_000:
        raise HTTPException(status_code=400, detail="Maximum batch size is 10,000 records.")

    # Serialize validated Pydantic models → DB-ready dicts
    # exclude_unset=False keeps defaults; exclude_none=True keeps schema clean
    db_rows = [
        record.model_dump(
            exclude={"genomic_signals", "resistance_gene_links"},
            exclude_none=True,
        )
        for record in payload
    ]

    # Async batch insert — returns the generated UUIDs
    stmt = insert(AMRRecord).values(db_rows).returning(AMRRecord.id)
    result = await db.execute(stmt)
    await db.commit()
    record_ids = list(result.scalars().all())

    # Dispatch ML pipeline to ARQ worker (durable, survives process restart)
    task_queued = False
    try:
        redis_pool = request.app.state.redis_pool
        await redis_pool.enqueue_job(
            "run_anomaly_pipeline",
            [str(rid) for rid in record_ids],
        )
        task_queued = True
        logger.info("Enqueued anomaly pipeline for %d records", len(record_ids))
    except Exception as exc:
        # Non-fatal: records are persisted, analysis will be retried manually
        logger.error("Failed to enqueue ARQ job: %s", exc)

    return BulkIngestResponse(
        status="success",
        processed_records=len(record_ids),
        failed_critical=0,
        record_ids=record_ids,
        task_queued=task_queued,
        message=(
            f"Inserted {len(record_ids)} records. "
            f"Anomaly analysis {'queued' if task_queued else 'NOT queued — check ARQ worker'}."
        ),
    )