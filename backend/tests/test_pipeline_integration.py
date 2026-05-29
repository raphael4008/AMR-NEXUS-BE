# Track Branch Naming Rule: backend/feature-api-name
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief, sector_enum
from src.services.ingestion.cleaner import DataCleaner
from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine

client = TestClient(app)

@pytest.fixture
def mock_anthropic_client():
    """Mocks the external Claude API response layer to prevent runtime network outbound lags."""
    with patch("src.services.intelligence.llm_advisory.anthropic.Anthropic") as mock_class:
        mock_instance = MagicMock()
        mock_message_output = MagicMock()
        mock_message_output.content = [MagicMock(text="### WHO AWaRe Veterinary Stewardship Guideline Brief\n1. Modify Prescribing Patterns.")]
        mock_instance.messages.create.return_model = mock_message_output
        mock_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_sms_gateway():
    """Mocks Africa's Talking gateway endpoint interactions."""
    with patch("src.services.notifications.sms_service.africastalking") as mock_at:
        mock_sms_instance = MagicMock()
        mock_sms_instance.send.return_value = {"SMSMessageData": {"Message": "Sent Successfully"}}
        mock_at.SMS.return_value = mock_sms_instance
        yield mock_sms_instance

def test_end_to_end_ingestion_to_ai_alert_pipeline(
    db_session: Session, 
    mock_anthropic_client, 
    mock_sms_gateway
):
    """
    Executes an Integration Test verifying Component A, B, and C connectivity.
    Validates: Raw Input -> Ingestion -> Cleaning -> Anomaly Flagging -> LLM Generation -> SMS Trigger.
    """
    # 1. Simulate an incoming dirty data payload from Nicole's synthetic pipeline structure
    raw_synthetic_payload = [
        {
            "sector": "ANIMAL",
            "pathogen_name": "E. coli",  # Shorthand string to trigger Raph's normalization logic
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Kiambu",
            "sub_county": None,          # Triggers sub-county modal imputation
            "facility_type": "Poultry Farm",
            "result_value": "R",         # High resistance target to trigger Naomi's AI anomaly engine
            "ncbi_tax_id": 562,
            "sequencing_platform": "Illumina Nanopore",
            "is_synthetic": 1
        }
    ]

    # 2. Overide FastAPI dependency injection engine to utilize our test database session
    app.dependency_overrides[get_db] = lambda: db_session

    # 3. Submit request to Raph's primary data backbone entrypoint router
    response = client.post("/api/v1/backbone/ingest/whonet", json=raw_synthetic_payload)
    
    # Assert successful background queue handoff
    assert response.status_code == 202
    assert response.json()["processed_records"] == 1
    assert response.json()["critical_failures"] == 0

    # 4. Force manual execution of the background task synchronously to evaluate state engines
    inserted_record = db_session.query(AMRRecord).filter(AMRRecord.county == "Kiambu").first()
    assert inserted_record is not None
    
    # Verify string normalization and sub-county imputation performed correctly
    assert inserted_record.pathogen_name == "Escherichia coli"
    assert inserted_record.data_quality_score > 0.80

    # 5. Invoke Naomi's downstream AI Engine task processor directly using our transaction session
    ai_engine = AMRAnomalyEngine()
    bg_tasks_mock = MagicMock()
    
    # Execute analysis pipeline 
    db_session.refresh(inserted_record)
    ai_engine.execute_analysis_pipeline(
        record_ids=[inserted_record.id], 
        db_session=db_session, 
        bg_tasks=bg_tasks_mock
    )

    # 6. Verify Anomaly engine successfully flagged record and saved an Alert tracking log
    generated_alert = db_session.query(Alert).filter(Alert.record_id == inserted_record.id).first()
    assert generated_alert is not None
    assert generated_alert.status == "PENDING"

    # 7. Execute the combined Claude Advisory & SMS generation task sub-routine synchronously
    db_session.refresh(generated_alert)
    ai_engine._process_advisory_and_sms(alert_id=generated_alert.id, db_session=db_session)

    # 8. Final Assertions: Ensure database states have transformed end-to-end smoothly
    db_session.refresh(generated_alert)
    assert generated_alert.status == "NOTIFIED"

    # Check if Claude's role-scoped advisory markdown was successfully saved to the database
    saved_brief = db_session.query(GuidanceBrief).filter(GuidanceBrief.alert_id == generated_alert.id).first()
    assert saved_brief is not None
    assert "WHO AWaRe" in saved_brief.guidance_markdown

    # Cleanup dependency overrides
    app.dependency_overrides.clear()
