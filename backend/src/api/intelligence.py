# Track: backend/feature-api-name
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.core.security import RoleChecker, TokenData, get_current_user_token
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief
from src.schemas.intelligence import DashboardTelemetrySummary, HeatmapGeoJsonResponse

router = APIRouter(tags=["AI Dashboard Insights Resource"])

@router.get("/intelligence/dashboard/summary", response_model=DashboardTelemetrySummary)
async def get_dashboard_telemetry(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(RoleChecker(["National Coordinator", "County Veterinarian"]))
):
    """
    Assembles real-time macro telemetry indexes across human and animal health clusters.
    Gated via strict RBAC controls to protect public health dashboards.
    """
    # High-performance analytical counts optimized with PostgreSQL indexes
    total_scanned = db.query(AMRRecord).count()
    active_hotspots = db.query(Alert).filter(Alert.status == "PENDING").count()
    
    # Calculate synthetic proxy compliance based on validated row counts
    clean_count = db.query(AMRRecord).filter(AMRRecord.data_quality_score >= 0.85).count()
    compliance_index = (clean_count / total_scanned) if total_scanned > 0 else 1.0

    # Fetch recent anomalies containing new genomic/surveillance markers
    recent_alerts = db.query(Alert).order_by(Alert.detection_timestamp.desc()).limit(10).all()
    anomalies_output = []
    
    for alert in recent_alerts:
        record = db.query(AMRRecord).filter(AMRRecord.id == alert.record_id).first()
        if record:
            anomalies_output.append({
                "record_id": str(record.record_id),
                "pathogen_name": record.pathogen_name,
                "antimicrobial_agent": record.antimicrobial_agent,
                "sir_result": record.result_value,
                "anomaly_score": float(alert.anomaly_score),
                "data_quality_score": float(record.data_quality_score)
            })

    return {
        "total_isolates_scanned": total_scanned,
        "active_hotspots_detected": active_hotspots,
        "national_compliance_index": round(compliance_index, 2),
        "recent_anomalies": anomalies_output
    }

@router.get("/intelligence/heatmap", response_model=List[HeatmapGeoJsonResponse])
async def get_heatmap_coordinates(db: Session = Depends(get_db)):
    """
    Streams multi-sector coordinate geometries to Lowell's Leaflet map renderer.
    """
    # Aggregate data using standard grouping fields
    records = db.query(AMRRecord).filter(AMRRecord.latitude.isnot(None)).limit(500).all()
    heatmap_collection = []

    for row in records:
        heatmap_collection.append({
            "location": {
                "county": row.county,
                "latitude": float(row.latitude),
                "longitude": float(row.longitude)
            },
            "intensity_weight": float(row.data_quality_score),
            "pathogen_profile": f"{row.pathogen_name} ({row.pathogen_code})",
            "resistance_level": row.result_value
        })

    return heatmap_collection
