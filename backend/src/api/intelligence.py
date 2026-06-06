# Track: backend/feature-api-name
# Intelligence API Router v1.3
# Route: GET /api/v1/intelligence/heatmap — eliminates hardcoded centroids
# Route: GET /api/v1/intelligence/dashboard/summary — live telemetry

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from typing import List, Optional

from src.core.security import RoleChecker, TokenData
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief
from src.schemas.intelligence import (
    DashboardTelemetrySummary,
    HeatmapGeoJsonResponse,
    GeoCentroidLocation,
    ResistanceBreakdown,
)

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
    Assembles real-time macro telemetry indexes across human and animal health clusters.
    Gated via strict RBAC controls to protect public health dashboards.
    Uses single JOIN query to prevent N+1 SELECT patterns.
    """
    # ── Aggregate counts ───────────────────────────────────────────────────────
    total_scanned = db.query(AMRRecord).count()
    active_hotspots = db.query(Alert).filter(Alert.status == "PENDING").count()

    clean_count = (
        db.query(AMRRecord)
        .filter(AMRRecord.data_quality_score >= 0.85)
        .count()
    )
    compliance_index = round((clean_count / total_scanned) if total_scanned > 0 else 1.0, 2)

    # ── Resistance breakdown (vectorized SQL aggregate) ────────────────────────
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

    # ── Top 5 resistant pathogens ──────────────────────────────────────────────
    top_pathogens = (
        db.query(AMRRecord.pathogen_name, func.count(AMRRecord.id).label("count"))
        .filter(AMRRecord.sir_result == "R")
        .group_by(AMRRecord.pathogen_name)
        .order_by(func.count(AMRRecord.id).desc())
        .limit(5)
        .all()
    )
    top_pathogens_list = [{"pathogen": row[0], "count": row[1]} for row in top_pathogens]

    # ── Recent anomalies (single JOIN — no N+1) ────────────────────────────────
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
                "antimicrobial_agent": record.antimicrobial_agent,
                "sir_result":       record.sir_result,
                "anomaly_score":    float(alert.anomaly_score),
                "data_quality_score": float(record.data_quality_score or 1.0),
            })

    from datetime import datetime, timezone
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
    description=(
        "Streams multi-sector coordinate geometries to Lowell's Leaflet map renderer. "
        "Queries LIVE database latitude/longitude columns — zero hardcoded centroids."
    ),
)
async def get_heatmap_coordinates(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"])),
    county: Optional[str] = Query(None, description="Filter by specific county"),
    sector: Optional[str] = Query(None, description="Filter by sector: HUMAN | ANIMAL | ENVIRONMENT"),
    limit: int = Query(500, ge=1, le=2000, description="Max records to return"),
):
    """
    Returns heatmap data points from live DB geo coordinates.
    Eliminates all hardcoded city data elements.
    Only returns records that have actual latitude/longitude coordinates stored.
    """
    query = (
        db.query(AMRRecord)
        .filter(
            AMRRecord.latitude.isnot(None),
            AMRRecord.longitude.isnot(None),
        )
    )

    if county:
        query = query.filter(AMRRecord.county.ilike(f"%{county}%"))
    if sector:
        query = query.filter(AMRRecord.sector == sector.upper())

    records = query.limit(limit).all()
    heatmap_collection = []

    for row in records:
        # Normalize intensity weight: use resistance_rate if available,
        # else fall back to data_quality_score as a proxy signal
        intensity = (
            float(row.resistance_rate)
            if row.resistance_rate is not None
            else float(row.data_quality_score or 1.0)
        )
        # Clamp to 0.0–1.0 range
        intensity = max(0.0, min(1.0, intensity))

        heatmap_collection.append({
            "location": {
                "county":    row.county,
                "sub_county": row.sub_county,
                "latitude":  float(row.latitude),
                "longitude": float(row.longitude),
            },
            "intensity_weight":  intensity,
            "pathogen_profile":  str(row.pathogen_name),
            "resistance_level":  str(row.sir_result),
            "classification":    row.classification,
            "resistance_percent": float(row.resistance_percent) if row.resistance_percent is not None else None,
            "sector":            row.sector,
            "sample_count":      row.sample_size,
        })

    return heatmap_collection
