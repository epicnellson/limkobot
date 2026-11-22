"""Speech-to-text and text-to-speech with zero-cost fallbacks.

Transcription uses Groq's free Whisper endpoint when ``GROQ_API_KEY`` is set,
then OpenAI as a secondary provider. Speech synthesis prefers the free Edge TTS
service (no API key) and falls back to OpenAI TTS.

Every helper degrades to None when no provider is usable or a request fails, so
the WhatsApp flow can still answer with text.
"""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TRANSCRIBE_TIMEOUT_SECONDS = 60
SPEECH_TIMEOUT_SECONDS = 60
MAX_TTS_CHARS = 700

_last_errors: dict[str, str] = {}


def _record_error(kind: str, message: str) -> None:
    _last_errors[kind] = message[:400]


def _stt_providers() -> list[str]:
    providers = []
    if settings.GROQ_API_KEY:
        providers.append("groq")
    if settings.OPENAI_API_KEY:
        providers.append("openai")
    return providers


def _tts_providers() -> list[str]:
    providers = []
    if settings.EDGE_TTS_ENABLED:
        providers.append("edge")
    if settings.OPENAI_API_KEY:
        providers.append("openai")
    return providers


def diagnostics() -> dict:
    return {
        "openai_key_configured": bool(settings.OPENAI_API_KEY),
        "groq_key_configured": bool(settings.GROQ_API_KEY),
        "stt_providers": _stt_providers(),
        "tts_providers": _tts_providers(),
        "stt_model": settings.STT_MODEL,
        "groq_stt_model": settings.GROQ_STT_MODEL,
        "tts_model": settings.TTS_MODEL,
        "tts_voice": settings.TTS_VOICE,
        "edge_tts_voice": settings.EDGE_TTS_VOICE,
        "voice_replies_enabled": settings.VOICE_REPLIES_ENABLED,
        "last_errors": dict(_last_errors),
    }


def _transcribe_with(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    audio_bytes: bytes,
    filename: str,
    content_type: str,
) -> str | None:
    url = f"{base_url}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (filename, audio_bytes, content_type)}
    data = {"model": model}

    try:
        with httpx.Client(timeout=TRANSCRIBE_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers, files=files, data=data)
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("%s transcription request failed", provider)
        _record_error(f"transcribe:{provider}", f"{type(exc).__name__}: {exc}")
        return None

    if response.status_code >= 400:
        logger.warning(
            "%s transcription HTTP %s (model=%s): %s",
            provider,
            response.status_code,
            model,
            response.text[:400],
        )
        _record_error(
            f"transcribe:{provider}",
            f"HTTP {response.status_code}: {response.text[:200]}",
        )
        return None

    try:
        return (response.json().get("text") or "").strip() or None
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("%s transcription response was not JSON", provider)
        _record_error(f"transcribe:{provider}", f"{type(exc).__name__}: {exc}")
        return None


def transcribe(
    audio_bytes: bytes,
    filename: str = "voice.ogg",
    content_type: str = "audio/ogg",
) -> str | None:
    if not audio_bytes:
        return None

    for provider in _stt_providers():
        if provider == "groq":
            text = _transcribe_with(
                "groq",
                settings.GROQ_BASE_URL,
                settings.GROQ_API_KEY,
                settings.GROQ_STT_MODEL,
                audio_bytes,
                filename,
                content_type,
            )
        else:
            text = _transcribe_with(
                "openai",
                settings.OPENAI_BASE_URL,
                settings.OPENAI_API_KEY,
                settings.STT_MODEL,
                audio_bytes,
                filename,
                content_type,
            )
        if text:
            return text

    if not _stt_providers():
        _record_error("transcribe", "No STT provider configured (set GROQ_API_KEY)")
    return None


def _synthesize_edge(text: str) -> bytes | None:
    try:
        import edge_tts
    except ImportError:
        _record_error("synthesize:edge", "edge-tts is not installed")
        return None

    async def _collect() -> bytes:
        communicate = edge_tts.Communicate(text, settings.EDGE_TTS_VOICE)
        buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                buffer.extend(chunk["data"])
        return bytes(buffer)

    try:
        audio = asyncio.run(_collect())
    except Exception as exc:  # noqa: BLE001 - voice is best-effort
        logger.exception("Edge TTS failed")
        _record_error("synthesize:edge", f"{type(exc).__name__}: {exc}")
        return None

    return audio or None


def _synthesize_openai(text: str) -> bytes | None:
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
        logger.exception("OpenAI text-to-speech request failed")
        _record_error("synthesize:openai", f"{type(exc).__name__}: {exc}")
        return None

    if response.status_code >= 400:
        logger.warning(
            "OpenAI text-to-speech HTTP %s (model=%s): %s",
            response.status_code,
            settings.TTS_MODEL,
            response.text[:400],
        )
        _record_error(
            "synthesize:openai",
            f"HTTP {response.status_code}: {response.text[:200]}",
        )
        return None

    return response.content or None


def synthesize(text: str) -> bytes | None:
    text = (text or "").strip()
    if not text:
        return None

    text = text[:MAX_TTS_CHARS]

    for provider in _tts_providers():
        if provider == "edge":
            audio = _synthesize_edge(text)
        else:
            audio = _synthesize_openai(text)
        if audio:
            return audio

    if not _tts_providers():
        _record_error("synthesize", "No TTS provider configured")
    return None
