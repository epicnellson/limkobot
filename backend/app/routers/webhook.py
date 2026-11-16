import logging
import os

from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["webhook"])

logger = logging.getLogger(__name__)


def process_message(from_number: str, message_text: str) -> None:
    """Route an incoming WhatsApp message for processing.

    TODO: detect intent, run RAG retrieval/answer generation, and send the
    bot reply back via whatsapp_service.send_message().
    """
    logger.info("Received WhatsApp message from=%s body=%r", from_number, message_text)


@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request) -> Response:
    query = request.query_params
    mode = query.get("hub.mode")
    verify_token = query.get("hub.verify_token")
    challenge = query.get("hub.challenge")

    if mode == "subscribe" and verify_token == os.getenv("WEBHOOK_VERIFY_TOKEN"):
        return Response(content=str(challenge), media_type="text/plain")

    return Response(status_code=403)


def _expected_phone_number_id() -> str:
    return os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> Response:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    expected_id = _expected_phone_number_id()

    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = str(metadata.get("phone_number_id") or "")

            if expected_id and phone_number_id != expected_id:
                logger.info(
                    "Ignoring webhook for phone_number_id=%s (expected %s)",
                    phone_number_id,
                    expected_id,
                )
                continue

            for message in value.get("messages") or []:
                from_number = message.get("from", "")
                message_text = message.get("text", {}).get("body", "")
                process_message(from_number, message_text)

    return Response(content="OK", status_code=200)