"""Real-time traffic and connection statistics tracking."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass


@dataclass
class ThroughputSample:
    timestamp: float
    bytes_count: int


class TrafficStats:
    """Tracks traffic volume, active connections, and rolling throughput."""

    def __init__(self, window_seconds: float = 5.0) -> None:
        self.window_seconds = window_seconds
        self.bytes_in: int = 0
        self.bytes_out: int = 0
        self.connections_total: int = 0
        self.connections_active: int = 0
        self.errors_total: int = 0
        self.created_at: float = time.time()

        self._samples_in: deque[ThroughputSample] = deque()
        self._samples_out: deque[ThroughputSample] = deque()

    def record_bytes_in(self, count: int) -> None:
        """Record bytes received from client (inbound)."""
        now = time.time()
        self.bytes_in += count
        self._samples_in.append(ThroughputSample(timestamp=now, bytes_count=count))
        self._prune_samples(self._samples_in, now)

    def record_bytes_out(self, count: int) -> None:
        """Record bytes sent back to client (outbound)."""
        now = time.time()
        self.bytes_out += count
        self._samples_out.append(ThroughputSample(timestamp=now, bytes_count=count))
        self._prune_samples(self._samples_out, now)

    def record_connection_open(self) -> None:
        """Increment connection counters when a client connects."""
        self.connections_total += 1
        self.connections_active += 1

    def record_connection_close(self) -> None:
        """Decrement active connections when a client disconnects."""
        if self.connections_active > 0:
            self.connections_active -= 1

    def record_error(self) -> None:
        """Record a socket or pipeline processing error."""
        self.errors_total += 1

    def _prune_samples(self, samples: deque[ThroughputSample], now: float) -> None:
        cutoff = now - self.window_seconds
        while samples and samples[0].timestamp < cutoff:
            samples.popleft()

    def get_throughput_kbps(self) -> tuple[float, float]:
        """Calculate current rolling throughput in KB/s (inbound, outbound)."""
        now = time.time()
        self._prune_samples(self._samples_in, now)
        self._prune_samples(self._samples_out, now)

        total_in = sum(s.bytes_count for s in self._samples_in)
        total_out = sum(s.bytes_count for s in self._samples_out)

        in_kbps = (total_in / 1024.0) / self.window_seconds
        out_kbps = (total_out / 1024.0) / self.window_seconds
        return round(in_kbps, 2), round(out_kbps, 2)

    def snapshot(self) -> dict[str, float | int]:
        """Return a serializable dictionary of all metrics."""
        in_kbps, out_kbps = self.get_throughput_kbps()
        uptime_seconds = round(time.time() - self.created_at, 2)
        return {
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "connections_total": self.connections_total,
            "connections_active": self.connections_active,
            "errors_total": self.errors_total,
            "throughput_in_kbps": in_kbps,
            "throughput_out_kbps": out_kbps,
            "uptime_seconds": uptime_seconds,
        }

    def reset(self) -> None:
        """Reset counters while keeping creation timestamp."""
        self.bytes_in = 0
        self.bytes_out = 0
        self.connections_total = 0
        self.connections_active = 0
        self.errors_total = 0
        self._samples_in.clear()
        self._samples_out.clear()
