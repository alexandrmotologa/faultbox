"""Integration tests for the Python Client SDK and context managers."""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Generator

import pytest
import uvicorn

from faultbox.api.server import create_app
from faultbox.client import AsyncFaultBoxClient, FaultBoxClient
from faultbox.core.proxy import ProxyManager


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server() -> Generator[str, None, None]:
    manager = ProxyManager()
    fastapi_app = create_app(manager)
    port = get_free_port()
    config = uvicorn.Config(
        app=fastapi_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    while not server.started:
        time.sleep(0.01)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=2.0)


def test_sync_client_full_workflow(live_server: str) -> None:
    with FaultBoxClient(base_url=live_server) as client:
        # 1. Health
        health = client.health()
        assert health["status"] == "ok"

        # 2. Temporary proxy context manager
        with client.temporary_proxy("sync-p1", "127.0.0.1:19111", "127.0.0.1:80") as p:
            assert p["name"] == "sync-p1"
            assert len(client.list_proxies()) == 1

            # 3. Toxic context manager
            with client.toxic("sync-p1", "latency", latency_ms=200) as t:
                assert t["type"] == "latency"
                toxics = client.list_toxics("sync-p1")
                assert len(toxics) == 1
                assert toxics[0]["name"] == t["name"]

            # Toxic should be cleaned up immediately on exit
            assert len(client.list_toxics("sync-p1")) == 0

            # 4. Paused context manager
            with client.paused("sync-p1"):
                proxy_info = client.get_proxy("sync-p1")
                assert proxy_info["enabled"] is False

            proxy_info = client.get_proxy("sync-p1")
            assert proxy_info["enabled"] is True

        # Temporary proxy should be deleted immediately on exit
        assert len(client.list_proxies()) == 0


@pytest.mark.asyncio
async def test_async_client_full_workflow(live_server: str) -> None:
    async with AsyncFaultBoxClient(base_url=live_server) as client:
        # 1. Health
        health = await client.health()
        assert health["status"] == "ok"

        # 2. Temporary proxy context manager
        async with client.temporary_proxy("async-p1", "127.0.0.1:19222", "127.0.0.1:80") as p:
            assert p["name"] == "async-p1"
            proxies = await client.list_proxies()
            assert len(proxies) == 1

            # 3. Toxic context manager
            async with client.toxic("async-p1", "bandwidth", rate_kbps=50) as t:
                assert t["type"] == "bandwidth"
                toxics = await client.list_toxics("async-p1")
                assert len(toxics) == 1

            # Cleaned up
            assert len(await client.list_toxics("async-p1")) == 0

            # 4. Paused context manager
            async with client.paused("async-p1"):
                proxy_info = await client.get_proxy("async-p1")
                assert proxy_info["enabled"] is False

            proxy_info = await client.get_proxy("async-p1")
            assert proxy_info["enabled"] is True

        # Proxy deleted
        assert len(await client.list_proxies()) == 0
