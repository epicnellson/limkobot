import logging
import os

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"
API_VERSION = "v20.0"


def send_message(to_number: str, text: str) -> dict | None:
    """Send a WhatsApp text message via Meta's Graph API."""
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

    if not phone_number_id or not access_token:
        logger.info(
            "WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_ACCESS_TOKEN not set; "
            "skipping send to %s",
            to_number,
        )
        return None

    url = f"{GRAPH_API_BASE}/{API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=body)

    response.raise_for_status()
    return response.json()