"""Unit tests for chaos scenario quality gates and resilience SLA assertions."""

from __future__ import annotations

import pytest

from faultbox.core.proxy import ProxyManager
from faultbox.scenarios.runner import ScenarioRunner
from faultbox.scenarios.schema import ScenarioConfig


@pytest.mark.asyncio
async def test_scenario_assertion_parsing() -> None:
    yaml_text = """
    name: "sla-check"
    target_proxy: "app"
    phases:
      - time_seconds: 0.01
        action: "reset"
    assertions:
      - metric: "errors_total"
        operator: "<="
        threshold: 5
        description: "Zero or minimal errors"
      - metric: "error_rate"
        operator: "<"
        threshold: 0.1
        target_proxy: "app"
      - metric: "connections_active"
        operator: "=="
        threshold: 0
    """
    cfg = ScenarioConfig.from_yaml_string(yaml_text)
    assert cfg.name == "sla-check"
    assert len(cfg.assertions) == 3
    assert cfg.assertions[0].metric == "errors_total"
    assert cfg.assertions[0].operator == "<="
    assert cfg.assertions[0].threshold == 5.0
    assert cfg.assertions[0].description == "Zero or minimal errors"
    assert cfg.assertions[1].target_proxy == "app"


@pytest.mark.asyncio
async def test_scenario_assertions_pass() -> None:
    manager = ProxyManager()
    proxy = await manager.create_proxy(
        "app", "127.0.0.1:19991", "127.0.0.1:80", start_immediately=False
    )
    # Simulate some traffic and errors
    proxy.stats.record_connection_open()
    proxy.stats.record_bytes_in(1024)
    proxy.stats.record_bytes_out(2048)
    proxy.stats.record_error()
    proxy.stats.record_connection_close()

    yaml_text = """
    name: "pass-scenario"
    target_proxy: "app"
    phases:
      - time_seconds: 0.01
        action: "reset"
    assertions:
      - metric: "errors_total"
        operator: "<="
        threshold: 10
      - metric: "bytes_total"
        operator: ">="
        threshold: 0
      - metric: "connections_active"
        operator: "=="
        threshold: 0
    """
    config = ScenarioConfig.from_yaml_string(yaml_text)
    runner = ScenarioRunner(manager, config)
    report = await runner.run()

    assert report.success is True
    assert report.assertions_passed is True
    assert len(report.assertions) == 3
    assert all(a.passed for a in report.assertions)


@pytest.mark.asyncio
async def test_scenario_assertions_fail_triggers_failure() -> None:
    manager = ProxyManager()
    proxy = await manager.create_proxy(
        "app", "127.0.0.1:19992", "127.0.0.1:80", start_immediately=False
    )

    yaml_text = """
    name: "fail-scenario"
    target_proxy: "app"
    phases:
      - time_seconds: 0.01
        action: "reset"
    assertions:
      - metric: "errors_total"
        operator: "<"
        threshold: 1
        description: "Strict zero-error tolerance"
    """
    config = ScenarioConfig.from_yaml_string(yaml_text)

    # Simulate errors occurring while scenario is running (via event hook)
    def on_event(_):
        proxy.stats.record_connection_open()
        for _ in range(5):
            proxy.stats.record_error()

    runner = ScenarioRunner(manager, config, on_event=on_event)
    report = await runner.run()

    assert report.assertions_passed is False
    assert report.success is False
    assert len(report.assertions) == 1
    assert report.assertions[0].passed is False
    assert report.assertions[0].actual_value == 5.0
    assert report.assertions[0].threshold == 1.0


@pytest.mark.asyncio
async def test_cluster_stats_aggregation() -> None:
    manager = ProxyManager()
    p1 = await manager.create_proxy(
        "p1", "127.0.0.1:19993", "127.0.0.1:80", start_immediately=False
    )
    p2 = await manager.create_proxy(
        "p2", "127.0.0.1:19994", "127.0.0.1:80", start_immediately=False
    )

    p1.stats.record_connection_open()
    p1.stats.record_bytes_in(500)
    p1.stats.record_error()

    p2.stats.record_connection_open()
    p2.stats.record_bytes_out(800)

    cluster_stats = manager.get_cluster_stats()
    assert cluster_stats["bytes_in"] == 500
    assert cluster_stats["bytes_out"] == 800
    assert cluster_stats["bytes_total"] == 1300
    assert cluster_stats["connections_total"] == 2
    assert cluster_stats["errors_total"] == 1
    assert cluster_stats["error_rate"] == 0.5
