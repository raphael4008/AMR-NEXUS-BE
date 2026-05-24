"""
services/intelligence/llm_advisory.py — Component C: Adaptive LLM Advisory Engine

Core competitive differentiator for the July 14 demonstration.

Architecture:
  - Role-gated system prompt router: separate prompts for National Coordinator
    vs. County Veterinarian — each calibrated to their decision domain.
  - Claude API (claude-sonnet-4-5) generates structured Markdown briefs.
  - Guidance rows persisted to DB with full generation metadata (model, tokens, latency).
  - Graceful failure: APIError returns a PENDING Guidance with error metadata,
    never raising an HTTP 500 to the caller.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.core.config import settings
from src.models.entities import Alert, AMRRecord, Guidance, GuidanceStatusEnum

logger = logging.getLogger(__name__)


# ── Role System Prompts ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT_NATIONAL_COORDINATOR = """\
You are an expert AMR (Antimicrobial Resistance) policy advisor for the Kenya National \
AMR Coordination Secretariat. Your role is to analyze resistance surveillance signals \
and produce high-level, policy-actionable advisories aligned with:

  - The Kenya National AMR Action Plan (KNAAP 2023–2028)
  - WHO AWaRe antibiotic classification framework
  - GLASS (Global Antimicrobial Resistance and Use Surveillance System) reporting standards
  - One Health inter-ministerial coordination protocols

RESPONSE FORMAT — You must return a structured Markdown document with exactly these sections:
  ## 🚨 Resistance Signal Summary
  ## 📊 Epidemiological Context
  ## 🏛️ Policy & Regulatory Triggers
  ## 🔄 Resource & Allocation Recommendations
  ## ✅ Immediate National Action Checklist
  ## 📅 Reporting & Escalation Timeline

CONSTRAINTS:
  - Write for a National AMR Coordinator audience (senior public health official).
  - Reference specific KNAAP strategic objectives and WHO AWaRe tiers where applicable.
  - Keep the Immediate Action Checklist to 3–5 concrete, measurable items.
  - Do not speculate beyond the provided surveillance data.
  - Use precise clinical and policy language — avoid vague generalities.
"""

_SYSTEM_PROMPT_COUNTY_VETERINARIAN = """\
You are an expert One Health field advisor supporting frontline County Veterinary Officers \
and County Clinicians in Kenya's devolved health system. Your role is to translate AMR \
resistance surveillance signals into localized, practical action guidance aligned with:

  - Kenya's County Health Management Team (CHMT) Standard Operating Procedures
  - WHO AWaRe antibiotic prescribing guidance (Access, Watch, Reserve tiers)
  - Kenya National Veterinary Policy and Livestock Health guidelines
  - One Health field action protocols for human-animal-environment interfaces

RESPONSE FORMAT — You must return a structured Markdown document with exactly these sections:
  ## ⚠️ Local Resistance Alert
  ## 🐔 One Health Field Assessment (Human + Animal Sector)
  ## 💊 Empiric Prescribing Guidance
  ## 📋 SOP Action Checklist
  ## 📞 Escalation & Reporting Contacts
  ## 🔬 Specimen Collection Priorities

CONSTRAINTS:
  - Write for a County Veterinary Officer or County Clinician audience.
  - Be specific to the county and sub-county level where data permits.
  - The SOP Action Checklist must have 4–6 concrete, implementable steps.
  - Prescribing guidance must reference AWaRe tier (Access/Watch/Reserve).
  - Use plain, field-accessible language — minimize jargon.
  - Do not recommend treatments that are not available at county facility level.
"""

_ROLE_PROMPT_MAP: Dict[str, str] = {
    "National Coordinator": _SYSTEM_PROMPT_NATIONAL_COORDINATOR,
    "County Veterinarian": _SYSTEM_PROMPT_COUNTY_VETERINARIAN,
    "County Clinician": _SYSTEM_PROMPT_COUNTY_VETERINARIAN,  # Same prompt, clinician variant
}


class LLMAdvisoryEngine:
    """
    Component C: Role-gated LLM advisory generation via Claude API.

    Interfaces with Anthropic claude-sonnet-4-5 to produce structured Markdown
    briefings calibrated to the requesting user's role and decision domain.
    """

    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 1024

    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ── System Prompt Router ──────────────────────────────────────────────────────

    def _build_system_prompt(self, role: str) -> str:
        """
        Routes to the correct system prompt based on user role.
        Defaults to County Veterinarian guidance for unrecognized roles (safe fallback).
        """
        prompt = _ROLE_PROMPT_MAP.get(role)
        if not prompt:
            logger.warning(
                "Unrecognized role '%s' in LLMAdvisoryEngine — defaulting to County Veterinarian prompt.", role
            )
            prompt = _SYSTEM_PROMPT_COUNTY_VETERINARIAN
        return prompt

    # ── User Context Builder ──────────────────────────────────────────────────────

    def _build_user_context(self, alert: Alert, record: AMRRecord) -> str:
        """
        Formats the structured alert payload as a rich context block for the LLM.
        Includes all fields needed for role-specific advisory generation.
        """
        feature_imp = alert.feature_importance or {}
        shap_summary = (
            f"County contribution: {feature_imp.get('county_weight', 'N/A'):.2%} | "
            f"Pathogen risk: {feature_imp.get('pathogen_risk_weight', 'N/A'):.2%} | "
            f"Drug class: {feature_imp.get('drug_class_weight', 'N/A'):.2%} | "
            f"Sector signal: {feature_imp.get('sector_weight', 'N/A'):.2%}"
            if isinstance(feature_imp.get('county_weight'), float)
            else str(feature_imp)
        )
        sector_val = record.sector.value if hasattr(record.sector, "value") else str(record.sector)

        return f"""
RESISTANCE SURVEILLANCE ALERT — STRUCTURED DATA PAYLOAD
========================================================
Detection Timestamp : {alert.timestamp.strftime('%Y-%m-%d %H:%M UTC') if alert.timestamp else 'Unknown'}
Alert ID            : {alert.id}

ISOLATE DETAILS
---------------
Pathogen            : {record.pathogen_name}
Antimicrobial Agent : {record.antimicrobial_agent}
Resistance Result   : {record.result_value}
MIC Value           : {record.mic_value if record.mic_value else 'Not recorded'}

GEOGRAPHIC CONTEXT
------------------
County              : {record.county}
Sub-County          : {record.sub_county or 'Not specified'}
Facility Type       : {record.facility_type or 'Unknown/Not Reported'}
Sector              : {sector_val.upper()} (One Health domain)

ANOMALY METRICS
---------------
Anomaly Score       : {alert.anomaly_score:.4f} (IsolationForest; negative = anomaly)
Hotspot Magnitude   : {alert.hotspot_magnitude:.4f} (0=low, 1=critical)
Data Quality Score  : {record.data_quality_score:.2f} (1.0 = complete GLASS-compliant record)

SHAP EXPLAINABILITY SUMMARY (Feature Contributions to Alert)
-------------------------------------------------------------
{shap_summary}

INTEROPERABILITY REFERENCES
---------------------------
HL7 FHIR ID         : {record.hl7_fhir_id or 'Not assigned'}
WOAH Reference      : {record.woah_reference or 'Not assigned'}
Synthetic Data Flag : {'Yes (validation data)' if record.is_synthetic else 'No (real surveillance data)'}
========================================================
Please generate a role-specific advisory brief based on the above surveillance data.
"""

    # ── Advisory Generation ───────────────────────────────────────────────────────

    def generate_advisory(self, alert_id: int, role: str, db: Session) -> Guidance:
        """
        Main orchestration method:
          1. Fetch Alert + AMRRecord from DB
          2. Build system prompt (role-gated) + user context
          3. Call Claude API
          4. Persist Guidance to DB with full provenance metadata
          5. Return Guidance entity

        On APIError: creates a PENDING Guidance with error metadata (never raises).
        """
        import anthropic

        # ── Fetch data ─────────────────────────────────────────────────────────
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert ID {alert_id} not found in database.")

        record = db.query(AMRRecord).filter(AMRRecord.id == alert.record_id).first()
        if not record:
            raise ValueError(f"AMRRecord ID {alert.record_id} not found (linked to Alert {alert_id}).")

        system_prompt = self._build_system_prompt(role)
        user_context = self._build_user_context(alert, record)

        guidance_markdown: Optional[str] = None
        generation_metadata: Dict[str, Any] = {
            "model": self.MODEL,
            "role": role,
            "alert_id": alert_id,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        status = GuidanceStatusEnum.PENDING
        start_time = time.monotonic()

        try:
            logger.info(
                "Calling Claude API: model=%s, role='%s', alert_id=%d",
                self.MODEL, role, alert_id,
            )

            response = self._client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_context}],
            )

            latency_ms = round((time.monotonic() - start_time) * 1000, 1)
            guidance_markdown = response.content[0].text

            generation_metadata.update({
                "status": "success",
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": latency_ms,
                "stop_reason": response.stop_reason,
            })

            logger.info(
                "Advisory generated: role='%s', alert=%d, tokens=%d/%d, latency=%.0fms",
                role, alert_id, response.usage.input_tokens, response.usage.output_tokens, latency_ms,
            )

        except anthropic.APIError as exc:
            latency_ms = round((time.monotonic() - start_time) * 1000, 1)
            logger.error(
                "Anthropic API error for role='%s', alert_id=%d: %s", role, alert_id, exc
            )
            generation_metadata.update({
                "status": "api_error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "latency_ms": latency_ms,
            })

        except Exception as exc:
            logger.error(
                "Unexpected error in LLMAdvisoryEngine for alert_id=%d: %s", alert_id, exc
            )
            generation_metadata.update({
                "status": "unexpected_error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })

        # ── Persist Guidance ───────────────────────────────────────────────────
        guidance = Guidance(
            alert_id=alert_id,
            user_role=role,
            guidance_markdown=guidance_markdown,
            generation_metadata=generation_metadata,
            status=status,
        )
        db.add(guidance)
        db.flush()

        return guidance
