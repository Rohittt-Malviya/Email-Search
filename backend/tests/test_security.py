import asyncio

from fastapi.testclient import TestClient

from backend.api import routes
from backend.core.config import settings
from backend.main import app
from backend.services.email_intel import EmailIntelligence
from backend.utils.logging import REDACTED, sanitize_headers

client = TestClient(app)


def test_sanitize_headers_redacts_sensitive_values() -> None:
    headers = {"hibp-api-key": "secret", "authorization": "Bearer token", "user-agent": "ua"}
    sanitized = sanitize_headers(headers)
    assert sanitized["hibp-api-key"] == REDACTED
    assert sanitized["authorization"] == REDACTED
    assert sanitized["user-agent"] == "ua"


def test_target_fingerprint_rate_limit_blocks_distributed_user_agents(monkeypatch) -> None:
    monkeypatch.setattr(routes, "TARGET_LIMIT_PER_HOUR", 1)
    monkeypatch.setattr(routes, "CLIENT_LIMIT_PER_MINUTE", 10)
    routes._rate_limit_state.clear()

    payload = {"target": "user@example.com", "target_type": "email", "user_consent": True}
    first = client.post("/api/v1/scan", json=payload, headers={"User-Agent": "agent-1"})
    second = client.post("/api/v1/scan", json=payload, headers={"User-Agent": "agent-2"})

    assert first.status_code == 200
    assert second.status_code == 429


def test_hibp_request_url_encodes_email(monkeypatch) -> None:
    service = EmailIntelligence()
    captured: dict[str, str] = {}

    class DummyResponse:
        status_code = 404

    async def fake_get(url: str, **_: object) -> DummyResponse:
        captured["url"] = url
        return DummyResponse()

    monkeypatch.setattr(settings, "hibp_api_key", "test-key")
    monkeypatch.setattr(service.client, "get", fake_get)

    asyncio.run(service.check_hibp("user+tag@example.com"))
    assert captured["url"].endswith("user%2Btag%40example.com")
    asyncio.run(service.aclose())
