"""Timeout toxic: halts data transmission or drops packets after a delay."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class TimeoutToxic(BaseToxic):
    """Freezes data transmission indefinitely or drops packets after a timeout period."""

    def __init__(
        self,
        name: str,
        timeout_ms: int = 0,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="timeout",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.timeout_ms = max(0, timeout_ms)

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if self.timeout_ms == 0:
            # Hang indefinitely until client or server times out
            await asyncio.Event().wait()
            return None

        await asyncio.sleep(self.timeout_ms / 1000.0)
        # Drop the chunk
        return None

    def get_attributes(self) -> dict[str, Any]:
        return {
            "timeout_ms": self.timeout_ms,
        }
