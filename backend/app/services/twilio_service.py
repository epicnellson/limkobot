import logging

from app.config import settings

logger = logging.getLogger(__name__)


def send_whatsapp_message(to: str, body: str) -> None:
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
        logger.info("Twilio credentials not set; skipping WhatsApp message to %s", to)
        return

    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM, to=f"whatsapp:{to}", body=body
    )