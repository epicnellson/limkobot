from fastapi.testclient import TestClient

from app.routers import webhook
from main import app

MESSAGE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "102290129340398",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "123456789012345",
                        },
                        "contacts": [
                            {"profile": {"name": "Test User"}, "wa_id": "155501234567"}
                        ],
                        "messages": [
                            {
                                "from": "155501234567",
                                "id": "wamid.HBgLPTAwMTcwMzEwNTUyNVUR",
                                "timestamp": "1700000000",
                                "type": "text",
                                "text": {"body": "What programmes do you offer?"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

STATUS_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "102290129340398",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "statuses": [{"status": "sent", "recipient_id": "155501234567"}],
                    },
                }
            ],
        }
    ],
}


def test_verify_success(monkeypatch):
    monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "test_verify_token")
    with TestClient(app) as client:
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "9876543210",
            },
        )
    assert response.status_code == 200
    assert response.text == "9876543210"


def test_verify_wrong_token(monkeypatch):
    monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "test_verify_token")
    with TestClient(app) as client:
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "not-the-token",
                "hub.challenge": "12345",
            },
        )
    assert response.status_code == 403


def test_verify_missing_token(monkeypatch):
    monkeypatch.delenv("WEBHOOK_VERIFY_TOKEN", raising=False)
    with TestClient(app) as client:
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "",
                "hub.challenge": "12345",
            },
        )
    assert response.status_code == 403


def test_webhook_message(monkeypatch):
    captured = {}

    def fake_process_message(from_number, message_text):
        captured["from"] = from_number
        captured["text"] = message_text

    monkeypatch.setattr(webhook, "process_message", fake_process_message)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=MESSAGE_PAYLOAD)
    assert response.status_code == 200
    assert captured["from"] == "155501234567"
    assert captured["text"] == "What programmes do you offer?"


def test_webhook_status_update_no_messages(monkeypatch):
    def fake_process_message(from_number, message_text):
        raise AssertionError("process_message should not be called")

    monkeypatch.setattr(webhook, "process_message", fake_process_message)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=STATUS_PAYLOAD)
    assert response.status_code == 200


def test_webhook_empty_body(monkeypatch):
    with TestClient(app) as client:
        response = client.post(
            "/webhook/whatsapp", content=b"", headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 200