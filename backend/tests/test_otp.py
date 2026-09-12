from fastapi.testclient import TestClient

from app.routers import auth
from app.services import auth_service, stub_data
from main import app

PHONE = "+260760222222"


def setup_function(_):
    stub_data.reset()


def test_request_otp_sends_whatsapp_and_stores_code(monkeypatch):
    sent = []

    def fake_send_message(to_number, text):
        sent.append((to_number, text))

    monkeypatch.setattr(auth, "send_message", fake_send_message)

    with TestClient(app) as client:
        response = client.post("/auth/otp/request", json={"phone_number": PHONE})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "sent"
    assert payload["expires_in_minutes"] == 5

    assert len(sent) == 1
    assert sent[0][0] == PHONE
    assert "verification code" in sent[0][1]

    otp = stub_data.get_active_otp(PHONE)
    assert otp is not None
    assert otp["code"] in sent[0][1]
    assert otp["used"] is False
    assert stub_data.get_student_by_id(stub_data.get_or_create_student(PHONE)["student_id"])["otp_verified"] is False


def test_verify_otp_success_returns_token(monkeypatch):
    monkeypatch.setattr(auth, "send_message", lambda _to, _text: None)
    with TestClient(app) as client:
        client.post("/auth/otp/request", json={"phone_number": PHONE})
        code = stub_data.get_active_otp(PHONE)["code"]
        response = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": code}
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "verified"
    assert payload["token"]
    assert payload["expires_in"] == 24 * 60 * 60

    student = stub_data.get_or_create_student(PHONE)
    decoded = auth_service.decode_student_access_token(payload["token"])
    assert decoded["student_id"] == student["student_id"]
    assert stub_data.get_student_by_id(student["student_id"])["otp_verified"] is True


def test_verify_otp_wrong_code_401(monkeypatch):
    monkeypatch.setattr(auth, "send_message", lambda _to, _text: None)
    with TestClient(app) as client:
        client.post("/auth/otp/request", json={"phone_number": PHONE})
        response = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": "000000"}
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired verification code"


def test_verify_otp_expired_code_401(monkeypatch):
    monkeypatch.setattr(auth, "send_message", lambda _to, _text: None)
    with TestClient(app) as client:
        client.post("/auth/otp/request", json={"phone_number": PHONE})
        code = stub_data.get_active_otp(PHONE)["code"]
        stub_data.force_expire_otp(PHONE)
        response = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": code}
        )

    assert response.status_code == 401


def test_verify_otp_used_code_401(monkeypatch):
    monkeypatch.setattr(auth, "send_message", lambda _to, _text: None)
    with TestClient(app) as client:
        client.post("/auth/otp/request", json={"phone_number": PHONE})
        code = stub_data.get_active_otp(PHONE)["code"]
        first = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": code}
        )
        second = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": code}
        )

    assert first.status_code == 200
    assert second.status_code == 401


def test_verify_otp_without_request_401():
    with TestClient(app) as client:
        response = client.post(
            "/auth/otp/verify", json={"phone_number": PHONE, "code": "123456"}
        )

    assert response.status_code == 401