from fastapi.testclient import TestClient

from app.services import stub_data
from main import app

client = TestClient(app)


def setup_function(_):
    stub_data.reset()


def _ask(text):
    return client.post(
        "/chat/ask",
        json={"phone_number": "+260760333333", "message_text": text},
    ).json()


def test_menu_fees():
    payload = _ask("1")
    assert payload["routing"] == "menu"
    assert payload["bot_message"]["intent_type"] == "fees"
    assert "Fees" in payload["bot_message"]["message_text"]


def test_menu_exam_schedule():
    payload = _ask("2")
    assert payload["routing"] == "menu"
    assert payload["bot_message"]["intent_type"] == "exam_schedule"


def test_menu_registration():
    payload = _ask("3")
    assert payload["routing"] == "menu"
    assert payload["bot_message"]["intent_type"] == "registration"


def test_menu_programmes():
    payload = _ask("4")
    assert payload["routing"] == "menu"
    assert payload["bot_message"]["intent_type"] == "programmes"


def test_menu_help():
    payload = _ask("5")
    assert payload["routing"] == "menu"
    assert payload["bot_message"]["intent_type"] == "help"


def test_menu_non_digit_falls_through_to_rag():
    payload = _ask("12")
    assert payload["routing"] == "rag"
    assert payload["bot_message"]["intent_type"] is None


def test_menu_still_runs_rule_keywords():
    payload = _ask("hello")
    assert payload["routing"] == "rule"
    assert payload["bot_message"]["intent_type"] == "greeting"