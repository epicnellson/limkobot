from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_twilio_webhook_returns_twiml():
    response = client.post(
        "/webhook/twilio",
        data={"From": "+260776000000", "Body": "What programmes do you offer?"},
    )
    assert response.status_code == 200
    assert '<Response><Message>' in response.text
    assert "</Response>" in response.text


def test_twilio_webhook_empty_body():
    response = client.post(
        "/webhook/twilio", data={"From": "+260776000000", "Body": ""}
    )
    assert response.status_code == 200
    assert "LimkoBot" in response.text