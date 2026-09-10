"""FastAPI application factory and background uvicorn runner."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI

from faultbox.api.routes import create_router

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


def create_app(manager: ProxyManager) -> FastAPI:
    """Instantiate and configure the FastAPI application for FaultBox."""
    app = FastAPI(
        title="FaultBox Control Plane",
        description="Programmable network and protocol chaos proxy control API",
        version="0.1.0",
    )
    router = create_router(manager)
    app.include_router(router)
    return app


async def start_api_server(
    manager: ProxyManager,
    host: str = "0.0.0.0",
    port: int = 8474,
) -> tuple[uvicorn.Server, asyncio.Task[None]]:
    """Start uvicorn server in a non-blocking background asyncio task."""
    app = create_app(manager)
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    # Allow uvicorn time to bind to port
    await asyncio.sleep(0.1)
    return server, task
