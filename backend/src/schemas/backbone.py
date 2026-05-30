import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.entities import SectorEnum


class GenomicSignalCreate(BaseModel):
    resistance_genes: Optional[Dict[str, Any]] = Field(
        None, description="e.g., {'blaCTX-M-15': 'detected'}"
    )
    sequencing_platform: Optional[str] = None


class AMRRecordCreate(BaseModel):
    sector: SectorEnum = Field(..., description="HUMAN, ANIMAL, or ENVIRONMENT")
    pathogen_name: str = Field(..., max_length=100, description="Priority pathogen name e.g., MDR E. coli")
    antimicrobial_agent: str = Field(..., max_length=100, description="Antimicrobial agent tested")

    county: str = Field(..., max_length=50)
    sub_county: Optional[str] = Field(None, max_length=50)
    facility_type: Optional[str] = Field(None, max_length=50)

    result_value: str = Field(..., max_length=1, description="SIR classification (S, I, R)")
    mic_value: Optional[float] = None

    is_synthetic: int = Field(default=1)

    hl7_fhir_id: Optional[str] = Field(None, max_length=50)
    woah_reference: Optional[str] = Field(None, max_length=50)

    ncbi_tax_id: Optional[int] = None
    sequencing_platform: Optional[str] = Field(None, max_length=50)
    assembly_id: Optional[str] = Field(None, max_length=50)
    accession_number: Optional[str] = Field(None, max_length=50)
    qc_status: Optional[str] = Field(None, max_length=20)

    # ── GAP-AMR Disaggregation & Metadata ─────────────────────────────────────────
    patient_sex: Optional[str] = Field(None, max_length=10)
    patient_age_years: Optional[int] = None
    admission_type: Optional[str] = Field(None, max_length=50)
    
    animal_species: Optional[str] = Field(None, max_length=50)
    production_system: Optional[str] = Field(None, max_length=50)
    
    infarm_compliant: Optional[bool] = False
    animuse_compliant: Optional[bool] = False
    glass_eligible: Optional[bool] = False
    woah_animal_aware_class: Optional[str] = Field(None, max_length=50)
    antimicrobial_residue_ppm: Optional[float] = None

    genomic_signals: List[GenomicSignalCreate] = []

    @field_validator("pathogen_name", mode="before")
    @classmethod
    def normalize_pathogen_name(cls, v: str) -> str:
        v_lower = v.lower()
        if "e. coli" in v_lower or "e coli" in v_lower:
            return "Escherichia coli"
        if "s. aureus" in v_lower or "s aureus" in v_lower:
            return "Staphylococcus aureus"
        if "k. pneumoniae" in v_lower or "k pneumoniae" in v_lower:
            return "Klebsiella pneumoniae"
        return v

    @model_validator(mode="after")
    def validate_sector_disaggregation(self) -> "AMRRecordCreate":
        if self.sector == SectorEnum.HUMAN:
            if self.patient_sex is None or self.patient_age_years is None or self.admission_type is None:
                raise ValueError("Human records require patient_sex, patient_age_years, and admission_type for GLASS compliance.")
        elif self.sector == SectorEnum.ANIMAL:
            if self.animal_species is None or self.production_system is None:
                raise ValueError("Animal records require animal_species and production_system for InFARM compliance.")
        return self


class AMRRecordResponse(AMRRecordCreate):
    id: uuid.UUID
    sample_collection_date: datetime
    data_quality_score: float
    missing_fields: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    """Inline alert summary returned within ingest responses when anomaly is flagged."""
    id: uuid.UUID
    amr_isolate_record_id: uuid.UUID
    anomaly_score: float
    hotspot_magnitude: float
    feature_importance: Optional[Dict[str, Any]] = None
    detection_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class WhonetIngestResponse(BaseModel):
    """Structured response for POST /ingest/whonet."""
    status: str = "success"
    processed_records: int
    failed_critical: int
    record_ids: List[uuid.UUID] = Field(default_factory=list)
    task_queued: bool = False
    message: str
