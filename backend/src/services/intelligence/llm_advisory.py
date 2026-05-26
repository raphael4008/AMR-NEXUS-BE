import logging
from sqlalchemy.orm import Session
from src.models.entities import Alert, Guidance

logger = logging.getLogger(__name__)

class LLMAdvisoryEngine:
    def __init__(self, anthropic_client=None):
        self.client = anthropic_client

    def _get_role_context(self, role: str) -> str:
        """Maps distinct system contexts based on the user's role target."""
        if role == "National Coordinator":
            return (
                "You are an AMR Policy Advisor following Kenya's National AMR Action Plan. "
                "Analyze the anomaly metrics and provide macro-level strategic guidance, "
                "policy modification recommendations, and resource allocation plans. "
                "Output strictly in Markdown, aligning with WHO AWaRe classification."
            )
        elif role == "County Veterinarian":
            return (
                "You are an AMR Clinical Advisor. Analyze the anomaly metrics and provide "
                "localized clinical summaries and direct SOP action checklists for poultry "
                "farmers. Output strictly in Markdown."
            )
        return "You are an AMR Advisor. Provide a standard briefing in Markdown."

    def _invoke_claude_stub(self, prompt: str, system: str) -> str:
        # Replaces raw anthropic.messages.create() logic for the MVP
        return f"### AMR Response Advisory\n\n**System Focus:** {system[:40]}...\n\n- Evaluate intervention protocols immediately."

    def trigger_role_guidance(self, alert_id: int, db_session: Session) -> None:
        """
        Extracts risk metrics and dynamically routes system prompts to the LLM.
        """
        alert = db_session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert {alert_id} not found.")
            return

        roles = ["National Coordinator", "County Veterinarian"]
        
        for role in roles:
            system_prompt = self._get_role_context(role)
            prompt_content = f"Analyze anomaly with magnitude {alert.hotspot_magnitude} for Alert #{alert.id}."
            
            content_markdown = self._invoke_claude_stub(prompt=prompt_content, system=system_prompt)

            guidance = Guidance(
                alert_id=alert.id,
                role_target=role,
                content_markdown=content_markdown,
                status="COMPLETED"
            )
            db_session.add(guidance)
        
        db_session.commit()
