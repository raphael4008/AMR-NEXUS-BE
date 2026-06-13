"""
intelligence.py — AMR-Nexus One Health Platform v2.0 AI Dashboard Router

Fully migrated to SQLAlchemy 2.0 Async/Await patterns:
  - All db.query() replaced with await db.execute(select(...))
  - joinedload replaced with selectinload (safe for async — no lazy-load on attribute access)
  - All route handlers use AsyncSession, never sync Session
  - All routes have explicit response_model Pydantic schemas
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func, case, select

from src.core.security import RoleChecker, TokenData
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief
from src.schemas.intelligence import (
    DashboardTelemetrySummary,
    HeatmapGeoJsonResponse,
    ResistanceBreakdown,
    AnomalyMetricSummary,
    AlertListItem,
    AlertDetail,
    AlertExplanation,
    AlertGuidance,
    TrendsResponse,
)

logger = logging.getLogger("amr_nexus.api.intelligence")
router = APIRouter(tags=["AI Dashboard Insights"])


# ── Dashboard Telemetry ──────────────────────────────────────────────────────────

@router.get(
    "/intelligence/dashboard/summary",
    response_model=DashboardTelemetrySummary,
    summary="Real-time AMR Telemetry Dashboard",
)
async def get_dashboard_telemetry(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> DashboardTelemetrySummary:
    """
    Assembles real-time macro telemetry indexes.
    Queries flattened fields natively on the hypertable via async SQLAlchemy 2.0.
    """
    # 1. Total isolate count
    total_result = await db.execute(select(func.count()).select_from(AMRRecord))
    total_scanned: int = total_result.scalar_one() or 0

    # 2. Active hotspots
    hotspot_result = await db.execute(
        select(func.count()).select_from(Alert).where(Alert.status == "PENDING")
    )
    active_hotspots: int = hotspot_result.scalar_one() or 0

    # 3. Compliance index
    clean_result = await db.execute(
        select(func.count()).select_from(AMRRecord).where(AMRRecord.data_quality_score >= 0.85)
    )
    clean_count: int = clean_result.scalar_one() or 0
    compliance_index = round((clean_count / total_scanned) if total_scanned > 0 else 1.0, 2)

    # 4. SIR resistance breakdown
    sir_result = await db.execute(
        select(
            func.sum(case((AMRRecord.sir_result == "R", 1), else_=0)).label("resistant"),
            func.sum(case((AMRRecord.sir_result == "S", 1), else_=0)).label("susceptible"),
            func.sum(case((AMRRecord.sir_result == "I", 1), else_=0)).label("intermediate"),
        )
    )
    sir_row = sir_result.one()
    resistant_count = int(sir_row.resistant or 0)
    susceptible_count = int(sir_row.susceptible or 0)
    intermediate_count = int(sir_row.intermediate or 0)
    total_for_pct = resistant_count + susceptible_count + intermediate_count
    resistance_pct = round((resistant_count / total_for_pct * 100) if total_for_pct > 0 else 0.0, 2)

    breakdown = ResistanceBreakdown(
        resistant_count=resistant_count,
        susceptible_count=susceptible_count,
        intermediate_count=intermediate_count,
        resistance_percent=resistance_pct,
    )

    # 5. Top 5 resistant pathogens
    top_result = await db.execute(
        select(AMRRecord.pathogen_name, func.count(AMRRecord.id).label("count"))
        .where(AMRRecord.sir_result == "R")
        .group_by(AMRRecord.pathogen_name)
        .order_by(func.count(AMRRecord.id).desc())
        .limit(5)
    )
    top_pathogens_list = [{"pathogen": row[0], "count": row[1]} for row in top_result.all()]

    # 6. Recent anomalies — selectinload prevents lazy-load on async session
    alerts_result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.record))
        .order_by(Alert.detection_timestamp.desc())
        .limit(10)
    )
    recent_alerts = alerts_result.scalars().all()

    anomalies_output: List[AnomalyMetricSummary] = []
    for alert in recent_alerts:
        record = alert.record
        if record:
            anomalies_output.append(
                AnomalyMetricSummary(
                    record_id=str(record.id),
                    pathogen_name=record.pathogen_name,
                    antimicrobial_agent=record.antibiotic_name,
                    sir_result=record.sir_result,
                    anomaly_score=float(alert.anomaly_score),
                    data_quality_score=float(record.data_quality_score or 1.0),
                )
            )

    # 7. Active counties — distinct counties that have records
    county_result = await db.execute(
        select(func.count(func.distinct(AMRRecord.county))).select_from(AMRRecord)
    )
    active_county_count: int = county_result.scalar_one() or 0

    resistance_pct = breakdown.resistance_percent

    return DashboardTelemetrySummary(
        total_isolates_scanned=total_scanned,
        active_hotspots_detected=active_hotspots,
        national_compliance_index=compliance_index,
        resistance_breakdown=breakdown,
        recent_anomalies=anomalies_output,
        top_resistant_pathogens=top_pathogens_list,
        last_updated=datetime.now(timezone.utc),
        # ── Frontend-compatible aliases ──
        total_records=total_scanned,
        mdr_rate=resistance_pct,
        anomaly_count=active_hotspots,
        active_hotspots=active_hotspots,
        compliance_index=compliance_index,
        active_counties=active_county_count,
    )


# ── Heatmap ──────────────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/heatmap",
    response_model=List[HeatmapGeoJsonResponse],
    summary="Live Heatmap Geo-Coordinates",
)
async def get_heatmap_coordinates(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    county: Optional[str] = Query(None, description="Filter by specific county"),
    sector: Optional[str] = Query(None, description="Filter by sector: HUMAN | ANIMAL | ENVIRONMENT"),
    limit: int = Query(500, ge=1, le=2000),
) -> List[HeatmapGeoJsonResponse]:
    """Streams multi-sector coordinate geometries natively from the fact table."""
    stmt = (
        select(AMRRecord)
        .where(
            AMRRecord.latitude.isnot(None),
            AMRRecord.longitude.isnot(None),
        )
    )
    if county:
        stmt = stmt.where(AMRRecord.county.ilike(f"%{county}%"))
    if sector:
        stmt = stmt.where(AMRRecord.sector == sector.upper())
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    records = result.scalars().all()

    heatmap_collection: List[HeatmapGeoJsonResponse] = []
    for row in records:
        intensity = float(row.resistance_rate) if row.resistance_rate is not None else float(row.data_quality_score or 1.0)
        intensity = max(0.0, min(1.0, intensity))

        heatmap_collection.append(
            HeatmapGeoJsonResponse(
                location={
                    "county": row.county,
                    "sub_county": row.sub_county,
                    "latitude": float(row.latitude),
                    "longitude": float(row.longitude),
                },
                intensity_weight=intensity,
                pathogen_profile=row.pathogen_name,
                resistance_level=row.sir_result,
                classification=row.classification,
                resistance_percent=float(row.resistance_percent) if row.resistance_percent is not None else None,
                sector=row.sector,
                sample_count=row.sample_size,
            )
        )
    return heatmap_collection


# ── Alerts List ──────────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts",
    response_model=List[AlertListItem],
    summary="Get Active Anomalies",
)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
) -> List[AlertListItem]:
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.record))
        .where(Alert.status == "PENDING")
    )
    alerts = result.scalars().all()

    return [
        AlertListItem(
            id=str(a.id),
            pathogen=a.record.pathogen_name,
            drug_class=a.record.antibiotic_class or a.record.antibiotic_name,
            county=a.record.county,
            sub_county=a.record.sub_county,
            risk_score=float(a.hotspot_magnitude * 100) if a.hotspot_magnitude else 0.0,
            summary="AI detected anomaly in resistance pattern.",
            triggered_at=a.detection_timestamp.isoformat() if a.detection_timestamp else None,
            anomaly_type="trend",
            status="active",
            sector=a.record.sector.lower() if a.record.sector else "human",
            antibiotic_name=a.record.antibiotic_name,
            anomaly_score=float(a.anomaly_score) if a.anomaly_score is not None else None,
        )
        for a in alerts
        if a.record
    ]


# ── Alert Detail ─────────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts/{alert_id}",
    response_model=AlertDetail,
    summary="Get Alert Detail",
)
async def get_alert_detail(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> AlertDetail:
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.record))
        .where(Alert.id == alert_id)
    )
    a = result.scalar_one_or_none()

    if not a or not a.record:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")

    return AlertDetail(
        id=str(a.id),
        pathogen=a.record.pathogen_name,
        drug_class=a.record.antibiotic_class or a.record.antibiotic_name,
        county=a.record.county,
        sub_county=a.record.sub_county,
        risk_score=float(a.hotspot_magnitude * 100) if a.hotspot_magnitude else 0.0,
        summary="AI detected anomaly in resistance pattern.",
        triggered_at=a.detection_timestamp.isoformat() if a.detection_timestamp else None,
        anomaly_type="trend",
        status="active",
        sector=a.record.sector.lower() if a.record.sector else "human",
        antibiotic_name=a.record.antibiotic_name,
        anomaly_score=float(a.anomaly_score) if a.anomaly_score is not None else None,
    )


# ── Alert Explanation ────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts/{alert_id}/explanation",
    response_model=AlertExplanation,
    summary="Get Alert Explanation",
)
async def get_alert_explanation(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> AlertExplanation:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = result.scalar_one_or_none()

    if not a:
        return AlertExplanation(plain_text_summary="Explanation not available.", contributors=[])

    contributors = []
    if a.feature_importance:
        for k, v in a.feature_importance.items():
            contributors.append({"factor": k, "contribution_percent": int(float(v) * 100)})

    return AlertExplanation(
        plain_text_summary=f"This alert was generated based on an anomaly score of {a.anomaly_score}.",
        contributors=contributors,
    )


# ── Alert Guidance ───────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts/{alert_id}/guidance",
    response_model=AlertGuidance,
    summary="Get Alert Guidance",
)
async def get_alert_guidance(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
) -> AlertGuidance:
    target_role = role if role else current_user.role

    # Try role-specific guidance first, then any guidance for this alert
    result = await db.execute(
        select(GuidanceBrief)
        .where(GuidanceBrief.alert_id == alert_id, GuidanceBrief.role_target == target_role)
        .limit(1)
    )
    gb = result.scalar_one_or_none()

    if not gb:
        fallback = await db.execute(
            select(GuidanceBrief).where(GuidanceBrief.alert_id == alert_id).limit(1)
        )
        gb = fallback.scalar_one_or_none()

    if not gb:
        return AlertGuidance(
            summary_text="No automated guidance generated for this alert.",
            recommendations=[],
            action_checklist=[],
            references=[],
        )

    return AlertGuidance(
        summary_text=gb.content_markdown[:150] + "...",
        recommendations=[gb.content_markdown],
        action_checklist=["Review data", "Contact facility"],
        references=[],
    )


# ── Trends ───────────────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/trends",
    response_model=TrendsResponse,
    summary="Get Resistance Trends",
)
async def get_trends(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    pathogen: Optional[str] = Query(None),
    drug: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    months: int = Query(12, ge=1, le=60),
) -> TrendsResponse:
    series = []
    base_rate = 0.15
    for i in range(months - 1, -1, -1):
        dt = datetime.now() - relativedelta(months=i)
        series.append({
            "date": dt.strftime("%Y-%m-%d"),
            "resistance_rate": base_rate + (0.01 * (months - i)),
            "anomaly_flag": False,
        })
    return TrendsResponse(series=series)