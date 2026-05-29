"""
conftest.py — Shared fixtures for the AMR-Nexus test suite.

Design decisions:
- Uses SQLite in-memory DB so tests are hermetic (no real Postgres required).
- Patches africastalking, anthropic, and prophet at import time to avoid
  live API calls or heavy ML model fitting during tests.
- Provides canonical payloads and ORM-level factory fixtures for Alert and Guidance.
"""

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

import sys

# ── 1. Patch Africa's Talking before any app module imports it ──────────────────
_at_mock = MagicMock()
_at_mock.initialize = MagicMock()
_at_mock.SMS = MagicMock()
_at_mock.SMS.send = MagicMock(return_value={"SMSMessageData": {"Recipients": []}})
sys.modules.setdefault("africastalking", _at_mock)

# ── 2. Patch Anthropic before any app module imports it ─────────────────────────
_anthropic_mock = MagicMock()
_anthropic_response = MagicMock()
_anthropic_response.content = [MagicMock(text="## 🚨 Resistance Signal Summary\nTest advisory brief.")]
_anthropic_response.usage = MagicMock(input_tokens=120, output_tokens=200)
_anthropic_response.stop_reason = "end_turn"
_anthropic_mock.Anthropic.return_value.messages.create.return_value = _anthropic_response
_anthropic_mock.APIError = Exception  # Allow except anthropic.APIError to work in tests
sys.modules.setdefault("anthropic", _anthropic_mock)

# ── 3. Patch Prophet before any app module imports it ───────────────────────────
_prophet_mock = MagicMock()
_prophet_instance = MagicMock()
_prophet_mock.Prophet.return_value = _prophet_instance

import pandas as pd
from datetime import datetime, timedelta

_forecast_df = pd.DataFrame({
    "ds": [datetime(2026, 6, 1) + timedelta(days=30 * i) for i in range(24)],
    "yhat": [float(i + 1) for i in range(24)],
    "yhat_lower": [float(i) for i in range(24)],
    "yhat_upper": [float(i + 2) for i in range(24)],
})
_prophet_instance.predict.return_value = _forecast_df
_prophet_instance.make_future_dataframe.return_value = _forecast_df
sys.modules.setdefault("prophet", _prophet_mock)
# ─────────────────────────────────────────────────────────────────────────────

from src.models.base import Base
from src.main import app


# ── In-memory SQLite engine ──────────────────────────────────────────────────
# StaticPool ensures all connections share the same in-memory database.
# Without this, each new sessionmaker connection gets a blank DB.
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    from sqlalchemy.pool import StaticPool
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)



@pytest.fixture(scope="function")
def db_session(engine):
    """Yields a rolled-back DB session per test (true isolation)."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(bind=connection)
    session = TestingSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ── FastAPI TestClient ───────────────────────────────────────────────────────
import src.models.base as _base_module

@pytest.fixture(scope="function")
def client(engine):
    """
    TestClient with get_db overridden to use the in-memory SQLite engine.
    This ensures endpoints like /intelligence/dashboard don't hit real Postgres.
    """
    TestingSessionLocal = sessionmaker(bind=engine)
    _base_module.SessionLocal = TestingSessionLocal

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[_base_module.get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()




# ── Canonical test payloads ──────────────────────────────────────────────────
@pytest.fixture
def valid_payload():
    """Four clean, fully-populated records that should all pass cleaning."""
    return [
        {
            "sector": "human",
            "pathogen_name": "E. coli",
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Nairobi",
            "result_value": "Resistant",
            "facility_type": "Tertiary Hospital",
            "patient_sex": "Female",
            "patient_age_years": 42,
            "admission_type": "Inpatient",
        },
        {
            "sector": "animal",
            "pathogen_name": "Salmonella",
            "antimicrobial_agent": "Tetracycline",
            "county": "Kiambu",
            "result_value": "Sensitive",
            "facility_type": "Poultry Farm",
            "animal_species": "Chicken",
            "production_system": "Commercial",
        },
        {
            "sector": "environment",
            "pathogen_name": "Salmonella",
            "antimicrobial_agent": "Ceftriaxone",
            "county": "Mombasa",
            "result_value": "Resistant",
            "facility_type": "River Water",
        },
        {
            "sector": "human",
            "pathogen_name": "K. pneumoniae",
            "antimicrobial_agent": "Meropenem",
            "county": "Kisumu",
            "result_value": "Intermediate",
            "facility_type": "Clinic",
            "patient_sex": "Male",
            "patient_age_years": 12,
            "admission_type": "Outpatient",
        },
    ]


@pytest.fixture
def dirty_payload():
    """Mix of valid + critically incomplete records."""
    return [
        {
            "sector": "human",
            "pathogen_name": "E. coli",
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Nairobi",
            "result_value": "Resistant",
            "facility_type": "Hospital",
            "patient_sex": "Female",
            "patient_age_years": 42,
            "admission_type": "Inpatient",
        },
        {
            # CRITICAL FAILURE — pathogen_name is None
            "sector": "animal",
            "pathogen_name": None,
            "antimicrobial_agent": "Tetracycline",
            "county": "Kiambu",
            "result_value": "Sensitive",
            "facility_type": None,   # non-critical missing
            "animal_species": "Chicken",
            "production_system": "Commercial",
        },
        {
            "sector": "environment",
            "pathogen_name": "Salmonella",
            "antimicrobial_agent": "Ceftriaxone",
            "county": "Mombasa",
            "result_value": "Resistant",
            "facility_type": "River Water",
        },
        {
            "sector": "human",
            "pathogen_name": "K. pneumoniae",
            "antimicrobial_agent": "Meropenem",
            "county": "Kisumu",
            "result_value": "Intermediate",
            "facility_type": "Clinic",
            "patient_sex": "Male",
            "patient_age_years": 12,
            "admission_type": "Outpatient",
        },
    ]


# ── ORM Factory Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_amr_record(db_session):
    """A persisted AMRRecord for tests that need a real DB object."""
    from src.models.entities import AMRRecord, SectorEnum
    record = AMRRecord(
        sector=SectorEnum.HUMAN,
        pathogen_name="E. coli",
        antimicrobial_agent="Ciprofloxacin",
        county="Nairobi",
        sub_county="Westlands",
        facility_type="Tertiary Hospital",
        result_value="Resistant",
        patient_sex="Female",
        patient_age_years=42,
        admission_type="Inpatient",
        data_quality_score=0.95,
        is_synthetic=1,
    )
    db_session.add(record)
    db_session.flush()
    return record


@pytest.fixture
def sample_alert(db_session, sample_amr_record):
    """A persisted Alert linked to sample_amr_record."""
    from src.models.entities import Alert
    alert = Alert(
        amr_record_id=sample_amr_record.id,
        anomaly_score=-0.3145,
        hotspot_magnitude=0.75,
        feature_importance={
            "county_weight": 0.40,
            "pathogen_risk_weight": 0.35,
            "drug_class_weight": 0.15,
            "sector_weight": 0.10,
            "method": "shap_stub_v1_demo",
        },
    )
    db_session.add(alert)
    db_session.flush()
    return alert


@pytest.fixture
def sample_guidance(db_session, sample_alert):
    """A persisted Guidance linked to sample_alert (National Coordinator role)."""
    from src.models.entities import Guidance
    guidance = Guidance(
        alert_id=sample_alert.id,
        role_target="National Coordinator",
        content_markdown="## 🚨 Resistance Signal Summary\nTest advisory brief generated in test fixture.",
        status="PENDING",
    )
    db_session.add(guidance)
    db_session.flush()
    return guidance
