"""Toxic pipeline for chaining and executing chaos transformations."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faultbox.toxics.base import BaseToxic, StreamContext


class ToxicPipeline:
    """Manages an ordered chain of toxics applied to stream data."""

    def __init__(self) -> None:
        self._toxics: list[BaseToxic] = []
        self._lock = asyncio.Lock()

    def add_toxic(self, toxic: BaseToxic, index: int | None = None) -> None:
        """Add a toxic to the pipeline. Raises ValueError if name is not unique."""
        if any(t.name == toxic.name for t in self._toxics):
            raise ValueError(f"Toxic with name '{toxic.name}' already exists in pipeline.")
        if index is not None and 0 <= index <= len(self._toxics):
            self._toxics.insert(index, toxic)
        else:
            self._toxics.append(toxic)

    def remove_toxic(self, name: str) -> bool:
        """Remove a toxic by name. Returns True if removed."""
        for i, toxic in enumerate(self._toxics):
            if toxic.name == name:
                self._toxics.pop(i)
                return True
        return False

    def get_toxic(self, name: str) -> BaseToxic | None:
        """Find a toxic by name."""
        for toxic in self._toxics:
            if toxic.name == name:
                return toxic
        return None

    def list_toxics(self) -> list[BaseToxic]:
        """Return a copy of all configured toxics in execution order."""
        return list(self._toxics)

    def clear(self) -> None:
        """Remove all toxics from the pipeline."""
        self._toxics.clear()

    async def process(self, chunk: bytes, context: StreamContext) -> list[bytes] | bytes | None:
        """
        Pass a chunk through all applicable toxics sequentially.

        Supports dropping chunks (None) and splitting chunks (list of bytes).
        """
        current_chunks: list[bytes] = [chunk]
        active_toxics = list(self._toxics)

        for toxic in active_toxics:
            if not toxic.applies_to(context.direction):
                continue
            if not toxic.should_apply():
                continue

            next_chunks: list[bytes] = []
            for item in current_chunks:
                transformed = await toxic.transform(item, context)
                if transformed is None:
                    continue
                if isinstance(transformed, list):
                    next_chunks.extend(transformed)
                else:
                    next_chunks.append(transformed)

            current_chunks = next_chunks
            if not current_chunks:
                return None

        if len(current_chunks) == 1:
            return current_chunks[0]
        return current_chunks

    async def notify_connect(self, context: StreamContext) -> None:
        """Notify applicable toxics of a new connection."""
        for toxic in list(self._toxics):
            if toxic.applies_to(context.direction):
                try:
                    await toxic.on_connect(context)
                except Exception:
                    pass

    async def notify_close(self, context: StreamContext) -> None:
        """Notify applicable toxics that a connection closed."""
        for toxic in list(self._toxics):
            if toxic.applies_to(context.direction):
                try:
                    await toxic.on_close(context)
                except Exception:
                    pass
