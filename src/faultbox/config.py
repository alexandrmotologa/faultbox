"""Configuration models and loader for FaultBox."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProxyDefinition(BaseModel):
    """Configuration definition for a single proxy."""

    name: str
    listen: str
    upstream: str


class FaultBoxConfig(BaseModel):
    """Global configuration settings for FaultBox daemon."""

    api_host: str = "0.0.0.0"
    api_port: int = 8474
    api_enabled: bool = True
    proxies: list[ProxyDefinition] = Field(default_factory=list)

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> FaultBoxConfig:
        """Load configuration from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)
