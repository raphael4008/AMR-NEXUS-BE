from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Numeric, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class AMRIsolateRecord(Base):
    __tablename__ = "amr_isolate_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    submission_type = Column(String(20))

    pathogen_code = Column(String(20))
    mdr_flag = Column(Boolean)

    antibiotic_class = Column(String(100))
    sir_result = Column(String(1))
    test_method = Column(String(50))

    sector = Column(String(20))
    sub_sector = Column(String(50))
    specimen_type = Column(String(100))
    animal_species = Column(String(100))
    production_system = Column(String(50))

    county = Column(String(100))
    urban_rural = Column(String(10))

    sample_collection_date = Column(Date)
    sample_month = Column(Integer)

    patient_age_years = Column(Numeric(5, 1))
    patient_sex = Column(String(1))
    ward_type = Column(String(50))
    prior_antibiotic_exposure = Column(Boolean)
    infection_origin = Column(String(20))

    anomaly_score = Column(Numeric(5, 4))
    anomaly_flag = Column(Boolean)
    shap_top_feature = Column(String(100))
    shap_value = Column(Numeric(8, 4))
    model_version = Column(String(20))
    mdr_probability = Column(Numeric(5, 4))
    shap_summary = Column(Text, nullable=True)

    gene_marker_blandm = Column(Boolean, nullable=True, default=False)
    gene_marker_mcr1 = Column(Boolean, nullable=True, default=False)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    overall_risk_score = Column(Numeric(5, 4), nullable=False)
    anomaly_component = Column(Numeric(5, 4), nullable=False)
    mdr_component = Column(Numeric(5, 4), nullable=False)
    sample_component = Column(Numeric(5, 4), nullable=False)


class DashboardNotification(Base):
    __tablename__ = "dashboard_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    county = Column(String(100), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="analyst")
    assigned_county = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    templates = relationship("UserTemplate", back_populates="user", cascade="all, delete-orphan")


class UserTemplate(Base):
    __tablename__ = "user_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    form_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="templates")