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


@pytest.mark.asyncio
async def test_api_database_toxics_workflow(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create proxy
        resp = await client.post(
            "/proxies",
            json={"name": "pg-proxy", "listen": "127.0.0.1:15432", "upstream": "127.0.0.1:5432"},
        )
        assert resp.status_code == 201

        # Add postgres_fault toxic
        resp = await client.post(
            "/proxies/pg-proxy/toxics",
            json={
                "name": "pg-deadlock",
                "type": "postgres_fault",
                "direction": "outbound",
                "toxicity": 1.0,
                "attributes": {
                    "sqlstate": "40001",
                    "severity": "ERROR",
                    "detail": "synthetic test deadlock",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "pg-deadlock"
        assert data["type"] == "postgres_fault"
        assert data["attributes"]["sqlstate"] == "40001"
        assert data["attributes"]["sqlstate_name"] == "serialization_failure"

        # Add redis_fault toxic
        resp = await client.post(
            "/proxies/pg-proxy/toxics",
            json={
                "name": "redis-ro",
                "type": "redis_fault",
                "direction": "outbound",
                "toxicity": 1.0,
                "attributes": {
                    "error_type": "READONLY",
                    "match_command": "SET",
                },
            },
        )
        assert resp.status_code == 201
        r_data = resp.json()
        assert r_data["name"] == "redis-ro"
        assert r_data["type"] == "redis_fault"
        assert r_data["attributes"]["error_type"] == "READONLY"
        assert r_data["attributes"]["match_command"] == "SET"


@pytest.mark.asyncio
async def test_api_udp_proxy_and_packet_toxics(proxy_manager: ProxyManager) -> None:
    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create UDP Proxy
        resp = await client.post(
            "/proxies",
            json={
                "name": "dns-udp-proxy",
                "listen": "127.0.0.1:15353",
                "upstream": "127.0.0.1:53",
                "protocol": "udp",
            },
        )
        assert resp.status_code == 201
        p_data = resp.json()
        assert p_data["name"] == "dns-udp-proxy"
        assert p_data["protocol"] == "udp"

        # 2. Add packet_drop toxic
        resp = await client.post(
            "/proxies/dns-udp-proxy/toxics",
            json={
                "name": "drop-packet",
                "type": "packet_drop",
                "direction": "inbound",
                "toxicity": 1.0,
                "attributes": {"drop_rate": 0.4, "consecutive": 2},
            },
        )
        assert resp.status_code == 201
        t_data = resp.json()
        assert t_data["type"] == "packet_drop"
        assert t_data["attributes"]["drop_rate"] == 0.4
        assert t_data["attributes"]["consecutive"] == 2

        # 3. Add packet_duplicate toxic
        resp = await client.post(
            "/proxies/dns-udp-proxy/toxics",
            json={
                "name": "dup-packet",
                "type": "packet_duplicate",
                "direction": "both",
                "toxicity": 1.0,
                "attributes": {"count": 2, "delay_ms": 5.0},
            },
        )
        assert resp.status_code == 201
        d_data = resp.json()
        assert d_data["type"] == "packet_duplicate"
        assert d_data["attributes"]["count"] == 2
        assert d_data["attributes"]["delay_ms"] == 5.0

        # 4. Add trace_inject toxic
        resp = await client.post(
            "/proxies/dns-udp-proxy/toxics",
            json={
                "name": "trace-w3c",
                "type": "trace_inject",
                "direction": "inbound",
                "toxicity": 1.0,
                "attributes": {"mode": "w3c", "baggage_extra": "env=test"},
            },
        )
        assert resp.status_code == 201
        tr_data = resp.json()
        assert tr_data["type"] == "trace_inject"
        assert tr_data["attributes"]["mode"] == "w3c"



