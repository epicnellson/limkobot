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
