"""
schemas/intelligence.py — Outbound API contract for Component B & C outputs.

Covers:
  - AlertSummaryResponse: anomaly engine outputs surfaced to the dashboard
  - DashboardSummaryResponse: high-level telemetry for the frontend
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict


# ── Anomaly Alert Schemas ─────────────────────────────────────────────────────────

class AlertSummaryResponse(BaseModel):
    """Serialized Alert row for dashboard and analytics endpoints."""
    id: int
    record_id: int
    timestamp: datetime
    county: str
    pathogen_name: str
    antimicrobial_agent: str
    sector: str
    anomaly_score: float = Field(..., description="IsolationForest decision function score (negative = anomaly)")
    hotspot_magnitude: float = Field(..., description="Normalized severity; higher = more severe")
    feature_importance: Optional[Dict[str, Any]] = Field(
        None, description="SHAP feature weight map: county_weight, pathogen_risk_weight, etc."
    )

    model_config = ConfigDict(from_attributes=True)



# ── Geography & Trend Schemas ─────────────────────────────────────────────────────

class GeographicCoordinate(BaseModel):
    county: str
    lat: float
    lng: float

class GuidanceBriefResponse(BaseModel):
    id: int
    alert_id: int
    user_role: str
    guidance_markdown: Optional[str]
    status: str

# ── Dashboard Summary ─────────────────────────────────────────────────────────────

class DashboardSummaryResponse(BaseModel):
    """High-level telemetry for the AMR-Nexus intelligence dashboard."""
    total_alerts: int
    alerts_last_30_days: int
    high_risk_counties: List[str] = Field(
        ..., description="Counties with the highest hotspot_magnitude in the current period"
    )
    top_pathogens: List[str] = Field(
        ..., description="Pathogens most frequently appearing in alerts"
    )
    recent_alerts: List[AlertSummaryResponse]
    geographic_coordinates: List[GeographicCoordinate] = Field(
        default_factory=list, description="Lat/lng coordinates mapping for UI."
    )
    trend_values: List[Dict[str, Any]] = Field(
        default_factory=list, description="Trend value series over time."
    )
    guidance_briefs: List[GuidanceBriefResponse] = Field(
        default_factory=list, description="Recent role-gated guidance generated."
    )
