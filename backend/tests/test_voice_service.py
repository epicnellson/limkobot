from app.config import settings
from app.services import voice_service


def test_transcribe_returns_none_without_providers(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    assert voice_service.transcribe(b"fake-audio") is None


def test_transcribe_prefers_groq_over_openai(monkeypatch):
    calls = []

    def fake_transcribe(provider, *args, **kwargs):
        calls.append(provider)
        return "transcript"

    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(voice_service, "_transcribe_with", fake_transcribe)

    assert voice_service.transcribe(b"fake-audio") == "transcript"
    assert calls == ["groq"]


def test_transcribe_falls_back_to_openai(monkeypatch):
    calls = []

    def fake_transcribe(provider, *args, **kwargs):
        calls.append(provider)
        if provider == "groq":
            return None
        return "openai transcript"

    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(voice_service, "_transcribe_with", fake_transcribe)

    assert voice_service.transcribe(b"fake-audio") == "openai transcript"
    assert calls == ["groq", "openai"]


def test_synthesize_returns_none_without_providers(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", False)

    assert voice_service.synthesize("Hello") is None


def test_synthesize_returns_none_for_blank_text(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", True)

    assert voice_service.synthesize("   ") is None


def test_synthesize_uses_edge_without_openai_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", True)
    monkeypatch.setattr(voice_service, "_synthesize_edge", lambda _text: b"mp3")

    assert voice_service.synthesize("Hello") == b"mp3"


def test_synthesize_falls_back_to_openai(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", True)
    monkeypatch.setattr(voice_service, "_synthesize_edge", lambda _text: None)
    monkeypatch.setattr(voice_service, "_synthesize_openai", lambda _text: b"openai-mp3")

    assert voice_service.synthesize("Hello") == b"openai-mp3"


def test_diagnostics_reports_provider_state(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")

    report = voice_service.diagnostics()

    assert report["openai_key_configured"] is False
    assert report["groq_key_configured"] is True
    assert report["stt_providers"] == ["groq"]
    assert "edge" in report["tts_providers"]
