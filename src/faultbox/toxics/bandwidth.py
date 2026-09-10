"""Bandwidth toxic: limits throughput to a specified rate."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class BandwidthToxic(BaseToxic):
    """Limits stream throughput to a maximum kilobytes-per-second rate."""

    def __init__(
        self,
        name: str,
        rate_kbps: int = 100,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="bandwidth",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.rate_kbps = max(1, rate_kbps)

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        bytes_count = len(chunk)
        if bytes_count == 0:
            return chunk

        bytes_per_second = self.rate_kbps * 1024.0
        delay_seconds = bytes_count / bytes_per_second
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "rate_kbps": self.rate_kbps,
        }
