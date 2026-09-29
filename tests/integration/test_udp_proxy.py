"""Integration tests for UDP and Datagram chaos proxy forwarding and session management."""

from __future__ import annotations

import asyncio
import socket

import pytest

from faultbox.core.proxy import ProxyManager
from faultbox.core.udp_proxy import UdpProxyInstance
from faultbox.toxics.packet_drop import PacketDropToxic
from faultbox.toxics.packet_duplicate import PacketDuplicateToxic


class _EchoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.received_packets: list[bytes] = []
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.received_packets.append(data)
        if self.transport is not None:
            # Echo back with prefix
            self.transport.sendto(b"echo:" + data, addr)


class _ClientUdpProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.queue.put_nowait(data)


def _get_free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.asyncio
async def test_udp_proxy_forwarding_lifecycle() -> None:
    loop = asyncio.get_running_loop()

    # 1. Start Echo Upstream UDP Server
    upstream_port = _get_free_udp_port()
    echo_proto = _EchoServerProtocol()
    upstream_transport, _ = await loop.create_datagram_endpoint(
        lambda: echo_proto,
        local_addr=("127.0.0.1", upstream_port),
    )

    # 2. Start UdpProxyInstance via ProxyManager
    proxy_port = _get_free_udp_port()
    manager = ProxyManager()
    proxy = await manager.create_proxy(
        name="dns-chaos",
        listen=f"127.0.0.1:{proxy_port}",
        upstream=f"127.0.0.1:{upstream_port}",
        protocol="udp",
    )
    assert isinstance(proxy, UdpProxyInstance)
    assert proxy.protocol == "udp"
    assert proxy.to_dict()["protocol"] == "udp"

    # 3. Create Async UDP Client
    client_proto = _ClientUdpProtocol()
    client_transport, _ = await loop.create_datagram_endpoint(
        lambda: client_proto,
        local_addr=("127.0.0.1", 0),
    )

    try:
        # 4. Client sends UDP datagram
        client_transport.sendto(b"query_example.com", ("127.0.0.1", proxy_port))
        data = await asyncio.wait_for(client_proto.queue.get(), timeout=2.0)
        assert data == b"echo:query_example.com"
        assert len(echo_proto.received_packets) == 1

        # 5. Attach PacketDropToxic (100% drop)
        drop_toxic = PacketDropToxic(name="drop-all", drop_rate=1.0)
        proxy.pipeline.add_toxic(drop_toxic)

        client_transport.sendto(b"query2_dropped.com", ("127.0.0.1", proxy_port))
        # Verify no response received within short timeout
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(client_proto.queue.get(), timeout=0.3)
        assert len(echo_proto.received_packets) == 1  # Not delivered

        # 6. Remove toxic and attach PacketDuplicateToxic
        proxy.pipeline.remove_toxic("drop-all")
        dup_toxic = PacketDuplicateToxic(name="dup-2", count=2)
        proxy.pipeline.add_toxic(dup_toxic)

        client_transport.sendto(b"query3_dup.com", ("127.0.0.1", proxy_port))
        data3 = await asyncio.wait_for(client_proto.queue.get(), timeout=2.0)
        assert data3.startswith(b"echo:query3_dup.com")

        # Allow time for duplicates to arrive at echo server
        await asyncio.sleep(0.1)
        # 1 original + 1 from query3 + 2 duplicates = 4 total packets received by upstream
        assert len(echo_proto.received_packets) == 4

        # 7. Verify Proxy Stats
        snap = proxy.stats.snapshot()
        assert snap["bytes_in"] > 0
        assert snap["bytes_out"] > 0
        assert snap["connections_total"] >= 1

        # 8. Test pause and resume
        await proxy.pause()
        assert proxy.enabled is False
        await proxy.resume()
        assert proxy.enabled is True

    finally:
        client_transport.close()
        await manager.stop_all()
        upstream_transport.close()
