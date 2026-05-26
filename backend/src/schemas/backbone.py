from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.entities import SectorEnum


class GenomicSignalCreate(BaseModel):
    resistance_genes: Optional[Dict[str, Any]] = Field(
        None, description="e.g., {'blaCTX-M-15': 'detected'}"
    )
    sequencing_platform: Optional[str] = None


class AMRRecordCreate(BaseModel):
    sector: SectorEnum = Field(..., description="human, animal, or environment")
    pathogen_name: str = Field(..., description="Priority pathogen name e.g., MDR E. coli")
    antimicrobial_agent: str = Field(..., description="Antimicrobial agent tested")

    county: str
    sub_county: Optional[str] = None
    facility_type: Optional[str] = None

    result_value: str = Field(..., description="SIR classification (Resistant, Intermediate, Sensitive)")
    mic_value: Optional[float] = None

    is_synthetic: int = Field(default=1)

    hl7_fhir_id: Optional[str] = None
    woah_reference: Optional[str] = None

    genomic_signals: List[GenomicSignalCreate] = []


class AMRRecordResponse(AMRRecordCreate):
    id: int
    timestamp: datetime
    data_quality_score: float
    missing_fields: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    """Inline alert summary returned within ingest responses when anomaly is flagged."""
    id: int
    record_id: int
    anomaly_score: float
    hotspot_magnitude: float
    feature_importance: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class WhonetIngestResponse(BaseModel):
    """Structured response for POST /ingest/whonet."""
    status: str = "success"
    processed_records: int
    failed_critical: int
    record_ids: List[int] = Field(default_factory=list)
    task_queued: bool = False
    message: str
