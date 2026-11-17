from fastapi.testclient import TestClient

from app.dependencies import require_admin
from app.services import stub_data
from main import app

client = TestClient(app)


def _as_admin():
    return type("Admin", (), {"role": "admin"})()


def _student_headers(phone_number: str) -> dict:
    client.post("/auth/otp/request", json={"phone_number": phone_number})
    code = stub_data.get_active_otp(phone_number)["code"]
    verified = client.post(
        "/auth/otp/verify", json={"phone_number": phone_number, "code": code}
    )
    return {"Authorization": f"Bearer {verified.json()['token']}"}


def setup_function(_):
    stub_data.reset()
    app.dependency_overrides[require_admin] = _as_admin


def teardown_function(_):
    app.dependency_overrides.clear()


def test_chat_ask_rule_greeting():
    phone = "+260760000001"
    response = client.post(
        "/chat/ask",
        json={"phone_number": phone, "message_text": "Hi there"},
        headers=_student_headers(phone),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routing"] == "rule"
    assert payload["bot_message"]["intent_type"] == "greeting"
    assert payload["bot_message"]["sender"] == "bot"
    assert payload["user_message"]["sender"] == "user"
    assert payload["user_message"]["message_text"] == "Hi there"


def test_chat_ask_rag_fallback():
    phone = "+260760000002"
    response = client.post(
        "/chat/ask",
        json={"phone_number": phone, "message_text": "What is quantum mechanics?"},
        headers=_student_headers(phone),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routing"] == "rag"
    assert payload["bot_message"]["message_text"]
    assert payload["bot_message"]["intent_type"] is None


def test_chat_ask_negative_message_flags():
    phone = "+260760000003"
    client.post(
        "/chat/ask",
        json={"phone_number": phone, "message_text": "This service is terrible"},
        headers=_student_headers(phone),
    )
    flags = stub_data.list_flags()
    assert len(flags) == 1
    assert flags[0]["severity"] == "high"
    assert "terrible" in flags[0]["message_text"]


def test_chat_ask_requires_student_token():
    response = client.post(
        "/chat/ask",
        json={"phone_number": "+260760000010", "message_text": "Hi"},
    )
    assert response.status_code == 401


def test_chat_ask_rejects_another_students_number():
    headers = _student_headers("+260760000011")
    response = client.post(
        "/chat/ask",
        json={"phone_number": "+260760000012", "message_text": "Hi"},
        headers=headers,
    )
    assert response.status_code == 403


def test_document_request_and_status():
    phone = "+260760000004"
    headers = _student_headers(phone)

    create = client.post(
        "/documents/request",
        json={"phone_number": phone, "doc_type": "fee_schedule"},
        headers=headers,
    )
    assert create.status_code == 201
    request_id = create.json()["request_id"]
    assert create.json()["status"] == "pending"
    assert create.json()["doc_type"] == "fee_schedule"

    status_response = client.get(
        "/documents/status", params={"phone_number": phone}, headers=headers
    )
    assert status_response.status_code == 200
    requests = status_response.json()
    assert len(requests) == 1
    assert requests[0]["request_id"] == request_id


def test_document_status_empty_for_other_phone():
    phone = "+260760000005"
    response = client.get(
        "/documents/status", params={"phone_number": phone}, headers=_student_headers(phone)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_document_request_requires_token():
    response = client.post(
        "/documents/request",
        json={"phone_number": "+260760000013", "doc_type": "prospectus"},
    )
    assert response.status_code == 401


def test_document_request_rejects_another_students_number():
    headers = _student_headers("+260760000014")
    response = client.post(
        "/documents/request",
        json={"phone_number": "+260760000015", "doc_type": "prospectus"},
        headers=headers,
    )
    assert response.status_code == 403


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
    phone = "+260760000006"
    client.post(
        "/chat/ask",
        json={"phone_number": phone, "message_text": "Really bad support"},
        headers=_student_headers(phone),
    )
    response = client.get("/admin/flags")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["severity"] == "high"

    filtered = client.get("/admin/flags", params={"severity": "low"})
    assert filtered.json() == []
