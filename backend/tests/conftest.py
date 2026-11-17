import pytest

from app.routers import auth


@pytest.fixture(autouse=True)
def offline_whatsapp(monkeypatch):
    """Keep the test suite off the Graph API."""
    monkeypatch.setattr(auth, "send_message", lambda *args, **kwargs: None)
