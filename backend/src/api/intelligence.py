"""
api/intelligence.py — Component B & C: AI Dashboard and Alerts Routes

Routes:
  GET  /intelligence/dashboard            — High-level telemetry (public)
  GET  /intelligence/alerts               — Paginated alert list with filters
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.core.security import RoleChecker, ROLE_NATIONAL_COORDINATOR, ROLE_COUNTY_VETERINARIAN, ROLE_COUNTY_CLINICIAN, TokenData
from src.models.base import get_db
from src.models.entities import Alert, AMRRecord, Guidance
from src.schemas.intelligence import (
    AlertSummaryResponse,
    DashboardSummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper: Alert → Response ──────────────────────────────────────────────────────

def _alert_to_response(alert: Alert, db: Session) -> AlertSummaryResponse:
    """Joins Alert with its parent AMRRecord to produce the API response shape."""
    record = db.query(AMRRecord).filter(AMRRecord.id == alert.amr_record_id).first()
    sector_val = ""
    if record and record.sector:
        sector_val = record.sector.value if hasattr(record.sector, "value") else str(record.sector)

    return AlertSummaryResponse(
        id=alert.id,
        record_id=alert.amr_record_id,
        timestamp=alert.detection_timestamp,
        county=record.county if record else "Unknown",
        pathogen_name=record.pathogen_name if record else "Unknown",
        antimicrobial_agent=record.antimicrobial_agent if record else "Unknown",
        sector=sector_val,
        anomaly_score=alert.anomaly_score,
        hotspot_magnitude=alert.hotspot_magnitude,
        feature_importance=alert.feature_importance,
    )


# ── GET /intelligence/dashboard ───────────────────────────────────────────────────

@router.get(
    "/intelligence/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="AMR-Nexus Intelligence Dashboard",
    description="High-level surveillance telemetry for the platform dashboard. Gated to authorized users.",
    tags=["AI Dashboard Insights"],
)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(
        RoleChecker([ROLE_NATIONAL_COORDINATOR, ROLE_COUNTY_VETERINARIAN, ROLE_COUNTY_CLINICIAN])
    ),
) -> DashboardSummaryResponse:
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    alerts_last_30 = (
        db.query(func.count(Alert.id))
        .filter(Alert.detection_timestamp >= thirty_days_ago)
        .scalar() or 0
    )

    # High-risk counties: top 5 by average hotspot_magnitude
    county_scores = (
        db.query(AMRRecord.county, func.avg(Alert.hotspot_magnitude).label("avg_magnitude"))
        .join(Alert, Alert.amr_record_id == AMRRecord.id)
        .group_by(AMRRecord.county)
        .order_by(desc("avg_magnitude"))
        .limit(5)
        .all()
    )
    high_risk_counties = [row.county for row in county_scores]

    # Top pathogens by alert frequency
    top_pathogens_query = (
        db.query(AMRRecord.pathogen_name, func.count(Alert.id).label("alert_count"))
        .join(Alert, Alert.amr_record_id == AMRRecord.id)
        .group_by(AMRRecord.pathogen_name)
        .order_by(desc("alert_count"))
        .limit(5)
        .all()
    )
    top_pathogens = [row.pathogen_name for row in top_pathogens_query]

    # Recent 5 alerts
    recent_alert_objs = (
        db.query(Alert).order_by(desc(Alert.detection_timestamp)).limit(5).all()
    )
    recent_alerts = [_alert_to_response(a, db) for a in recent_alert_objs]

    # ── Stubbed Geographic Coordinates for Frontend Mapping ──
    geo_coords = [
        {"county": "Nairobi", "lat": -1.2921, "lng": 36.8219},
        {"county": "Kiambu", "lat": -1.1714, "lng": 36.8356},
        {"county": "Mombasa", "lat": -4.0435, "lng": 39.6682},
    ]

    # ── Fetch Recent Guidance Briefs ──
    recent_guidance_objs = (
        db.query(Guidance).order_by(desc(Guidance.generation_timestamp)).limit(5).all()
    )
    guidance_briefs = [
        {
            "id": g.id,
            "alert_id": g.alert_id,
            "user_role": g.role_target,
            "guidance_markdown": g.content_markdown,
            "status": g.status.value if hasattr(g.status, "value") else str(g.status)
        }
        for g in recent_guidance_objs
    ]

    # ── Stubbed Trend Values ──
    trend_values = [
        {"month": "2026-01", "value": 12},
        {"month": "2026-02", "value": 15},
        {"month": "2026-03", "value": 20},
        {"month": "2026-04", "value": 18},
        {"month": "2026-05", "value": 25},
    ]

    return DashboardSummaryResponse(
        total_alerts=total_alerts,
        alerts_last_30_days=alerts_last_30,
        high_risk_counties=high_risk_counties,
        top_pathogens=top_pathogens,
        recent_alerts=recent_alerts,
        geographic_coordinates=geo_coords,
        trend_values=trend_values,
        guidance_briefs=guidance_briefs,
    )


# ── GET /intelligence/alerts ──────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts",
    response_model=List[AlertSummaryResponse],
    summary="List AMR resistance alerts",
    tags=["AI Dashboard Insights"],
)
async def list_alerts(
    county: Optional[str] = Query(None, description="Filter by county"),
    pathogen: Optional[str] = Query(None, description="Filter by pathogen name"),
    start_date: Optional[datetime] = Query(None, description="Filter alerts from this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter alerts to this date (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[AlertSummaryResponse]:
    query = db.query(Alert)

    # Join on AMRRecord for county/pathogen filters
    if county or pathogen:
        query = query.join(AMRRecord, AMRRecord.id == Alert.amr_record_id)
        if county:
            query = query.filter(AMRRecord.county.ilike(f"%{county}%"))
        if pathogen:
            query = query.filter(AMRRecord.pathogen_name.ilike(f"%{pathogen}%"))

    if start_date:
        query = query.filter(Alert.detection_timestamp >= start_date)
    if end_date:
        query = query.filter(Alert.detection_timestamp <= end_date)

    alerts = query.order_by(desc(Alert.detection_timestamp)).offset(skip).limit(limit).all()
    return [_alert_to_response(a, db) for a in alerts]



