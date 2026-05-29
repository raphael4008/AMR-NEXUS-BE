# Monorepo Branch Track: backend/feature-api-name
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.base import get_db
from src.models.entities import AMRRecord, Alert, GuidanceBrief

client = TestClient(app)

@pytest.fixture
def mock_claud_client():
    """Mocks out external Claude API response loops to protect the testing environment from network lag."""
    with patch("src.services.intelligence.llm_advisory.anthropic.Anthropic") as mock_anthropic:
        mock_instance = MagicMock()
        mock_msg_output = MagicMock()
        mock_msg_output.content = [MagicMock(text="### WHO AWaRe Stewardship Brief\n1. Enforce alternative prescribing patterns.")]
        mock_instance.messages.create.return_value = mock_msg_output
        mock_anthropic.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_sms_gateway():
    """Mocks the Africa's Talking SMS network engine layer."""
    with patch("src.services.notifications.sms_service.africastalking") as mock_at:
        mock_sms_instance = MagicMock()
        mock_sms_instance.send.return_value = {"SMSMessageData": {"Message": "Dispatched successfully to Sandbox"}}
        mock_at.SMS.return_value = mock_sms_instance
        yield mock_sms_instance

def test_complete_end_to_end_backend_processing_flow(
    db_session: Session, 
    mock_claud_client, 
    mock_sms_gateway
):
    """
    Executes a complete Integration Test across Component A, B, and C.
    Validates: Raw Data Upload -> Cleaning -> Storage -> Anomaly Scoring -> LLM Briefing -> SMS Notification.
    """
    # 1. Mock incoming synthetic lab payload matching Nicole's data model criteria
    raw_incoming_payload = [
        {
            "sector": "ANIMAL",
            "pathogen_name": "E. coli",  # Shorthand string to trigger Raph's normalization logic
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Kiambu",
            "sub_county": None,          # Triggers sub-county modal group imputation
            "facility_type": "Poultry Farm",
            "result_value": "R",         # High resistance flag to trigger Naomi's AI anomaly engine
            "ncbi_tax_id": 562,
            "sequencing_platform": "Illumina",
            "is_synthetic": 1
        }
    ]

    # 2. Bind FastAPI's dependency injection to our isolated test database session
    app.dependency_overrides[get_db] = lambda: db_session

    # 3. Post data payload to Raph's ingestion route gateway
    response = client.post("/api/v1/backbone/ingest/whonet", json=raw_incoming_payload)
    
    # Assert successful async handoff status code
    assert response.status_code == 202
    assert response.json()["processed_records"] == 1
    assert response.json()["critical_failures"] == 0

    # 4. Verify data cleaning and string normalization rules executed smoothly
    saved_record = db_session.query(AMRRecord).filter(AMRRecord.county == "Kiambu").first()
    assert saved_record is not None
    assert saved_record.pathogen_name == "Escherichia coli"
    assert saved_record.data_quality_score > 0.80

    # 5. Invoke Naomi's downstream AI pipeline worker synchronously for testing evaluation
    ai_engine = AMRAnomalyEngine()
    mock_bg_tasks = MagicMock()
    
    db_session.refresh(saved_record)
    ai_engine.execute_analysis_pipeline(
        record_ids=[saved_record.id], 
        db_session=db_session, 
        bg_tasks=mock_bg_tasks
    )

    # 6. Assert that the record was correctly flagged and committed as a system alert
    triggered_alert = db_session.query(Alert).filter(Alert.record_id == saved_record.id).first()
    assert triggered_alert is not None
    assert triggered_alert.status == "PENDING"

    # 7. Execute the combined Claude Advisory & SMS generation task synchronously
    db_session.refresh(triggered_alert)
    ai_engine._process_advisory_and_sms(alert_id=triggered_alert.id, db_session=db_session)

    # 8. Assert that the database transaction completed end-to-end smoothly
    db_session.refresh(triggered_alert)
    assert triggered_alert.status == "NOTIFIED"

    # Confirm Claude's role-scoped advisory markdown was successfully saved to the database
    saved_brief = db_session.query(GuidanceBrief).filter(GuidanceBrief.alert_id == triggered_alert.id).first()
    assert saved_brief is not None
    assert "WHO AWaRe" in saved_brief.guidance_markdown

    # Clear dependency overrides to prevent test contamination
    app.dependency_overrides.clear()
