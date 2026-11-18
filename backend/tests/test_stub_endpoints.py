import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import require_admin
from app.services import stub_data
from main import app

client = TestClient(app)


class _FakeFlagsQuery:
    def __init__(self, rows):
        self._rows = rows

    def outerjoin(self, *_args, **_kwargs):
        return self

    def filter(self, criterion):
        key = getattr(criterion.left, "key", None)
        right = criterion.right
        if hasattr(right, "value"):
            value = right.value
        elif type(right).__name__ in ("True_", "False_"):
            value = type(right).__name__ == "True_"
        else:
            raise AssertionError(f"Unsupported filter: {criterion}")
        self._rows = [
            row for row in self._rows if getattr(row[0], key) == value
        ]
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self._rows


class _FakeFlagsSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, *_models):
        return _FakeFlagsQuery(list(self._rows))


class _FakeUploadSession:
    def __init__(self):
        self.added = []

    def add(self, document):
        self.added.append(document)

    def commit(self):
        pass

    def refresh(self, document):
        now = datetime.now(timezone.utc)
        if document.id is None:
            document.id = uuid.uuid4()
        if document.created_at is None:
            document.created_at = now
        if document.updated_at is None:
            document.updated_at = now


def _use_upload_db():
    session = _FakeUploadSession()
    app.dependency_overrides[get_db] = lambda: session
    return session


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
    db = _use_upload_db()
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Fee Schedule 2026", "category": "fees"},
        files={"file": ("fees.txt", b"Tuition fees for 2026", "text/plain")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Fee Schedule 2026"
    assert payload["category"] == "fees"
    assert payload["embedded"] is False
    assert payload["doc_id"]

    assert len(db.added) == 1
    saved = db.added[0]
    assert saved.source_type == "txt"
    assert saved.content == "Tuition fees for 2026"
    assert saved.category == "fees"
    assert saved.chunked is False


def test_admin_knowledge_base_too_large():
    _use_upload_db()
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Big"},
        files={"file": ("big.txt", b"x" * (10 * 1024 * 1024 + 1), "text/plain")},
    )
    assert response.status_code == 413


def test_admin_knowledge_base_rejects_unsupported_file_type():
    _use_upload_db()
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Binary"},
        files={"file": ("notes.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_admin_knowledge_base_rejects_empty_text():
    _use_upload_db()
    response = client.post(
        "/admin/knowledge-base",
        data={"title": "Blank"},
        files={"file": ("blank.txt", b"   ", "text/plain")},
    )
    assert response.status_code == 422


def test_admin_flags_listing_and_filter():
    flag = SimpleNamespace(
        flag_id=uuid.uuid4(),
        log_id=uuid.uuid4(),
        severity="high",
        reviewed_by=None,
        resolved=False,
    )
    log = SimpleNamespace(
        message_text="Really bad support",
        timestamp=datetime(2026, 11, 17, 12, 0),
    )
    app.dependency_overrides[get_db] = lambda: _FakeFlagsSession([(flag, log)])

    response = client.get("/admin/flags")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["flag_id"] == str(flag.flag_id)
    assert payload[0]["severity"] == "high"
    assert payload[0]["message_text"] == "Really bad support"
    assert payload[0]["timestamp"].startswith("2026-11-17T12:00:00")
    assert payload[0]["resolved"] is False

    filtered = client.get("/admin/flags", params={"severity": "low"})
    assert filtered.json() == []

    open_flags = client.get("/admin/flags", params={"resolved": "false"})
    assert len(open_flags.json()) == 1

    resolved_flags = client.get("/admin/flags", params={"resolved": "true"})
    assert resolved_flags.json() == []
