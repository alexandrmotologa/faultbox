"""Pytest plugin providing fixtures for FaultBox testing."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

import pytest

from faultbox.client import AsyncFaultBoxClient, FaultBoxClient


@pytest.fixture
def faultbox_url() -> str:
    """Return configured or default FaultBox control plane base URL."""
    return os.environ.get("FAULTBOX_API_URL", "http://127.0.0.1:8474")


@pytest.fixture
def faultbox_client(faultbox_url: str) -> Generator[FaultBoxClient, None, None]:
    """Provide a synchronous FaultBoxClient fixture."""
    client = FaultBoxClient(base_url=faultbox_url)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
async def async_faultbox_client(faultbox_url: str) -> AsyncGenerator[AsyncFaultBoxClient, None]:
    """Provide an asynchronous AsyncFaultBoxClient fixture."""
    client = AsyncFaultBoxClient(base_url=faultbox_url)
    try:
        yield client
    finally:
        await client.close()
