from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_rejects_without_consent() -> None:
    response = client.post(
        "/api/v1/scan",
        json={"target": "user@example.com", "target_type": "email", "user_consent": False},
    )
    assert response.status_code == 422


def test_rejects_invalid_phone() -> None:
    response = client.post(
        "/api/v1/scan",
        json={"target": "12345", "target_type": "phone", "user_consent": True},
    )
    assert response.status_code == 422


def test_accepts_valid_scan() -> None:
    response = client.post(
        "/api/v1/scan",
        json={"target": "user@example.com", "target_type": "email", "user_consent": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert "scan_id" in body
