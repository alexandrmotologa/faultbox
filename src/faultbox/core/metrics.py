"""Prometheus metrics text exposition generator for FaultBox."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


def generate_prometheus_metrics(manager: ProxyManager) -> str:
    """Generate Prometheus plain text metrics for all registered proxies."""
    lines: list[str] = [
        "# HELP faultbox_bytes_total Total bytes transferred by proxy and direction.",
        "# TYPE faultbox_bytes_total counter",
    ]

    proxies = manager.list_proxies()

    for p in proxies:
        snap = p.stats.snapshot()
        lines.append(
            f'faultbox_bytes_total{{proxy="{p.name}",direction="inbound"}} {snap["bytes_in"]}'
        )
        lines.append(
            f'faultbox_bytes_total{{proxy="{p.name}",direction="outbound"}} {snap["bytes_out"]}'
        )

    lines.extend(
        [
            "# HELP faultbox_connections_active Number of currently active TCP connections.",
            "# TYPE faultbox_connections_active gauge",
        ]
    )
    for p in proxies:
        snap = p.stats.snapshot()
        lines.append(
            f'faultbox_connections_active{{proxy="{p.name}"}} {snap["connections_active"]}'
        )

    lines.extend(
        [
            "# HELP faultbox_connections_total Total lifetime connections accepted by proxy.",
            "# TYPE faultbox_connections_total counter",
        ]
    )
    for p in proxies:
        snap = p.stats.snapshot()
        lines.append(f'faultbox_connections_total{{proxy="{p.name}"}} {snap["connections_total"]}')

    lines.extend(
        [
            "# HELP faultbox_errors_total Total network and pipeline errors recorded.",
            "# TYPE faultbox_errors_total counter",
        ]
    )
    for p in proxies:
        snap = p.stats.snapshot()
        lines.append(f'faultbox_errors_total{{proxy="{p.name}"}} {snap["errors_total"]}')

    lines.extend(
        [
            "# HELP faultbox_throughput_kbps Rolling throughput calculation in kilobytes per second.",
            "# TYPE faultbox_throughput_kbps gauge",
        ]
    )
    for p in proxies:
        in_kbps, out_kbps = p.stats.get_throughput_kbps()
        lines.append(f'faultbox_throughput_kbps{{proxy="{p.name}",direction="inbound"}} {in_kbps}')
        lines.append(
            f'faultbox_throughput_kbps{{proxy="{p.name}",direction="outbound"}} {out_kbps}'
        )

    lines.extend(
        [
            "# HELP faultbox_proxy_enabled Whether the proxy is active (1) or paused (0).",
            "# TYPE faultbox_proxy_enabled gauge",
        ]
    )
    for p in proxies:
        val = 1 if p.enabled else 0
        lines.append(f'faultbox_proxy_enabled{{proxy="{p.name}"}} {val}')

    lines.extend(
        [
            "# HELP faultbox_toxics_configured Number of toxics attached to the proxy pipeline.",
            "# TYPE faultbox_toxics_configured gauge",
        ]
    )
    for p in proxies:
        count = len(p.pipeline.list_toxics())
        lines.append(f'faultbox_toxics_configured{{proxy="{p.name}"}} {count}')

    lines.append("")  # trailing newline required by Prometheus specification
    return "\n".join(lines)
