"""Synchronous and asynchronous Python client SDK for the FaultBox Control Plane."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import httpx


class FaultBoxClient:
    """Synchronous HTTP client for interacting with the FaultBox Control Plane."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8474",
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
        )

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._client.close()

    def __enter__(self) -> FaultBoxClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        """Check API server health."""
        resp = self._client.get("/healthz")
        resp.raise_for_status()
        return resp.json()

    def list_proxies(self) -> list[dict[str, Any]]:
        """Retrieve list of all active proxies."""
        resp = self._client.get("/proxies")
        resp.raise_for_status()
        return resp.json()

    def create_proxy(self, name: str, listen: str, upstream: str) -> dict[str, Any]:
        """Create and start a new proxy route."""
        resp = self._client.post(
            "/proxies",
            json={"name": name, "listen": listen, "upstream": upstream},
        )
        resp.raise_for_status()
        return resp.json()

    def get_proxy(self, name: str) -> dict[str, Any]:
        """Get proxy state, active toxics, and traffic statistics."""
        resp = self._client.get(f"/proxies/{name}")
        resp.raise_for_status()
        return resp.json()

    def delete_proxy(self, name: str) -> dict[str, Any]:
        """Stop and remove a proxy route."""
        resp = self._client.delete(f"/proxies/{name}")
        resp.raise_for_status()
        return resp.json()

    def pause_proxy(self, name: str) -> dict[str, Any]:
        """Pause a proxy from accepting new connections."""
        resp = self._client.post(f"/proxies/{name}/pause")
        resp.raise_for_status()
        return resp.json()

    def resume_proxy(self, name: str) -> dict[str, Any]:
        """Resume a paused proxy."""
        resp = self._client.post(f"/proxies/{name}/resume")
        resp.raise_for_status()
        return resp.json()

    def reset_proxy(self, name: str) -> dict[str, Any]:
        """Clear all active toxics on a proxy."""
        resp = self._client.post(f"/proxies/{name}/reset")
        resp.raise_for_status()
        return resp.json()

    def list_toxics(self, proxy: str) -> list[dict[str, Any]]:
        """List all toxics currently attached to a proxy."""
        resp = self._client.get(f"/proxies/{proxy}/toxics")
        resp.raise_for_status()
        return resp.json()

    def add_toxic(
        self,
        proxy: str,
        name: str,
        toxic_type: str,
        direction: str = "both",
        toxicity: float = 1.0,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Attach a toxic disruption to a proxy."""
        resp = self._client.post(
            f"/proxies/{proxy}/toxics",
            json={
                "name": name,
                "type": toxic_type,
                "direction": direction,
                "toxicity": toxicity,
                "attributes": attributes or {},
            },
        )
        resp.raise_for_status()
        return resp.json()

    def remove_toxic(self, proxy: str, name: str) -> dict[str, Any]:
        """Remove a toxic disruption from a proxy."""
        resp = self._client.delete(f"/proxies/{proxy}/toxics/{name}")
        resp.raise_for_status()
        return resp.json()

    @contextmanager
    def toxic(
        self,
        proxy: str,
        toxic_type: str,
        name: str | None = None,
        direction: str = "both",
        toxicity: float = 1.0,
        **attributes: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager that applies a toxic on block entry and cleans it up on exit.

        Example:
            with client.toxic("redis-proxy", "latency", latency_ms=300):
                perform_request()
        """
        toxic_name = name or f"{toxic_type}-{uuid.uuid4().hex[:8]}"
        created = self.add_toxic(
            proxy=proxy,
            name=toxic_name,
            toxic_type=toxic_type,
            direction=direction,
            toxicity=toxicity,
            attributes=attributes,
        )
        try:
            yield created
        finally:
            try:
                self.remove_toxic(proxy, toxic_name)
            except Exception:
                pass

    @contextmanager
    def temporary_proxy(
        self,
        name: str,
        listen: str,
        upstream: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager that creates an ephemeral proxy and deletes it on exit."""
        proxy = self.create_proxy(name, listen, upstream)
        try:
            yield proxy
        finally:
            try:
                self.delete_proxy(name)
            except Exception:
                pass

    @contextmanager
    def paused(self, proxy: str) -> Generator[None, None, None]:
        """Context manager that pauses a proxy during the block and resumes it on exit."""
        self.pause_proxy(proxy)
        try:
            yield
        finally:
            try:
                self.resume_proxy(proxy)
            except Exception:
                pass


class AsyncFaultBoxClient:
    """Asynchronous HTTP client for interacting with the FaultBox Control Plane."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8474",
        timeout: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
        )

    async def close(self) -> None:
        """Close the underlying asynchronous HTTP transport."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncFaultBoxClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def health(self) -> dict[str, Any]:
        """Check API server health."""
        resp = await self._client.get("/healthz")
        resp.raise_for_status()
        return resp.json()

    async def list_proxies(self) -> list[dict[str, Any]]:
        """Retrieve list of all active proxies."""
        resp = await self._client.get("/proxies")
        resp.raise_for_status()
        return resp.json()

    async def create_proxy(self, name: str, listen: str, upstream: str) -> dict[str, Any]:
        """Create and start a new proxy route."""
        resp = await self._client.post(
            "/proxies",
            json={"name": name, "listen": listen, "upstream": upstream},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_proxy(self, name: str) -> dict[str, Any]:
        """Get proxy state, active toxics, and traffic statistics."""
        resp = await self._client.get(f"/proxies/{name}")
        resp.raise_for_status()
        return resp.json()

    async def delete_proxy(self, name: str) -> dict[str, Any]:
        """Stop and remove a proxy route."""
        resp = await self._client.delete(f"/proxies/{name}")
        resp.raise_for_status()
        return resp.json()

    async def pause_proxy(self, name: str) -> dict[str, Any]:
        """Pause a proxy from accepting new connections."""
        resp = await self._client.post(f"/proxies/{name}/pause")
        resp.raise_for_status()
        return resp.json()

    async def resume_proxy(self, name: str) -> dict[str, Any]:
        """Resume a paused proxy."""
        resp = await self._client.post(f"/proxies/{name}/resume")
        resp.raise_for_status()
        return resp.json()

    async def reset_proxy(self, name: str) -> dict[str, Any]:
        """Clear all active toxics on a proxy."""
        resp = await self._client.post(f"/proxies/{name}/reset")
        resp.raise_for_status()
        return resp.json()

    async def list_toxics(self, proxy: str) -> list[dict[str, Any]]:
        """List all toxics currently attached to a proxy."""
        resp = await self._client.get(f"/proxies/{proxy}/toxics")
        resp.raise_for_status()
        return resp.json()

    async def add_toxic(
        self,
        proxy: str,
        name: str,
        toxic_type: str,
        direction: str = "both",
        toxicity: float = 1.0,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Attach a toxic disruption to a proxy."""
        resp = await self._client.post(
            f"/proxies/{proxy}/toxics",
            json={
                "name": name,
                "type": toxic_type,
                "direction": direction,
                "toxicity": toxicity,
                "attributes": attributes or {},
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def remove_toxic(self, proxy: str, name: str) -> dict[str, Any]:
        """Remove a toxic disruption from a proxy."""
        resp = await self._client.delete(f"/proxies/{proxy}/toxics/{name}")
        resp.raise_for_status()
        return resp.json()

    @asynccontextmanager
    async def toxic(
        self,
        proxy: str,
        toxic_type: str,
        name: str | None = None,
        direction: str = "both",
        toxicity: float = 1.0,
        **attributes: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronous context manager applying a toxic on entry and clearing it on exit."""
        toxic_name = name or f"{toxic_type}-{uuid.uuid4().hex[:8]}"
        created = await self.add_toxic(
            proxy=proxy,
            name=toxic_name,
            toxic_type=toxic_type,
            direction=direction,
            toxicity=toxicity,
            attributes=attributes,
        )
        try:
            yield created
        finally:
            try:
                await self.remove_toxic(proxy, toxic_name)
            except Exception:
                pass

    @asynccontextmanager
    async def temporary_proxy(
        self,
        name: str,
        listen: str,
        upstream: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronous context manager creating an ephemeral proxy and removing it on exit."""
        proxy = await self.create_proxy(name, listen, upstream)
        try:
            yield proxy
        finally:
            try:
                await self.delete_proxy(name)
            except Exception:
                pass

    @asynccontextmanager
    async def paused(self, proxy: str) -> AsyncGenerator[None, None]:
        """Asynchronous context manager pausing a proxy on entry and resuming on exit."""
        await self.pause_proxy(proxy)
        try:
            yield
        finally:
            try:
                await self.resume_proxy(proxy)
            except Exception:
                pass
