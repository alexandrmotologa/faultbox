"""Integration tests for the embedded Web UI and WebSocket telemetry."""

from __future__ import annotations

import httpx
import pytest
from starlette.testclient import TestClient

from faultbox.api.server import create_app
from faultbox.core.proxy import ProxyManager


@pytest.fixture
def proxy_manager() -> ProxyManager:
    return ProxyManager()


@pytest.mark.asyncio
async def test_ui_endpoints_html(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/", "/ui"):
            resp = await client.get(path)
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]
            assert "FaultBox Control Dashboard" in resp.text
            assert "kpi-card" in resp.text


def test_websocket_telemetry(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    client = TestClient(app)

    with client.websocket_connect("/ws/telemetry") as ws:
        data = ws.receive_json()
        assert isinstance(data, list)
