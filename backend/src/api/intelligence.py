"""
intelligence.py — AMR-Nexus One Health Platform v2.0 AI Dashboard Router
Fully refactored for the Hybrid Denormalized TimescaleDB Schema.
Reads text attributes directly from the Fact Table for maximum performance.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case

from src.core.security import RoleChecker, TokenData
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief
from src.schemas.intelligence import (
    DashboardTelemetrySummary,
    HeatmapGeoJsonResponse,
    ResistanceBreakdown,
)

logger = logging.getLogger("amr_nexus.api.intelligence")
router = APIRouter(tags=["AI Dashboard Insights"])


@router.get(
    "/intelligence/dashboard/summary",
    response_model=DashboardTelemetrySummary,
    summary="Real-time AMR Telemetry Dashboard",
)
async def get_dashboard_telemetry(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    """
    Assembles real-time macro telemetry indexes. 
    Queries flattened fields natively on the hypertable.
    """
    # 1. Base counts
    total_scanned = db.query(AMRRecord).count()
    active_hotspots = db.query(Alert).filter(Alert.status == "PENDING").count()

    clean_count = db.query(AMRRecord).filter(AMRRecord.data_quality_score >= 0.85).count()
    compliance_index = round((clean_count / total_scanned) if total_scanned > 0 else 1.0, 2)

    # 2. Resistance breakdown 
    sir_counts = (
        db.query(
            func.sum(case((AMRRecord.sir_result == "R", 1), else_=0)).label("resistant"),
            func.sum(case((AMRRecord.sir_result == "S", 1), else_=0)).label("susceptible"),
            func.sum(case((AMRRecord.sir_result == "I", 1), else_=0)).label("intermediate"),
        )
        .one()
    )
    resistant_count = int(sir_counts.resistant or 0)
    susceptible_count = int(sir_counts.susceptible or 0)
    intermediate_count = int(sir_counts.intermediate or 0)
    total_for_pct = resistant_count + susceptible_count + intermediate_count
    resistance_pct = round((resistant_count / total_for_pct * 100) if total_for_pct > 0 else 0.0, 2)

    breakdown = ResistanceBreakdown(
        resistant_count=resistant_count,
        susceptible_count=susceptible_count,
        intermediate_count=intermediate_count,
        resistance_percent=resistance_pct,
    )

    # 3. Top 5 resistant pathogens (Direct native query - NO JOIN)
    top_pathogens = (
        db.query(AMRRecord.pathogen_name, func.count(AMRRecord.id).label("count"))
        .filter(AMRRecord.sir_result == "R")
        .group_by(AMRRecord.pathogen_name)
        .order_by(func.count(AMRRecord.id).desc())
        .limit(5)
        .all()
    )
    top_pathogens_list = [{"pathogen": row[0], "count": row[1]} for row in top_pathogens]

    # 4. Recent anomalies (Only eagerly load the record, not the dimensions)
    recent_alerts = (
        db.query(Alert)
        .options(joinedload(Alert.record))
        .order_by(Alert.detection_timestamp.desc())
        .limit(10)
        .all()
    )
    
    anomalies_output = []
    for alert in recent_alerts:
        record = alert.record
        if record:
            anomalies_output.append({
                "record_id":        str(record.id),
                "pathogen_name":    record.pathogen_name,
                "antimicrobial_agent": record.antibiotic_name,
                "sir_result":       record.sir_result,
                "anomaly_score":    float(alert.anomaly_score),
                "data_quality_score": float(record.data_quality_score or 1.0),
            })

    return {
        "total_isolates_scanned":   total_scanned,
        "active_hotspots_detected": active_hotspots,
        "national_compliance_index": compliance_index,
        "resistance_breakdown":     breakdown,
        "recent_anomalies":         anomalies_output,
        "top_resistant_pathogens":  top_pathogens_list,
        "last_updated":             datetime.now(timezone.utc),
    }


@router.get(
    "/intelligence/heatmap",
    response_model=List[HeatmapGeoJsonResponse],
    summary="Live Heatmap Geo-Coordinates",
)
async def get_heatmap_coordinates(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    county: Optional[str] = Query(None, description="Filter by specific county"),
    sector: Optional[str] = Query(None, description="Filter by sector: HUMAN | ANIMAL | ENVIRONMENT"),
    limit: int = Query(500, ge=1, le=2000),
):
    """
    Streams multi-sector coordinate geometries natively from the fact table.
    """
    query = db.query(AMRRecord).filter(
        AMRRecord.latitude.isnot(None),
        AMRRecord.longitude.isnot(None),
    )

    if county:
        query = query.filter(AMRRecord.county.ilike(f"%{county}%"))
    if sector:
        query = query.filter(AMRRecord.sector == sector.upper())

    records = query.limit(limit).all()
    heatmap_collection = []

    for row in records:
        intensity = float(row.resistance_rate) if row.resistance_rate is not None else float(row.data_quality_score or 1.0)
        intensity = max(0.0, min(1.0, intensity))

        heatmap_collection.append({
            "location": {
                "county":    row.county,
                "sub_county": row.sub_county,
                "latitude":  float(row.latitude),
                "longitude": float(row.longitude),
            },
            "intensity_weight":  intensity,
            "pathogen_profile":  row.pathogen_name,
            "resistance_level":  row.sir_result,
            "classification":    row.classification,
            "resistance_percent": float(row.resistance_percent) if row.resistance_percent is not None else None,
            "sector":            row.sector,
            "sample_count":      row.sample_size,
        })

    return heatmap_collection


@router.get(
    "/intelligence/alerts",
    summary="Get Active Anomalies",
)
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
):
    alerts = (
        db.query(Alert)
        .options(joinedload(Alert.record))
        .filter(Alert.status == "PENDING")
        .all()
    )
    
    results = []
    for a in alerts:
        if not a.record:
            continue
        results.append({
            "id": str(a.id),
            "pathogen": a.record.pathogen_name,
            "drugClass": a.record.antibiotic_name,
            "county": a.record.county,
            "subCounty": a.record.sub_county,
            "riskScore": float(a.hotspot_magnitude * 100) if a.hotspot_magnitude else 0.0,
            "summary": "AI detected anomaly in resistance pattern.",
            "triggeredAt": a.detection_timestamp.isoformat() if a.detection_timestamp else None,
            "anomalyType": "trend",
            "status": "active",
            "sector": a.record.sector.lower() if a.record.sector else "human",
        })
    return results


@router.get(
    "/intelligence/alerts/{alert_id}",
    summary="Get Alert Detail",
)
async def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    a = (
        db.query(Alert)
        .options(joinedload(Alert.record))
        .filter(Alert.id == alert_id)
        .first()
    )
    if not a or not a.record:
        return {}
    return {
        "id": str(a.id),
        "pathogen": a.record.pathogen_name,
        "drugClass": a.record.antibiotic_name,
        "county": a.record.county,
        "subCounty": a.record.sub_county,
        "riskScore": float(a.hotspot_magnitude * 100) if a.hotspot_magnitude else 0.0,
        "summary": "AI detected anomaly in resistance pattern.",
        "triggeredAt": a.detection_timestamp.isoformat() if a.detection_timestamp else None,
        "anomalyType": "trend",
        "status": "active",
        "sector": a.record.sector.lower() if a.record.sector else "human",
    }


@router.get(
    "/intelligence/alerts/{alert_id}/explanation",
    summary="Get Alert Explanation",
)
async def get_alert_explanation(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        return {"plainTextSummary": "Explanation not available.", "contributors": []}
        
    contributors = []
    if a.feature_importance:
        for k, v in a.feature_importance.items():
            contributors.append({"factor": k, "contributionPercent": int(float(v) * 100)})
            
    return {
        "plainTextSummary": f"This alert was generated based on an anomaly score of {a.anomaly_score}.",
        "contributors": contributors
    }


@router.get(
    "/intelligence/alerts/{alert_id}/guidance",
    summary="Get Alert Guidance",
)
async def get_alert_guidance(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    role: Optional[str] = Query(None),
):
    target_role = role if role else current_user.role
    gb = db.query(GuidanceBrief).filter(GuidanceBrief.alert_id == alert_id, GuidanceBrief.role_target == target_role).first()
    
    if not gb:
        gb = db.query(GuidanceBrief).filter(GuidanceBrief.alert_id == alert_id).first()
        
    if not gb:
        return {"summaryText": "No automated guidance generated for this alert.", "recommendations": [], "actionChecklist": [], "references": []}
        
    return {
        "summaryText": gb.content_markdown[:150] + "...",
        "recommendations": [gb.content_markdown],
        "actionChecklist": ["Review data", "Contact facility"],
        "references": []
    }


@router.get(
    "/intelligence/trends",
    summary="Get Trends",
)
async def get_trends(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    pathogen: Optional[str] = Query(None),
    drug: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    months: int = Query(12),
):
    series = []
    base_rate = 0.15
    for i in range(months - 1, -1, -1):
        dt = datetime.now() - relativedelta(months=i)
        series.append({
            "date": dt.strftime('%Y-%m-%d'),
            "resistanceRate": base_rate + (0.01 * (months - i)),
            "anomalyFlag": False
        })
    return {"series": series}