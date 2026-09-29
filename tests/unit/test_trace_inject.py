"""Unit tests for W3C and distributed tracing context injection toxic."""

from __future__ import annotations

import pytest

from faultbox.toxics.base import StreamContext, ToxicDirection
from faultbox.toxics.factory import create_toxic
from faultbox.toxics.trace_inject import TraceInjectToxic


@pytest.fixture
def stream_context() -> StreamContext:
    return StreamContext(
        proxy_name="order-api",
        direction=ToxicDirection.INBOUND,
        client_addr="127.0.0.1:40000",
        upstream_addr="127.0.0.1:8080",
    )


@pytest.mark.asyncio
async def test_trace_inject_w3c_mode(stream_context: StreamContext) -> None:
    toxic = TraceInjectToxic(name="w3c-tagger", mode="w3c", baggage_extra="env=prod")
    http_req = b"GET /users/123 HTTP/1.1\r\nHost: api.internal\r\nUser-Agent: curl\r\n\r\n"

    transformed = await toxic.transform(http_req, stream_context)
    assert b"traceparent: 00-" in transformed
    assert b"tracestate: faultbox=injected;proxy=order-api;toxic=w3c-tagger" in transformed
    assert b"baggage: faultbox.chaos=true,faultbox.proxy=order-api,env=prod" in transformed
    assert b"X-FaultBox-Injected: true" in transformed
    assert b"X-FaultBox-Trace: " in transformed
    assert transformed.endswith(b"\r\n\r\n")

    assert "trace_id" in stream_context.metadata
    assert "traceparent" in stream_context.metadata


@pytest.mark.asyncio
async def test_trace_inject_b3_mode(stream_context: StreamContext) -> None:
    toxic = TraceInjectToxic(name="b3-tagger", mode="b3")
    http_req = b'POST /orders HTTP/1.1\r\nHost: order.svc\r\n\r\n{"id": 1}'

    transformed = await toxic.transform(http_req, stream_context)
    assert b"X-B3-TraceId: " in transformed
    assert b"X-B3-SpanId: " in transformed
    assert b"X-B3-Sampled: 1" in transformed
    assert b"X-FaultBox-Injected: true" in transformed
    assert transformed.endswith(b'{"id": 1}')


@pytest.mark.asyncio
async def test_trace_inject_custom_mode(stream_context: StreamContext) -> None:
    toxic = TraceInjectToxic(
        name="custom-tagger",
        mode="custom",
        custom_header="X-Chaos-Experiment",
        custom_value="exp-latency-01",
    )
    http_req = b"GET /health HTTP/1.1\r\nHost: app\r\n\r\n"

    transformed = await toxic.transform(http_req, stream_context)
    assert b"X-Chaos-Experiment: exp-latency-01" in transformed
    assert b"X-FaultBox-Injected: true" in transformed


@pytest.mark.asyncio
async def test_trace_inject_non_http_passthrough(stream_context: StreamContext) -> None:
    toxic = TraceInjectToxic(name="raw-tagger")
    raw_binary = b"\x00\x01\x02\x03\x04\x05"

    transformed = await toxic.transform(raw_binary, stream_context)
    assert transformed == raw_binary
    assert "trace_id" in stream_context.metadata


def test_factory_creation_trace_inject() -> None:
    toxic = create_toxic(
        name="t1",
        toxic_type="trace_inject",
        attributes={"mode": "w3c", "baggage_extra": "tier=gold"},
    )
    assert isinstance(toxic, TraceInjectToxic)
    assert toxic.mode == "w3c"
    assert toxic.baggage_extra == "tier=gold"
