# Track: backend/feature-api-name
import uuid
import os
from litellm import acompletion
from litellm.exceptions import APIError
from sqlalchemy.orm import Session
from src.models.entities import Alert, AMRRecord, GuidanceBrief

from src.core.config import settings

class LLMAdvisoryEngine:
    def __init__(self):
        # Set environment variables for litellm
        os.environ["ANTHROPIC_API_KEY"] = getattr(settings, "ANTHROPIC_API_KEY", "")
        os.environ["OPENAI_API_KEY"] = getattr(settings, "OPENAI_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = getattr(settings, "GEMINI_API_KEY", "")

        # Define model fallback list for high reliability
        self.models = [
            "gpt-4o", # Acts as Copilot proxy / top tier
            "claude-3-5-sonnet-20240620",
            "gemini/gemini-1.5-pro"
        ]

    async def trigger_role_guidance(self, alert_id: uuid.UUID, db_session: Session):
        alert = db_session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return
            
        record = db_session.query(AMRRecord).filter(AMRRecord.id == alert.amr_isolate_record_id).first()
        if not record:
            return

        roles_to_generate = ["National Coordinator", "County Veterinarian"]
        
        for role in roles_to_generate:
            if role == "National Coordinator":
                system_prompt = "You are advising a National Coordinator. Frame outputs strictly around national threshold analysis, resource reallocation vectors, and policy modifications."
            elif role == "County Veterinarian":
                system_prompt = "You are advising a County Veterinarian. Frame outputs around sub-county poultry empiric prescribing modifications, WHO AWaRe drug classifications, and direct action items linking to Kenya VMD SOP checklists."
            
            prompt = f"Alert for {record.pathogen_name} resistant to {record.antimicrobial_agent} in {record.county} County."
            
            try:
                # Use litellm acompletion with fallback
                response = await acompletion(
                    model=self.models[0],
                    fallbacks=self.models[1:],
                    max_tokens=1000,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                content_markdown = response.choices[0].message.content
                
                # Save into guidance_briefs table
                new_brief = GuidanceBrief(
                    alert_id=alert.id,
                    role_target=role,
                    content_markdown=content_markdown
                )
                db_session.add(new_brief)
                db_session.commit()
            except Exception as e:
                print(f"LLM API Error for role {role} after attempting all fallbacks: {e}")
