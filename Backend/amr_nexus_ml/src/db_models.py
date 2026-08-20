from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
import uuid
from datetime import datetime

class AMRIsolateRecord(Base):
    __tablename__ = "amr_isolate_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submission_type = Column(String(20))

    # Pathogen
    pathogen_code = Column(String(20))
    mdr_flag = Column(Boolean)

    # AST
    antibiotic_class = Column(String(100))
    sir_result = Column(String(1))
    test_method = Column(String(50))

    # Sector & specimen
    sector = Column(String(20))
    sub_sector = Column(String(50))
    specimen_type = Column(String(100))
    animal_species = Column(String(100))
    production_system = Column(String(50))

    # Geography
    county = Column(String(100))
    urban_rural = Column(String(10))

    # Temporal
    sample_collection_date = Column(Date)
    sample_month = Column(Integer)

    # Demographics
    patient_age_years = Column(Numeric(5,1))
    patient_sex = Column(String(1))
    ward_type = Column(String(50))
    prior_antibiotic_exposure = Column(Boolean)
    infection_origin = Column(String(20))

    # AI output fields
    anomaly_score = Column(Numeric(5,4))
    anomaly_flag = Column(Boolean)
    shap_top_feature = Column(String(100))
    shap_value = Column(Numeric(8,4))
    model_version = Column(String(20))
    mdr_probability = Column(Numeric(5,4))
    shap_summary = Column(Text, nullable=True)          

# ---------- New: Comments table ----------
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("amr_isolate_records.record_id"), nullable=False)
    user_name = Column(String(100), nullable=False, default="Anonymous")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------- New: Risk Scores table ----------
class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    county = Column(String(100))
    pathogen_code = Column(String(20))
    antibiotic_class = Column(String(100))
    risk_score = Column(Float)
    anomaly_score = Column(Float)
    mdr_rate = Column(Float)
    sample_size = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
