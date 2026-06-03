import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
    Numeric,
    SmallInteger,
    UniqueConstraint,
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
    Central One Health isolate record. Aligned with WHO GLASS / FAO InFARM /
    WOAH ANIMUSE / WHO GAP-AMR (2026-2036).
    Schema v1.3 — maps all 10 previously unmapped dataset variables.
    """
    __tablename__ = "amr_isolate_records"

    # ── Primary Key (renamed record_id in SQL; aliased as id for ORM compat) ──
    id = Column("record_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_collection_date = Column(DateTime(timezone=True), nullable=False, index=True,
                                    default=lambda: datetime.now(timezone.utc))

    # ── One Health Sector ──────────────────────────────────────────────────────
    sector = Column(String(20), nullable=False, index=True)

    # ── Pathogen Taxonomy (Unmapped Variables 1–3) ─────────────────────────────
    pathogen_name       = Column(String(150), nullable=False, index=True)
    pathogen_code       = Column(String(30),  nullable=True)
    ncbi_taxonomy_id    = Column(Integer,     nullable=True, index=True)

    # ── Antimicrobial Profile (Unmapped Variables 4–6) ────────────────────────
    antibiotic_code     = Column(String(20),  nullable=True)
    antibiotic_name     = Column(String(100), nullable=False)
    antibiotic_class    = Column(String(100), nullable=True)

    # ── Backwards-compat alias: antimicrobial_agent → antibiotic_name ─────────
    # Routes from legacy API surface; do NOT add a separate column.
    @property
    def antimicrobial_agent(self) -> str:
        return self.antibiotic_name

    # ── Resistance Result (Unmapped Variables 7–8) ────────────────────────────
    mic_value  = Column(Numeric(10, 4), nullable=True)
    sir_result = Column(String(1),      nullable=False)   # S | I | R

    # ── Backwards-compat alias: result_value → sir_result ─────────────────────
    @property
    def result_value(self) -> str:
        return self.sir_result

    # ── Geography (Unmapped Variables 9–10) ───────────────────────────────────
    county     = Column(String(50), nullable=False, index=True)
    sub_county = Column(String(50), nullable=True)

    # ── Dataset-Specific Indicators ────────────────────────────────────────────
    latitude           = Column(Numeric(9, 6),  nullable=True)
    longitude          = Column(Numeric(9, 6),  nullable=True)
    specimen_type      = Column(String(100),    nullable=True)
    resistance_rate    = Column(Numeric(5, 4),  nullable=True)  # decimal e.g. 0.6850
    resistance_percent = Column(Numeric(6, 2),  nullable=True)  # human-readable e.g. 68.50
    classification     = Column(String(20),     nullable=True)  # MDR | XDR | PDR | Susceptible
    sample_size        = Column(Integer,         nullable=True)
    hospitalised       = Column(String(30),     nullable=True)
    outcome            = Column(String(50),     nullable=True)
    reported_by        = Column(String(100),    nullable=True)

    # ── Data Integrity ──────────────────────────────────────────────────────────
    is_synthetic       = Column(SmallInteger, default=1)
    data_quality_score = Column(Numeric(4, 3), default=1.0)
    missing_fields     = Column(JSON, nullable=True)
    submission_type    = Column(String(30), nullable=False, default="SYNTHETIC")

    # ── Interoperability Metadata ───────────────────────────────────────────────
    hl7_fhir_id    = Column(String(50), nullable=True)
    woah_reference = Column(String(50), nullable=True)

    # ── Genomic Metadata ───────────────────────────────────────────────────────
    sequencing_platform = Column(String(50), nullable=True)
    assembly_id         = Column(String(50), nullable=True)
    accession_number    = Column(String(50), nullable=True)
    qc_status           = Column(String(20), nullable=True)

    # ── GAP-AMR Disaggregation — Human ────────────────────────────────────────
    patient_sex       = Column(String(10),  nullable=True)
    patient_age_years = Column(Integer,      nullable=True)
    admission_type    = Column(String(50),  nullable=True)
    clinical_indication = Column(String(150), nullable=True)

    # ── GAP-AMR Disaggregation — Animal ───────────────────────────────────────
    animal_species    = Column(String(100), nullable=True)
    production_system = Column(String(100), nullable=True)

    # ── Compliance Flags ──────────────────────────────────────────────────────
    infarm_compliant          = Column(Boolean, default=False, index=True)
    animuse_compliant         = Column(Boolean, default=False, index=True)
    glass_eligible            = Column(Boolean, default=False, index=True)
    woah_animal_aware_class   = Column(String(50),    nullable=True)
    antimicrobial_residue_ppm = Column(Numeric(10, 4), nullable=True)

    # ── Legacy facility_type (kept for v1.2 compat) ───────────────────────────
    facility_type = Column(String(50), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────────────
    genomic_signals     = relationship("GenomicSignal",       back_populates="record",  cascade="all, delete-orphan")
    resistance_gene_links = relationship("IsolateResistanceGene", back_populates="record", cascade="all, delete-orphan")
    alerts              = relationship("Alert",               back_populates="record",  cascade="all, delete-orphan")


# ── Bioinformatics Signal (Legacy JSONB — kept for backward compat) ──────────────────

class GenomicSignal(Base):
    """Legacy Component A extension. Replaced by ResistanceGene M2M for v1.3+."""
    __tablename__ = "genomic_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amr_isolate_record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id", ondelete="CASCADE"), nullable=False)
    resistance_genes = Column(JSON)        # e.g., {"blaCTX-M-15": "detected"}
    sequencing_platform = Column(String(50))

    record = relationship("AMRRecord", back_populates="genomic_signals")


# ── Resistance Gene Reference Dimension ──────────────────────────────────────────────

class ResistanceGene(Base):
    """
    Normalized WHO-priority AMR gene catalog (Tier 2).
    Pre-populated with 15 priority ARGs via schema_v1.3.sql seed script.
    """
    __tablename__ = "resistance_genes"

    gene_id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gene_name            = Column(String(100), nullable=False, unique=True)
    gene_family          = Column(String(100), nullable=True)
    resistance_mechanism = Column(String(150), nullable=True)
    drug_class_target    = Column(String(150), nullable=True)
    phenotype            = Column(String(200), nullable=True)
    detection_method     = Column(String(100), nullable=True)
    glass_relevant       = Column(Boolean, nullable=False, default=False)
    who_priority_flag    = Column(Boolean, nullable=False, default=False)

    # ── Relationships ────────────────────────────────────────────────────────
    isolate_links = relationship("IsolateResistanceGene", back_populates="gene", cascade="all, delete-orphan")


# ── Isolate↔Gene Junction (Many-to-Many) ─────────────────────────────────────────────

class IsolateResistanceGene(Base):
    """
    Junction table linking AMR isolate records to detected resistance genes (Tier 3).
    Replaces JSONB blob storage; enables structured ARG-level querying.
    """
    __tablename__ = "isolate_resistance_genes"
    __table_args__ = (
        UniqueConstraint("record_id", "gene_id", name="uq_isolate_gene_link"),
    )

    link_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id        = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id", ondelete="CASCADE"), nullable=False)
    gene_id          = Column(UUID(as_uuid=True), ForeignKey("resistance_genes.gene_id",      ondelete="RESTRICT"), nullable=False)
    detection_method = Column(String(100), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    record = relationship("AMRRecord",      back_populates="resistance_gene_links")
    gene   = relationship("ResistanceGene", back_populates="isolate_links")


# ── AI Alert ─────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    Component B output: persisted when IsolationForest flags a credible anomaly
    (anomaly_score < 0 AND data_quality_score > 0.7).
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amr_isolate_record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id", ondelete="CASCADE"), nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

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
    Component C output: role-gated advisory brief generated by LLMAdvisoryEngine.
    Linked 1:many to an Alert (one brief per user role).
    """
    __tablename__ = "guidance_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    generation_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # ── Role-Gated Content ──────────────────────────────────────────────────────
    role_target      = Column(String(50), nullable=False)   # "National Coordinator" | "County Veterinarian"
    content_markdown = Column(Text, nullable=False)         # Full markdown brief

    # Alias used by test suite (GuidanceBrief.user_role and GuidanceBrief.guidance_markdown)
    @property
    def user_role(self) -> str:
        return self.role_target

    @property
    def guidance_markdown(self) -> str:
        return self.content_markdown

    # ── Generation Provenance ───────────────────────────────────────────────────
    status = Column(String(20), default="PENDING", nullable=False)

    # ── Relationships ───────────────────────────────────────────────────────────
    alert = relationship("Alert", back_populates="guidance")
