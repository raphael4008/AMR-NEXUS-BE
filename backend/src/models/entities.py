import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
    Numeric,
    SmallInteger,
    UniqueConstraint,
    ForeignKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

# ── Authentication Table ──────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="National Coordinator")
    is_active = Column(Boolean, default=True)
# ── Enumerations ─────────────────────────────────────────────────────────────────

class SectorEnum(enum.Enum):
    HUMAN = "HUMAN"
    ANIMAL = "ANIMAL"
    ENVIRONMENT = "ENVIRONMENT"

class GuidanceStatusEnum(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"

# ── Dimension Tables ──────────────────────────────────────────────────────────────

class Pathogen(Base):
    __tablename__ = "pathogens"
    pathogen_code    = Column(String(30), primary_key=True)
    pathogen_name    = Column(String(150), nullable=False, unique=True, index=True)
    glass_category   = Column(String(50), nullable=True)

class Antibiotic(Base):
    __tablename__ = "antibiotics"
    antibiotic_code  = Column(String(20), primary_key=True)
    antibiotic_name  = Column(String(100), nullable=False, unique=True, index=True)
    antibiotic_class = Column(String(100), nullable=True)

class Facility(Base):
    __tablename__ = "facilities"
    facility_id   = Column(String(50), primary_key=True)
    facility_name = Column(String(150), nullable=False, index=True)
    facility_type = Column(String(50), nullable=True)

class DataSource(Base):
    __tablename__ = "data_sources"
    source_id   = Column(String(50), primary_key=True)
    source_name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=True)

class ResistanceGene(Base):
    __tablename__ = "resistance_genes"

    gene_id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gene_name                = Column(String(100), nullable=False, unique=True)
    gene_family              = Column(String(100), nullable=True)
    gene_variant             = Column(String(50), nullable=True)
    resistance_mechanism     = Column(String(150), nullable=True)
    drug_class_target        = Column(String(200), nullable=True)
    phenotype                = Column(String(200), nullable=True)
    detection_method         = Column(String(100), nullable=True)
    mobile_element           = Column(Boolean, default=False)
    mge_type                 = Column(String(50), nullable=True)
    horizontal_transfer_risk = Column(String(10), nullable=True)
    first_reported_year      = Column(Integer, nullable=True)
    first_reported_region    = Column(String(100), nullable=True)
    kenya_reported           = Column(Boolean, default=False)
    ea_reported              = Column(Boolean, default=False)
    glass_relevant           = Column(Boolean, nullable=False, default=False)
    who_priority_flag        = Column(Boolean, nullable=False, default=False)
    notes                    = Column(Text, nullable=True)
    created_at               = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at               = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    isolate_links = relationship("IsolateResistanceGene", back_populates="gene", cascade="all, delete-orphan")


# ── Core AMR Record (Fact Table) ─────────────────────────────────────────────────

class AMRRecord(Base):
    """
    Central One Health isolate fact table. Aligned with WHO GLASS / FAO InFARM.
    Hybrid Denormalized Star Schema: Contains direct strings for rapid dashboard querying,
    and Composite Primary Keys for TimescaleDB partitioning.
    """
    __tablename__ = "amr_isolate_records"

    # ── Composite Primary Key (Required by TimescaleDB) ──
    id = Column("record_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_collection_date = Column(DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(timezone.utc))
    
    # ── Metadata ──
    record_version = Column(Integer, default=1)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_source_id = Column(String(50), ForeignKey("data_sources.source_id"), nullable=True)

    # ── Temporal Partitioning ──
    sample_year  = Column(Integer, nullable=True)
    sample_month = Column(Integer, nullable=True)
    sample_week  = Column(Integer, nullable=True)
    result_date  = Column(Date, nullable=True)
    turnaround_days = Column(Integer, nullable=True)

    # ── One Health Sector ──
    sector     = Column(String(20), nullable=False, index=True)
    sub_sector = Column(String(50), nullable=True)

    # ── Pathogen Taxonomy (Flattened) ──
    pathogen_name      = Column(String(150), nullable=False)
    pathogen_code      = Column(String(30), ForeignKey("pathogens.pathogen_code"), nullable=True)
    ncbi_taxonomy_id   = Column(Integer, nullable=True)
    genus              = Column(String(100), nullable=True)
    species            = Column(String(100), nullable=True)
    resistance_profile = Column(String(50), nullable=False, default="Unknown")
    mdr_flag           = Column(Boolean, default=False)

    # ── Antimicrobial Profile (Flattened) ──
    antibiotic_name  = Column(String(100), nullable=False)
    antibiotic_code  = Column(String(20), ForeignKey("antibiotics.antibiotic_code"), nullable=True)
    antibiotic_class = Column(String(100), nullable=True)

    # ── Resistance Result & AST ──
    mic_value           = Column(Numeric(10, 4), nullable=True)
    mic_operator        = Column(String(2), nullable=True)
    disk_diffusion_mm   = Column(Integer, nullable=True)
    sir_result          = Column(String(1), nullable=False)   # S | I | R
    breakpoint_standard = Column(String(20), nullable=True)
    test_method         = Column(String(50), nullable=True)

    # ── Geography & Facility (Flattened) ──
    country_code  = Column(String(3), default="KEN")
    country_name  = Column(String(100), default="Kenya")
    region        = Column(String(100), nullable=True)
    county        = Column(String(50), nullable=False)
    sub_county    = Column(String(50), nullable=True)
    facility_id   = Column(String(50), ForeignKey("facilities.facility_id"), nullable=True)
    facility_type = Column(String(50), nullable=True)
    urban_rural   = Column(String(10), nullable=True)
    latitude      = Column(Numeric(9, 6), nullable=True)
    longitude     = Column(Numeric(9, 6), nullable=True)

    # ── Dataset-Specific Indicators ──
    specimen_type      = Column(String(100), nullable=True)
    sample_source      = Column(String(100), nullable=True)
    resistance_rate    = Column(Numeric(5, 4), nullable=True)
    resistance_percent = Column(Numeric(6, 2), nullable=True)
    classification     = Column(String(20), nullable=True)
    sample_size        = Column(Integer, nullable=True)
    hospitalised       = Column(String(30), nullable=True)
    outcome            = Column(String(50), nullable=True)
    reported_by        = Column(String(100), nullable=True)

    # ── Patient/Host Demographics ──
    patient_sex               = Column(String(10), nullable=True)
    patient_age_years         = Column(Numeric(5, 1), nullable=True)
    patient_age_group         = Column(String(20), nullable=True)
    ward_type                 = Column(String(50), nullable=True)
    admission_type            = Column(String(50), nullable=True)
    clinical_indication       = Column(String(150), nullable=True)
    prior_antibiotic_exposure = Column(Boolean, nullable=True)
    infection_origin          = Column(String(20), nullable=True)

    # ── Animal Disaggregation ──
    animal_species    = Column(String(100), nullable=True)
    production_system = Column(String(100), nullable=True)

    # ── Data Integrity ──
    is_synthetic       = Column(SmallInteger, default=1)
    data_quality_score = Column(Numeric(4, 3), default=1.0)
    missing_fields     = Column(JSON, nullable=True)
    submission_type    = Column(String(30), nullable=False, default="SYNTHETIC")

    # ── Interoperability & GLASS/WHONET Metadata ──
    hl7_fhir_id           = Column(String(50), nullable=True)
    woah_reference        = Column(String(50), nullable=True)
    glass_specimen_code   = Column(String(10), nullable=True)
    glass_pathogen_code   = Column(String(10), nullable=True)
    glass_antibiotic_code = Column(String(10), nullable=True)
    whonet_org_code       = Column(String(20), nullable=True)
    dhis2_org_unit        = Column(String(50), nullable=True)
    dhis2_data_element    = Column(String(50), nullable=True)

    # ── Genomic Metadata ──
    sequencing_platform = Column(String(100), nullable=True)
    assembly_id         = Column(String(100), nullable=True)
    accession_number    = Column(String(100), nullable=True)
    sequencing_date     = Column(Date, nullable=True)
    coverage_depth      = Column(Numeric(6, 2), nullable=True)
    qc_status           = Column(String(50), nullable=True)

    # ── Compliance Flags ──
    infarm_compliant          = Column(Boolean, default=False, index=True)
    animuse_compliant         = Column(Boolean, default=False, index=True)
    glass_eligible            = Column(Boolean, default=False, index=True)
    woah_animal_aware_class   = Column(String(50), nullable=True)
    antimicrobial_residue_ppm = Column(Numeric(10, 4), nullable=True)

    # ── 8 Core AI Model Output Fields ──
    anomaly_score        = Column(Numeric(10, 4), nullable=True)
    anomaly_flag         = Column(Boolean, default=False)
    forecast_cluster_id  = Column(String(50), nullable=True)
    shap_top_feature     = Column(String(100), nullable=True)
    shap_value           = Column(Numeric(10, 4), nullable=True)
    model_version        = Column(String(50), nullable=True)
    prediction_timestamp = Column(DateTime(timezone=True), nullable=True)
    confidence_interval  = Column(Numeric(10, 4), nullable=True)
    alert_triggered      = Column(Boolean, default=False)
    alert_timestamp      = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    resistance_gene_links = relationship("IsolateResistanceGene", back_populates="record", cascade="all, delete-orphan")
    alerts                = relationship("Alert", back_populates="record", cascade="all, delete-orphan")

    @property
    def result_value(self) -> str:
        return self.sir_result

    @property
    def antimicrobial_agent(self) -> str:
        return self.antibiotic_name


# ── Isolate↔Gene Junction (Many-to-Many) ─────────────────────────────────────────────

class IsolateResistanceGene(Base):
    """
    Junction table linking AMR isolate records to detected resistance genes (Tier 3).
    Must map to the composite Primary Key of AMRRecord.
    """
    __tablename__ = "isolate_resistance_genes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["record_id", "sample_date"],
            ["amr_isolate_records.record_id", "amr_isolate_records.sample_collection_date"],
            ondelete="CASCADE"
        ),
        UniqueConstraint("record_id", "gene_id", name="uq_isolate_gene_link"),
    )

    link_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id        = Column(UUID(as_uuid=True), nullable=False)
    sample_date      = Column(DateTime(timezone=True), nullable=False)
    gene_id          = Column(UUID(as_uuid=True), ForeignKey("resistance_genes.gene_id", ondelete="RESTRICT"), nullable=False)
    
    detection_method = Column(String(100), nullable=True)
    copies_detected  = Column(Integer, nullable=True)
    co_carriage_flag = Column(Boolean, default=False)
    confirmed_by_wgs = Column(Boolean, default=False)
    notes            = Column(Text, nullable=True)
    detected_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    record = relationship("AMRRecord", back_populates="resistance_gene_links")
    gene   = relationship("ResistanceGene", back_populates="isolate_links")


# ── AI Alert ─────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    Component B output. Must map to the composite Primary Key of AMRRecord.
    """
    __tablename__ = "alerts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["amr_isolate_record_id", "sample_date"],
            ["amr_isolate_records.record_id", "amr_isolate_records.sample_collection_date"],
            ondelete="CASCADE"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amr_isolate_record_id = Column(UUID(as_uuid=True), nullable=False)
    sample_date           = Column(DateTime(timezone=True), nullable=False)
    detection_timestamp   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    anomaly_score      = Column(Numeric, nullable=False) 
    hotspot_magnitude  = Column(Numeric, nullable=False) 
    feature_importance = Column(JSON, nullable=True)     
    status             = Column(String(50), default="PENDING", nullable=False)  

    record   = relationship("AMRRecord", back_populates="alerts")
    guidance = relationship("GuidanceBrief", back_populates="alert")


# ── LLM Guidance ─────────────────────────────────────────────────────────────────

class GuidanceBrief(Base):
    """
    Component C output: role-gated advisory brief.
    """
    __tablename__ = "guidance_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    generation_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    role_target      = Column(String(50), nullable=False)
    content_markdown = Column(Text, nullable=False)
    status           = Column(String(20), default="PENDING", nullable=False)

    @property
    def user_role(self) -> str:
        return self.role_target

    @property
    def guidance_markdown(self) -> str:
        return self.content_markdown

    alert = relationship("Alert", back_populates="guidance")