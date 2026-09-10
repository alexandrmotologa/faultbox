"""Slicer toxic: fragments byte chunks into smaller pieces with micro-delays."""

from __future__ import annotations

from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class SlicerToxic(BaseToxic):
    """Fragments byte payloads into small chunks to test streaming and buffering."""

    def __init__(
        self,
        name: str,
        slice_size: int = 64,
        delay_ms: int = 10,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="slicer",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.slice_size = max(1, slice_size)
        self.delay_ms = max(0, delay_ms)

    async def transform(self, chunk: bytes, context: StreamContext) -> list[bytes] | bytes | None:
        if len(chunk) <= self.slice_size:
            return chunk

        slices = [chunk[i : i + self.slice_size] for i in range(0, len(chunk), self.slice_size)]
        return slices

    def get_attributes(self) -> dict[str, Any]:
        return {
            "slice_size": self.slice_size,
            "delay_ms": self.delay_ms,
        }
