"""Unit tests for high-performance event loop engine initialization."""

from __future__ import annotations

from faultbox.core.engine import setup_event_loop


def test_setup_event_loop() -> None:
    engine = setup_event_loop()
    assert engine in ("uvloop", "asyncio")
