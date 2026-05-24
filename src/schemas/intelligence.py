"""
schemas/intelligence.py — Outbound API contract for Component B & C outputs.

Covers:
  - AlertSummaryResponse: anomaly engine outputs surfaced to the dashboard
  - ForecastDataPoint / CountyForecastResponse: Prophet trajectory payloads
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


# ── Forecast Schemas ──────────────────────────────────────────────────────────────

class ForecastDataPoint(BaseModel):
    """Single Prophet forecast row."""
    ds: str = Field(..., description="Forecast date in YYYY-MM-DD format")
    yhat: float = Field(..., description="Predicted resistance event count")
    yhat_lower: float = Field(..., description="Lower confidence bound (80%)")
    yhat_upper: float = Field(..., description="Upper confidence bound (80%)")


class CountyForecastResponse(BaseModel):
    """24-month resistance trajectory for a county/pathogen combination."""
    county: str
    pathogen: Optional[str] = None
    generated_at: datetime
    periods: int = Field(24, description="Number of forecast months")
    historical_points: int = Field(..., description="Number of historical data points used to fit the model")
    forecast: List[ForecastDataPoint]


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
