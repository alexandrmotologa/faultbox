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
    ScenarioAssertionResponse,
    ScenarioEventResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
    TopologyExportResponse,
    TopologyImportRequest,
    ToxicCreateRequest,
    ToxicResponse,
)
from faultbox.api.ui import get_ui_html
from faultbox.core.metrics import generate_prometheus_metrics
from faultbox.scenarios.runner import ScenarioRunner
from faultbox.scenarios.schema import ScenarioConfig
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
                protocol=payload.protocol,
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

    @router.post("/scenarios/run", response_model=ScenarioRunResponse)
    async def run_scenario_endpoint(payload: ScenarioRunRequest) -> ScenarioRunResponse:
        """Execute a declarative YAML chaos scenario against active proxies."""
        try:
            scenario = ScenarioConfig.from_yaml_string(payload.yaml_content)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scenario YAML: {exc}",
            ) from exc

        runner = ScenarioRunner(manager=manager, scenario=scenario)
        report = await runner.run()

        return ScenarioRunResponse(
            name=report.name,
            total_phases=report.total_phases,
            executed_phases=report.executed_phases,
            duration_seconds=report.duration_seconds,
            events=[
                ScenarioEventResponse(
                    timestamp=e.timestamp,
                    time_offset=e.time_offset,
                    action=e.action,
                    target_proxy=e.target_proxy,
                    success=e.success,
                    message=e.message,
                )
                for e in report.events
            ],
            assertions=[
                ScenarioAssertionResponse(
                    metric=a.metric,
                    operator=a.operator,
                    threshold=a.threshold,
                    actual_value=a.actual_value,
                    passed=a.passed,
                    target_proxy=a.target_proxy,
                    description=a.description,
                    message=a.message,
                )
                for a in report.assertions
            ],
            assertions_passed=report.assertions_passed,
            success=report.success,
        )

    @router.get("/topology/export", response_model=TopologyExportResponse)
    async def export_topology() -> dict[str, Any]:
        """Export the full cluster configuration and active toxics topology."""
        proxies_data = [p.to_dict() for p in manager.list_proxies()]
        return {"version": "1.0", "proxies": proxies_data}

    @router.post("/topology/import", response_model=MessageResponse)
    async def import_topology(payload: TopologyImportRequest) -> MessageResponse:
        """Restore or apply a cluster topology snapshot."""
        try:
            for item in payload.proxies:
                name = item["name"]
                listen = item["listen"]
                upstream = item["upstream"]
                protocol = item.get("protocol", "tcp")
                enabled = item.get("enabled", True)

                instance = manager.get_proxy(name)
                if not instance:
                    instance = await manager.create_proxy(
                        name=name,
                        listen=listen,
                        upstream=upstream,
                        protocol=protocol,
                    )

                if enabled:
                    await instance.resume()
                else:
                    await instance.pause()

                instance.pipeline.clear()
                for t_dict in item.get("toxics", []):
                    t_type = t_dict.get("type") or t_dict.get("toxic_type", "")
                    toxic = create_toxic(
                        name=t_dict["name"],
                        toxic_type=t_type,
                        direction=t_dict.get("direction", "both"),
                        toxicity=float(t_dict.get("toxicity", 1.0)),
                        attributes=t_dict.get("attributes", {}),
                        enabled=t_dict.get("enabled", True),
                    )
                    instance.pipeline.add_toxic(toxic)

            return MessageResponse(
                status="ok",
                message=f"Successfully imported topology with {len(payload.proxies)} proxies.",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import topology: {exc}",
            ) from exc

    return router
