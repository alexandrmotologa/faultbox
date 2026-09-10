"""Pytest configuration and asynchronous fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest


@pytest.fixture
async def echo_server() -> AsyncGenerator[tuple[str, int], None]:
    """Spins up a lightweight asyncio TCP echo server for integration testing."""

    async def handle_echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while not reader.at_eof():
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handle_echo, "127.0.0.1", 0)
    sockets = server.sockets
    assert sockets is not None and len(sockets) > 0
    host, port = sockets[0].getsockname()[:2]

    yield (host, port)

    server.close()
    await server.wait_closed()
