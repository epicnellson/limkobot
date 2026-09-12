from fastapi.testclient import TestClient

from app.dependencies import require_admin
from app.services import stub_data
from main import app

client = TestClient(app)


def _as_admin():
    return type("Admin", (), {"role": "admin"})()


def setup_function(_):
    stub_data.reset()
    app.dependency_overrides[require_admin] = _as_admin


def teardown_function(_):
    app.dependency_overrides.clear()


def test_chat_ask_rule_greeting():
    response = client.post(
        "/chat/ask",
        json={"phone_number": "+260760000001", "message_text": "Hi there"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routing"] == "rule"
    assert payload["bot_message"]["intent_type"] == "greeting"
    assert payload["bot_message"]["sender"] == "bot"
    assert payload["user_message"]["sender"] == "user"
    assert payload["user_message"]["message_text"] == "Hi there"


def test_chat_ask_rag_fallback():
    response = client.post(
        "/chat/ask",
        json={"phone_number": "+260760000002", "message_text": "What is quantum mechanics?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routing"] == "rag"
    assert payload["bot_message"]["message_text"]
    assert payload["bot_message"]["intent_type"] is None


def test_chat_ask_negative_message_flags():
    client.post(
        "/chat/ask",
        json={"phone_number": "+260760000003", "message_text": "This service is terrible"},
    )
    flags = stub_data.list_flags()
    assert len(flags) == 1
    assert flags[0]["severity"] == "high"
    assert "terrible" in flags[0]["message_text"]


def test_document_request_and_status():
    create = client.post(
        "/documents/request",
        json={"phone_number": "+260760000004", "doc_type": "fee_schedule"},
    )
    assert create.status_code == 201
    request_id = create.json()["request_id"]
    assert create.json()["status"] == "pending"
    assert create.json()["doc_type"] == "fee_schedule"

    status_response = client.get(
        "/documents/status", params={"phone_number": "+260760000004"}
    )
    assert status_response.status_code == 200
    requests = status_response.json()
    assert len(requests) == 1
    assert requests[0]["request_id"] == request_id


def test_document_status_empty_for_other_phone():
    response = client.get(
        "/documents/status", params={"phone_number": "+260760000005"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_admin_knowledge_base_upload():
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Fee Schedule 2026", "category": "fees"},
        files={"file": ("fees.pdf", b"%PDF-1.4 fake fee table", "application/pdf")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Fee Schedule 2026"
    assert payload["embedded"] is False


def test_admin_knowledge_base_too_large():
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Big"},
        files={"file": ("big.txt", b"x" * (10 * 1024 * 1024 + 1), "text/plain")},
    )
    assert response.status_code == 413


def test_admin_flags_listing_and_filter():
    client.post(
        "/chat/ask",
        json={"phone_number": "+260760000006", "message_text": "Really bad support"},
    )
    response = client.get("/admin/flags")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["severity"] == "high"

    filtered = client.get("/admin/flags", params={"severity": "low"})
    assert filtered.json() == []