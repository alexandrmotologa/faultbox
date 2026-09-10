"""Reset peer toxic: abruptly closes TCP connection."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class ResetPeerToxic(BaseToxic):
    """Abruptly terminates the connection, raising a ConnectionResetError."""

    def __init__(
        self,
        name: str,
        byte_offset: int = 0,
        timeout_ms: int = 0,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="reset_peer",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.byte_offset = max(0, byte_offset)
        self.timeout_ms = max(0, timeout_ms)

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if self.timeout_ms > 0:
            await asyncio.sleep(self.timeout_ms / 1000.0)

        if context.bytes_streamed >= self.byte_offset:
            raise ConnectionResetError("Connection reset by peer (faultbox chaos)")

        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "byte_offset": self.byte_offset,
            "timeout_ms": self.timeout_ms,
        }
