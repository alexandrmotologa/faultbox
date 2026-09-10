"""Unit tests for all individual toxics."""

from __future__ import annotations

import time

import pytest

from faultbox.toxics import (
    BandwidthToxic,
    CorruptToxic,
    FlappingToxic,
    HttpErrorToxic,
    LatencyToxic,
    ResetPeerToxic,
    SlicerToxic,
    StreamContext,
    TimeoutToxic,
    ToxicDirection,
    create_toxic,
)


@pytest.fixture
def dummy_context() -> StreamContext:
    return StreamContext(
        proxy_name="test_proxy",
        direction=ToxicDirection.INBOUND,
        client_addr="127.0.0.1:50000",
        upstream_addr="127.0.0.1:80",
    )


@pytest.mark.asyncio
async def test_latency_toxic(dummy_context: StreamContext) -> None:
    toxic = LatencyToxic(name="lat", latency_ms=50, jitter_ms=5)
    start = time.perf_counter()
    result = await toxic.transform(b"hello", dummy_context)
    elapsed = (time.perf_counter() - start) * 1000.0

    assert result == b"hello"
    assert elapsed >= 40.0


@pytest.mark.asyncio
async def test_bandwidth_toxic(dummy_context: StreamContext) -> None:
    # 10 KB/s rate, 1024 bytes payload => ~0.1s delay
    toxic = BandwidthToxic(name="bw", rate_kbps=10)
    data = b"x" * 1024
    start = time.perf_counter()
    result = await toxic.transform(data, dummy_context)
    elapsed = time.perf_counter() - start

    assert result == data
    assert elapsed >= 0.08


@pytest.mark.asyncio
async def test_reset_peer_toxic(dummy_context: StreamContext) -> None:
    toxic = ResetPeerToxic(name="rst", byte_offset=10)
    dummy_context.bytes_streamed = 5
    # Should not reset yet
    res = await toxic.transform(b"abc", dummy_context)
    assert res == b"abc"

    dummy_context.bytes_streamed = 10
    with pytest.raises(ConnectionResetError):
        await toxic.transform(b"abc", dummy_context)


@pytest.mark.asyncio
async def test_timeout_toxic_drop(dummy_context: StreamContext) -> None:
    toxic = TimeoutToxic(name="timeout", timeout_ms=20)
    start = time.perf_counter()
    result = await toxic.transform(b"data", dummy_context)
    elapsed = (time.perf_counter() - start) * 1000.0

    assert result is None
    assert elapsed >= 15.0


@pytest.mark.asyncio
async def test_corrupt_toxic(dummy_context: StreamContext) -> None:
    toxic = CorruptToxic(name="corrupt", rate=0.2, mode="bitflip")
    original = b"This is a pristine test string containing sufficient bytes to corrupt."
    corrupted = await toxic.transform(original, dummy_context)

    assert corrupted is not None
    assert len(corrupted) == len(original)
    assert corrupted != original


@pytest.mark.asyncio
async def test_slicer_toxic(dummy_context: StreamContext) -> None:
    toxic = SlicerToxic(name="slicer", slice_size=4)
    data = b"1234567890"
    slices = await toxic.transform(data, dummy_context)

    assert isinstance(slices, list)
    assert len(slices) == 3
    assert slices[0] == b"1234"
    assert slices[1] == b"5678"
    assert slices[2] == b"90"


@pytest.mark.asyncio
async def test_flapping_toxic(dummy_context: StreamContext) -> None:
    # 1 second UP, 1 second DOWN
    toxic = FlappingToxic(
        name="flap", up_duration_sec=1.0, down_duration_sec=1.0, down_action="drop"
    )
    assert toxic.is_currently_up is True
    res = await toxic.transform(b"msg", dummy_context)
    assert res == b"msg"


@pytest.mark.asyncio
async def test_http_error_toxic() -> None:
    ctx = StreamContext(
        proxy_name="http_proxy",
        direction=ToxicDirection.OUTBOUND,
    )
    toxic = HttpErrorToxic(
        name="http_err",
        status_code=503,
        status_message="Service Unavailable",
        body='{"error": "downstream failure"}',
    )
    original_resp = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
    synthetic = await toxic.transform(original_resp, ctx)

    assert synthetic is not None
    assert b"503 Service Unavailable" in synthetic
    assert b"downstream failure" in synthetic


def test_factory_registry() -> None:
    lat = create_toxic("my_lat", "latency", attributes={"latency_ms": 150})
    assert isinstance(lat, LatencyToxic)
    assert lat.latency_ms == 150

    with pytest.raises(ValueError, match="Unknown toxic type"):
        create_toxic("bad", "non_existent_type")
