"""Asynchronous executor for declarative chaos scenarios."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from faultbox.scenarios.schema import ScenarioConfig, ScenarioPhase
from faultbox.toxics.factory import create_toxic

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


@dataclass
class PhaseEvent:
    """Record of an executed phase action."""

    timestamp: float
    time_offset: float
    action: str
    target_proxy: str
    success: bool
    message: str


@dataclass
class ScenarioReport:
    """Summary of scenario execution."""

    name: str
    total_phases: int
    executed_phases: int
    duration_seconds: float
    events: list[PhaseEvent] = field(default_factory=list)
    success: bool = True


class ScenarioRunner:
    """Executes timed phases from a ScenarioConfig against active proxies."""

    def __init__(
        self,
        manager: ProxyManager,
        scenario: ScenarioConfig,
        on_event: Callable[[PhaseEvent], None] | None = None,
    ) -> None:
        self.manager = manager
        self.scenario = scenario
        self.on_event = on_event

    async def run(self) -> ScenarioReport:
        """Run all phases in chronological order."""
        phases = sorted(self.scenario.phases, key=lambda p: p.time_seconds)
        events: list[PhaseEvent] = []
        start_time = time.perf_counter()
        last_offset = 0.0

        for phase in phases:
            # Sleep delta between current phase and last phase
            delta = max(0.0, phase.time_seconds - last_offset)
            if delta > 0:
                await asyncio.sleep(delta)
            last_offset = phase.time_seconds

            event = await self._execute_phase(phase)
            events.append(event)
            if self.on_event:
                self.on_event(event)

        duration = time.perf_counter() - start_time
        all_success = all(e.success for e in events)

        return ScenarioReport(
            name=self.scenario.name,
            total_phases=len(phases),
            executed_phases=len(events),
            duration_seconds=round(duration, 3),
            events=events,
            success=all_success,
        )

    async def _execute_phase(self, phase: ScenarioPhase) -> PhaseEvent:
        proxy_name = phase.target_proxy or self.scenario.target_proxy or ""
        proxy = self.manager.get_proxy(proxy_name)

        if not proxy:
            return PhaseEvent(
                timestamp=time.time(),
                time_offset=phase.time_seconds,
                action=phase.action,
                target_proxy=proxy_name,
                success=False,
                message=f"Proxy '{proxy_name}' not found.",
            )

        try:
            if phase.action == "add_toxic":
                if not phase.toxic:
                    raise ValueError("action 'add_toxic' requires a 'toxic' definition.")
                toxic = create_toxic(
                    name=phase.toxic.name,
                    toxic_type=phase.toxic.type,
                    direction=phase.toxic.direction,
                    toxicity=phase.toxic.toxicity,
                    attributes=phase.toxic.attributes,
                    enabled=phase.toxic.enabled,
                )
                proxy.pipeline.add_toxic(toxic)
                msg = f"Added toxic '{toxic.name}' ({toxic.toxic_type})"

            elif phase.action == "remove_toxic":
                toxic_name = phase.toxic_name or (phase.toxic.name if phase.toxic else "")
                if not toxic_name:
                    raise ValueError("action 'remove_toxic' requires toxic_name.")
                removed = proxy.pipeline.remove_toxic(toxic_name)
                msg = (
                    f"Removed toxic '{toxic_name}'"
                    if removed
                    else f"Toxic '{toxic_name}' not in pipeline"
                )

            elif phase.action == "reset":
                proxy.pipeline.clear()
                msg = f"Cleared all toxics on proxy '{proxy_name}'"

            elif phase.action == "pause":
                await proxy.pause()
                msg = f"Paused proxy '{proxy_name}'"

            elif phase.action == "resume":
                await proxy.resume()
                msg = f"Resumed proxy '{proxy_name}'"

            else:
                raise ValueError(f"Unknown scenario action '{phase.action}'.")

            return PhaseEvent(
                timestamp=time.time(),
                time_offset=phase.time_seconds,
                action=phase.action,
                target_proxy=proxy_name,
                success=True,
                message=msg,
            )
        except Exception as exc:
            return PhaseEvent(
                timestamp=time.time(),
                time_offset=phase.time_seconds,
                action=phase.action,
                target_proxy=proxy_name,
                success=False,
                message=str(exc),
            )
