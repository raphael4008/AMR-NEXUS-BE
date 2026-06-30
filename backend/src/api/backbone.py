import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func, desc
from sqlalchemy.orm import selectinload

from src.models.base import get_db
from src.models.entities import AMRRecord
from src.schemas.backbone import AMRRecordCreate, BulkIngestResponse
from src.core.security import RoleChecker, TokenData, ROLE_NATIONAL_COORDINATOR

logger = logging.getLogger("amr_nexus.api.backbone")
router = APIRouter(tags=["Data Backbone"])

# --- Helper: Move to top level ---
def _to_str(val):
    if val is None: return None
    if isinstance(val, list): return str(val[0])
    return str(val)

# ── GET /records ──────────────────────────────────────────────────────────────

@router.get("/predictions", status_code=status.HTTP_200_OK)
async def get_records(
    limit:          int           = Query(default=50),
    skip:           int           = Query(default=0),
    county:         Optional[str] = Query(None),
    pathogen_name:  Optional[str] = Query(None),
    sir_result:     Optional[str] = Query(None),
    sector:         Optional[str] = Query(None),
    start_date:     Optional[str] = Query(None),
    end_date:       Optional[str] = Query(None),
    db:             AsyncSession  = Depends(get_db),
    current_user:   Optional[TokenData] = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    stmt = (
        select(AMRRecord)
        .where(AMRRecord.deleted_at.is_(None))
        .order_by(AMRRecord.sample_collection_date.desc())
    )

    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        stmt = stmt.where(AMRRecord.county == current_user.county)

    if county:
        stmt = stmt.where(AMRRecord.county.ilike(f"%{county}%"))
    if pathogen_name:
        stmt = stmt.where(AMRRecord.pathogen_name.ilike(f"%{pathogen_name}%"))
    
    if sir_result and _to_str(sir_result).strip():
        stmt = stmt.where(func.upper(AMRRecord.sir_result) == _to_str(sir_result).upper())
    
    if sector and _to_str(sector).strip():
        stmt = stmt.where(func.upper(AMRRecord.sector) == _to_str(sector).upper())

    # Date parsing using the top-level helper
    sd_str = _to_str(start_date)
    if sd_str and sd_str.strip():
        try:
            sd = datetime.fromisoformat(sd_str).replace(tzinfo=timezone.utc)
            stmt = stmt.where(AMRRecord.sample_collection_date >= sd)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid start_date: {sd_str}")

    ed_str = _to_str(end_date)
    if ed_str and ed_str.strip():
        try:
            ed = datetime.fromisoformat(ed_str).replace(tzinfo=timezone.utc)
            stmt = stmt.where(AMRRecord.sample_collection_date <= ed)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid end_date: {ed_str}")

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [_serialise_record(r) for r in records]

# ... (Rest of your functions: get_record, delete_record, bulk_ingest_records, _serialise_record)


# ── GET /records/{record_id} ──────────────────────────────────────────────────

@router.get("/records/{record_id}", status_code=status.HTTP_200_OK)
async def get_record(
    record_id:    str,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """Returns a single AMR isolate record by UUID."""
    result = await db.execute(
        select(AMRRecord).where(
            AMRRecord.id == record_id,
            AMRRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found.")

    # County Veterinarian can only view their own county's records
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        if record.county != current_user.county:
            raise HTTPException(status_code=403, detail="Access restricted to your county.")

    return _serialise_record(record, include_full=True)


@router.get("/analytics/by_pathogen")
async def get_pathogen_stats(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"]))
):
    """
    Returns the top pathogens by record count.
    County Veterinarians only see data scoped to their county.
    """
    
    # 1. Base query: count records grouped by pathogen_name
    stmt = (
        select(
            AMRRecord.pathogen_name, 
            func.count(AMRRecord.id).label("count")
        )
        .where(AMRRecord.deleted_at.is_(None))
        .group_by(AMRRecord.pathogen_name)
        .order_by(desc("count"))
        .limit(limit)
    )

    # 2. Apply RBAC: If not National, scope to county
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        stmt = stmt.where(AMRRecord.county == current_user.county)

    result = await db.execute(stmt)
    
    # 3. Format into a list of dictionaries
    data = [
        {"pathogen_name": row.pathogen_name, "count": row.count} 
        for row in result.all()
    ]

    return {"status": "success", "data": data}

# ── DELETE /records/{record_id} — soft-delete ─────────────────────────────────

@router.delete("/records/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id:    str,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """
    Soft-deletes an AMR isolate record by setting deleted_at timestamp.
    The record remains in the database for audit trail purposes.
    County Veterinarians can only delete records within their county.
    """
    result = await db.execute(
        select(AMRRecord).where(
            AMRRecord.id == record_id,
            AMRRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found.")

    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        if record.county != current_user.county:
            raise HTTPException(status_code=403, detail="Access restricted to your county.")

    await db.execute(
        update(AMRRecord)
        .where(AMRRecord.id == record_id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()

    logger.info("Record %s soft-deleted by %s", record_id, current_user.username)
    return {"status": "deleted", "record_id": record_id, "deleted_at": datetime.now(timezone.utc).isoformat()}


# ── POST /records/bulk/ ───────────────────────────────────────────────────────

@router.post(
    "/records/bulk/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BulkIngestResponse,
    summary="Bulk ingest AMR isolate records",
    description=(
        "Accepts up to 10,000 validated AMR isolate records per batch. "
        "Each record is validated against the AMRRecordCreate schema "
        "(WHO GAP-AMR 2026-2036 compliance). "
        "ML anomaly analysis is dispatched to an async ARQ worker."
    ),
)
async def bulk_ingest_records(
    payload:      List[AMRRecordCreate],
    request:      Request,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> BulkIngestResponse:
    """Schema-first bulk ingest endpoint with async ARQ anomaly dispatch."""
    if not payload:
        raise HTTPException(status_code=400, detail="Payload is empty.")
    if len(payload) > 10_000:
        raise HTTPException(status_code=400, detail="Maximum batch size is 10,000 records.")

    now = datetime.now(timezone.utc)

    db_rows = []
    for record in payload:
        row = record.model_dump(
            exclude={"genomic_signals", "resistance_gene_links"},
            exclude_none=True,
        )
        # Derive sample_year and sample_month from sample_collection_date for trend queries
        scd = record.sample_collection_date
        row["sample_year"]  = scd.year
        row["sample_month"] = scd.month
        row["sample_week"]  = scd.isocalendar()[1]
        row["created_at"]   = now
        row["updated_at"]   = now
        db_rows.append(row)

    stmt   = insert(AMRRecord).values(db_rows).returning(AMRRecord.id)
    result = await db.execute(stmt)
    await db.commit()
    record_ids = list(result.scalars().all())

    # Dispatch ML pipeline to ARQ worker (non-blocking)
    task_queued = False
    try:
        redis_pool = request.app.state.redis_pool
        if redis_pool:
            await redis_pool.enqueue_job(
                "run_anomaly_pipeline",
                [str(rid) for rid in record_ids],
            )
            task_queued = True
            logger.info("Enqueued anomaly pipeline for %d records", len(record_ids))
    except Exception as exc:
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


# ── Serialiser helper ─────────────────────────────────────────────────────────

def _serialise_record(r: AMRRecord, include_full: bool = False) -> dict:
    """Serialises an AMRRecord to the API response dict. No hardcoded fields."""
    base = {
        "record_id":        str(r.id),
        "pathogen_code":    r.pathogen_name,
        "pathogen_name":    r.pathogen_name,
        "county":           r.county,
        "sub_county":       r.sub_county,
        "sector":           r.sector,
        "mdr_flag":         r.sir_result == "R",
        "mdr_probability":  float(r.resistance_percent) if r.resistance_percent else 0.0,
        "anomaly_detected": bool(r.anomaly_flag),
        "anomaly_score":    float(r.anomaly_score) if r.anomaly_score is not None else None,
        "shap_top_feature": r.shap_top_feature,
        "shap_value":       float(r.shap_value) if r.shap_value is not None else None,
        "antibiotic_class": r.antibiotic_class or r.antibiotic_name,
        "antibiotic_name":  r.antibiotic_name,
        "sir_result":       r.sir_result,
        "timestamp":        r.sample_collection_date.isoformat() if r.sample_collection_date else None,
        "data_quality_score": float(r.data_quality_score) if r.data_quality_score else None,
        "classification":   r.classification,
    }
    if include_full:
        base.update({
            "latitude":         float(r.latitude) if r.latitude else None,
            "longitude":        float(r.longitude) if r.longitude else None,
            "specimen_type":    r.specimen_type,
            "sample_source":    r.sample_source,
            "resistance_rate":  float(r.resistance_rate) if r.resistance_rate else None,
            "resistance_percent": float(r.resistance_percent) if r.resistance_percent else None,
            "patient_sex":      r.patient_sex,
            "patient_age_years": float(r.patient_age_years) if r.patient_age_years else None,
            "patient_age_group": r.patient_age_group,
            "infection_origin": r.infection_origin,
            "hospitalised":     r.hospitalised,
            "outcome":          r.outcome,
            "facility_id":      r.facility_id,
            "facility_type":    r.facility_type,
            "is_synthetic":     r.is_synthetic,
            "model_version":    r.model_version,
            "confidence_interval": float(r.confidence_interval) if r.confidence_interval else None,
            "forecast_cluster_id": r.forecast_cluster_id,
        })
    return base