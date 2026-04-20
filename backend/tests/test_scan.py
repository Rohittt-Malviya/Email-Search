import pytest
from fastapi.testclient import TestClient

from backend.api.routes import _rate_limit_state
from backend.core.config import settings
from backend.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_rate_limit_state() -> None:
    _rate_limit_state.clear()


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


def test_rejects_invalid_email_format() -> None:
    response = client.post(
        "/api/v1/scan",
        json={"target": "user..name@example.com", "target_type": "email", "user_consent": True},
    )
    assert response.status_code == 422


def test_allows_cors_preflight_for_configured_origin() -> None:
    origin = settings.cors_allowed_origins[0]
    response = client.options(
        "/api/v1/scan",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
