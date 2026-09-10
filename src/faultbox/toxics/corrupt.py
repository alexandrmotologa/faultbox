"""Corrupt toxic: injects random byte corruption or bit flips."""

from __future__ import annotations

import random
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class CorruptToxic(BaseToxic):
    """Mutates payload bytes by flipping bits, zeroing, or substituting random bytes."""

    def __init__(
        self,
        name: str,
        rate: float = 0.05,
        mode: str = "bitflip",
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="corrupt",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.rate = max(0.001, min(1.0, float(rate)))
        self.mode = mode if mode in ("bitflip", "zero", "random_byte") else "bitflip"

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        buffer = bytearray(chunk)
        corrupt_count = max(1, int(len(buffer) * self.rate))
        indices = random.sample(range(len(buffer)), min(corrupt_count, len(buffer)))

        for idx in indices:
            if self.mode == "bitflip":
                buffer[idx] ^= 1 << random.randint(0, 7)
            elif self.mode == "zero":
                buffer[idx] = 0
            elif self.mode == "random_byte":
                buffer[idx] = random.randint(0, 255)

        return bytes(buffer)

    def get_attributes(self) -> dict[str, Any]:
        return {
            "rate": self.rate,
            "mode": self.mode,
        }
