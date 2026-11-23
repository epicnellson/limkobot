import json

from app.config import settings
from app.services import llm_service


def test_answer_returns_none_without_groq_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    assert llm_service.answer("Aw much di fees?") is None


def test_answer_returns_none_for_blank_question(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")

    assert llm_service.answer("   ") is None


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.payloads = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, headers=None, json=None):
        self.payloads.append(json)
        return self.responses.pop(0)


def test_answer_falls_back_when_model_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-key")
    monkeypatch.setattr(settings, "GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
    missing = _FakeResponse(
        404,
        {"error": {"message": "model_not_found", "code": "model_not_found"}},
    )
    ok = _FakeResponse(
        200,
        {"choices": [{"message": {"content": " Di fees na USD 100."}}]},
    )
    fake = _FakeClient([missing, ok])
    monkeypatch.setattr(llm_service.httpx, "Client", lambda timeout: fake)

    assert llm_service.answer("Aw much di fees?") == "Di fees na USD 100."
    assert fake.payloads[0]["model"] == "llama-3.3-70b-versatile"
    assert fake.payloads[1]["model"] == "openai/gpt-oss-120b"
