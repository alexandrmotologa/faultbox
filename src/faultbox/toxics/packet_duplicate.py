"""Packet duplicate toxic for simulating UDP/datagram duplicate delivery."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class PacketDuplicateToxic(BaseToxic):
    """
    Simulates packet duplication where a single transmitted datagram is delivered multiple times.

    Attributes:
        count: Number of duplicate copies to emit (e.g. 1 means 1 original + 1 duplicate = 2 packets).
        delay_ms: Milliseconds delay before duplicate packets are emitted.
    """

    def __init__(
        self,
        name: str,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
        count: int = 1,
        delay_ms: float = 0.0,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="packet_duplicate",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.count = max(1, int(count))
        self.delay_ms = max(0.0, float(delay_ms))

    def get_attributes(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "delay_ms": self.delay_ms,
        }

    async def transform(self, chunk: bytes, context: StreamContext) -> list[bytes] | bytes:
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000.0)
        return [chunk] * (self.count + 1)
