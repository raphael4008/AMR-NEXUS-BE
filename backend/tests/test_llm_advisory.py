import pytest
import uuid
from unittest.mock import patch, MagicMock
from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
from src.models.entities import Alert, AMRRecord, GuidanceBrief

@pytest.mark.asyncio
async def test_llm_advisory_engine_fallback(db_session, sample_alert):
    engine = LLMAdvisoryEngine()
    
    # Mock litellm acompletion to return a specific response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "## Fallback Advisory\nThis is a mock response."
    
    with patch("src.services.intelligence.llm_advisory.acompletion", return_value=mock_response) as mock_acompletion:
        await engine.trigger_role_guidance(sample_alert.id, db_session)
        
        # Verify that acompletion was called twice (once for National Coordinator, once for County Veterinarian)
        assert mock_acompletion.call_count == 2
        
        # Verify fallbacks are set correctly in the call args
        args, kwargs = mock_acompletion.call_args
        assert kwargs["model"] == engine.models[0]
        assert kwargs["fallbacks"] == engine.models[1:]
        
        # Verify GuidanceBrief was inserted in db
        briefs = db_session.query(GuidanceBrief).filter(GuidanceBrief.alert_id == sample_alert.id).all()
        assert len(briefs) == 2
        
        roles = [b.role_target for b in briefs]
        assert "National Coordinator" in roles
        assert "County Veterinarian" in roles
        
        for brief in briefs:
            assert brief.content_markdown == "## Fallback Advisory\nThis is a mock response."
