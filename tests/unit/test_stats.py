"""Unit tests for TrafficStats."""

from __future__ import annotations

from faultbox.core.stats import TrafficStats


def test_traffic_stats_counters() -> None:
    stats = TrafficStats(window_seconds=2.0)

    stats.record_bytes_in(1024)
    stats.record_bytes_out(2048)
    stats.record_connection_open()
    stats.record_connection_open()
    stats.record_connection_close()
    stats.record_error()

    snap = stats.snapshot()
    assert snap["bytes_in"] == 1024
    assert snap["bytes_out"] == 2048
    assert snap["connections_total"] == 2
    assert snap["connections_active"] == 1
    assert snap["errors_total"] == 1
    assert snap["uptime_seconds"] >= 0.0


def test_traffic_stats_throughput() -> None:
    stats = TrafficStats(window_seconds=1.0)
    # Record 10240 bytes (10 KB)
    stats.record_bytes_in(10240)
    in_kbps, out_kbps = stats.get_throughput_kbps()

    assert in_kbps == 10.0
    assert out_kbps == 0.0


def test_traffic_stats_reset() -> None:
    stats = TrafficStats()
    stats.record_bytes_in(500)
    stats.record_connection_open()
    stats.reset()

    snap = stats.snapshot()
    assert snap["bytes_in"] == 0
    assert snap["connections_active"] == 0
    assert snap["connections_total"] == 0
