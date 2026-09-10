"""Base classes and interfaces for toxic chaos plugins."""

from __future__ import annotations

import abc
import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToxicDirection(StrEnum):
    """Direction of traffic affected by the toxic."""

    INBOUND = "inbound"  # Client to upstream
    OUTBOUND = "outbound"  # Upstream to client
    BOTH = "both"  # Both directions


@dataclass
class StreamContext:
    """Per-connection streaming context provided to toxics."""

    proxy_name: str
    direction: ToxicDirection
    client_addr: str = ""
    upstream_addr: str = ""
    bytes_streamed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseToxic(abc.ABC):
    """Abstract base class for all toxic plugins."""

    def __init__(
        self,
        name: str,
        toxic_type: str,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        self.name = name
        self.toxic_type = toxic_type
        self.direction = direction
        self.toxicity = max(0.0, min(1.0, float(toxicity)))
        self.enabled = enabled

    def applies_to(self, direction: ToxicDirection) -> bool:
        """Check if toxic applies to the given traffic direction."""
        if not self.enabled:
            return False
        if self.direction == ToxicDirection.BOTH:
            return True
        return self.direction == direction

    def should_apply(self) -> bool:
        """Evaluate probabilistic toxicity trigger."""
        if self.toxicity >= 1.0:
            return True
        if self.toxicity <= 0.0:
            return False
        return random.random() < self.toxicity

    @abc.abstractmethod
    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        """
        Process and transform raw payload chunk.

        Returning None drops the chunk (packet loss).
        Raising ConnectionResetError aborts the connection.
        """
        ...

    async def on_connect(self, context: StreamContext) -> None:  # noqa: B027
        """Lifecycle hook invoked when a new connection is established."""
        pass

    async def on_close(self, context: StreamContext) -> None:  # noqa: B027
        """Lifecycle hook invoked when a connection closes."""
        pass

    def get_attributes(self) -> dict[str, Any]:
        """Return toxic-specific configuration attributes."""
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize toxic configuration."""
        return {
            "name": self.name,
            "type": self.toxic_type,
            "direction": self.direction.value,
            "toxicity": self.toxicity,
            "enabled": self.enabled,
            "attributes": self.get_attributes(),
        }
