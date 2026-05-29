# Track: backend/feature-api-name
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class GeoCentroidLocation(BaseModel):
    county: str = Field(..., examples=["Nairobi", "Kiambu", "Machakos"])
    latitude: float = Field(..., json_schema_extra={"geo_upper_bound": 90.0, "geo_lower_bound": -90.0})
    longitude: float = Field(..., json_schema_extra={"geo_upper_bound": 180.0, "geo_lower_bound": -180.0})

class AnomalyMetricSummary(BaseModel):
    record_id: str
    pathogen_name: str
    antimicrobial_agent: str
    sir_result: str
    anomaly_score: float
    data_quality_score: float

class DynamicRoleGuidanceResponse(BaseModel):
    alert_id: int
    user_role: str
    guidance_markdown: str
    generated_at: datetime

class DashboardTelemetrySummary(BaseModel):
    total_isolates_scanned: int
    active_hotspots_detected: int
    national_compliance_index: float
    recent_anomalies: List[AnomalyMetricSummary]

class HeatmapGeoJsonResponse(BaseModel):
    location: GeoCentroidLocation
    intensity_weight: float
    pathogen_profile: str
    resistance_level: str
