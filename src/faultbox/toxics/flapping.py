"""Flapping toxic: periodically alternates between operational and failing states."""

from __future__ import annotations

import time
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class FlappingToxic(BaseToxic):
    """Periodically fails connections to simulate flapping dependencies and retry storms."""

    def __init__(
        self,
        name: str,
        up_duration_sec: float = 10.0,
        down_duration_sec: float = 5.0,
        down_action: str = "drop",
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="flapping",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.up_duration_sec = max(0.1, float(up_duration_sec))
        self.down_duration_sec = max(0.1, float(down_duration_sec))
        self.down_action = down_action if down_action in ("drop", "reset") else "drop"
        self._start_time = time.time()

    @property
    def is_currently_up(self) -> bool:
        """Evaluate if the flapping cycle is currently in the UP phase."""
        cycle = self.up_duration_sec + self.down_duration_sec
        elapsed = (time.time() - self._start_time) % cycle
        return elapsed < self.up_duration_sec

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if self.is_currently_up:
            return chunk

        if self.down_action == "reset":
            raise ConnectionResetError("Flapping service connection dropped (faultbox chaos)")

        # Default action: drop packet
        return None

    def get_attributes(self) -> dict[str, Any]:
        return {
            "up_duration_sec": self.up_duration_sec,
            "down_duration_sec": self.down_duration_sec,
            "down_action": self.down_action,
            "currently_up": self.is_currently_up,
        }
