import pytest

from app.services import chat_store, stub_data


@pytest.fixture(autouse=True)
def _reset_stub():
    stub_data.reset()
    yield
    stub_data.reset()


def test_falls_back_to_memory_when_database_missing(monkeypatch):
    monkeypatch.setattr(chat_store, "SessionLocal", None)

    result = chat_store.answer_message("155501234567", "1")

    assert result["persisted"] is False
    assert result["routing"] == "menu"
    assert "Fees" in result["bot_message"]["message_text"]


def test_database_available_reflects_session_maker(monkeypatch):
    monkeypatch.setattr(chat_store, "SessionLocal", object)
    assert chat_store.database_available() is True

    monkeypatch.setattr(chat_store, "SessionLocal", None)
    assert chat_store.database_available() is False


def test_quick_reply_without_database_uses_rules(monkeypatch):
    monkeypatch.setattr(chat_store, "SessionLocal", None)

    reply, intent, routing = chat_store.quick_reply("155501234567", "Hi")

    assert "Limkokwing" in reply
    assert intent == "greeting"
    assert routing == "rule"


def test_record_exchange_without_database_is_noop(monkeypatch):
    monkeypatch.setattr(chat_store, "SessionLocal", None)

    assert chat_store.record_exchange("155501234567", "Hi", "Hello", "greeting", "rule") is False
