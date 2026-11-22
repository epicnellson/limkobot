from app.config import settings
from app.services import llm_service


def test_answer_returns_none_without_groq_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    assert llm_service.answer("Aw much di fees?") is None


def test_answer_returns_none_for_blank_question(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")

    assert llm_service.answer("   ") is None
