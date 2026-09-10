"""Unit tests for protocol-aware toxics (gRPC and TLS)."""

from __future__ import annotations

import pytest

from faultbox.toxics import (
    GrpcFaultToxic,
    StreamContext,
    TlsFaultToxic,
    ToxicDirection,
    create_toxic,
)


@pytest.fixture
def outbound_context() -> StreamContext:
    return StreamContext(proxy_name="test_grpc", direction=ToxicDirection.OUTBOUND)


@pytest.fixture
def inbound_context() -> StreamContext:
    return StreamContext(proxy_name="test_tls", direction=ToxicDirection.INBOUND)


@pytest.mark.asyncio
async def test_grpc_fault_injection(outbound_context: StreamContext) -> None:
    toxic = GrpcFaultToxic(
        name="grpc_down",
        grpc_status=14,  # UNAVAILABLE
        grpc_message="Database cluster unreachable",
    )
    incoming = b"HTTP/2.0 200 OK\r\ncontent-type: application/grpc\r\n\r\n"
    synthetic = await toxic.transform(incoming, outbound_context)

    assert synthetic is not None
    assert b"grpc-status: 14" in synthetic
    assert b"Database cluster unreachable" in synthetic
    assert b"application/grpc" in synthetic

    # Second chunk on same stream should be suppressed
    trailing = await toxic.transform(b"extra data", outbound_context)
    assert trailing is None


@pytest.mark.asyncio
async def test_grpc_custom_status() -> None:
    ctx = StreamContext(proxy_name="test", direction=ToxicDirection.OUTBOUND)
    toxic = GrpcFaultToxic(name="grpc_perm", grpc_status=7)  # PERMISSION_DENIED
    attrs = toxic.get_attributes()
    assert attrs["status_name"] == "PERMISSION_DENIED"

    resp = await toxic.transform(b"HTTP/1.1 200 OK\r\n\r\n", ctx)
    assert resp is not None
    assert b"grpc-status: 7" in resp


@pytest.mark.asyncio
async def test_tls_alert_handshake_failure(inbound_context: StreamContext) -> None:
    toxic = TlsFaultToxic(name="tls_fail", mode="alert_handshake_failure")
    # Simulate TLS Client Hello record (0x16, TLS 1.2, length...)
    client_hello = b"\x16\x03\x03\x00\x10\x01\x00\x00\x0c" + b"fake_tls_data"

    res = await toxic.transform(client_hello, inbound_context)
    # Expect Fatal Alert 40 (handshake_failure)
    assert res == b"\x15\x03\x03\x00\x02\x02\x28"


@pytest.mark.asyncio
async def test_tls_alert_bad_certificate(inbound_context: StreamContext) -> None:
    toxic = TlsFaultToxic(name="tls_cert_fail", mode="alert_bad_certificate")
    res = await toxic.transform(b"\x16\x03\x03\x00\x05hello", inbound_context)
    # Expect Fatal Alert 42 (bad_certificate)
    assert res == b"\x15\x03\x03\x00\x02\x02\x2a"


@pytest.mark.asyncio
async def test_tls_corrupt_handshake(inbound_context: StreamContext) -> None:
    toxic = TlsFaultToxic(name="tls_corrupt", mode="corrupt_handshake")
    client_hello = b"\x16\x03\x03\x00\x20\x01" + (b"\xaa" * 20)

    res = await toxic.transform(client_hello, inbound_context)
    assert res is not None
    assert res != client_hello
    # First byte is still handshake content type
    assert res[0] == 0x16


def test_protocol_factory_registration() -> None:
    grpc = create_toxic("g1", "grpc_fault", attributes={"grpc_status": 4})
    assert isinstance(grpc, GrpcFaultToxic)
    assert grpc.grpc_status == 4

    tls = create_toxic("t1", "tls_fault", attributes={"mode": "alert_bad_certificate"})
    assert isinstance(tls, TlsFaultToxic)
    assert tls.mode == "alert_bad_certificate"
