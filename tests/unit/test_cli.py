"""Unit tests for the Typer CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from faultbox.cli import app, parse_proxy_spec

runner = CliRunner()


def test_parse_proxy_spec() -> None:
    name, listen, upstream = parse_proxy_spec("redis:9000->127.0.0.1:6379")
    assert name == "redis"
    assert listen == "9000"
    assert upstream == "127.0.0.1:6379"

    name2, listen2, upstream2 = parse_proxy_spec("8080->127.0.0.1:80")
    assert name2 == "proxy-8080"
    assert listen2 == "8080"
    assert upstream2 == "127.0.0.1:80"


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "FaultBox version" in result.stdout


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Programmable network and protocol chaos injection proxy" in result.stdout
