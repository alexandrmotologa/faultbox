"""Factory registry for creating toxic instances from types and attributes."""

from __future__ import annotations

from typing import Any

from faultbox.toxics.bandwidth import BandwidthToxic
from faultbox.toxics.base import BaseToxic, ToxicDirection
from faultbox.toxics.corrupt import CorruptToxic
from faultbox.toxics.flapping import FlappingToxic
from faultbox.toxics.http_error import HttpErrorToxic
from faultbox.toxics.latency import LatencyToxic
from faultbox.toxics.reset_peer import ResetPeerToxic
from faultbox.toxics.slicer import SlicerToxic
from faultbox.toxics.timeout import TimeoutToxic
from faultbox.toxics.waveform_latency import WaveformLatencyToxic

TOXIC_REGISTRY: dict[str, type[BaseToxic]] = {
    "latency": LatencyToxic,
    "waveform_latency": WaveformLatencyToxic,
    "bandwidth": BandwidthToxic,
    "reset_peer": ResetPeerToxic,
    "timeout": TimeoutToxic,
    "corrupt": CorruptToxic,
    "slicer": SlicerToxic,
    "flapping": FlappingToxic,
    "http_error": HttpErrorToxic,
}


def create_toxic(
    name: str,
    toxic_type: str,
    direction: str = "both",
    toxicity: float = 1.0,
    attributes: dict[str, Any] | None = None,
    enabled: bool = True,
) -> BaseToxic:
    """Instantiate a toxic plugin by type name with custom attributes."""
    toxic_cls = TOXIC_REGISTRY.get(toxic_type.lower())
    if toxic_cls is None:
        valid_types = ", ".join(sorted(TOXIC_REGISTRY.keys()))
        raise ValueError(f"Unknown toxic type '{toxic_type}'. Supported types: {valid_types}")

    try:
        toxic_direction = ToxicDirection(direction.lower())
    except ValueError as exc:
        raise ValueError(
            f"Invalid direction '{direction}'. Supported: inbound, outbound, both"
        ) from exc

    attrs = attributes or {}
    return toxic_cls(
        name=name,
        direction=toxic_direction,
        toxicity=toxicity,
        enabled=enabled,
        **attrs,
    )
