"""
intelligence.py — AMR-Nexus One Health Platform v2.2 AI Dashboard Router

All routes query real database data — no hardcoded or synthetic series.
Trends use GROUP BY sample_year/sample_month with statistical forecast projection.
RBAC: National Coordinator sees all; County Veterinarian sees own county only.
"""

import logging
import math
from datetime import datetime, timezone, date
from typing import List, Optional

from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func, case, select, and_

from src.core.security import RoleChecker, TokenData, ROLE_NATIONAL_COORDINATOR
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
    TrendPoint,
    RiskSummaryResponse,
)

logger = logging.getLogger("amr_nexus.api.intelligence")
router = APIRouter(tags=["AI Dashboard Insights"])


# ── RBAC helper ───────────────────────────────────────────────────────────────

def _apply_county_scope(stmt, current_user: TokenData):
    """
    Applies county filter when the user is a County Veterinarian.
    National Coordinator has unrestricted access.
    """
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        stmt = stmt.where(AMRRecord.county == current_user.county)
    return stmt


# ── Dashboard Telemetry ───────────────────────────────────────────────────────

@router.get("/analytics/summary",
    response_model=DashboardTelemetrySummary,
    summary="Real-time AMR Telemetry Dashboard",
)
async def get_dashboard_telemetry(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> DashboardTelemetrySummary:
    """Assembles real-time macro telemetry from the database, scoped by role."""

    base_stmt = select(AMRRecord)
    base_stmt = _apply_county_scope(base_stmt, current_user)

    # 1. Total isolate count (scoped)
    total_result = await db.execute(
        select(func.count()).select_from(base_stmt.subquery())
    )
    total_scanned: int = total_result.scalar_one() or 0

    # 2. Active hotspots (alerts scoped via AMRRecord join)
    hotspot_stmt = (
        select(func.count())
        .select_from(Alert)
        .join(AMRRecord, Alert.amr_isolate_record_id == AMRRecord.id)
        .where(Alert.status == "PENDING")
    )
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        hotspot_stmt = hotspot_stmt.where(AMRRecord.county == current_user.county)
    hotspot_result = await db.execute(hotspot_stmt)
    active_hotspots: int = hotspot_result.scalar_one() or 0

    # 3. Compliance index
    clean_stmt = select(func.count()).select_from(
        base_stmt.where(AMRRecord.data_quality_score >= 0.85).subquery()
    )
    clean_result = await db.execute(clean_stmt)
    clean_count: int = clean_result.scalar_one() or 0
    compliance_index = round((clean_count / total_scanned) if total_scanned > 0 else 1.0, 2)

    # 4. SIR resistance breakdown (scoped)
    scoped_sub = base_stmt.subquery()
    sir_result = await db.execute(
        select(
            func.sum(case((scoped_sub.c.sir_result == "R", 1), else_=0)).label("resistant"),
            func.sum(case((scoped_sub.c.sir_result == "S", 1), else_=0)).label("susceptible"),
            func.sum(case((scoped_sub.c.sir_result == "I", 1), else_=0)).label("intermediate"),
        )
    )
    sir_row = sir_result.one()
    resistant_count    = int(sir_row.resistant or 0)
    susceptible_count  = int(sir_row.susceptible or 0)
    intermediate_count = int(sir_row.intermediate or 0)
    total_for_pct      = resistant_count + susceptible_count + intermediate_count
    resistance_pct     = round((resistant_count / total_for_pct * 100) if total_for_pct > 0 else 0.0, 2)

    breakdown = ResistanceBreakdown(
        resistant_count=resistant_count,
        susceptible_count=susceptible_count,
        intermediate_count=intermediate_count,
        resistance_percent=resistance_pct,
    )

    # 5. Top 5 resistant pathogens (scoped)
    top_stmt = (
        select(AMRRecord.pathogen_name, func.count(AMRRecord.id).label("count"))
        .where(AMRRecord.sir_result == "R")
        .group_by(AMRRecord.pathogen_name)
        .order_by(func.count(AMRRecord.id).desc())
        .limit(5)
    )
    top_stmt = _apply_county_scope(top_stmt, current_user)
    top_result = await db.execute(top_stmt)
    top_pathogens_list = [{"pathogen": row[0], "count": row[1]} for row in top_result.all()]

    # 6. Recent anomalies
    alert_stmt = (
        select(Alert)
        .join(AMRRecord, Alert.amr_isolate_record_id == AMRRecord.id)
        .options(selectinload(Alert.record))
        .order_by(Alert.detection_timestamp.desc())
        .limit(10)
    )
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        alert_stmt = alert_stmt.where(AMRRecord.county == current_user.county)
    alerts_result = await db.execute(alert_stmt)
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

    # 7. Active counties
    county_stmt = select(func.count(func.distinct(AMRRecord.county))).select_from(AMRRecord)
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        county_stmt = county_stmt.where(AMRRecord.county == current_user.county)
    county_result = await db.execute(county_stmt)
    active_county_count: int = county_result.scalar_one() or 0

    return DashboardTelemetrySummary(
        total_isolates_scanned=total_scanned,
        active_hotspots_detected=active_hotspots,
        national_compliance_index=compliance_index,
        resistance_breakdown=breakdown,
        recent_anomalies=anomalies_output,
        top_resistant_pathogens=top_pathogens_list,
        last_updated=datetime.now(timezone.utc),
        total_records=total_scanned,
        mdr_rate=resistance_pct,
        anomaly_count=active_hotspots,
        active_hotspots=active_hotspots,
        compliance_index=compliance_index,
        active_counties=active_county_count,
    )


# ── Heatmap ───────────────────────────────────────────────────────────────────

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
    """Streams multi-sector coordinate geometries from the fact table, scoped by role."""
    stmt = select(AMRRecord).where(
        AMRRecord.latitude.isnot(None),
        AMRRecord.longitude.isnot(None),
    )
    stmt = _apply_county_scope(stmt, current_user)
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
                    "county":    row.county,
                    "sub_county": row.sub_county,
                    "latitude":  float(row.latitude),
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


# ── Trends (Real DB Query + Optional Forecast) ────────────────────────────────

@router.get("/analytics/mdr_trend",
    response_model=TrendsResponse,
    summary="Resistance Trends from Real Data (with optional forecast)",
)
async def get_trends(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    pathogen: Optional[str] = Query(None),
    drug:     Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
    county:   Optional[str] = Query(None),
    months:   int           = Query(12, ge=1, le=60),
    forecast: bool          = Query(False, description="Append a statistical forecast series"),
    forecast_months: int    = Query(3, ge=1, le=24),
) -> TrendsResponse:
    """
    Queries the real amr_isolate_records table, groups by year+month, computes
    resistance rate (resistant / total) per period, then optionally appends a
    linear-regression forecast for the requested number of future months.

    County Veterinarians automatically see only their county's data.
    """
    # Cut-off date: go back `months` calendar months from now
    cutoff = datetime.now(timezone.utc) - relativedelta(months=months)

    stmt = (
        select(
            AMRRecord.sample_year.label("yr"),
            AMRRecord.sample_month.label("mo"),
            func.count(AMRRecord.id).label("total"),
            func.sum(case((AMRRecord.sir_result == "R", 1), else_=0)).label("resistant"),
        )
        .where(
            AMRRecord.sample_year.isnot(None),
            AMRRecord.sample_month.isnot(None),
            AMRRecord.sample_collection_date >= cutoff,
            AMRRecord.deleted_at.is_(None),
        )
        .group_by(AMRRecord.sample_year, AMRRecord.sample_month)
        .order_by(AMRRecord.sample_year, AMRRecord.sample_month)
    )

    # Role-based county scoping
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        stmt = stmt.where(AMRRecord.county == current_user.county)
    if county:
        stmt = stmt.where(AMRRecord.county.ilike(f"%{county}%"))
    if pathogen:
        stmt = stmt.where(AMRRecord.pathogen_name.ilike(f"%{pathogen}%"))
    if drug:
        stmt = stmt.where(
            (AMRRecord.antibiotic_name.ilike(f"%{drug}%")) |
            (AMRRecord.antibiotic_class.ilike(f"%{drug}%"))
        )
    if region:
        stmt = stmt.where(AMRRecord.county.ilike(f"%{region}%"))

    result = await db.execute(stmt)
    rows = result.all()

    series: List[TrendPoint] = []
    rates: List[float] = []

    for row in rows:
        yr, mo, total, resistant = row.yr, row.mo, row.total, (row.resistant or 0)
        rate = round(resistant / total, 4) if total > 0 else 0.0
        rates.append(rate)
        # Compute anomaly flag: simple z-score threshold (>1.5 std above running mean)
        anomaly = False
        if len(rates) >= 3:
            mu  = sum(rates) / len(rates)
            var = sum((r - mu) ** 2 for r in rates) / len(rates)
            std = math.sqrt(var) if var > 0 else 0
            anomaly = std > 0 and (rate - mu) / std > 1.5

        series.append(TrendPoint(
            date=f"{yr}-{mo:02d}-01",
            resistance_rate=rate,
            anomaly_flag=anomaly,
            forecast=False,
        ))

    # ── Statistical forecast (simple linear regression) ──────────────────────
    if forecast and len(series) >= 2:
        n = len(rates)
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(rates) / n
        numerator   = sum((xs[i] - x_mean) * (rates[i] - y_mean) for i in range(n))
        denominator = sum((xs[i] - x_mean) ** 2 for i in range(n))
        slope     = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        last_series_date = datetime.strptime(series[-1].date, "%Y-%m-%d")
        for j in range(1, forecast_months + 1):
            future_dt   = last_series_date + relativedelta(months=j)
            future_rate = max(0.0, min(1.0, intercept + slope * (n + j - 1)))
            series.append(TrendPoint(
                date=future_dt.strftime("%Y-%m-%d"),
                resistance_rate=round(future_rate, 4),
                anomaly_flag=False,
                forecast=True,
            ))

    return TrendsResponse(series=series)


# ── Risk Summary ──────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/risk-summary",
    response_model=RiskSummaryResponse,
    summary="Aggregated Risk Summary across anomaly scores and hotspot magnitude",
)
async def get_risk_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> RiskSummaryResponse:
    """
    Aggregates alert anomaly scores to produce a national or county-scoped risk picture.
    """
    alert_stmt = (
        select(
            func.count(Alert.id).label("total_alerts"),
            func.avg(Alert.anomaly_score).label("avg_score"),
            func.max(Alert.hotspot_magnitude).label("max_magnitude"),
            func.sum(case((Alert.anomaly_score >= 0.8, 1), else_=0)).label("critical"),
            func.sum(case((and_(Alert.anomaly_score >= 0.5, Alert.anomaly_score < 0.8), 1), else_=0)).label("high"),
            func.sum(case((Alert.anomaly_score < 0.5, 1), else_=0)).label("medium"),
        )
        .join(AMRRecord, Alert.amr_isolate_record_id == AMRRecord.id)
        .where(Alert.status == "PENDING")
    )
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        alert_stmt = alert_stmt.where(AMRRecord.county == current_user.county)

    row = (await db.execute(alert_stmt)).one()

    # Top risky counties
    county_stmt = (
        select(
            AMRRecord.county,
            func.avg(Alert.anomaly_score).label("avg_score"),
            func.count(Alert.id).label("alert_count"),
        )
        .join(AMRRecord, Alert.amr_isolate_record_id == AMRRecord.id)
        .where(Alert.status == "PENDING")
        .group_by(AMRRecord.county)
        .order_by(func.avg(Alert.anomaly_score).desc())
        .limit(5)
    )
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        county_stmt = county_stmt.where(AMRRecord.county == current_user.county)
    county_rows = (await db.execute(county_stmt)).all()

    return RiskSummaryResponse(
        total_alerts=int(row.total_alerts or 0),
        avg_anomaly_score=round(float(row.avg_score or 0), 3),
        max_hotspot_magnitude=round(float(row.max_magnitude or 0), 3),
        critical_count=int(row.critical or 0),
        high_count=int(row.high or 0),
        medium_count=int(row.medium or 0),
        top_risk_counties=[
            {"county": cr.county, "avg_score": round(float(cr.avg_score), 3), "alert_count": int(cr.alert_count)}
            for cr in county_rows
        ],
    )


# ── Alerts List ───────────────────────────────────────────────────────────────

@router.get("/alerts",
    response_model=List[AlertListItem],
    summary="Get Active Anomaly Alerts",
)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
) -> List[AlertListItem]:
    stmt = (
        select(Alert)
        .join(AMRRecord, Alert.amr_isolate_record_id == AMRRecord.id)
        .options(selectinload(Alert.record))
        .where(Alert.status == "PENDING")
    )
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        stmt = stmt.where(AMRRecord.county == current_user.county)

    alerts = (await db.execute(stmt)).scalars().all()

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


# ── Alert Detail ──────────────────────────────────────────────────────────────

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
    stmt = (
        select(Alert)
        .options(selectinload(Alert.record))
        .where(Alert.id == alert_id)
    )
    a = (await db.execute(stmt)).scalar_one_or_none()

    if not a or not a.record:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")

    # County Vet can only view alerts within their county
    if current_user.role != ROLE_NATIONAL_COORDINATOR and current_user.county:
        if a.record.county != current_user.county:
            raise HTTPException(status_code=403, detail="Access restricted to your county.")

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


# ── Alert Explanation ─────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts/{alert_id}/explanation",
    response_model=AlertExplanation,
    summary="Get Alert Explanation (SHAP contributors)",
)
async def get_alert_explanation(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
) -> AlertExplanation:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = result.scalar_one_or_none()

    if not a:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")

    contributors = []
    if a.feature_importance:
        for k, v in a.feature_importance.items():
            contributors.append({"factor": k, "contribution_percent": int(float(v) * 100)})

    summary = (
        f"Anomaly detected with score {round(float(a.anomaly_score), 3)}. "
        f"Hotspot magnitude: {round(float(a.hotspot_magnitude), 3)}."
    )
    return AlertExplanation(plain_text_summary=summary, contributors=contributors)


# ── Alert Guidance ────────────────────────────────────────────────────────────

@router.get(
    "/intelligence/alerts/{alert_id}/guidance",
    response_model=AlertGuidance,
    summary="Get Role-Specific Alert Guidance",
)
async def get_alert_guidance(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
) -> AlertGuidance:
    target_role = role if role else current_user.role

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
        raise HTTPException(
            status_code=404,
            detail="No guidance generated for this alert yet. Trigger decision support to generate it.",
        )

    return AlertGuidance(
        summary_text=gb.content_markdown[:200] + "..." if len(gb.content_markdown) > 200 else gb.content_markdown,
        recommendations=[gb.content_markdown],
        action_checklist=["Review isolate data", "Contact reporting facility", "Escalate if recurring"],
        references=[],
    )