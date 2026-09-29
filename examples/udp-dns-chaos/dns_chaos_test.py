"""UDP Datagram Chaos Testing with FaultBox.

This script demonstrates testing a connectionless UDP service (like DNS, Syslog, or gaming RPC)
through a FaultBox UDP proxy with packet drop, packet duplication, and reordering.
"""

from __future__ import annotations

import asyncio

from faultbox.client import FaultBoxClient


class _EchoServerProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore[override]
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        # Echo back with timestamp tag
        self.transport.sendto(b"ECHO:" + data, addr)


class _ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.received_packets: list[bytes] = []

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.received_packets.append(data)


async def run_udp_chaos_demo() -> None:
    print("=" * 60)
    print("FaultBox UDP / Datagram Chaos Testing Demo")
    print("=" * 60)

    loop = asyncio.get_running_loop()

    # 1. Start a local UDP echo server (upstream)
    print("\n[1] Starting upstream UDP echo service on 127.0.0.1:19053...")
    upstream_transport, _ = await loop.create_datagram_endpoint(
        _EchoServerProtocol,
        local_addr=("127.0.0.1", 19053),
    )

    # 2. Register UDP proxy in FaultBox
    client = FaultBoxClient(base_url="http://localhost:8474")
    proxy_name = "udp-dns-proxy"
    print(f"\n[2] Registering UDP proxy '{proxy_name}' on 127.0.0.1:18053 -> 127.0.0.1:19053...")
    try:
        await client.create_proxy(
            name=proxy_name,
            listen="127.0.0.1:18053",
            upstream="127.0.0.1:19053",
            protocol="udp",
        )
    except Exception as exc:
        print(f"    Proxy exists: {exc}")

    # 3. Inject Packet Drop Toxic (40% loss)
    print("\n[3] Attaching 40% packet drop toxic...")
    await client.add_toxic(
        proxy_name=proxy_name,
        name="packet-loss",
        toxic_type="packet_drop",
        direction="inbound",
        attributes={"drop_rate": 0.4, "consecutive": 1},
    )

    # 4. Inject Packet Duplicate Toxic
    print("\n[4] Attaching packet duplication toxic (duplicate count: 1)...")
    await client.add_toxic(
        proxy_name=proxy_name,
        name="packet-dup",
        toxic_type="packet_duplicate",
        direction="both",
        attributes={"count": 1, "delay_ms": 10.0},
    )

    # 5. Send test datagrams
    print("\n[5] Sending 10 UDP datagram packets through FaultBox proxy...")
    client_proto = _ClientProtocol()
    client_transport, _ = await loop.create_datagram_endpoint(
        lambda: client_proto,
        remote_addr=("127.0.0.1", 18053),
    )

    for seq in range(1, 11):
        payload = f"seq={seq:02d};timestamp={asyncio.get_event_loop().time():.3f}".encode()
        client_transport.sendto(payload)
        await asyncio.sleep(0.05)

    # Wait for responses
    await asyncio.sleep(0.5)

    print("\n[6] Results summary:")
    print("    Sent:     10 datagrams")
    print(
        f"    Received: {len(client_proto.received_packets)} responses (with drops and duplications)"
    )
    for p in client_proto.received_packets:
        print(f"      -> {p.decode('utf-8', errors='ignore')}")

    # Cleanup
    client_transport.close()
    upstream_transport.close()
    await client.reset_proxy(proxy_name)
    await client.close()
    print("\n[7] Cleaned up and completed.")


if __name__ == "__main__":
    asyncio.run(run_udp_chaos_demo())
