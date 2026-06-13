import uuid
import logging
from typing import Optional
from litellm import acompletion
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.entities import Alert, AMRRecord, GuidanceBrief
from src.core.config import settings

logger = logging.getLogger(__name__)

# Registry remains as is
_ROLE_SYSTEM_PROMPTS = {
    "National Coordinator": "...",
    "County Veterinarian": "..."
}

class LLMAdvisoryEngine:
    def __init__(self):
        # Prefer configuration over environment mutation
        self.models = ["claude-3-5-sonnet-20241022", "gemini/gemini-1.5-pro", "gpt-4o-mini"]
        self.max_tokens = 900

    async def trigger_role_guidance(
        self,
        alert_id: uuid.UUID,
        target_role: str,
        db: AsyncSession, # Changed from Session to AsyncSession
    ) -> Optional[GuidanceBrief]:
        
        if target_role not in _ROLE_SYSTEM_PROMPTS:
            raise ValueError(f"Invalid role: {target_role}")

        # 1. Async Fetch with Join (Optimization: fetch record and alert together)
        stmt = (
            select(Alert)
            .options(selectinload(Alert.amr_record))
            .where(Alert.id == alert_id)
        )
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert or not alert.amr_record:
            logger.warning(f"Data missing for alert {alert_id}")
            return None

        record = alert.amr_record
        system_prompt = _ROLE_SYSTEM_PROMPTS[target_role]

        # 2. Build Prompt (Logic unchanged)
        prompt = self._construct_prompt(alert, record, target_role)

        try:
            # 3. Async LLM Call
            response = await acompletion(
                model=self.models[0],
                fallbacks=self.models[1:],
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content

            # 4. Async Persistence
            new_brief = GuidanceBrief(
                alert_id=alert.id,
                role_target=target_role,
                content_markdown=content,
                status="PENDING",
            )
            db.add(new_brief)
            await db.commit()
            await db.refresh(new_brief)

            return new_brief

        except Exception as exc:
            logger.error(f"LLM API failed: {exc}")
            return None

    def _construct_prompt(self, alert: Alert, record: AMRRecord, role: str) -> str:
        # Helper method to keep the main logic clean
        return (f"Context: ...")