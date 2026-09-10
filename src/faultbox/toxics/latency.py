"""Latency toxic: injects constant or jittered delays."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class LatencyToxic(BaseToxic):
    """Adds artificial latency with optional variance to stream data."""

    def __init__(
        self,
        name: str,
        latency_ms: int = 200,
        jitter_ms: int = 0,
        distribution: str = "uniform",
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="latency",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.latency_ms = max(0, latency_ms)
        self.jitter_ms = max(0, jitter_ms)
        self.distribution = distribution if distribution in ("uniform", "normal") else "uniform"

    def _calculate_delay_seconds(self) -> float:
        if self.jitter_ms == 0:
            delay_ms = float(self.latency_ms)
        elif self.distribution == "normal":
            delay_ms = random.gauss(self.latency_ms, self.jitter_ms / 2.0)
        else:
            delay_ms = self.latency_ms + random.uniform(-self.jitter_ms, self.jitter_ms)

        delay_ms = max(0.0, delay_ms)
        return delay_ms / 1000.0

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        delay = self._calculate_delay_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "distribution": self.distribution,
        }
