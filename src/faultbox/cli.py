"""Typer command-line interface for FaultBox."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console
from rich.table import Table

from faultbox import __version__
from faultbox.api.server import start_api_server
from faultbox.config import FaultBoxConfig
from faultbox.core.proxy import ProxyManager
from faultbox.scenarios.runner import ScenarioRunner
from faultbox.scenarios.schema import ScenarioConfig
from faultbox.tui.app import run_dashboard

app = typer.Typer(
    name="faultbox",
    help="Programmable network and protocol chaos injection proxy.",
    no_args_is_help=True,
)
proxy_app = typer.Typer(name="proxy", help="Manage active proxy instances.")
toxic_app = typer.Typer(name="toxic", help="Manage chaos toxics on proxies.")
scenario_app = typer.Typer(name="scenario", help="Execute declarative YAML chaos scenarios.")

app.add_typer(proxy_app)
app.add_typer(toxic_app)
app.add_typer(scenario_app)

console = Console()


def parse_proxy_spec(spec: str) -> tuple[str, str, str]:
    """Parse 'name:listen->upstream' or 'listen->upstream'."""
    if "->" not in spec:
        raise ValueError(f"Invalid proxy specification '{spec}'. Format: [name:]listen->upstream")

    left, upstream = spec.split("->", 1)
    if ":" in left and not left.split(":", 1)[0].isdigit():
        name, listen = left.split(":", 1)
    else:
        name = f"proxy-{left.replace(':', '-')}"
        listen = left
    return name.strip(), listen.strip(), upstream.strip()


@app.command()
def version() -> None:
    """Show FaultBox version."""
    console.print(f"[bold cyan]FaultBox[/bold cyan] version [bold green]{__version__}[/bold green]")


@app.command()
def run(
    proxies: Annotated[
        list[str] | None,
        typer.Option("--proxy", "-p", help="Proxy route in [name:]listen->upstream format."),
    ] = None,
    config_file: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
    scenario_file: Annotated[
        Path | None,
        typer.Option("--scenario", "-s", help="Declarative scenario YAML to run after startup."),
    ] = None,
    api: Annotated[bool, typer.Option("--api/--no-api", help="Start REST Control Plane.")] = True,
    api_host: Annotated[
        str, typer.Option("--api-host", help="REST API listening address.")
    ] = "0.0.0.0",
    api_port: Annotated[int, typer.Option("--api-port", help="REST API port.")] = 8474,
    dashboard: Annotated[
        bool, typer.Option("--dashboard/--no-dashboard", help="Display live TUI dashboard.")
    ] = False,
) -> None:
    """Start FaultBox proxy listeners and control services."""

    async def _async_run() -> None:
        manager = ProxyManager()

        # Load from config file if supplied
        if config_file and config_file.exists():
            cfg = FaultBoxConfig.from_yaml_file(config_file)
            for p_def in cfg.proxies:
                await manager.create_proxy(p_def.name, p_def.listen, p_def.upstream)

        # Load proxies supplied via CLI arguments
        if proxies:
            for spec in proxies:
                p_name, p_listen, p_upstream = parse_proxy_spec(spec)
                await manager.create_proxy(p_name, p_listen, p_upstream)

        # Start API server if enabled
        api_server = None
        api_task = None
        if api:
            api_server, api_task = await start_api_server(manager, host=api_host, port=api_port)
            console.print(
                f"[bold green]Control Plane API active[/bold green] at http://{api_host}:{api_port}"
            )

        # Print initial summary
        active_proxies = manager.list_proxies()
        if not active_proxies:
            console.print(
                "[dim]No initial proxies configured. Awaiting creation via API or CLI.[/dim]"
            )
        else:
            for p in active_proxies:
                console.print(
                    f"  Forwarding [cyan]{p.name}[/cyan] ({p.listen_address}) -> [yellow]{p.upstream_address}[/yellow]"
                )

        # Execute scenario if supplied
        if scenario_file and scenario_file.exists():
            sc_cfg = ScenarioConfig.from_yaml_file(scenario_file)
            runner = ScenarioRunner(
                manager,
                sc_cfg,
                on_event=lambda e: console.print(f"[dim][{e.time_offset:.1f}s][/dim] {e.message}"),
            )
            asyncio.create_task(runner.run())

        # Run dashboard or wait forever
        stop_event = asyncio.Event()
        try:
            if dashboard:
                await run_dashboard(manager, stop_event=stop_event)
            else:
                console.print("[dim]FaultBox running. Press Ctrl+C to terminate.[/dim]")
                await asyncio.Event().wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            stop_event.set()
            if api_server:
                api_server.should_exit = True
            await manager.stop_all()
            console.print("[yellow]FaultBox shut down cleanly.[/yellow]")

    asyncio.run(_async_run())


@proxy_app.command("list")
def list_proxies_cmd(
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """List all registered proxies from the control plane."""
    try:
        resp = httpx.get(f"{api_url}/proxies", timeout=5.0)
        resp.raise_for_status()
        proxies = resp.json()

        table = Table(title="FaultBox Active Proxies", border_style="cyan")
        table.add_column("Name", style="bold cyan")
        table.add_column("Listen", style="white")
        table.add_column("Upstream", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Toxics", style="yellow")
        table.add_column("Bytes In", justify="right")
        table.add_column("Bytes Out", justify="right")

        for p in proxies:
            status_text = "[green]ACTIVE[/green]" if p["enabled"] else "[yellow]PAUSED[/yellow]"
            toxics_str = ", ".join(t["name"] for t in p.get("toxics", [])) or "[dim]None[/dim]"
            table.add_row(
                p["name"],
                p["listen"],
                p["upstream"],
                status_text,
                toxics_str,
                str(p["stats"]["bytes_in"]),
                str(p["stats"]["bytes_out"]),
            )
        console.print(table)
    except Exception as exc:
        console.print(f"[bold red]Failed to connect to API ({api_url}):[/bold red] {exc}")


@proxy_app.command("create")
def create_proxy_cmd(
    name: Annotated[str, typer.Argument(help="Unique proxy name.")],
    listen: Annotated[str, typer.Argument(help="Listen port or host:port.")],
    upstream: Annotated[str, typer.Argument(help="Upstream host:port.")],
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """Create a new proxy route via the control plane."""
    try:
        resp = httpx.post(
            f"{api_url}/proxies",
            json={"name": name, "listen": listen, "upstream": upstream},
            timeout=5.0,
        )
        resp.raise_for_status()
        console.print(f"[bold green]Proxy '{name}' created successfully.[/bold green]")
    except httpx.HTTPStatusError as exc:
        console.print(
            f"[bold red]Error ({exc.response.status_code}):[/bold red] {exc.response.text}"
        )
    except Exception as exc:
        console.print(f"[bold red]Connection error:[/bold red] {exc}")


@proxy_app.command("delete")
def delete_proxy_cmd(
    name: Annotated[str, typer.Argument(help="Proxy name to delete.")],
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """Delete a proxy route."""
    try:
        resp = httpx.delete(f"{api_url}/proxies/{name}", timeout=5.0)
        resp.raise_for_status()
        console.print(f"[green]Proxy '{name}' deleted.[/green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")


@proxy_app.command("reset")
def reset_proxy_cmd(
    name: Annotated[str, typer.Argument(help="Proxy name to reset.")],
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """Remove all toxics from a proxy to restore pristine connection."""
    try:
        resp = httpx.post(f"{api_url}/proxies/{name}/reset", timeout=5.0)
        resp.raise_for_status()
        console.print(f"[green]All toxics cleared for proxy '{name}'.[/green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")


@toxic_app.command("list")
def list_toxics_cmd(
    proxy: Annotated[str, typer.Argument(help="Proxy name.")],
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """List toxics attached to a proxy."""
    try:
        resp = httpx.get(f"{api_url}/proxies/{proxy}/toxics", timeout=5.0)
        resp.raise_for_status()
        toxics = resp.json()

        table = Table(title=f"Toxics on '{proxy}'", border_style="yellow")
        table.add_column("Name", style="bold red")
        table.add_column("Type", style="cyan")
        table.add_column("Direction", style="magenta")
        table.add_column("Toxicity", justify="center")
        table.add_column("Attributes", style="white")

        for t in toxics:
            table.add_row(
                t["name"],
                t["type"],
                t["direction"],
                f"{t['toxicity'] * 100:.0f}%",
                json.dumps(t["attributes"]),
            )
        console.print(table)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")


@toxic_app.command("add")
def add_toxic_cmd(
    proxy: Annotated[str, typer.Argument(help="Target proxy name.")],
    name: Annotated[str, typer.Argument(help="Unique toxic name.")],
    toxic_type: Annotated[
        str, typer.Option("--type", "-t", help="Toxic type (latency, bandwidth, etc.)")
    ],
    direction: Annotated[
        str, typer.Option("--direction", "-d", help="Direction (inbound, outbound, both)")
    ] = "both",
    toxicity: Annotated[
        float, typer.Option("--toxicity", help="Probability of applying toxic (0.0 - 1.0).")
    ] = 1.0,
    attributes: Annotated[
        str, typer.Option("--attributes", "-a", help="JSON dictionary of toxic attributes.")
    ] = "{}",
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """Attach a toxic to a proxy."""
    try:
        attr_dict = json.loads(attributes)
    except json.JSONDecodeError:
        console.print("[bold red]Invalid JSON passed to --attributes[/bold red]")
        raise typer.Exit(1) from None

    try:
        resp = httpx.post(
            f"{api_url}/proxies/{proxy}/toxics",
            json={
                "name": name,
                "type": toxic_type,
                "direction": direction,
                "toxicity": toxicity,
                "attributes": attr_dict,
            },
            timeout=5.0,
        )
        resp.raise_for_status()
        console.print(f"[bold green]Toxic '{name}' attached to '{proxy}'.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")


@toxic_app.command("remove")
def remove_toxic_cmd(
    proxy: Annotated[str, typer.Argument(help="Target proxy name.")],
    name: Annotated[str, typer.Argument(help="Toxic name to remove.")],
    api_url: Annotated[
        str, typer.Option("--api-url", help="FaultBox API base URL.")
    ] = "http://127.0.0.1:8474",
) -> None:
    """Remove a toxic from a proxy."""
    try:
        resp = httpx.delete(f"{api_url}/proxies/{proxy}/toxics/{name}", timeout=5.0)
        resp.raise_for_status()
        console.print(f"[green]Toxic '{name}' removed from '{proxy}'.[/green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")


@scenario_app.command("run")
def run_scenario_cmd(
    file_path: Annotated[Path, typer.Argument(help="Path to YAML scenario file.")],
) -> None:
    """Execute a scenario locally against active proxies."""
    if not file_path.exists():
        console.print(f"[bold red]Scenario file not found:[/bold red] {file_path}")
        raise typer.Exit(1)

    cfg = ScenarioConfig.from_yaml_file(file_path)
    console.print(f"[bold cyan]Running scenario:[/bold cyan] {cfg.name}")
    if cfg.description:
        console.print(f"[dim]{cfg.description}[/dim]")

    # Run scenario runner
    manager = ProxyManager()

    async def _exec() -> None:
        runner = ScenarioRunner(
            manager,
            cfg,
            on_event=lambda e: console.print(
                f"  [{e.time_offset:.1f}s] {'[green]OK[/green]' if e.success else '[red]FAIL[/red]'} - {e.message}"
            ),
        )
        report = await runner.run()
        if report.success:
            console.print(
                f"\n[bold green]Scenario completed successfully[/bold green] in {report.duration_seconds}s"
            )
        else:
            console.print(
                f"\n[bold red]Scenario finished with errors[/bold red] in {report.duration_seconds}s"
            )

    asyncio.run(_exec())


if __name__ == "__main__":
    app()
