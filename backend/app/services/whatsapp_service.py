import logging
import os

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"
API_VERSION = "v20.0"
MAX_MEDIA_BYTES = 16 * 1024 * 1024


def _credentials() -> tuple[str | None, str | None]:
    return os.getenv("WHATSAPP_PHONE_NUMBER_ID"), os.getenv("WHATSAPP_ACCESS_TOKEN")


def _messages_url(phone_number_id: str) -> str:
    return f"{GRAPH_API_BASE}/{API_VERSION}/{phone_number_id}/messages"


def download_media(media_id: str) -> tuple[bytes, str] | None:
    """Download one inbound media object; returns (bytes, mime_type)."""
    phone_number_id, access_token = _credentials()
    if not media_id or not phone_number_id or not access_token:
        logger.info("WhatsApp credentials missing; cannot download media %s", media_id)
        return None

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        with httpx.Client(timeout=30) as client:
            meta = client.get(f"{GRAPH_API_BASE}/{API_VERSION}/{media_id}", headers=headers)
            meta.raise_for_status()
            info = meta.json()
            url = info.get("url")
            if not url:
                logger.warning("Media %s has no download url", media_id)
                return None
            media = client.get(url, headers=headers)
            media.raise_for_status()
    except Exception:  # noqa: BLE001 - media is best-effort
        logger.exception("Failed to download media %s", media_id)
        return None

    content = media.content
    if not content or len(content) > MAX_MEDIA_BYTES:
        logger.warning("Media %s rejected: %s bytes", media_id, len(content))
        return None
    return content, info.get("mime_type") or "audio/ogg"


def upload_media(
    content: bytes,
    mime_type: str = "audio/mpeg",
    filename: str = "reply.mp3",
) -> str | None:
    """Upload outbound media; returns the media id."""
    phone_number_id, access_token = _credentials()
    if not content or not phone_number_id or not access_token:
        return None

    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"messaging_product": "whatsapp", "type": mime_type}
    files = {"file": (filename, content, mime_type)}
    url = f"{GRAPH_API_BASE}/{API_VERSION}/{phone_number_id}/media"

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()
        return response.json().get("id")
    except Exception:  # noqa: BLE001 - media is best-effort
        logger.exception("Failed to upload outbound media")
        return None


def send_message(to_number: str, text: str) -> dict | None:
    """Send a WhatsApp text message via Meta's Graph API."""
    phone_number_id, access_token = _credentials()

    if not phone_number_id or not access_token:
        logger.info(
            "WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_ACCESS_TOKEN not set; "
            "skipping send to %s",
            to_number,
        )
        return None

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
        response = client.post(_messages_url(phone_number_id), headers=headers, json=body)

    response.raise_for_status()
    return response.json()


def send_audio(to_number: str, media_id: str) -> dict | None:
    """Send a WhatsApp voice message using an uploaded media id."""
    phone_number_id, access_token = _credentials()

    if not phone_number_id or not access_token or not media_id:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "audio",
        "audio": {"id": media_id},
    }

    try:
        with httpx.Client() as client:
            response = client.post(_messages_url(phone_number_id), headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    except Exception:  # noqa: BLE001 - voice reply is best-effort
        logger.exception("Failed to send audio reply to %s", to_number)
        return None
