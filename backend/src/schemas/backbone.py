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

    ncbi_tax_id: Optional[int] = None
    sequencing_platform: Optional[str] = None
    assembly_id: Optional[str] = None
    accession_number: Optional[str] = None
    qc_status: Optional[str] = None

    # ── GAP-AMR Disaggregation & Metadata ─────────────────────────────────────────
    patient_sex: Optional[str] = None
    patient_age_years: Optional[int] = None
    admission_type: Optional[str] = None
    
    animal_species: Optional[str] = None
    production_system: Optional[str] = None
    
    infarm_compliant: Optional[bool] = False
    animuse_compliant: Optional[bool] = False
    glass_eligible: Optional[bool] = False
    woah_animal_aware_class: Optional[str] = None
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
    id: int
    sample_collection_date: datetime
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
