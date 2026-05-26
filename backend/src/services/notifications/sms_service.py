"""
services/notifications/sms_service.py — Async Africa's Talking SMS Dispatcher

Runs against the Africa's Talking Sandbox for the July 14 demo.
The dispatch_alert method is async and wraps the blocking SDK call in
run_in_executor so it never blocks the FastAPI event loop.
"""

import asyncio
import logging
from typing import Any, Dict

import africastalking

from src.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    Async wrapper around the Africa's Talking SMS SDK.

    Trigger condition: anomaly_score < 0 AND data_quality_score > 0.7
    (enforced upstream in AMRAnomalyEngine — SMSService has no threshold logic).
    """

    def __init__(self):
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        self._sms = africastalking.SMS

    # ── Message Builder ───────────────────────────────────────────────────────────

    def build_stewardship_message(
        self,
        county: str,
        pathogen: str,
        drug: str,
        role: str,
    ) -> str:
        """
        Generates role-differentiated SMS copy.

        - County Veterinarian / Clinician: concise action line (SMS-friendly, <160 chars target)
        - National Coordinator: structured one-line brief with policy trigger note
        """
        if role == "National Coordinator":
            return (
                f"[AMR-Nexus NATIONAL ALERT] Resistance hotspot detected: {pathogen} resistant to "
                f"{drug} in {county}. KNAAP policy trigger activated. Review dashboard & escalate "
                f"to inter-ministerial AMR coordination team immediately."
            )
        else:
            # County Veterinarian / County Clinician — field-action focused
            return (
                f"AMR-Nexus Alert [{county}]: High {drug} resistance in {pathogen} detected. "
                f"Review empiric Rx. Use Access-tier alternatives per WHO AWaRe guidelines. "
                f"Submit isolate specimens. Contact CHMT if >3 cases this week."
            )

    # ── Async Dispatch ────────────────────────────────────────────────────────────

    async def dispatch_alert(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Sends an SMS via Africa's Talking Sandbox without blocking the event loop.

        The africastalking SDK is synchronous; this method wraps it in
        asyncio.get_event_loop().run_in_executor() for safe async usage.

        Args:
            phone: E.164 format phone number (e.g., "+254712345678").
            message: SMS body text.

        Returns:
            Dict with {"status": "sent" | "failed", "response": ..., "reason": ...}
        """
        def _blocking_send():
            return self._sms.send(message, [phone])

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _blocking_send)
            logger.info("SMS dispatched to %s: %s", phone, response)
            return {"status": "sent", "phone": phone, "response": response}

        except Exception as exc:
            logger.warning(
                "SMS dispatch failed for %s (sandbox timeout or SDK error): %s", phone, exc
            )
            return {"status": "failed", "phone": phone, "reason": str(exc)}
