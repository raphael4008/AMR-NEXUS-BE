# Track: backend/feature-api-name
# Schema v1.3 — Pydantic validation layer aligned with WHO GAP-AMR 2026-2036
# and AMR_Nexus_Kenya_Dataset_CLEANED.csv.xls column definitions.

import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.entities import SectorEnum


# ── Genomic Gene Signal (legacy; use ResistanceGeneLink for v1.3+) ────────────

class GenomicSignalCreate(BaseModel):
    resistance_genes: Optional[Dict[str, Any]] = Field(
        None, description="Legacy JSONB gene map e.g., {'blaCTX-M-15': 'detected'}"
    )
    sequencing_platform: Optional[str] = None


class ResistanceGeneLinkCreate(BaseModel):
    """Structured M2M gene linkage payload for v1.3 normalized junction table."""
    gene_name: str = Field(..., description="Unique gene name e.g., 'blaNDM-1'")
    detection_method: Optional[str] = Field(None, description="e.g., 'PCR', 'WGS'")


# ── Core AMR Record Input ─────────────────────────────────────────────────────

class AMRRecordCreate(BaseModel):
    """
    Strict input schema for AMR isolate record ingestion.
    Aligns with the 10 previously unmapped dataset variables and enforces
    WHO GAP-AMR 2026-2036 disaggregation rules.
    """

    # ── One Health Sector & Core Timeline ──────────────────────────────────────
    sector: SectorEnum = Field(..., description="HUMAN | ANIMAL | ENVIRONMENT")
    sample_collection_date: datetime = Field(..., description="ISO format: YYYY-MM-DDTHH:MM:SS")    
    submission_type: Optional[str] = Field("SYNTHETIC", description="SYNTHETIC | REAL | IMPORTED")

    # ── Pathogen Taxonomy (Unmapped Variables 1–3) ─────────────────────────────
    pathogen_name: str = Field(..., max_length=150)
    pathogen_code: Optional[str] = Field(None, max_length=30, description="e.g., 'eco'")
    ncbi_taxonomy_id: Optional[int] = Field(None, description="e.g., 562 for E. coli")

    # ── Antimicrobial Profile (Unmapped Variables 4–6) ────────────────────────
    antibiotic_code: Optional[str] = Field(None, max_length=20, description="e.g., 'CIP'")
    antibiotic_name: str = Field(..., max_length=100, description="e.g., 'Ciprofloxacin'")
    antibiotic_class: Optional[str] = Field(None, max_length=100, description="e.g., 'Fluoroquinolone'")

    # ── Resistance Result (Unmapped Variables 7–8) ────────────────────────────
    mic_value: Optional[float] = Field(None, ge=0)
    sir_result: str = Field(..., max_length=1, description="S | I | R")

    # ── Geography (Unmapped Variables 9–10) ───────────────────────────────────
    county: str = Field(..., max_length=50)
    sub_county: Optional[str] = Field(None, max_length=50)

    # ── Dataset-Specific Indicators ────────────────────────────────────────────
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    specimen_type: Optional[str] = Field(None, max_length=100)
    resistance_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Decimal 0–1, e.g. 0.685")
    resistance_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Human-readable, e.g. 68.50")
    classification: Optional[str] = Field(None, description="MDR | XDR | PDR | Susceptible | Unknown")
    sample_size: Optional[int] = Field(None, ge=1)
    hospitalised: Optional[str] = Field(None, max_length=30)
    outcome: Optional[str] = Field(None, max_length=50)
    reported_by: Optional[str] = Field(None, max_length=100)

    # ── Data Integrity ─────────────────────────────────────────────────────────
    is_synthetic: int = Field(default=1)

    # ── Interoperability Metadata ──────────────────────────────────────────────
    hl7_fhir_id: Optional[str] = Field(None, max_length=50)
    woah_reference: Optional[str] = Field(None, max_length=50)

    # ── Genomic Metadata ───────────────────────────────────────────────────────
    sequencing_platform: Optional[str] = Field(None, max_length=50)
    assembly_id: Optional[str] = Field(None, max_length=50)
    accession_number: Optional[str] = Field(None, max_length=50)
    qc_status: Optional[str] = Field(None, max_length=20)

    # ── GAP-AMR Disaggregation — Human ────────────────────────────────────────
    patient_sex: Optional[str] = Field(None, max_length=10)
    patient_age_years: Optional[int] = Field(None, ge=0, le=130)
    admission_type: Optional[str] = Field(None, max_length=50)
    clinical_indication: Optional[str] = Field(None, max_length=150)

    # ── GAP-AMR Disaggregation — Animal ───────────────────────────────────────
    animal_species: Optional[str] = Field(None, max_length=100)
    production_system: Optional[str] = Field(None, max_length=100)

    # ── Compliance Flags ──────────────────────────────────────────────────────
    infarm_compliant: Optional[bool] = False
    animuse_compliant: Optional[bool] = False
    glass_eligible: Optional[bool] = False
    woah_animal_aware_class: Optional[str] = Field(None, max_length=50)
    antimicrobial_residue_ppm: Optional[float] = None

    # ── Legacy compat ─────────────────────────────────────────────────────────
    facility_type: Optional[str] = Field(None, max_length=50)

    # ── Genomic Gene Links ────────────────────────────────────────────────────
    genomic_signals: List[GenomicSignalCreate] = []
    resistance_gene_links: List[ResistanceGeneLinkCreate] = []

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDATORS
    # ─────────────────────────────────────────────────────────────────────────

    @field_validator("sector", mode="before")
    @classmethod
    def sanitize_sector_input(cls, v: Any) -> Any:
        """Sanitizes fuzzy string entries to map cleanly to SectorEnum values."""
        if isinstance(v, str):
            clean_v = v.strip().upper()
            if clean_v in ["HUMAN", "ANIMAL", "ENVIRONMENT"]:
                return clean_v
        return v

    @field_validator("pathogen_name", mode="before")
    @classmethod
    def normalize_pathogen_name(cls, v: str) -> str:
        """
        Pre-commit normalization: maps common shorthand to full taxonomic names.
        Mirrors the DB-level tg_normalize_pathogen_name trigger for double safety.
        """
        if not isinstance(v, str):
            return v
        vl = v.lower().strip()
        if "e. coli" in vl or (vl.startswith("e coli") or " e coli" in vl):
            return "Escherichia coli"
        if "s. aureus" in vl or "s aureus" in vl:
            return "Staphylococcus aureus"
        if "k. pneumoniae" in vl or "k pneumoniae" in vl:
            return "Klebsiella pneumoniae"
        if "a. baumannii" in vl or "a baumannii" in vl:
            return "Acinetobacter baumannii"
        if "p. aeruginosa" in vl or "p aeruginosa" in vl:
            return "Pseudomonas aeruginosa"
        if "s. typhi" in vl or "s typhi" in vl:
            return "Salmonella typhi"
        if "s. enterica" in vl or "s enterica" in vl:
            return "Salmonella enterica"
        if "s. pneumoniae" in vl or "s pneumoniae" in vl:
            return "Streptococcus pneumoniae"
        return v

    @field_validator("sir_result", mode="before")
    @classmethod
    def normalize_sir_result(cls, v: str) -> str:
        """Maps full-word SIR values to single CHAR(1) to prevent DB truncation."""
        _SIR_MAP = {
            "resistant": "R", "susceptible": "S", "intermediate": "I",
            "sensitive": "S", "nonsusceptible": "R",
        }
        if isinstance(v, str):
            mapped = _SIR_MAP.get(v.lower().strip())
            if mapped:
                return mapped
        return v

    @field_validator("classification", mode="before")
    @classmethod
    def normalize_classification(cls, v: Optional[str]) -> Optional[str]:
        """Normalize resistance classification to standardized MDR/XDR/PDR/Unknown codes."""
        if v is None:
            return v
        v_upper = v.strip().upper()
        valid_uppercase = {"MDR", "XDR", "PDR"}
        if v_upper in valid_uppercase:
            return v_upper
        if v_upper in ["SUSCEPTIBLE", "UNKNOWN"]:
            return v_upper.capitalize()
        return v

    @model_validator(mode="after")
    def validate_sector_disaggregation(self) -> "AMRRecordCreate":
        """
        Enforces WHO GAP-AMR 2026-2036 disaggregation requirements:
        - HUMAN records: require patient_sex, patient_age_years, clinical_indication
        - ANIMAL records: require animal_species, production_system
        """
        # Handle string value checking or SectorEnum checking gracefully
        sector_str = self.sector.value if hasattr(self.sector, "value") else str(self.sector)
        
        if sector_str == "HUMAN":
            missing = [f for f in ["patient_sex", "patient_age_years", "clinical_indication"]
                       if getattr(self, f) is None]
            if missing:
                raise ValueError(
                    f"Human records require {', '.join(missing)} for GLASS compliance (GAP-AMR 2026-2036)."
                )
        elif sector_str == "ANIMAL":
            missing = [f for f in ["animal_species", "production_system"]
                       if getattr(self, f) is None]
            if missing:
                raise ValueError(
                    f"Animal records require {', '.join(missing)} for FAO InFARM compliance (GAP-AMR 2026-2036)."
                )
        return self


# ── Response Models ──────────────────────────────────────────────────────────

class AMRRecordResponse(BaseModel):
    id: uuid.UUID
    sector: str
    pathogen_name: str
    antibiotic_name: str
    sir_result: str
    county: str
    sub_county: Optional[str] = None
    sample_collection_date: datetime
    data_quality_score: Optional[float] = None
    missing_fields: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    classification: Optional[str] = None
    reported_by: Optional[str] = None

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


class BulkIngestResponse(BaseModel):
    """Structured response for POST /api/v1/records/bulk/"""
    status: str = "success"
    processed_records: int
    failed_critical: int
    record_ids: List[uuid.UUID] = Field(default_factory=list)
    task_queued: bool = False
    message: str


# Legacy alias for backward compatibility with existing test suite
WhonetIngestResponse = BulkIngestResponse