# Track: backend/feature-api-name
import africastalking
from src.core.config import settings

class NotificationService:
    def __init__(self):
        # Initialize the SDK
        username = getattr(settings, "AT_USERNAME", "sandbox")
        api_key = getattr(settings, "AT_API_KEY", "dummy_key")
        
        africastalking.initialize(username, api_key)
        self.sms = africastalking.SMS

    def dispatch_stewardship_trigger(self, phone: str, message: str):
        try:
            # Send the SMS
            response = self.sms.send(message, [phone])
            print(f"SMS dispatch successful: {response}")
            return response
        except Exception as e:
            # Gracefully handle sandbox timeouts or other errors without interrupting
            print(f"Failed to dispatch SMS to {phone}: {e}")
            return None
