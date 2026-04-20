import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.core.config import settings
from backend.main import app

client = TestClient(app)
IDLE_TIMEOUT_TEST_SLEEP_SECONDS = 0.35


def test_websocket_rejects_oversized_messages(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ws_max_message_size_bytes", 8)
    with client.websocket_connect("/ws/test-scan") as websocket:
        websocket.send_text("x" * 32)
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
    assert exc.value.code == 1009


def test_websocket_idle_timeout(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ws_idle_timeout_seconds", 0.1)
    with client.websocket_connect("/ws/test-timeout") as websocket:
        # Sleep comfortably past timeout to deterministically trigger server-side idle disconnect.
        time.sleep(IDLE_TIMEOUT_TEST_SLEEP_SECONDS)
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
    assert exc.value.code == 1000
