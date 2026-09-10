"""Waveform latency toxic: generates dynamic, time-varying latency curves."""

from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class WaveformLatencyToxic(BaseToxic):
    """Adds time-varying latency following mathematical waveforms (sine, sawtooth, burst, brownian)."""

    def __init__(
        self,
        name: str,
        base_latency_ms: int = 100,
        amplitude_ms: int = 200,
        period_sec: float = 10.0,
        waveform: str = "sine",
        jitter_ms: int = 0,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="waveform_latency",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.base_latency_ms = max(0, base_latency_ms)
        self.amplitude_ms = max(0, amplitude_ms)
        self.period_sec = max(0.1, float(period_sec))
        self.waveform = (
            waveform if waveform in ("sine", "sawtooth", "burst", "brownian") else "sine"
        )
        self.jitter_ms = max(0, jitter_ms)

        self._start_time = time.time()
        self._current_brownian = float(self.base_latency_ms + self.amplitude_ms / 2.0)

    def calculate_current_latency_ms(self, now: float | None = None) -> float:
        """Calculate the target latency in milliseconds for the current point in time."""
        current_time = now if now is not None else time.time()
        elapsed = current_time - self._start_time
        phase = (elapsed % self.period_sec) / self.period_sec

        if self.waveform == "sine":
            # Smooth oscillation between base and base + amplitude
            factor = (math.sin(2 * math.pi * phase) + 1.0) / 2.0
            latency = self.base_latency_ms + (self.amplitude_ms * factor)

        elif self.waveform == "sawtooth":
            # Linear ramp from base to base + amplitude, then sharp drop
            latency = self.base_latency_ms + (self.amplitude_ms * phase)

        elif self.waveform == "burst":
            # Baseline for first 80% of cycle, sharp spike during the last 20%
            if phase >= 0.8:
                latency = self.base_latency_ms + self.amplitude_ms
            else:
                latency = float(self.base_latency_ms)

        elif self.waveform == "brownian":
            # Bounded random walk drift
            step = random.uniform(-self.amplitude_ms * 0.15, self.amplitude_ms * 0.15)
            self._current_brownian = max(
                float(self.base_latency_ms),
                min(
                    float(self.base_latency_ms + self.amplitude_ms),
                    self._current_brownian + step,
                ),
            )
            latency = self._current_brownian

        else:
            latency = float(self.base_latency_ms)

        if self.jitter_ms > 0:
            latency += random.uniform(-self.jitter_ms, self.jitter_ms)

        return max(0.0, latency)

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        delay_ms = self.calculate_current_latency_ms()
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)
        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "base_latency_ms": self.base_latency_ms,
            "amplitude_ms": self.amplitude_ms,
            "period_sec": self.period_sec,
            "waveform": self.waveform,
            "jitter_ms": self.jitter_ms,
        }
