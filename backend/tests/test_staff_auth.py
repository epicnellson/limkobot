import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.services import auth_service, stub_data
from main import app

client = TestClient(app)

PASSWORD = "secret123"


def _user(**overrides):
    values = {
        "id": uuid.uuid4(),
        "phone": "+23225000000",
        "full_name": "LimkoBot Administrator",
        "student_id": None,
        "email": "admin@limkobot.test",
        "role": "admin",
        "is_verified": True,
        "hashed_password": auth_service.hash_password(PASSWORD),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _FakeQuery:
    def __init__(self, user):
        self._user = user

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._user


class _FakeSession:
    def __init__(self, user):
        self._user = user

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def query(self, _model):
        return _FakeQuery(self._user)

    def get(self, _model, _key):
        return self._user


def _use_db(user):
    app.dependency_overrides[get_db] = lambda: _FakeSession(user)


def _student_headers(phone_number: str) -> dict:
    client.post("/auth/otp/request", json={"phone_number": phone_number})
    code = stub_data.get_active_otp(phone_number)["code"]
    verified = client.post(
        "/auth/otp/verify", json={"phone_number": phone_number, "code": code}
    )
    return {"Authorization": f"Bearer {verified.json()['token']}"}


def setup_function(_):
    stub_data.reset()


def teardown_function(_):
    app.dependency_overrides.clear()


def test_password_hashing_round_trip():
    hashed = auth_service.hash_password(PASSWORD)
    assert hashed != PASSWORD
    assert auth_service.verify_password(PASSWORD, hashed) is True
    assert auth_service.verify_password("wrong-password", hashed) is False
    assert auth_service.verify_password(PASSWORD, None) is False


def test_password_longer_than_72_bytes_does_not_raise():
    long_password = "x" * 200
    hashed = auth_service.hash_password(long_password)
    assert auth_service.verify_password(long_password, hashed) is True


def test_staff_login_returns_admin_token():
    user = _user()
    _use_db(user)

    response = client.post(
        "/auth/staff/login",
        json={"email": "Admin@LimkoBot.test", "password": PASSWORD},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert payload["user"]["role"] == "admin"

    claims = auth_service.decode_access_token(payload["token"])
    assert claims["sub"] == str(user.id)
    assert claims["role"] == "admin"


def test_staff_login_wrong_password_401():
    _use_db(_user())
    response = client.post(
        "/auth/staff/login",
        json={"email": "admin@limkobot.test", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_staff_login_unknown_email_401():
    _use_db(None)
    response = client.post(
        "/auth/staff/login",
        json={"email": "nobody@limkobot.test", "password": PASSWORD},
    )
    assert response.status_code == 401


def test_auth_me_accepts_staff_token(monkeypatch):
    user = _user()
    _use_db(user)
    monkeypatch.setattr("app.dependencies.SessionLocal", lambda: _FakeSession(user))
    login = client.post(
        "/auth/staff/login", json={"email": user.email, "password": PASSWORD}
    )
    token = login.json()["token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user.id)
    assert payload["role"] == "admin"


def test_auth_me_accepts_student_token():
    phone = "+260760333333"
    response = client.get("/auth/me", headers=_student_headers(phone))

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "student"
    assert payload["phone"] == phone
    assert payload["is_verified"] is True


def test_auth_me_requires_token():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_documents_list_requires_authentication():
    _use_db(_user())
    response = client.get("/documents")
    assert response.status_code == 401


def test_documents_list_rejects_non_admin_token():
    user = _user(role="student", email="student@limkobot.test")
    _use_db(user)
    login = client.post(
        "/auth/staff/login", json={"email": user.email, "password": PASSWORD}
    )
    token = login.json()["token"]

    response = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
