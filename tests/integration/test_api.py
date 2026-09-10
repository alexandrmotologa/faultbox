"""Integration tests for the REST Control Plane API."""

from __future__ import annotations

import httpx
import pytest

from faultbox.api.server import create_app
from faultbox.core.proxy import ProxyManager


@pytest.fixture
def proxy_manager() -> ProxyManager:
    return ProxyManager()


@pytest.mark.asyncio
async def test_api_full_crud_workflow(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Healthcheck
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # 2. Create Proxy
        resp = await client.post(
            "/proxies",
            json={
                "name": "test-redis",
                "listen": "127.0.0.1:16379",
                "upstream": "127.0.0.1:6379",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-redis"
        assert data["enabled"] is True

        # 3. List Proxies
        resp = await client.get("/proxies")
        assert resp.status_code == 200
        proxies = resp.json()
        assert len(proxies) == 1
        assert proxies[0]["name"] == "test-redis"

        # 4. Add Toxic
        resp = await client.post(
            "/proxies/test-redis/toxics",
            json={
                "name": "latency-test",
                "type": "latency",
                "direction": "inbound",
                "toxicity": 1.0,
                "attributes": {"latency_ms": 150, "jitter_ms": 10},
            },
        )
        assert resp.status_code == 201
        toxic_data = resp.json()
        assert toxic_data["name"] == "latency-test"
        assert toxic_data["attributes"]["latency_ms"] == 150

        # 5. List Toxics
        resp = await client.get("/proxies/test-redis/toxics")
        assert resp.status_code == 200
        toxics = resp.json()
        assert len(toxics) == 1
        assert toxics[0]["name"] == "latency-test"

        # 6. Pause and Resume Proxy
        resp = await client.post("/proxies/test-redis/pause")
        assert resp.status_code == 200

        resp = await client.get("/proxies/test-redis")
        assert resp.json()["enabled"] is False

        resp = await client.post("/proxies/test-redis/resume")
        assert resp.status_code == 200

        resp = await client.get("/proxies/test-redis")
        assert resp.json()["enabled"] is True

        # 7. Delete Toxic
        resp = await client.delete("/proxies/test-redis/toxics/latency-test")
        assert resp.status_code == 200

        resp = await client.get("/proxies/test-redis/toxics")
        assert len(resp.json()) == 0

        # 8. Delete Proxy
        resp = await client.delete("/proxies/test-redis")
        assert resp.status_code == 200

        resp = await client.get("/proxies")
        assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_api_error_handling(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Not found proxy
        resp = await client.get("/proxies/non-existent")
        assert resp.status_code == 404

        # Add toxic to non-existent proxy
        resp = await client.post(
            "/proxies/non-existent/toxics",
            json={"name": "x", "type": "latency"},
        )
        assert resp.status_code == 404

        # Create proxy with invalid/duplicate
        await client.post(
            "/proxies",
            json={"name": "p1", "listen": "127.0.0.1:19001", "upstream": "127.0.0.1:80"},
        )
        resp = await client.post(
            "/proxies",
            json={"name": "p1", "listen": "127.0.0.1:19002", "upstream": "127.0.0.1:80"},
        )
        assert resp.status_code == 400
