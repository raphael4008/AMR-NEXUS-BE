from typing import Any, Optional
import africastalking
from src.core.config import settings
from src.utils.logger import logger


def send_sms_alert(phone: str, message: str) -> Optional[Any]:
    try:
        africastalking.initialize(
            username=settings.AT_USERNAME, 
            api_key=settings.AT_API_KEY
        )
        sms = africastalking.SMS
        
        response = sms.send(
            message=message, 
            recipients=[phone], 
            sender_id=settings.AT_SENDER_ID if settings.AT_SENDER_ID else None
        )
        logger.info(f"SMS alert dispatched securely via Africa's Talking gateway to {phone}.")
        return response
    except Exception as e:
        logger.error(f"Asynchronous SMS transmission protocol failed: {str(e)}")
        return None
