import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base


# ── Enumerations ─────────────────────────────────────────────────────────────────

class SectorEnum(enum.Enum):
    HUMAN = "HUMAN"
    ANIMAL = "ANIMAL"
    ENVIRONMENT = "ENVIRONMENT"


class GuidanceStatusEnum(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"


# ── Core AMR Record ───────────────────────────────────────────────────────────────

class AMRRecord(Base):
    """
    Central One Health isolate record. Aligned with WHO GLASS and HL7 FHIR.
    Covers human clinical, veterinary/poultry, and environmental sectors.
    """
    __tablename__ = "amr_isolate_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_collection_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ── One Health Dimensions ───────────────────────────────────────────────────
    sector = Column(String(20), nullable=False, index=True)
    pathogen_name = Column(String(100), nullable=False, index=True)      # e.g., "MDR E. coli"
    antimicrobial_agent = Column(String(100), nullable=False)            # e.g., "Ciprofloxacin"

    # ── Location & Source ───────────────────────────────────────────────────────
    county = Column(String(50), nullable=False, index=True)
    sub_county = Column(String(50), nullable=True)
    facility_type = Column(String(50), nullable=True)

    # ── Resistance Profile ──────────────────────────────────────────────────────
    result_value = Column(String(1), nullable=False)                   # SIR: "S", "I", "R"
    mic_value = Column(Numeric(6, 2), nullable=True)

    # ── Data Integrity ──────────────────────────────────────────────────────────
    is_synthetic = Column(Integer, default=1)                       # 1=synthetic, 0=real
    data_quality_score = Column(Numeric(4, 3), default=1.0)
    missing_fields = Column(JSON, nullable=True)                    # Tracks imputed fields

    # ── Interoperability Metadata ───────────────────────────────────────────────
    hl7_fhir_id = Column(String(50), nullable=True)
    woah_reference = Column(String(50), nullable=True)

    # ── Genomic Metadata (Module 2 Placeholders) ────────────────────────────────
    ncbi_tax_id = Column(Integer, index=True, nullable=True)
    sequencing_platform = Column(String(50), nullable=True)
    assembly_id = Column(String(50), nullable=True)
    accession_number = Column(String(50), nullable=True)
    qc_status = Column(String(20), nullable=True)

    # ── Disaggregation Fields ───────────────────────────────────────────────────
    patient_sex = Column(String(10), nullable=True)
    patient_age_years = Column(Integer, nullable=True)
    admission_type = Column(String(50), nullable=True)
    animal_species = Column(String(50), nullable=True)
    production_system = Column(String(50), nullable=True)

    # ── GAP-AMR 2026-2036 Compliance & Metadata ────────────────────────────────
    infarm_compliant = Column(Boolean, default=False, index=True)
    animuse_compliant = Column(Boolean, default=False, index=True)
    glass_eligible = Column(Boolean, default=False, index=True)
    woah_animal_aware_class = Column(String(50), nullable=True)
    antimicrobial_residue_ppm = Column(Numeric(10, 4), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────────────
    genomic_signals = relationship("GenomicSignal", back_populates="record")
    alerts = relationship("Alert", back_populates="record")


# ── Bioinformatics Signal ─────────────────────────────────────────────────────────

class GenomicSignal(Base):
    """Component A extension: bioinformatics integration for resistance gene tracking."""
    __tablename__ = "genomic_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amr_isolate_record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.id", ondelete="CASCADE"), nullable=False)
    resistance_genes = Column(JSON)                                 # e.g., {"blaCTX-M-15": "detected"}
    sequencing_platform = Column(String(50))

    record = relationship("AMRRecord", back_populates="genomic_signals")


# ── AI Alert ─────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    Component B output: persisted when IsolationForest flags a credible anomaly
    (anomaly_score < 0 AND data_quality_score > 0.7).
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amr_isolate_record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.id", ondelete="CASCADE"), nullable=False)
    detection_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ── Anomaly Scoring ─────────────────────────────────────────────────────────
    anomaly_score = Column(Numeric, nullable=False)                   # IsolationForest decision_function score
    hotspot_magnitude = Column(Numeric, nullable=False)              # Normalized severity: higher = more severe

    # ── Explainability (SHAP stub → real-SHAP ready) ────────────────────────────
    feature_importance = Column(JSON, nullable=True)               # {"county_weight": 0.4, "pathogen_risk_weight": 0.35, ...}
    
    # ── Workflow State ──────────────────────────────────────────────────────────
    status = Column(String(50), default="PENDING", nullable=False)  # "PENDING", "NOTIFIED"

    # ── Relationships ───────────────────────────────────────────────────────────
    record = relationship("AMRRecord", back_populates="alerts")
    guidance = relationship("GuidanceBrief", back_populates="alert")


# ── LLM Guidance ─────────────────────────────────────────────────────────────────

class GuidanceBrief(Base):
    """
    Component C output: role-gated advisory brief generated by LLMAdvisoryEngine
    (Claude API). Linked 1:many to an Alert (one brief per user role).
    """
    __tablename__ = "guidance_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    generation_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ── Role-Gated Content ──────────────────────────────────────────────────────
    role_target = Column(String(50), nullable=False)                      # "National Coordinator" | "County Veterinarian"
    content_markdown = Column(Text, nullable=False)                 # Full markdown brief from Claude

    # ── Generation Provenance ───────────────────────────────────────────────────
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────────────────────
    alert = relationship("Alert", back_populates="guidance")
