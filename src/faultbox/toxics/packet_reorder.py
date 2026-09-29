"""Packet reordering toxic for simulating out-of-order datagram arrival."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class PacketReorderToxic(BaseToxic):
    """
    Simulates network packet reordering by introducing differential delay across datagrams.

    Attributes:
        delay_ms: Base delay in milliseconds applied to out-of-order packets.
        jitter_ms: Random jitter added or subtracted from delay.
        reorder_ratio: Fraction of packets to delay relative to immediate forwarding (0.0 to 1.0).
    """

    def __init__(
        self,
        name: str,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
        delay_ms: float = 50.0,
        jitter_ms: float = 10.0,
        reorder_ratio: float = 0.5,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="packet_reorder",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.delay_ms = max(0.0, float(delay_ms))
        self.jitter_ms = max(0.0, float(jitter_ms))
        self.reorder_ratio = max(0.0, min(1.0, float(reorder_ratio)))

    def get_attributes(self) -> dict[str, Any]:
        return {
            "delay_ms": self.delay_ms,
            "jitter_ms": self.jitter_ms,
            "reorder_ratio": self.reorder_ratio,
        }

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes:
        if random.random() < self.reorder_ratio:
            jitter = random.uniform(-self.jitter_ms, self.jitter_ms) if self.jitter_ms > 0 else 0.0
            actual_delay = max(0.0, self.delay_ms + jitter)
            if actual_delay > 0:
                await asyncio.sleep(actual_delay / 1000.0)
        return chunk
