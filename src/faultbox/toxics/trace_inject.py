"""Distributed tracing and W3C traceparent context injection toxic."""

from __future__ import annotations

import secrets
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class TraceInjectToxic(BaseToxic):
    """
    Injects W3C Trace Context, B3, or custom distributed tracing headers into HTTP traffic streams.

    Enables end-to-end tracing and correlation of chaos injection events in OpenTelemetry,
    Jaeger, Datadog, Zipkin, and Prometheus exemplars.

    Attributes:
        mode: Tracing standard: 'w3c' (default), 'b3', or 'custom'.
        custom_header: Header name when using mode='custom' (e.g. 'X-FaultBox-Chaos').
        custom_value: Header value when using mode='custom'.
        baggage_extra: Additional key=value baggage to propagate.
        override_existing: Whether to overwrite trace headers if already present in stream.
    """

    def __init__(
        self,
        name: str,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
        mode: str = "w3c",
        custom_header: str = "X-FaultBox-Chaos",
        custom_value: str = "true",
        baggage_extra: str = "",
        override_existing: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="trace_inject",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.mode = mode.lower().strip()
        self.custom_header = custom_header.strip()
        self.custom_value = custom_value.strip()
        self.baggage_extra = baggage_extra.strip()
        self.override_existing = override_existing

    def get_attributes(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "custom_header": self.custom_header,
            "custom_value": self.custom_value,
            "baggage_extra": self.baggage_extra,
            "override_existing": self.override_existing,
        }

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes:
        # Generate 16-byte (32-hex-char) trace_id and 8-byte (16-hex-char) span_id
        trace_id = secrets.token_hex(16)
        span_id = secrets.token_hex(8)

        context.metadata["trace_id"] = trace_id
        context.metadata["span_id"] = span_id

        # Inspect if chunk looks like an HTTP request/response header block
        if b"\r\n\r\n" not in chunk:
            return chunk

        header_bytes, body_bytes = chunk.split(b"\r\n\r\n", 1)
        headers_lower = header_bytes.lower()

        # Check if first line resembles HTTP
        first_line = header_bytes.split(b"\r\n", 1)[0]
        http_verbs = (b"GET ", b"POST ", b"PUT ", b"DELETE ", b"PATCH ", b"HEAD ", b"OPTIONS ", b"HTTP/")
        if not any(first_line.startswith(verb) for verb in http_verbs):
            return chunk

        headers_to_inject: list[bytes] = []

        if self.mode == "w3c":
            if self.override_existing or b"traceparent:" not in headers_lower:
                traceparent_val = f"00-{trace_id}-{span_id}-01"
                headers_to_inject.append(f"traceparent: {traceparent_val}".encode("ascii"))
                context.metadata["traceparent"] = traceparent_val

            tracestate_val = f"faultbox=injected;proxy={context.proxy_name};toxic={self.name}"
            headers_to_inject.append(f"tracestate: {tracestate_val}".encode("ascii"))

            baggage_items = ["faultbox.chaos=true", f"faultbox.proxy={context.proxy_name}"]
            if self.baggage_extra:
                baggage_items.append(self.baggage_extra)
            headers_to_inject.append(f"baggage: {','.join(baggage_items)}".encode("ascii"))

        elif self.mode == "b3":
            if self.override_existing or b"x-b3-traceid:" not in headers_lower:
                headers_to_inject.append(f"X-B3-TraceId: {trace_id}".encode("ascii"))
                headers_to_inject.append(f"X-B3-SpanId: {span_id}".encode("ascii"))
                headers_to_inject.append(b"X-B3-Sampled: 1")

        elif self.mode == "custom":
            headers_to_inject.append(f"{self.custom_header}: {self.custom_value}".encode("ascii"))

        # Add general observability marker
        headers_to_inject.append(b"X-FaultBox-Injected: true")
        headers_to_inject.append(f"X-FaultBox-Trace: {trace_id}".encode("ascii"))

        if not headers_to_inject:
            return chunk

        injected_block = b"\r\n".join(headers_to_inject)
        return header_bytes + b"\r\n" + injected_block + b"\r\n\r\n" + body_bytes
