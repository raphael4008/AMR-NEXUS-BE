# Track: backend/feature-api-name
import uuid
import anthropic
from sqlalchemy.orm import Session
from src.models.entities import Alert, AMRRecord, GuidanceBrief

from src.core.config import settings

class LLMAdvisoryEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "stub_key")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

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
                response = await self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content_markdown = response.content[0].text
                
                # Save into guidance_briefs table
                new_brief = GuidanceBrief(
                    alert_id=alert.id,
                    role_target=role,
                    content_markdown=content_markdown
                )
                db_session.add(new_brief)
                db_session.commit()
            except Exception as e:
                print(f"LLM API Error for role {role}: {e}")
