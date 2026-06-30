"""
api/reports.py — AMR-Nexus Report Scheduling Router v2.2

Endpoint:
  POST /api/v1/reports/schedule — Schedules a report delivery via webhook

Webhook delivery model:
  - Stores report schedule in the database (ScheduledReport table)
  - ARQ worker picks up pending schedules and delivers via configured webhook URL
  - No direct SMTP/email — uses webhook for maximum provider flexibility

Request body:
  { email, format: "pdf"|"csv"|"xlsx", type: "weekly"|"monthly"|"custom", schedule: "cron_or_label" }
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.base import get_db
from src.models.entities import ScheduledReport
from src.core.security import RoleChecker, TokenData

logger = logging.getLogger("amr_nexus.api.reports")
router = APIRouter(tags=["Reports"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ReportScheduleRequest(BaseModel):
    email:    str
    format:   str = "pdf"       # pdf | csv | xlsx
    type:     str = "weekly"    # weekly | monthly | custom
    schedule: str = "weekly"    # cron expression or label


class ReportScheduleResponse(BaseModel):
    status:      str
    report_id:   str
    email:       str
    format:      str
    type:        str
    schedule:    str
    created_at:  str


# ── POST /reports/schedule ────────────────────────────────────────────────────

@router.post(
    "/reports/schedule",
    response_model=ReportScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a report for webhook delivery",
)
async def schedule_report(
    payload:      ReportScheduleRequest,
    request:      Request,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> ReportScheduleResponse:
    """
    Persists a report schedule to the database and enqueues it for webhook delivery
    via the ARQ worker. No SMTP dependency — uses webhook endpoint.
    """
    valid_formats   = {"pdf", "csv", "xlsx"}
    valid_types     = {"weekly", "monthly", "custom"}
    payload.format  = payload.format.lower()
    payload.type    = payload.type.lower()

    if payload.format not in valid_formats:
        raise HTTPException(status_code=422, detail=f"format must be one of: {', '.join(valid_formats)}")
    if payload.type not in valid_types:
        raise HTTPException(status_code=422, detail=f"type must be one of: {', '.join(valid_types)}")

    now = datetime.now(timezone.utc)

    report = ScheduledReport(
        recipient_email=payload.email,
        format=payload.format,
        report_type=payload.type,
        schedule=payload.schedule,
        created_by=current_user.username,
        status="SCHEDULED",
        created_at=now,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Dispatch delivery job to ARQ
    try:
        redis_pool = request.app.state.redis_pool
        if redis_pool:
            await redis_pool.enqueue_job(
                "run_report_delivery",
                str(report.id),
                payload.email,
                payload.format,
                payload.type,
            )
            logger.info("Enqueued report delivery for %s, report %s", payload.email, report.id)
    except Exception as exc:
        logger.error("Failed to enqueue report delivery: %s", exc)

    return ReportScheduleResponse(
        status="scheduled",
        report_id=str(report.id),
        email=payload.email,
        format=payload.format,
        type=payload.type,
        schedule=payload.schedule,
        created_at=now.isoformat(),
    )


# ── GET /reports/schedule (list user's schedules) ─────────────────────────────

@router.get(
    "/reports/schedule",
    summary="List your scheduled reports",
)
async def list_scheduled_reports(
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """Returns all report schedules created by the authenticated user."""
    result = await db.execute(
        select(ScheduledReport)
        .where(ScheduledReport.created_by == current_user.username)
        .order_by(ScheduledReport.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        {
            "report_id":   str(r.id),
            "email":       r.recipient_email,
            "format":      r.format,
            "type":        r.report_type,
            "schedule":    r.schedule,
            "status":      r.status,
            "created_at":  r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]
