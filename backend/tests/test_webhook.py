from starlette.testclient import TestClient

from main import app


def test_twilio_webhook_returns_twiml():
    with TestClient(app) as client:
        response = client.post(
            "/webhook/twilio",
            data={"From": "+260776000000", "Body": "What programmes do you offer?"},
        )
        assert response.status_code == 200
        assert '<Response><Message>' in response.text
        assert "</Response>" in response.text


def test_twilio_webhook_empty_body():
    with TestClient(app) as client:
        response = client.post(
            "/webhook/twilio", data={"From": "+260776000000", "Body": ""}
        )
        assert response.status_code == 200
        assert "LimkoBot" in response.text
