# Track: backend/feature-api-name
# Schema v1.4 — Intelligence output schemas aligned with updated dataset definitions.
# Provides stable contracts for Lowell's React frontend maps and telemetry panels.
# v1.4: Added AlertListItem, AlertDetail, AlertExplanation, AlertGuidance, TrendsResponse
#        so all /intelligence/* routes have explicit response_model= contracts.

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ── Geographic Coordinate Model ───────────────────────────────────────────────

class GeoCentroidLocation(BaseModel):
    """
    Geographic centroid for a county/sub-county aggregate.
    Populated from live DB latitude/longitude columns — no hardcoded centroids.
    """
    county: str = Field(..., examples=["Nairobi", "Kiambu", "Machakos"])
    sub_county: Optional[str] = Field(None, examples=["Kikuyu", "Ruiru"])
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


# ── Anomaly Metric Summary ────────────────────────────────────────────────────

class AnomalyMetricSummary(BaseModel):
    record_id: str
    pathogen_name: str
    antimicrobial_agent: str
    sir_result: str
    anomaly_score: float
    data_quality_score: float


# ── LLM Advisory Response ─────────────────────────────────────────────────────

class DynamicRoleGuidanceResponse(BaseModel):
    alert_id: str
    user_role: str
    guidance_markdown: str
    generated_at: datetime


# ── Dashboard Telemetry ───────────────────────────────────────────────────────

class ResistanceBreakdown(BaseModel):
    """Breakdown of SIR results across a sector or pathogen group."""
    resistant_count: int
    susceptible_count: int
    intermediate_count: int
    resistance_percent: float


class DashboardTelemetrySummary(BaseModel):
    """
    Real-time macro telemetry snapshot for the national AMR intelligence dashboard.
    Feeds top-level KPI cards and hotspot counters.

    Frontend-compatible aliases are included alongside canonical field names
    so components reading old names (total_records, mdr_rate, etc.) work
    without any frontend transformation.
    """
    # Canonical backend fields
    total_isolates_scanned: int
    active_hotspots_detected: int
    national_compliance_index: float
    resistance_breakdown: Optional[ResistanceBreakdown] = None
    recent_anomalies: List[AnomalyMetricSummary]
    top_resistant_pathogens: Optional[List[Dict[str, Any]]] = None
    last_updated: Optional[datetime] = None

    # Frontend-compatible aliases (computed by route handler, always present)
    total_records: Optional[int] = None          # == total_isolates_scanned
    mdr_rate: Optional[float] = None             # == resistance_breakdown.resistance_percent
    anomaly_count: Optional[int] = None          # == active_hotspots_detected
    active_hotspots: Optional[int] = None        # == active_hotspots_detected
    compliance_index: Optional[float] = None     # == national_compliance_index
    active_counties: Optional[int] = None        # distinct reporting counties


# ── Heatmap GeoJSON Response ──────────────────────────────────────────────────

class HeatmapGeoJsonResponse(BaseModel):
    """
    Single data point for Lowell's Leaflet heatmap renderer.
    Aggregated from live isolate records with real DB geo coordinates.
    Fields align with the updated dataset column definitions (v1.4).
    """
    location: GeoCentroidLocation
    intensity_weight: float = Field(..., ge=0.0, le=1.0, description="Normalized heatmap weight (0–1)")
    pathogen_profile: str = Field(..., description="Primary pathogen detected at this location")
    resistance_level: str = Field(..., description="Dominant SIR result: S | I | R")
    classification: Optional[str] = Field(None, description="MDR | XDR | PDR | Susceptible")
    resistance_percent: Optional[float] = Field(None, description="Human-readable resistance rate")
    sector: Optional[str] = Field(None, description="HUMAN | ANIMAL | ENVIRONMENT")
    sample_count: Optional[int] = Field(None, description="Number of isolates at this point")


# ── Gene Intelligence ─────────────────────────────────────────────────────────

class ResistanceGeneResponse(BaseModel):
    """Reference gene record from the normalized resistance_genes catalog."""
    gene_id: str
    gene_name: str
    gene_family: Optional[str] = None
    resistance_mechanism: Optional[str] = None
    drug_class_target: Optional[str] = None
    phenotype: Optional[str] = None
    glass_relevant: bool
    who_priority_flag: bool


# ── Alert Response Schemas ────────────────────────────────────────────────────

class AlertListItem(BaseModel):
    """Single item in GET /intelligence/alerts list."""
    id: str
    pathogen: str
    drug_class: str
    county: str
    sub_county: Optional[str] = None
    risk_score: float
    summary: str
    triggered_at: Optional[str] = None
    anomaly_type: str
    status: str
    sector: str
    antibiotic_name: Optional[str] = None
    anomaly_score: Optional[float] = None


class AlertDetail(AlertListItem):
    """Full detail response for GET /intelligence/alerts/{alert_id}."""
    pass


class ContributorFactor(BaseModel):
    factor: str
    contribution_percent: int


class AlertExplanation(BaseModel):
    """Response for GET /intelligence/alerts/{alert_id}/explanation."""
    plain_text_summary: str
    contributors: List[ContributorFactor] = Field(default_factory=list)


class AlertGuidance(BaseModel):
    """Response for GET /intelligence/alerts/{alert_id}/guidance."""
    summary_text: str
    recommendations: List[str] = Field(default_factory=list)
    action_checklist: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


# ── Trends Response Schema ────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    date: str
    resistance_rate: float
    anomaly_flag: bool


class TrendsResponse(BaseModel):
    """Response for GET /intelligence/trends."""
    series: List[TrendPoint]

