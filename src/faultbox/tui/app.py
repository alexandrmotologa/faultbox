"""Live terminal dashboard runner for FaultBox."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live

from faultbox.tui.widgets import make_dashboard_layout

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


async def run_dashboard(
    manager: ProxyManager,
    refresh_rate_hz: float = 2.0,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Run interactive live terminal dashboard loop until stopped."""
    console = Console()
    event = stop_event or asyncio.Event()

    with Live(
        make_dashboard_layout(manager),
        console=console,
        refresh_per_second=int(refresh_rate_hz),
        screen=True,
    ) as live:
        while not event.is_set():
            live.update(make_dashboard_layout(manager))
            try:
                await asyncio.wait_for(event.wait(), timeout=1.0 / refresh_rate_hz)
            except TimeoutError:
                pass
