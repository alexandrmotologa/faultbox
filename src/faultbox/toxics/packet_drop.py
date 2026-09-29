"""Packet drop toxic for simulating UDP/datagram packet loss and burst loss."""

from __future__ import annotations

import random
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class PacketDropToxic(BaseToxic):
    """
    Simulates packet loss on datagram streams and TCP frames.

    Attributes:
        drop_rate: Probability of dropping an individual packet (0.0 to 1.0).
        consecutive: Number of consecutive packets to drop when a drop event triggers (burst loss).
    """

    def __init__(
        self,
        name: str,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
        drop_rate: float = 0.2,
        consecutive: int = 1,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="packet_drop",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.drop_rate = max(0.0, min(1.0, float(drop_rate)))
        self.consecutive = max(1, int(consecutive))
        self._remaining_burst: int = 0

    def get_attributes(self) -> dict[str, Any]:
        return {
            "drop_rate": self.drop_rate,
            "consecutive": self.consecutive,
        }

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if self._remaining_burst > 0:
            self._remaining_burst -= 1
            return None

        if random.random() < self.drop_rate:
            if self.consecutive > 1:
                self._remaining_burst = self.consecutive - 1
            return None

        return chunk
