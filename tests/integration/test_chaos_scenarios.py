"""Integration tests for declarative chaos scenarios."""

from __future__ import annotations

import pytest

from faultbox.core.proxy import ProxyManager
from faultbox.scenarios.runner import ScenarioRunner
from faultbox.scenarios.schema import ScenarioConfig


@pytest.mark.asyncio
async def test_scenario_execution_lifecycle() -> None:
    manager = ProxyManager()
    await manager.create_proxy(
        "test-app", "127.0.0.1:19999", "127.0.0.1:80", start_immediately=False
    )

    yaml_content = """
    name: "fast-test-scenario"
    description: "Fast scenario for test execution"
    target_proxy: "test-app"
    phases:
      - time_seconds: 0.01
        action: "add_toxic"
        toxic:
          name: "quick-lat"
          type: "latency"
          attributes:
            latency_ms: 10
      - time_seconds: 0.03
        action: "pause"
      - time_seconds: 0.05
        action: "resume"
      - time_seconds: 0.07
        action: "reset"
    """
    config = ScenarioConfig.from_yaml_string(yaml_content)
    runner = ScenarioRunner(manager, config)

    report = await runner.run()

    assert report.name == "fast-test-scenario"
    assert report.total_phases == 4
    assert report.executed_phases == 4
    assert report.success is True
    assert len(report.events) == 4

    proxy = manager.get_proxy("test-app")
    assert proxy is not None
    # Reset was called in final phase, so toxics list should be empty
    assert len(proxy.pipeline.list_toxics()) == 0
    assert proxy.enabled is True
