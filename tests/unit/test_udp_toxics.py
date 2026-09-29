"""Unit tests for UDP packet chaos toxics (packet_drop, packet_duplicate, packet_reorder)."""

from __future__ import annotations

import pytest

from faultbox.toxics.base import StreamContext, ToxicDirection
from faultbox.toxics.factory import create_toxic
from faultbox.toxics.packet_drop import PacketDropToxic
from faultbox.toxics.packet_duplicate import PacketDuplicateToxic
from faultbox.toxics.packet_reorder import PacketReorderToxic


@pytest.fixture
def stream_context() -> StreamContext:
    return StreamContext(
        proxy_name="test-udp-proxy",
        direction=ToxicDirection.INBOUND,
        client_addr="127.0.0.1:53000",
        upstream_addr="127.0.0.1:53",
    )


@pytest.mark.asyncio
async def test_packet_drop_toxic(stream_context: StreamContext) -> None:
    # 100% drop rate
    toxic_drop_all = PacketDropToxic(name="drop-all", drop_rate=1.0)
    result = await toxic_drop_all.transform(b"dns-query", stream_context)
    assert result is None

    # 0% drop rate
    toxic_drop_none = PacketDropToxic(name="drop-none", drop_rate=0.0)
    result2 = await toxic_drop_none.transform(b"dns-query", stream_context)
    assert result2 == b"dns-query"


@pytest.mark.asyncio
async def test_packet_drop_burst(stream_context: StreamContext) -> None:
    toxic = PacketDropToxic(name="burst-drop", drop_rate=1.0, consecutive=3)
    # Consecutive burst should drop 3 packets
    for _ in range(3):
        res = await toxic.transform(b"packet", stream_context)
        assert res is None


@pytest.mark.asyncio
async def test_packet_duplicate_toxic(stream_context: StreamContext) -> None:
    toxic = PacketDuplicateToxic(name="dup-1", count=2, delay_ms=1.0)
    result = await toxic.transform(b"quic-frame", stream_context)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [b"quic-frame", b"quic-frame", b"quic-frame"]
    assert toxic.get_attributes()["count"] == 2


@pytest.mark.asyncio
async def test_packet_reorder_toxic(stream_context: StreamContext) -> None:
    toxic = PacketReorderToxic(name="reorder-1", delay_ms=5.0, jitter_ms=2.0, reorder_ratio=1.0)
    result = await toxic.transform(b"webrtc-audio", stream_context)
    assert result == b"webrtc-audio"
    assert toxic.get_attributes()["delay_ms"] == 5.0
    assert toxic.get_attributes()["reorder_ratio"] == 1.0


def test_factory_creation_packet_toxics() -> None:
    t_drop = create_toxic(
        name="d1",
        toxic_type="packet_drop",
        attributes={"drop_rate": 0.5, "consecutive": 2},
    )
    assert isinstance(t_drop, PacketDropToxic)
    assert t_drop.drop_rate == 0.5
    assert t_drop.consecutive == 2

    t_dup = create_toxic(
        name="d2",
        toxic_type="packet_duplicate",
        attributes={"count": 3, "delay_ms": 10},
    )
    assert isinstance(t_dup, PacketDuplicateToxic)
    assert t_dup.count == 3
    assert t_dup.delay_ms == 10.0

    t_reorder = create_toxic(
        name="d3",
        toxic_type="packet_reorder",
        attributes={"delay_ms": 20, "jitter_ms": 5, "reorder_ratio": 0.8},
    )
    assert isinstance(t_reorder, PacketReorderToxic)
    assert t_reorder.delay_ms == 20.0
    assert t_reorder.reorder_ratio == 0.8
