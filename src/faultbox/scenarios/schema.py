"""Pydantic schemas for declarative YAML chaos scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ToxicStepConfig(BaseModel):
    """Toxic definition inside a scenario phase."""

    name: str
    type: str
    direction: str = "both"
    toxicity: float = 1.0
    attributes: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ScenarioPhase(BaseModel):
    """Individual scheduled action within a chaos scenario."""

    time_seconds: float = Field(..., ge=0.0, description="Execution offset in seconds")
    action: str = Field(..., description="Action: add_toxic, remove_toxic, reset, pause, resume")
    target_proxy: str | None = Field(None, description="Override default scenario proxy target")
    toxic: ToxicStepConfig | None = Field(None, description="Toxic to add when action is add_toxic")
    toxic_name: str | None = Field(None, description="Toxic identifier when action is remove_toxic")


class ScenarioAssertion(BaseModel):
    """Assertion condition to validate resilience SLAs."""

    metric: str = Field(
        ...,
        description="Metric name: errors_total, error_rate, bytes_in, bytes_out, bytes_total, connections_total, connections_active",
    )
    operator: str = Field(..., description="Comparison operator: <, <=, >, >=, ==, !=")
    threshold: float = Field(..., description="Numeric boundary threshold value")
    target_proxy: str | None = Field(
        None, description="Optional target proxy; if None, evaluated against aggregate stats"
    )
    description: str = Field("", description="Human-readable SLA or assertion description")


class ScenarioConfig(BaseModel):
    """Complete declarative chaos scenario definition."""

    name: str
    description: str = ""
    target_proxy: str | None = None
    phases: list[ScenarioPhase] = Field(default_factory=list)
    assertions: list[ScenarioAssertion] = Field(default_factory=list)

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> ScenarioConfig:
        """Parse a scenario from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def from_yaml_string(cls, content: str) -> ScenarioConfig:
        """Parse a scenario from a YAML string."""
        data = yaml.safe_load(content)
        return cls.model_validate(data)
