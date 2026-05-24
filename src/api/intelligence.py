"""
api/intelligence.py — Component B & C: AI Dashboard, Alerts, Advisory & Forecast Routes

Routes:
  GET  /intelligence/dashboard            — High-level telemetry (public)
  GET  /intelligence/alerts               — Paginated alert list with filters
  POST /intelligence/alerts/{id}/advisory — LLM advisory generation (role-gated)
  GET  /intelligence/forecasts/{county}   — On-demand Prophet forecast
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
from src.schemas.guidance import GuidanceRequest, GuidanceResponse
from src.schemas.intelligence import (
    AlertSummaryResponse,
    CountyForecastResponse,
    DashboardSummaryResponse,
    ForecastDataPoint,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper: Alert → Response ──────────────────────────────────────────────────────

def _alert_to_response(alert: Alert, db: Session) -> AlertSummaryResponse:
    """Joins Alert with its parent AMRRecord to produce the API response shape."""
    record = db.query(AMRRecord).filter(AMRRecord.id == alert.record_id).first()
    sector_val = ""
    if record and record.sector:
        sector_val = record.sector.value if hasattr(record.sector, "value") else str(record.sector)

    return AlertSummaryResponse(
        id=alert.id,
        record_id=alert.record_id,
        timestamp=alert.timestamp,
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
    "/intelligence/dashboard",
    response_model=DashboardSummaryResponse,
    summary="AMR-Nexus Intelligence Dashboard",
    description="High-level surveillance telemetry for the platform dashboard. No authentication required.",
    tags=["AI Dashboard Insights"],
)
async def get_dashboard(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    alerts_last_30 = (
        db.query(func.count(Alert.id))
        .filter(Alert.timestamp >= thirty_days_ago)
        .scalar() or 0
    )

    # High-risk counties: top 5 by average hotspot_magnitude
    county_scores = (
        db.query(AMRRecord.county, func.avg(Alert.hotspot_magnitude).label("avg_magnitude"))
        .join(Alert, Alert.record_id == AMRRecord.id)
        .group_by(AMRRecord.county)
        .order_by(desc("avg_magnitude"))
        .limit(5)
        .all()
    )
    high_risk_counties = [row.county for row in county_scores]

    # Top pathogens by alert frequency
    top_pathogens_query = (
        db.query(AMRRecord.pathogen_name, func.count(Alert.id).label("alert_count"))
        .join(Alert, Alert.record_id == AMRRecord.id)
        .group_by(AMRRecord.pathogen_name)
        .order_by(desc("alert_count"))
        .limit(5)
        .all()
    )
    top_pathogens = [row.pathogen_name for row in top_pathogens_query]

    # Recent 5 alerts
    recent_alert_objs = (
        db.query(Alert).order_by(desc(Alert.timestamp)).limit(5).all()
    )
    recent_alerts = [_alert_to_response(a, db) for a in recent_alert_objs]

    return DashboardSummaryResponse(
        total_alerts=total_alerts,
        alerts_last_30_days=alerts_last_30,
        high_risk_counties=high_risk_counties,
        top_pathogens=top_pathogens,
        recent_alerts=recent_alerts,
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
        query = query.join(AMRRecord, AMRRecord.id == Alert.record_id)
        if county:
            query = query.filter(AMRRecord.county.ilike(f"%{county}%"))
        if pathogen:
            query = query.filter(AMRRecord.pathogen_name.ilike(f"%{pathogen}%"))

    if start_date:
        query = query.filter(Alert.timestamp >= start_date)
    if end_date:
        query = query.filter(Alert.timestamp <= end_date)

    alerts = query.order_by(desc(Alert.timestamp)).offset(skip).limit(limit).all()
    return [_alert_to_response(a, db) for a in alerts]


# ── POST /intelligence/alerts/{alert_id}/advisory ─────────────────────────────────

@router.post(
    "/intelligence/alerts/{alert_id}/advisory",
    response_model=GuidanceResponse,
    summary="Generate LLM advisory brief for an alert",
    description=(
        "Triggers LLMAdvisoryEngine (Claude claude-sonnet-4-5) to generate a role-specific "
        "Markdown advisory brief for the specified alert. Role-gated: National Coordinator "
        "or County Veterinarian only."
    ),
    tags=["AI Dashboard Insights"],
)
async def generate_advisory(
    alert_id: int,
    request: GuidanceRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(
        RoleChecker([ROLE_NATIONAL_COORDINATOR, ROLE_COUNTY_VETERINARIAN, ROLE_COUNTY_CLINICIAN])
    ),
) -> GuidanceResponse:
    from src.services.intelligence.llm_advisory import LLMAdvisoryEngine

    # Verify alert exists
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert ID {alert_id} not found.")

    if request.alert_id != alert_id:
        raise HTTPException(
            status_code=400,
            detail="alert_id in request body must match the URL path parameter.",
        )

    try:
        engine = LLMAdvisoryEngine()
        guidance = engine.generate_advisory(
            alert_id=alert_id,
            role=request.user_role,
            db=db,
        )
        db.commit()
        db.refresh(guidance)
        return guidance

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Advisory generation failed for alert %d: %s", alert_id, exc)
        raise HTTPException(status_code=500, detail="Advisory generation encountered an internal error.")


# ── GET /intelligence/forecasts/{county} ──────────────────────────────────────────

@router.get(
    "/intelligence/forecasts/{county}",
    response_model=CountyForecastResponse,
    summary="24-month resistance trajectory forecast for a county",
    description=(
        "On-demand Prophet time-series forecast. Returns 24 months of projected "
        "resistance event counts for the specified county and optional pathogen filter."
    ),
    tags=["AI Dashboard Insights"],
)
async def get_county_forecast(
    county: str,
    pathogen: Optional[str] = Query(None, description="Filter forecast to a specific pathogen"),
    sector: Optional[str] = Query(None, description="Filter by sector: human, animal, environment"),
    periods: int = Query(24, ge=3, le=60, description="Forecast horizon in months"),
    db: Session = Depends(get_db),
) -> CountyForecastResponse:
    from src.services.ml_engine.forecaster import AMRForecaster

    forecaster = AMRForecaster()
    result = forecaster.generate_forecast(
        county=county, db=db, pathogen=pathogen, sector=sector, periods=periods
    )

    forecast_points = [
        ForecastDataPoint(
            ds=fp["ds"],
            yhat=fp["yhat"],
            yhat_lower=fp["yhat_lower"],
            yhat_upper=fp["yhat_upper"],
        )
        for fp in result["forecast"]
    ]

    return CountyForecastResponse(
        county=result["county"],
        pathogen=result.get("pathogen"),
        generated_at=datetime.fromisoformat(result["generated_at"]),
        periods=result["periods"],
        historical_points=result["historical_points"],
        forecast=forecast_points,
    )
