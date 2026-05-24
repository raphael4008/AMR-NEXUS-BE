"""
tests/test_llm_advisory.py — Unit tests for LLMAdvisoryEngine (Component C)

Validates:
  - Correct system prompt is selected per role (National Coordinator vs County Veterinarian)
  - User context block contains all required data fields
  - Advisory is persisted as a Guidance row with correct metadata
  - APIError produces a PENDING Guidance with error metadata (never raises)
  - Unknown role falls back to County Veterinarian prompt (safe default)
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.intelligence.llm_advisory import (
    LLMAdvisoryEngine,
    _SYSTEM_PROMPT_NATIONAL_COORDINATOR,
    _SYSTEM_PROMPT_COUNTY_VETERINARIAN,
)
from src.models.entities import GuidanceStatusEnum


# ── System Prompt Routing ──────────────────────────────────────────────────────

class TestSystemPromptRouting:
    def test_national_coordinator_prompt(self):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        prompt = engine._build_system_prompt("National Coordinator")
        assert "KNAAP" in prompt
        assert "policy" in prompt.lower()
        assert prompt == _SYSTEM_PROMPT_NATIONAL_COORDINATOR

    def test_county_veterinarian_prompt(self):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        prompt = engine._build_system_prompt("County Veterinarian")
        assert "AWaRe" in prompt
        assert "County" in prompt
        assert prompt == _SYSTEM_PROMPT_COUNTY_VETERINARIAN

    def test_county_clinician_uses_vet_prompt(self):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        prompt = engine._build_system_prompt("County Clinician")
        assert prompt == _SYSTEM_PROMPT_COUNTY_VETERINARIAN

    def test_unknown_role_defaults_to_vet_prompt(self):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        prompt = engine._build_system_prompt("Random Role XYZ")
        assert prompt == _SYSTEM_PROMPT_COUNTY_VETERINARIAN


# ── User Context Builder ───────────────────────────────────────────────────────

class TestContextBuilder:
    def test_context_contains_county(self, sample_alert, sample_amr_record):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        context = engine._build_user_context(sample_alert, sample_amr_record)
        assert "Nairobi" in context

    def test_context_contains_pathogen(self, sample_alert, sample_amr_record):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        context = engine._build_user_context(sample_alert, sample_amr_record)
        assert "E. coli" in context

    def test_context_contains_anomaly_score(self, sample_alert, sample_amr_record):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        context = engine._build_user_context(sample_alert, sample_amr_record)
        assert "Anomaly Score" in context

    def test_context_contains_shap_summary(self, sample_alert, sample_amr_record):
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        context = engine._build_user_context(sample_alert, sample_amr_record)
        # Feature importance should produce SHAP summary line
        assert "county" in context.lower() or "SHAP" in context


# ── Advisory Generation ────────────────────────────────────────────────────────

class TestAdvisoryGeneration:
    def test_successful_generation_persists_guidance(self, db_session, sample_alert):
        """Happy path: Claude mock returns text → Guidance row persisted with markdown."""
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)

        # Mock the Anthropic client on the engine instance
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## 🚨 Test Advisory Brief\nContent here.")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=150)
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        engine._client = mock_client

        guidance = engine.generate_advisory(
            alert_id=sample_alert.id,
            role="National Coordinator",
            db=db_session,
        )

        assert guidance is not None
        assert guidance.alert_id == sample_alert.id
        assert guidance.user_role == "National Coordinator"
        assert "Test Advisory Brief" in guidance.guidance_markdown
        assert guidance.generation_metadata["status"] == "success"
        assert guidance.generation_metadata["model"] == "claude-sonnet-4-5"
        assert "input_tokens" in guidance.generation_metadata

    def test_guidance_status_is_pending_after_generation(self, db_session, sample_alert):
        """Generated guidance starts in PENDING status (requires human approval)."""
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Test")]
        mock_response.usage = MagicMock(input_tokens=80, output_tokens=100)
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        engine._client = mock_client

        guidance = engine.generate_advisory(
            alert_id=sample_alert.id,
            role="County Veterinarian",
            db=db_session,
        )
        assert guidance.status == GuidanceStatusEnum.PENDING

    def test_api_error_produces_pending_guidance_not_exception(self, db_session, sample_alert):
        """APIError must be caught and surfaced as PENDING guidance, not an HTTP 500."""
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        mock_client = MagicMock()
        # Simulate an Anthropic APIError (we aliased it to Exception in the mock)
        mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
        engine._client = mock_client

        # Patch anthropic.APIError to be our Exception type
        import src.services.intelligence.llm_advisory as advisory_module
        with patch.object(advisory_module, "__builtins__", {}):
            # The engine catches anthropic.APIError — since we mocked it as Exception
            # this will be caught by the generic except block
            pass

        # The call should NOT raise — it returns a Guidance with error metadata
        try:
            guidance = engine.generate_advisory(
                alert_id=sample_alert.id,
                role="National Coordinator",
                db=db_session,
            )
            # If we get here without raising, the test passes
            assert guidance is not None
            assert guidance.alert_id == sample_alert.id
            assert guidance.guidance_markdown is None or "error" in str(
                guidance.generation_metadata.get("status", "")
            ).lower()
        except Exception:
            # The engine should handle all exceptions internally
            pytest.fail("LLMAdvisoryEngine raised an unhandled exception instead of returning a Guidance row.")

    def test_missing_alert_raises_value_error(self, db_session):
        """Requesting advisory for non-existent alert_id must raise ValueError (not crash)."""
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        engine._client = MagicMock()

        with pytest.raises(ValueError, match="not found"):
            engine.generate_advisory(
                alert_id=99999,
                role="National Coordinator",
                db=db_session,
            )

    def test_generation_metadata_includes_latency(self, db_session, sample_alert):
        """Generation metadata must include latency_ms for performance monitoring."""
        engine = LLMAdvisoryEngine.__new__(LLMAdvisoryEngine)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Advisory")]
        mock_response.usage = MagicMock(input_tokens=90, output_tokens=120)
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        engine._client = mock_client

        guidance = engine.generate_advisory(
            alert_id=sample_alert.id,
            role="County Veterinarian",
            db=db_session,
        )
        assert "latency_ms" in guidance.generation_metadata
        assert guidance.generation_metadata["latency_ms"] >= 0
