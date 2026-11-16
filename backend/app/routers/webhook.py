import logging
import os
import threading
import time

from fastapi import APIRouter, BackgroundTasks, Request, Response

from app.services import stub_data, whatsapp_service

router = APIRouter(tags=["webhook"])

logger = logging.getLogger(__name__)

_seen_message_ids: dict[str, float] = {}
_seen_lock = threading.Lock()
_SEEN_TTL_SECONDS = 600


def reset_dedupe() -> None:
    with _seen_lock:
        _seen_message_ids.clear()


def _is_duplicate(message_id: str) -> bool:
    if not message_id:
        return False

    now = time.monotonic()
    with _seen_lock:
        stale = [k for k, seen_at in _seen_message_ids.items() if now - seen_at > _SEEN_TTL_SECONDS]
        for key in stale:
            _seen_message_ids.pop(key, None)

        if message_id in _seen_message_ids:
            return True

        _seen_message_ids[message_id] = now
        return False


def process_message(from_number: str, message_text: str) -> None:
    """Answer an incoming WhatsApp message with a menu/rule/RAG reply."""
    logger.info("Received WhatsApp message from=%s body=%r", from_number, message_text)

    if not message_text.strip():
        logger.info("No text content from %s; not replying", from_number)
        return

    try:
        result = stub_data.ask(from_number, message_text)
        reply = result["bot_message"]["message_text"]
        whatsapp_service.send_message(from_number, reply)
    except Exception:
        logger.exception("Failed to reply to %s", from_number)


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
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
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
                message_id = str(message.get("id") or "")
                if _is_duplicate(message_id):
                    logger.info("Ignoring duplicate webhook message id=%s", message_id)
                    continue

                from_number = message.get("from", "")
                message_text = message.get("text", {}).get("body", "")
                background_tasks.add_task(process_message, from_number, message_text)

    return Response(content="OK", status_code=200)