"""Proxy server listener and multi-proxy lifecycle management."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.core.connection import BidirectionalPipe
from faultbox.core.pipeline import ToxicPipeline
from faultbox.core.stats import TrafficStats


def parse_address(addr: str, default_host: str = "0.0.0.0") -> tuple[str, int]:
    """Parse 'host:port' or 'port' string into (host, port) tuple."""
    addr = addr.strip()
    if ":" in addr:
        host, port_str = addr.rsplit(":", 1)
        return host or default_host, int(port_str)
    return default_host, int(addr)


class ProxyInstance:
    """Manages an individual TCP listening socket and forwards to upstream."""

    def __init__(
        self,
        name: str,
        listen_host: str,
        listen_port: int,
        upstream_host: str,
        upstream_port: int,
    ) -> None:
        self.name = name
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port

        self.pipeline = ToxicPipeline()
        self.stats = TrafficStats()
        self.enabled = True

        self._server: asyncio.Server | None = None
        self._active_pipes: set[BidirectionalPipe] = set()
        self._lock = asyncio.Lock()

    @property
    def listen_address(self) -> str:
        return f"{self.listen_host}:{self.listen_port}"

    @property
    def upstream_address(self) -> str:
        return f"{self.upstream_host}:{self.upstream_port}"

    async def start(self) -> None:
        """Start listening for incoming client connections."""
        async with self._lock:
            if self._server is not None:
                return
            self._server = await asyncio.start_server(
                self._handle_client,
                host=self.listen_host,
                port=self.listen_port,
            )

    async def stop(self) -> None:
        """Stop listener and terminate all active connection pipes."""
        async with self._lock:
            if self._server is not None:
                self._server.close()
                await self._server.wait_closed()
                self._server = None

            # Cancel active pipes
            pipes = list(self._active_pipes)
            for pipe in pipes:
                await pipe.close()
            self._active_pipes.clear()

    async def pause(self) -> None:
        """Pause accepting traffic on this proxy."""
        self.enabled = False

    async def resume(self) -> None:
        """Resume accepting traffic on this proxy."""
        self.enabled = True

    async def _handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        """Accept a client connection and bridge it to upstream."""
        if not self.enabled:
            client_writer.close()
            await client_writer.wait_closed()
            return

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host,
                self.upstream_port,
            )
        except Exception:
            self.stats.record_error()
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except Exception:
                pass
            return

        pipe = BidirectionalPipe(
            client_reader=client_reader,
            client_writer=client_writer,
            upstream_reader=upstream_reader,
            upstream_writer=upstream_writer,
            pipeline=self.pipeline,
            stats=self.stats,
            proxy_name=self.name,
        )

        self._active_pipes.add(pipe)
        try:
            await pipe.run()
        finally:
            self._active_pipes.discard(pipe)

    def to_dict(self) -> dict[str, Any]:
        """Return proxy configuration and live runtime state."""
        return {
            "name": self.name,
            "listen": self.listen_address,
            "upstream": self.upstream_address,
            "enabled": self.enabled,
            "stats": self.stats.snapshot(),
            "toxics": [t.to_dict() for t in self.pipeline.list_toxics()],
        }


class ProxyManager:
    """Registry and lifecycle manager for multiple proxy instances."""

    def __init__(self) -> None:
        self._proxies: dict[str, ProxyInstance] = {}
        self._lock = asyncio.Lock()

    async def create_proxy(
        self,
        name: str,
        listen: str,
        upstream: str,
        start_immediately: bool = True,
    ) -> ProxyInstance:
        """Create and register a new proxy instance."""
        async with self._lock:
            if name in self._proxies:
                raise ValueError(f"Proxy with name '{name}' already exists.")

            listen_host, listen_port = parse_address(listen, default_host="0.0.0.0")
            upstream_host, upstream_port = parse_address(upstream, default_host="127.0.0.1")

            instance = ProxyInstance(
                name=name,
                listen_host=listen_host,
                listen_port=listen_port,
                upstream_host=upstream_host,
                upstream_port=upstream_port,
            )

            if start_immediately:
                await instance.start()

            self._proxies[name] = instance
            return instance

    def get_proxy(self, name: str) -> ProxyInstance | None:
        """Find a proxy by name."""
        return self._proxies.get(name)

    def list_proxies(self) -> list[ProxyInstance]:
        """Return list of all registered proxies."""
        return list(self._proxies.values())

    async def delete_proxy(self, name: str) -> bool:
        """Stop and remove a proxy by name."""
        async with self._lock:
            instance = self._proxies.pop(name, None)
            if instance is None:
                return False
            await instance.stop()
            return True

    def reset_proxy(self, name: str) -> bool:
        """Clear all toxics from the named proxy."""
        instance = self.get_proxy(name)
        if instance is None:
            return False
        instance.pipeline.clear()
        return True

    async def stop_all(self) -> None:
        """Stop all running proxies."""
        async with self._lock:
            for instance in self._proxies.values():
                await instance.stop()
            self._proxies.clear()
