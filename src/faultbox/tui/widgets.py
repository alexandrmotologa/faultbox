"""Rich UI components and dashboard layouts for terminal presentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from faultbox.core.proxy import ProxyManager


def create_header_panel(version: str = "0.1.0") -> Panel:
    """Render top header bar with application metadata."""
    title = Text("FAULTBOX: Chaos Engineering Proxy", style="bold white on blue")
    subtitle = Text(
        f" v{version} | Asynchronous Protocol & Network Degradation Engine", style="dim"
    )
    combined = Text.assemble(title, subtitle)
    return Panel(combined, border_style="blue")


def create_kpi_table(manager: ProxyManager) -> Table:
    """Render KPI summary cards showing aggregate traffic metrics."""
    table = Table(expand=True, show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Total Proxies", justify="center")
    table.add_column("Active Connections", justify="center")
    table.add_column("Total Connections", justify="center")
    table.add_column("Throughput In (KB/s)", justify="center")
    table.add_column("Throughput Out (KB/s)", justify="center")
    table.add_column("Total Errors", justify="center")

    proxies = manager.list_proxies()
    total_active_conn = sum(p.stats.connections_active for p in proxies)
    total_conn = sum(p.stats.connections_total for p in proxies)
    total_errors = sum(p.stats.errors_total for p in proxies)
    total_in_kbps = sum(p.stats.get_throughput_kbps()[0] for p in proxies)
    total_out_kbps = sum(p.stats.get_throughput_kbps()[1] for p in proxies)

    err_style = "bold red" if total_errors > 0 else "green"

    table.add_row(
        str(len(proxies)),
        str(total_active_conn),
        str(total_conn),
        f"{total_in_kbps:.2f}",
        f"{total_out_kbps:.2f}",
        f"[{err_style}]{total_errors}[/{err_style}]",
    )
    return table


def create_proxies_table(manager: ProxyManager) -> Table:
    """Render detailed table of registered proxies and their active toxics."""
    table = Table(
        expand=True,
        title="Registered Proxies & Active Disruptions",
        title_style="bold white",
        header_style="bold magenta",
        border_style="dim",
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Listen Address", style="white")
    table.add_column("Upstream Target", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Active Toxics", style="yellow")
    table.add_column("Bytes In / Out", justify="right")

    for proxy in manager.list_proxies():
        status_text = "[green]ACTIVE[/green]" if proxy.enabled else "[yellow]PAUSED[/yellow]"
        toxics = proxy.pipeline.list_toxics()

        if not toxics:
            toxic_badges = "[green]PRISTINE (None)[/green]"
        else:
            badges = []
            for t in toxics:
                state = "on" if t.enabled else "off"
                badges.append(f"[bold red]{t.name}[/bold red] ({t.toxic_type}:{state})")
            toxic_badges = ", ".join(badges)

        snap = proxy.stats.snapshot()
        bytes_in_kb = snap["bytes_in"] / 1024.0
        bytes_out_kb = snap["bytes_out"] / 1024.0
        traffic_str = f"{bytes_in_kb:.1f} KB / {bytes_out_kb:.1f} KB"

        table.add_row(
            proxy.name,
            proxy.listen_address,
            proxy.upstream_address,
            status_text,
            toxic_badges,
            traffic_str,
        )

    if not manager.list_proxies():
        table.add_row("-", "No proxies configured", "-", "-", "-", "-")

    return table


def make_dashboard_layout(manager: ProxyManager, version: str = "0.1.0") -> Layout:
    """Assemble entire dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(create_header_panel(version), size=3, name="header"),
        Layout(
            Panel(create_kpi_table(manager), title="Cluster Traffic KPIs", border_style="cyan"),
            size=6,
            name="kpis",
        ),
        Layout(Panel(create_proxies_table(manager), border_style="magenta"), name="proxies"),
    )
    return layout
