"""Integration tests for proxy data forwarding and baseline latency."""

from __future__ import annotations

import asyncio
import time

import pytest

from faultbox.core.proxy import ProxyInstance
from faultbox.toxics.latency import LatencyToxic


@pytest.mark.asyncio
async def test_clean_forwarding_zero_corruption(echo_server: tuple[str, int]) -> None:
    upstream_host, upstream_port = echo_server

    proxy = ProxyInstance(
        name="test_echo",
        listen_host="127.0.0.1",
        listen_port=0,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
    )
    await proxy.start()
    assert proxy._server is not None
    proxy_port = proxy._server.sockets[0].getsockname()[1]

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
        payload = b"Hello FaultBox! Zero byte corruption test."
        writer.write(payload)
        await writer.drain()

        received = await reader.read(len(payload))
        assert received == payload

        writer.close()
        await writer.wait_closed()

        snap = proxy.stats.snapshot()
        assert snap["bytes_in"] == len(payload)
        assert snap["bytes_out"] == len(payload)
        assert snap["connections_total"] >= 1
    finally:
        await proxy.stop()


@pytest.mark.asyncio
async def test_proxy_with_latency_toxic(echo_server: tuple[str, int]) -> None:
    upstream_host, upstream_port = echo_server

    proxy = ProxyInstance(
        name="test_latency",
        listen_host="127.0.0.1",
        listen_port=0,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
    )
    # Inject 100ms latency on inbound traffic
    proxy.pipeline.add_toxic(LatencyToxic(name="lat100", latency_ms=100))
    await proxy.start()
    assert proxy._server is not None
    proxy_port = proxy._server.sockets[0].getsockname()[1]

    try:
        start = time.perf_counter()
        reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
        writer.write(b"ping")
        await writer.drain()

        resp = await reader.read(4)
        elapsed = (time.perf_counter() - start) * 1000.0

        assert resp == b"ping"
        assert elapsed >= 90.0

        writer.close()
        await writer.wait_closed()
    finally:
        await proxy.stop()
