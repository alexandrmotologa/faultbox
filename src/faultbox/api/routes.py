"""FastAPI routes for the FaultBox Control Plane."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse

from faultbox.api.schemas import (
    MessageResponse,
    ProxyCreateRequest,
    ProxyResponse,
    ToxicCreateRequest,
    ToxicResponse,
)
from faultbox.api.ui import get_ui_html
from faultbox.core.metrics import generate_prometheus_metrics
from faultbox.toxics.factory import create_toxic

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


def create_router(manager: ProxyManager) -> APIRouter:
    """Create configured control plane router bound to a ProxyManager instance."""
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    @router.get("/ui", response_class=HTMLResponse)
    async def dashboard_ui() -> HTMLResponse:
        """Serve embedded single-page Web UI dashboard."""
        return HTMLResponse(get_ui_html())

    @router.websocket("/ws/telemetry")
    async def websocket_telemetry(websocket: WebSocket) -> None:
        """Stream real-time proxy metrics and status to connected browser clients."""
        await websocket.accept()
        try:
            while True:
                payload = [p.to_dict() for p in manager.list_proxies()]
                await websocket.send_json(payload)
                await asyncio.sleep(1.0)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    @router.get("/healthz", response_model=MessageResponse)
    async def healthcheck() -> MessageResponse:
        return MessageResponse(status="ok", message="FaultBox Control Plane operational")

    @router.get("/metrics")
    async def metrics() -> Response:
        """Prometheus text exposition format endpoint."""
        content = generate_prometheus_metrics(manager)
        return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

    @router.get("/proxies", response_model=list[ProxyResponse])
    async def list_proxies() -> list[dict[str, Any]]:
        return [p.to_dict() for p in manager.list_proxies()]

    @router.post("/proxies", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
    async def create_proxy(payload: ProxyCreateRequest) -> dict[str, Any]:
        try:
            instance = await manager.create_proxy(
                name=payload.name,
                listen=payload.listen,
                upstream=payload.upstream,
            )
            return instance.to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.get("/proxies/{name}", response_model=ProxyResponse)
    async def get_proxy(name: str) -> dict[str, Any]:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        return instance.to_dict()

    @router.delete("/proxies/{name}", response_model=MessageResponse)
    async def delete_proxy(name: str) -> MessageResponse:
        deleted = await manager.delete_proxy(name)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        return MessageResponse(status="ok", message=f"Proxy '{name}' deleted.")

    @router.post("/proxies/{name}/pause", response_model=MessageResponse)
    async def pause_proxy(name: str) -> MessageResponse:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        await instance.pause()
        return MessageResponse(status="ok", message=f"Proxy '{name}' paused.")

    @router.post("/proxies/{name}/resume", response_model=MessageResponse)
    async def resume_proxy(name: str) -> MessageResponse:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        await instance.resume()
        return MessageResponse(status="ok", message=f"Proxy '{name}' resumed.")

    @router.post("/proxies/{name}/reset", response_model=MessageResponse)
    async def reset_proxy(name: str) -> MessageResponse:
        reset_ok = manager.reset_proxy(name)
        if not reset_ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        return MessageResponse(status="ok", message=f"All toxics cleared for proxy '{name}'.")

    @router.get("/proxies/{name}/toxics", response_model=list[ToxicResponse])
    async def list_toxics(name: str) -> list[dict[str, Any]]:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )
        return [t.to_dict() for t in instance.pipeline.list_toxics()]

    @router.post(
        "/proxies/{name}/toxics", response_model=ToxicResponse, status_code=status.HTTP_201_CREATED
    )
    async def add_toxic(name: str, payload: ToxicCreateRequest) -> dict[str, Any]:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )

        try:
            toxic = create_toxic(
                name=payload.name,
                toxic_type=payload.type,
                direction=payload.direction,
                toxicity=payload.toxicity,
                attributes=payload.attributes,
                enabled=payload.enabled,
            )
            instance.pipeline.add_toxic(toxic)
            return toxic.to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.delete("/proxies/{name}/toxics/{toxic_name}", response_model=MessageResponse)
    async def remove_toxic(name: str, toxic_name: str) -> MessageResponse:
        instance = manager.get_proxy(name)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy '{name}' not found."
            )

        removed = instance.pipeline.remove_toxic(toxic_name)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Toxic '{toxic_name}' not found on proxy '{name}'.",
            )
        return MessageResponse(status="ok", message=f"Toxic '{toxic_name}' removed.")

    return router
