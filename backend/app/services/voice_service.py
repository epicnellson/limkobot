"""Speech-to-text and text-to-speech helpers backed by the OpenAI API.

Both helpers degrade to None when no OpenAI key is configured or the request
fails, so the WhatsApp flow can fall back to text replies.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TRANSCRIBE_TIMEOUT_SECONDS = 60
SPEECH_TIMEOUT_SECONDS = 60

_last_errors: dict[str, str] = {}


def _record_error(kind: str, message: str) -> None:
    _last_errors[kind] = message[:400]


def diagnostics() -> dict:
    return {
        "openai_key_configured": bool(settings.OPENAI_API_KEY),
        "stt_model": settings.STT_MODEL,
        "tts_model": settings.TTS_MODEL,
        "tts_voice": settings.TTS_VOICE,
        "voice_replies_enabled": settings.VOICE_REPLIES_ENABLED,
        "last_errors": dict(_last_errors),
    }


def transcribe(
    audio_bytes: bytes,
    filename: str = "voice.ogg",
    content_type: str = "audio/ogg",
) -> str | None:
    if not settings.OPENAI_API_KEY or not audio_bytes:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not configured; cannot transcribe audio")
            _record_error("transcribe", "OPENAI_API_KEY is not configured")
        return None

    url = f"{settings.OPENAI_BASE_URL}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    files = {"file": (filename, audio_bytes, content_type)}
    data = {"model": settings.STT_MODEL}

    try:
        with httpx.Client(timeout=TRANSCRIBE_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers, files=files, data=data)
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("Speech-to-text request failed")
        _record_error("transcribe", f"{type(exc).__name__}: {exc}")
        return None

    if response.status_code >= 400:
        logger.warning(
            "Speech-to-text HTTP %s (model=%s): %s",
            response.status_code,
            settings.STT_MODEL,
            response.text[:400],
        )
        _record_error("transcribe", f"HTTP {response.status_code}: {response.text[:200]}")
        return None

    try:
        text = (response.json().get("text") or "").strip()
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("Speech-to-text response was not JSON")
        _record_error("transcribe", f"{type(exc).__name__}: {exc}")
        return None

    return text or None


def synthesize(text: str) -> bytes | None:
    if not settings.OPENAI_API_KEY or not text.strip():
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not configured; cannot synthesize audio")
            _record_error("synthesize", "OPENAI_API_KEY is not configured")
        return None

    url = f"{settings.OPENAI_BASE_URL}/audio/speech"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.TTS_MODEL,
        "voice": settings.TTS_VOICE,
        "input": text,
        "response_format": "mp3",
    }

    try:
        with httpx.Client(timeout=SPEECH_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers, json=payload)
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("Text-to-speech request failed")
        _record_error("synthesize", f"{type(exc).__name__}: {exc}")
        return None

    if response.status_code >= 400:
        logger.warning(
            "Text-to-speech HTTP %s (model=%s): %s",
            response.status_code,
            settings.TTS_MODEL,
            response.text[:400],
        )
        _record_error("synthesize", f"HTTP {response.status_code}: {response.text[:200]}")
        return None

    return response.content or None
