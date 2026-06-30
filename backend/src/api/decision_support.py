"""
api/decision_support.py — AMR-Nexus Decision Support (LLM Advisory) Router v2.2

Design decision: ARQ async dispatch (non-blocking).
  - POST dispatches to ARQ worker which calls LLMAdvisoryEngine
  - Returns immediately with task_id + status "pending"
  - GET polls for completed GuidanceBrief
  - Frontend polls GET until status == "COMPLETED"

This keeps the API responsive when LLM providers are slow (~3-15s).
System remains functional even if LLM API is unavailable — it simply returns pending.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief
from src.core.security import RoleChecker, TokenData, ROLE_NATIONAL_COORDINATOR

logger = logging.getLogger("amr_nexus.api.decision_support")
router = APIRouter(tags=["Decision Support"])


# ── Response schemas ───────────────────────────────────────────────────────────

class DecisionSupportStatus(BaseModel):
    record_id:    str
    status:       str            # "pending" | "completed" | "no_alert"
    task_id:      Optional[str]  = None
    guidance:     Optional[str]  = None
    role_target:  Optional[str]  = None
    generated_at: Optional[str]  = None


# ── POST /decision-support/{record_id} ───────────────────────────────────────

@router.post(
    "/decision-support/{record_id}",
    response_model=DecisionSupportStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger LLM Decision Support for an AMR record",
)
async def trigger_decision_support(
    record_id:    str,
    request:      Request,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> DecisionSupportStatus:
    """
    Dispatches an LLM advisory job for the alert linked to the given record.
    Returns immediately with status='pending'. Poll the GET endpoint for results.
    County Veterinarians can only trigger support for records in their county.
    """
    # 1. Look up the record
    record_result = await db.execute(
        select(AMRRecord).where(
            AMRRecord.id == record_id,
            AMRRecord.deleted_at.is_(None),
        )
    )
    record = record_result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found.")

    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        if record.county != current_user.county:
            raise HTTPException(status_code=403, detail="Access restricted to your county.")

    # 2. Find the most recent alert for this record
    alert_result = await db.execute(
        select(Alert)
        .where(Alert.amr_isolate_record_id == record_id)
        .order_by(Alert.detection_timestamp.desc())
        .limit(1)
    )
    alert = alert_result.scalar_one_or_none()

    if not alert:
        return DecisionSupportStatus(record_id=record_id, status="no_alert")

    # 3. Dispatch to ARQ worker (non-blocking)
    task_id: Optional[str] = None
    try:
        redis_pool = request.app.state.redis_pool
        if redis_pool:
            job = await redis_pool.enqueue_job(
                "run_decision_support",
                str(alert.id),
                current_user.role,
            )
            task_id = job.job_id if job else None
            logger.info("Dispatched decision support for alert %s, job %s", alert.id, task_id)
    except Exception as exc:
        logger.error("Failed to enqueue decision support job: %s", exc)

    return DecisionSupportStatus(
        record_id=record_id,
        status="pending",
        task_id=task_id,
    )


# ── GET /decision-support/{record_id} ────────────────────────────────────────

@router.get(
    "/decision-support/{record_id}",
    response_model=DecisionSupportStatus,
    summary="Poll for Decision Support guidance result",
)
async def get_decision_support(
    record_id:    str,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> DecisionSupportStatus:
    """
    Returns the most recent completed GuidanceBrief for the alert linked to this record.
    If still pending, returns status='pending'.
    """
    # Find the alert for this record
    alert_result = await db.execute(
        select(Alert)
        .where(Alert.amr_isolate_record_id == record_id)
        .order_by(Alert.detection_timestamp.desc())
        .limit(1)
    )
    alert = alert_result.scalar_one_or_none()

    if not alert:
        return DecisionSupportStatus(record_id=record_id, status="no_alert")

    # Look for completed guidance brief
    brief_result = await db.execute(
        select(GuidanceBrief)
        .where(
            GuidanceBrief.alert_id == str(alert.id),
            GuidanceBrief.role_target == current_user.role,
            GuidanceBrief.status == "COMPLETED",
        )
        .order_by(GuidanceBrief.generated_at.desc())
        .limit(1)
    )
    brief = brief_result.scalar_one_or_none()

    if not brief:
        # Fall back to any completed brief for this alert
        fallback_result = await db.execute(
            select(GuidanceBrief)
            .where(
                GuidanceBrief.alert_id == str(alert.id),
                GuidanceBrief.status == "COMPLETED",
            )
            .order_by(GuidanceBrief.generated_at.desc())
            .limit(1)
        )
        brief = fallback_result.scalar_one_or_none()

    if not brief:
        return DecisionSupportStatus(record_id=record_id, status="pending")

    return DecisionSupportStatus(
        record_id=record_id,
        status="completed",
        guidance=brief.content_markdown,
        role_target=brief.role_target,
        generated_at=brief.generated_at.isoformat() if brief.generated_at else None,
    )
