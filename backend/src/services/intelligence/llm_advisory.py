# Track: backend/feature-api-name
# LLMAdvisoryEngine v1.3 — Cost-optimized single-role advisory generation.
# Fixes: dual-role evaluation on a single alert transaction (cost overrun bug).
# Refactored: trigger_role_guidance now accepts explicit target_role parameter.

import uuid
import os
import logging
from typing import Optional
from litellm import acompletion
from litellm.exceptions import APIError
from sqlalchemy.orm import Session

from src.models.entities import Alert, AMRRecord, GuidanceBrief
from src.core.config import settings

logger = logging.getLogger(__name__)

# ── Role-specific system prompt registry ──────────────────────────────────────
_ROLE_SYSTEM_PROMPTS: dict[str, str] = {
    "National Coordinator": (
        "You are an AMR intelligence advisor supporting a National Coordinator in Kenya. "
        "Frame all outputs strictly around national-level resistance threshold analysis, "
        "resource reallocation vectors across counties, policy modification recommendations, "
        "and WHO GAP-AMR 2026-2036 strategic alignment. Use evidence-based language and "
        "reference Kenya's National Action Plan on AMR where relevant."
    ),
    "County Veterinarian": (
        "You are an AMR stewardship advisor supporting a County Veterinarian in Kenya. "
        "Frame all outputs around sub-county poultry and livestock empiric prescribing "
        "modifications, WHO AWaRe drug classifications (Watch/Reserve/Access), direct "
        "action items linking to Kenya VMD SOP checklists, and FAO InFARM reporting "
        "obligations. Prioritize field-practical, actionable guidance."
    ),
}

_VALID_ROLES = frozenset(_ROLE_SYSTEM_PROMPTS.keys())


class LLMAdvisoryEngine:
    """
    Cost-optimized LLM advisory engine using litellm with multi-model fallback.
    Each call targets exactly ONE explicit role, eliminating the dual-role
    evaluation bug that doubled API cost per alert transaction.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Allow api_key injection for testing (mock compatibility)
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        else:
            os.environ["ANTHROPIC_API_KEY"] = getattr(settings, "ANTHROPIC_API_KEY", "")

        os.environ["OPENAI_API_KEY"] = getattr(settings, "OPENAI_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = getattr(settings, "GEMINI_API_KEY", "")

        # Model fallback list — primary + fallbacks for high reliability
        self.models = [
            "claude-3-5-sonnet-20241022",  # Primary: best cost/quality for structured health briefs
            "gemini/gemini-1.5-pro",       # Fallback 1: low cost, high context
            "gpt-4o-mini",                 # Fallback 2: fast, inexpensive
        ]
        self.max_tokens = 900  # Capped to control cost; sufficient for a structured advisory

    async def trigger_role_guidance(
        self,
        alert_id: uuid.UUID,
        target_role: str,
        db_session: Session,
    ) -> Optional[GuidanceBrief]:
        """
        Generates a single role-specific advisory brief for the specified target_role.
        Routes the alert context through the role's dedicated system prompt architecture.
        Commits the generated markdown directly to the guidance_briefs table.

        Args:
            alert_id:    UUID of the alert record to generate guidance for.
            target_role: Explicit role string — 'National Coordinator' or 'County Veterinarian'.
            db_session:  Active SQLAlchemy session.

        Returns:
            The persisted GuidanceBrief ORM object, or None on failure.

        Raises:
            ValueError: If target_role is not a recognized role string.
        """
        if target_role not in _VALID_ROLES:
            raise ValueError(
                f"Invalid target_role '{target_role}'. "
                f"Must be one of: {sorted(_VALID_ROLES)}"
            )

        alert = db_session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.warning(f"trigger_role_guidance: Alert {alert_id} not found.")
            return None

        record = db_session.query(AMRRecord).filter(
            AMRRecord.id == alert.amr_isolate_record_id
        ).first()
        if not record:
            logger.warning(f"trigger_role_guidance: AMRRecord for alert {alert_id} not found.")
            return None

        system_prompt = _ROLE_SYSTEM_PROMPTS[target_role]

        # Build a structured, context-rich prompt from available record fields
        classification_note = f" ({record.classification})" if getattr(record, "classification", None) else ""
        prompt = (
            f"### AMR-Nexus Resistance Alert — {target_role} Advisory\n\n"
            f"**Pathogen:** {record.pathogen_name}{classification_note}\n"
            f"**Antimicrobial:** {record.antimicrobial_agent}\n"
            f"**SIR Result:** {record.result_value}\n"
            f"**Location:** {record.county} County"
            + (f", {record.sub_county} Sub-County" if record.sub_county else "") + "\n"
            f"**Sector:** {record.sector}\n"
            f"**Anomaly Score:** {float(alert.anomaly_score):.2f} | "
            f"**Hotspot Magnitude:** {float(alert.hotspot_magnitude):.2f}\n\n"
            f"Generate a structured Stewardship Guidance Brief in markdown format "
            f"with clear action items, clinical/policy implications, and next steps "
            f"tailored specifically for a {target_role}."
        )

        try:
            response = await acompletion(
                model=self.models[0],
                fallbacks=self.models[1:],
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
            )
            content_markdown: str = response.choices[0].message.content

            new_brief = GuidanceBrief(
                alert_id=alert.id,
                role_target=target_role,
                content_markdown=content_markdown,
                status="PENDING",
            )
            db_session.add(new_brief)
            db_session.commit()
            db_session.refresh(new_brief)

            logger.info(
                f"Advisory generated for role='{target_role}', alert={alert_id}, "
                f"brief={new_brief.id}"
            )
            return new_brief

        except Exception as exc:
            logger.error(
                f"LLM API error for role='{target_role}', alert={alert_id} "
                f"after all fallbacks exhausted: {exc}"
            )
            return None
