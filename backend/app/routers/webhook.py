import logging
import os
import threading
import time

from fastapi import APIRouter, BackgroundTasks, Request, Response

from app.config import settings
from app.services import chat_store, reply_engine, voice_service, whatsapp_service

router = APIRouter(tags=["webhook"])

logger = logging.getLogger(__name__)

_seen_message_ids: dict[str, float] = {}
_seen_lock = threading.Lock()
_SEEN_TTL_SECONDS = 600

_AUDIO_FILENAMES = {
    "audio/ogg": "voice.ogg",
    "audio/opus": "voice.opus",
    "audio/mpeg": "voice.mp3",
    "audio/mp4": "voice.m4a",
    "audio/aac": "voice.aac",
    "audio/amr": "voice.amr",
}

_UNSUPPORTED_REPLIES = {
    "image": "I can't read images yet.",
    "video": "I can't watch videos yet.",
    "sticker": "I can't read stickers yet.",
    "document": "I can't open documents yet.",
    "location": "I can't read locations yet.",
    "contacts": "I can't read contact cards yet.",
}


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


def _answer_and_persist(from_number: str, message_text: str, input_type: str = "text") -> str:
    reply, intent_type, routing = chat_store.quick_reply(from_number, message_text)
    whatsapp_service.send_message(from_number, reply)
    chat_store.record_exchange(
        from_number, message_text, reply, intent_type, routing, input_type=input_type
    )
    return reply


def process_message(from_number: str, message_text: str) -> None:
    """Answer an incoming WhatsApp text message with a menu/rule/RAG reply."""
    logger.info("Received WhatsApp message from=%s body=%r", from_number, message_text)

    if not message_text.strip():
        logger.info("No text content from %s; not replying", from_number)
        return

    try:
        _answer_and_persist(from_number, message_text)
    except Exception:
        logger.exception("Failed to reply to %s", from_number)


def process_audio_message(from_number: str, media_id: str) -> None:
    """Transcribe an inbound voice note, answer it, and reply with voice + text."""
    if not media_id:
        whatsapp_service.send_message(
            from_number,
            "I couldn't open that voice note. Please try again or type your question. "
            + reply_engine.MENU_HINT,
        )
        return

    media = whatsapp_service.download_media(media_id)
    if media is None:
        whatsapp_service.send_message(
            from_number,
            "I couldn't download that voice note. Please try again or type your question. "
            + reply_engine.MENU_HINT,
        )
        return

    audio_bytes, mime_type = media
    filename = _AUDIO_FILENAMES.get(mime_type.split(";")[0].strip(), "voice.ogg")
    transcript = voice_service.transcribe(audio_bytes, filename=filename, content_type=mime_type)

    if not transcript:
        whatsapp_service.send_message(
            from_number,
            "I received your voice note but I can't listen to audio yet. "
            "Please type your question. " + reply_engine.MENU_HINT,
        )
        return

    logger.info("Transcribed voice note from=%s text=%r", from_number, transcript)

    try:
        reply = _answer_and_persist(from_number, transcript, input_type="audio")
    except Exception:
        logger.exception("Failed to answer voice note from %s", from_number)
        return

    if not settings.VOICE_REPLIES_ENABLED:
        return

    audio_reply = voice_service.synthesize(reply)
    if not audio_reply:
        return

    outbound_media_id = whatsapp_service.upload_media(
        audio_reply, mime_type="audio/mpeg", filename="reply.mp3"
    )
    if outbound_media_id:
        whatsapp_service.send_audio(from_number, outbound_media_id)


def process_unsupported_message(from_number: str, message_type: str) -> None:
    prefix = _UNSUPPORTED_REPLIES.get(message_type, "I can't read that kind of message yet.")
    whatsapp_service.send_message(from_number, f"{prefix} {reply_engine.MENU_HINT}")


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
                message_type = str(message.get("type") or "")

                if message_type == "text":
                    message_text = (message.get("text") or {}).get("body", "")
                    background_tasks.add_task(process_message, from_number, message_text)
                elif message_type == "audio":
                    media_id = str((message.get("audio") or {}).get("id") or "")
                    background_tasks.add_task(process_audio_message, from_number, media_id)
                else:
                    background_tasks.add_task(
                        process_unsupported_message, from_number, message_type
                    )

    return Response(content="OK", status_code=200)

