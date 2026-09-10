"""Integration tests for the Prometheus metrics endpoint."""

from __future__ import annotations

import httpx
import pytest

from faultbox.api.server import create_app
from faultbox.core.proxy import ProxyManager
from faultbox.toxics.latency import LatencyToxic


@pytest.fixture
def proxy_manager() -> ProxyManager:
    return ProxyManager()


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(proxy_manager: ProxyManager) -> None:
    # Set up proxy with traffic and toxics
    proxy = await proxy_manager.create_proxy(
        "test-metric-proxy", "127.0.0.1:19555", "127.0.0.1:80", start_immediately=False
    )
    proxy.stats.record_bytes_in(4096)
    proxy.stats.record_bytes_out(8192)
    proxy.stats.record_connection_open()
    proxy.pipeline.add_toxic(LatencyToxic(name="prom_lat", latency_ms=100))

    app = create_app(proxy_manager)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]

        body = resp.text
        assert "# HELP faultbox_bytes_total" in body
        assert "# TYPE faultbox_bytes_total counter" in body
        assert 'faultbox_bytes_total{proxy="test-metric-proxy",direction="inbound"} 4096' in body
        assert 'faultbox_bytes_total{proxy="test-metric-proxy",direction="outbound"} 8192' in body
        assert 'faultbox_connections_active{proxy="test-metric-proxy"} 1' in body
        assert 'faultbox_toxics_configured{proxy="test-metric-proxy"} 1' in body
        assert 'faultbox_proxy_enabled{proxy="test-metric-proxy"} 1' in body
