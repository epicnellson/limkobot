import pytest
from fastapi.testclient import TestClient

from app.routers import webhook
from main import app


@pytest.fixture(autouse=True)
def _clear_dedupe():
    webhook.reset_dedupe()
    yield
    webhook.reset_dedupe()


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

    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789012345")
    monkeypatch.setattr(webhook, "process_message", fake_process_message)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=MESSAGE_PAYLOAD)
    assert response.status_code == 200
    assert captured["from"] == "155501234567"
    assert captured["text"] == "What programmes do you offer?"


def test_webhook_ignores_other_phone_number(monkeypatch):
    def fake_process_message(from_number, message_text):
        raise AssertionError("process_message should not be called")

    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "1347248705147718")
    monkeypatch.setattr(webhook, "process_message", fake_process_message)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=MESSAGE_PAYLOAD)
    assert response.status_code == 200


def test_webhook_ignores_duplicate_delivery(monkeypatch):
    calls = []

    def fake_process_message(from_number, message_text):
        calls.append(message_text)

    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789012345")
    monkeypatch.setattr(webhook, "process_message", fake_process_message)
    with TestClient(app) as client:
        first = client.post("/webhook/whatsapp", json=MESSAGE_PAYLOAD)
        second = client.post("/webhook/whatsapp", json=MESSAGE_PAYLOAD)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(calls) == 1


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


def test_process_message_sends_reply(monkeypatch):
    sent = {}

    def fake_send(to_number, text):
        sent["to"] = to_number
        sent["text"] = text

    monkeypatch.setattr(webhook.whatsapp_service, "send_message", fake_send)
    webhook.process_message("155501234567", "Hi")

    assert sent["to"] == "155501234567"
    assert "Limkokwing" in sent["text"]


def test_process_message_survives_send_failure(monkeypatch):
    def failing_send(to_number, text):
        raise RuntimeError("graph api down")

    monkeypatch.setattr(webhook.whatsapp_service, "send_message", failing_send)
    webhook.process_message("155501234567", "Hi")


def test_process_message_ignores_empty_text(monkeypatch):
    def unexpected_send(to_number, text):
        raise AssertionError("should not send for empty text")

    monkeypatch.setattr(webhook.whatsapp_service, "send_message", unexpected_send)
    webhook.process_message("155501234567", "   ")


AUDIO_PAYLOAD = {
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
                        "messages": [
                            {
                                "from": "155501234567",
                                "id": "wamid.audio.1",
                                "timestamp": "1700000001",
                                "type": "audio",
                                "audio": {
                                    "id": "media-123",
                                    "mime_type": "audio/ogg; codecs=opus",
                                    "voice": True,
                                },
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

IMAGE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "102290129340398",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"phone_number_id": "123456789012345"},
                        "messages": [
                            {
                                "from": "155501234567",
                                "id": "wamid.image.1",
                                "type": "image",
                                "image": {"id": "media-456", "mime_type": "image/jpeg"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}


def test_webhook_audio_message(monkeypatch):
    captured = {}

    def fake_process_audio(from_number, media_id):
        captured["from"] = from_number
        captured["media_id"] = media_id

    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789012345")
    monkeypatch.setattr(webhook, "process_audio_message", fake_process_audio)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    assert captured["from"] == "155501234567"
    assert captured["media_id"] == "media-123"


def test_webhook_unsupported_message_type(monkeypatch):
    captured = {}

    def fake_process_unsupported(from_number, message_type):
        captured["from"] = from_number
        captured["type"] = message_type

    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456789012345")
    monkeypatch.setattr(webhook, "process_unsupported_message", fake_process_unsupported)
    with TestClient(app) as client:
        response = client.post("/webhook/whatsapp", json=IMAGE_PAYLOAD)

    assert response.status_code == 200
    assert captured["type"] == "image"


def test_process_audio_without_transcription_falls_back_to_text(monkeypatch):
    sent = {}

    def fake_send(to_number, text):
        sent["text"] = text

    monkeypatch.setattr(
        webhook.whatsapp_service, "download_media", lambda _id: (b"audio", "audio/ogg")
    )
    monkeypatch.setattr(webhook.voice_service, "transcribe", lambda *a, **k: None)
    monkeypatch.setattr(webhook.whatsapp_service, "send_message", fake_send)

    webhook.process_audio_message("155501234567", "media-123")

    assert "type your question" in sent["text"].lower()


def test_process_audio_replies_with_voice_and_text(monkeypatch):
    sent = {"text": None, "audio": None}
    answered = {}

    def fake_answer(phone_number, message_text, input_type="text"):
        answered["text"] = message_text
        answered["input_type"] = input_type
        return {"reply": "Here are the fees."}

    monkeypatch.setattr(webhook.chat_store, "answer_message", fake_answer)
    monkeypatch.setattr(
        webhook.whatsapp_service, "download_media", lambda _id: (b"audio", "audio/ogg")
    )
    monkeypatch.setattr(webhook.voice_service, "transcribe", lambda *a, **k: "How much are fees?")
    monkeypatch.setattr(webhook.voice_service, "synthesize", lambda _text: b"mp3-bytes")
    monkeypatch.setattr(webhook.whatsapp_service, "upload_media", lambda *a, **k: "out-media-1")

    def fake_send(to_number, text):
        sent["text"] = text

    def fake_send_audio(to_number, media_id):
        sent["audio"] = media_id

    monkeypatch.setattr(webhook.whatsapp_service, "send_message", fake_send)
    monkeypatch.setattr(webhook.whatsapp_service, "send_audio", fake_send_audio)

    webhook.process_audio_message("155501234567", "media-123")

    assert answered["text"] == "How much are fees?"
    assert answered["input_type"] == "audio"
    assert sent["text"] == "Here are the fees."
    assert sent["audio"] == "out-media-1"


def test_process_audio_skips_voice_reply_when_disabled(monkeypatch):
    sent = {"audio": None}

    def fake_answer(phone_number, message_text, input_type="text"):
        return {"reply": "Text only reply."}

    monkeypatch.setattr(webhook.chat_store, "answer_message", fake_answer)
    monkeypatch.setattr(webhook.settings, "VOICE_REPLIES_ENABLED", False)
    monkeypatch.setattr(
        webhook.whatsapp_service, "download_media", lambda _id: (b"audio", "audio/ogg")
    )
    monkeypatch.setattr(webhook.voice_service, "transcribe", lambda *a, **k: "Hi")
    monkeypatch.setattr(webhook.whatsapp_service, "send_message", lambda *a, **k: None)
    monkeypatch.setattr(
        webhook.whatsapp_service,
        "send_audio",
        lambda to_number, media_id: sent.update(audio=media_id),
    )

    webhook.process_audio_message("155501234567", "media-123")

    assert sent["audio"] is None
