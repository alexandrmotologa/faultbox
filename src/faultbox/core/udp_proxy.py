"""UDP and Datagram chaos proxy server implementation with connectionless session tracking."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from faultbox.core.pipeline import ToxicPipeline
from faultbox.core.stats import TrafficStats
from faultbox.toxics.base import StreamContext, ToxicDirection


class _UdpListenProtocol(asyncio.DatagramProtocol):
    """Protocol attached to the public listening UDP socket."""

    def __init__(self, proxy: UdpProxyInstance) -> None:
        self.proxy = proxy

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.proxy._transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self.proxy._handle_client_datagram(data, addr))

    def error_received(self, exc: Exception) -> None:
        self.proxy.stats.record_error()

    def connection_lost(self, exc: Exception | None) -> None:
        self.proxy._transport = None


class _UdpUpstreamProtocol(asyncio.DatagramProtocol):
    """Protocol for communicating with upstream target per client session."""

    def __init__(self, proxy: UdpProxyInstance, client_addr: tuple[str, int]) -> None:
        self.proxy = proxy
        self.client_addr = client_addr
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self.proxy._handle_upstream_datagram(data, self.client_addr))

    def error_received(self, exc: Exception) -> None:
        self.proxy.stats.record_error()

    def connection_lost(self, exc: Exception | None) -> None:
        self.transport = None


class UdpSession:
    """Represents a virtual connectionless session for a specific client address."""

    def __init__(
        self,
        client_addr: tuple[str, int],
        upstream_transport: asyncio.DatagramTransport,
        proxy_name: str,
        upstream_addr: str,
    ) -> None:
        self.client_addr = client_addr
        self.upstream_transport = upstream_transport
        self.last_activity = time.time()
        client_str = f"{client_addr[0]}:{client_addr[1]}"
        self.inbound_context = StreamContext(
            proxy_name=proxy_name,
            direction=ToxicDirection.INBOUND,
            client_addr=client_str,
            upstream_addr=upstream_addr,
        )
        self.outbound_context = StreamContext(
            proxy_name=proxy_name,
            direction=ToxicDirection.OUTBOUND,
            client_addr=client_str,
            upstream_addr=upstream_addr,
        )

    def touch(self) -> None:
        self.last_activity = time.time()

    def close(self) -> None:
        try:
            self.upstream_transport.close()
        except Exception:
            pass


class UdpProxyInstance:
    """Manages an individual UDP listening socket and forwards datagrams to upstream."""

    def __init__(
        self,
        name: str,
        listen_host: str,
        listen_port: int,
        upstream_host: str,
        upstream_port: int,
        session_timeout: float = 60.0,
    ) -> None:
        self.name = name
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.session_timeout = session_timeout
        self.protocol = "udp"

        self.pipeline = ToxicPipeline()
        self.stats = TrafficStats()
        self.enabled = True

        self._transport: asyncio.DatagramTransport | None = None
        self._sessions: dict[tuple[str, int], UdpSession] = {}
        self._lock = asyncio.Lock()
        self._reaper_task: asyncio.Task[None] | None = None

    @property
    def listen_address(self) -> str:
        return f"{self.listen_host}:{self.listen_port}"

    @property
    def upstream_address(self) -> str:
        return f"{self.upstream_host}:{self.upstream_port}"

    async def start(self) -> None:
        """Start listening for incoming UDP datagrams."""
        async with self._lock:
            if self._transport is not None:
                return

            loop = asyncio.get_running_loop()
            transport, _ = await loop.create_datagram_endpoint(
                lambda: _UdpListenProtocol(self),
                local_addr=(self.listen_host, self.listen_port),
            )
            self._transport = transport
            self._reaper_task = asyncio.create_task(self._reap_idle_sessions())

    async def stop(self) -> None:
        """Stop UDP listener and clean up all client sessions."""
        async with self._lock:
            if self._reaper_task is not None:
                self._reaper_task.cancel()
                try:
                    await self._reaper_task
                except asyncio.CancelledError:
                    pass
                self._reaper_task = None

            if self._transport is not None:
                self._transport.close()
                self._transport = None

            for session in list(self._sessions.values()):
                session.close()
                await self.pipeline.notify_close(session.inbound_context)
                self.stats.record_connection_close()
            self._sessions.clear()

    async def pause(self) -> None:
        """Pause accepting or routing traffic."""
        self.enabled = False

    async def resume(self) -> None:
        """Resume traffic processing."""
        self.enabled = True

    async def _get_or_create_session(self, client_addr: tuple[str, int]) -> UdpSession | None:
        session = self._sessions.get(client_addr)
        if session is not None:
            session.touch()
            return session

        loop = asyncio.get_running_loop()
        try:
            proto = _UdpUpstreamProtocol(self, client_addr)
            transport, _ = await loop.create_datagram_endpoint(
                lambda: proto,
                remote_addr=(self.upstream_host, self.upstream_port),
            )
            session = UdpSession(
                client_addr=client_addr,
                upstream_transport=transport,
                proxy_name=self.name,
                upstream_addr=self.upstream_address,
            )
            self._sessions[client_addr] = session
            self.stats.record_connection_open()
            await self.pipeline.notify_connect(session.inbound_context)
            return session
        except Exception:
            self.stats.record_error()
            return None

    async def _handle_client_datagram(self, data: bytes, client_addr: tuple[str, int]) -> None:
        if not self.enabled:
            return

        session = await self._get_or_create_session(client_addr)
        if session is None:
            return

        self.stats.record_bytes_in(len(data))
        session.inbound_context.bytes_streamed += len(data)

        try:
            processed = await self.pipeline.process(data, session.inbound_context)
            if processed is None:
                # Packet dropped by toxic
                return
            if isinstance(processed, bytes):
                session.upstream_transport.sendto(processed)
            elif isinstance(processed, list):
                for chunk in processed:
                    session.upstream_transport.sendto(chunk)
        except Exception:
            self.stats.record_error()

    async def _handle_upstream_datagram(
        self, data: bytes, client_addr: tuple[str, int]
    ) -> None:
        if not self.enabled or self._transport is None:
            return

        session = self._sessions.get(client_addr)
        if session is None:
            return

        session.touch()
        self.stats.record_bytes_out(len(data))
        session.outbound_context.bytes_streamed += len(data)

        try:
            processed = await self.pipeline.process(data, session.outbound_context)
            if processed is None:
                # Packet dropped by toxic
                return
            if isinstance(processed, bytes):
                self._transport.sendto(processed, client_addr)
            elif isinstance(processed, list):
                for chunk in processed:
                    self._transport.sendto(chunk, client_addr)
        except Exception:
            self.stats.record_error()

    async def _reap_idle_sessions(self) -> None:
        """Periodically clean up expired client UDP sessions."""
        while True:
            try:
                await asyncio.sleep(10.0)
                now = time.time()
                expired: list[tuple[str, int]] = []
                for addr, session in list(self._sessions.items()):
                    if now - session.last_activity > self.session_timeout:
                        expired.append(addr)

                for addr in expired:
                    session = self._sessions.pop(addr, None)
                    if session:
                        session.close()
                        await self.pipeline.notify_close(session.inbound_context)
                        self.stats.record_connection_close()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def to_dict(self) -> dict[str, Any]:
        """Return proxy configuration and live runtime state."""
        return {
            "name": self.name,
            "protocol": self.protocol,
            "listen": self.listen_address,
            "upstream": self.upstream_address,
            "enabled": self.enabled,
            "stats": self.stats.snapshot(),
            "toxics": [t.to_dict() for t in self.pipeline.list_toxics()],
        }
