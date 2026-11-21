from app.config import settings
from app.services import voice_service


def test_transcribe_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    assert voice_service.transcribe(b"fake-audio") is None


def test_synthesize_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    assert voice_service.synthesize("Hello") is None


def test_synthesize_returns_none_for_blank_text(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    assert voice_service.synthesize("   ") is None
