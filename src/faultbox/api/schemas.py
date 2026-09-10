"""Pydantic request and response schemas for the REST Control Plane."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProxyCreateRequest(BaseModel):
    """Payload to register a new proxy."""

    name: str = Field(..., description="Unique proxy identifier", examples=["redis-chaos"])
    listen: str = Field(
        ..., description="Listen address or port", examples=["0.0.0.0:9000", "9000"]
    )
    upstream: str = Field(
        ..., description="Upstream destination address", examples=["127.0.0.1:6379"]
    )


class ProxyResponse(BaseModel):
    """Proxy details including active toxics and traffic counters."""

    name: str
    listen: str
    upstream: str
    enabled: bool
    stats: dict[str, Any]
    toxics: list[dict[str, Any]]


class ToxicCreateRequest(BaseModel):
    """Payload to attach a toxic to a proxy."""

    name: str = Field(..., description="Unique toxic name", examples=["latency-spike"])
    type: str = Field(
        ..., description="Toxic plugin type", examples=["latency", "bandwidth", "reset_peer"]
    )
    direction: str = Field("both", description="Traffic direction: inbound, outbound, both")
    toxicity: float = Field(1.0, ge=0.0, le=1.0, description="Probability of applying toxic")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Toxic-specific configuration"
    )
    enabled: bool = Field(True, description="Whether toxic is initially active")


class ToxicResponse(BaseModel):
    """Serialized toxic configuration."""

    name: str
    type: str
    direction: str
    toxicity: float
    enabled: bool
    attributes: dict[str, Any]


class MessageResponse(BaseModel):
    """Generic status response."""

    status: str
    message: str
