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


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> Response:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}
    messages = value.get("messages") or []

    if messages:
        message = messages[0]
        from_number = message.get("from", "")
        message_text = message.get("text", {}).get("body", "")
        process_message(from_number, message_text)

    return Response(content="OK", status_code=200)