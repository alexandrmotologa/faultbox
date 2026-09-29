"""Unit tests for protocol-aware toxics (gRPC and TLS)."""

from __future__ import annotations

import pytest

from faultbox.toxics import (
    GrpcFaultToxic,
    PostgresFaultToxic,
    RedisFaultToxic,
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


@pytest.mark.asyncio
async def test_postgres_fault_admin_shutdown(outbound_context: StreamContext) -> None:
    toxic = PostgresFaultToxic(
        name="pg_kill",
        sqlstate="57P01",
        message="terminating connection due to administrator command",
        close_connection=True,
    )
    res = await toxic.transform(b"dummy_query_response", outbound_context)
    assert res is not None
    # Must start with ErrorResponse identifier 'E'
    assert res[0] == ord(b"E")
    # Must contain SQLSTATE 57P01
    assert b"C57P01\x00" in res
    assert b"Mterminating connection due to administrator command\x00" in res
    assert b"SERROR\x00" in res

    # Trailing responses should be suppressed when close_connection is True
    trailing = await toxic.transform(b"extra", outbound_context)
    assert trailing is None


@pytest.mark.asyncio
async def test_postgres_fault_with_ready_for_query(outbound_context: StreamContext) -> None:
    toxic = PostgresFaultToxic(
        name="pg_deadlock",
        sqlstate="40001",
        send_ready_for_query=True,
    )
    res = await toxic.transform(b"dummy", outbound_context)
    assert res is not None
    assert b"C40001\x00" in res
    # Should end with ReadyForQuery packet: 'Z' + len(5) + 'E'
    assert res.endswith(b"Z\x00\x00\x00\x05E")


@pytest.mark.asyncio
async def test_postgres_fault_query_matching() -> None:
    in_ctx = StreamContext(proxy_name="pg", direction=ToxicDirection.INBOUND)
    out_ctx = StreamContext(proxy_name="pg", direction=ToxicDirection.OUTBOUND)

    toxic = PostgresFaultToxic(name="pg_match", match_query="SELECT * FROM orders")

    # Inbound non-matching query
    await toxic.transform(b"Q\x00\x00\x00\x12SELECT 1;\x00", in_ctx)
    res1 = await toxic.transform(b"original_resp", out_ctx)
    assert res1 == b"original_resp"

    # Inbound matching query
    await toxic.transform(b"Q\x00\x00\x00\x22SELECT * FROM orders WHERE id=1;\x00", in_ctx)
    res2 = await toxic.transform(b"original_resp", out_ctx)
    assert res2 is not None
    assert res2[0] == ord(b"E")
    assert b"C57P01\x00" in res2


@pytest.mark.asyncio
async def test_redis_fault_readonly(outbound_context: StreamContext) -> None:
    toxic = RedisFaultToxic(name="r_ro", error_type="READONLY")
    res = await toxic.transform(b"+OK\r\n", outbound_context)
    assert res is not None
    assert res.startswith(b"-READONLY ")
    assert res.endswith(b"\r\n")


@pytest.mark.asyncio
async def test_redis_fault_clusterdown(outbound_context: StreamContext) -> None:
    toxic = RedisFaultToxic(
        name="r_cluster",
        error_type="CLUSTERDOWN",
        message="The cluster is down for maintenance",
    )
    res = await toxic.transform(b":1\r\n", outbound_context)
    assert res == b"-CLUSTERDOWN The cluster is down for maintenance\r\n"


@pytest.mark.asyncio
async def test_redis_fault_command_matching() -> None:
    in_ctx = StreamContext(proxy_name="redis", direction=ToxicDirection.INBOUND)
    out_ctx = StreamContext(proxy_name="redis", direction=ToxicDirection.OUTBOUND)

    toxic = RedisFaultToxic(name="r_cmd", error_type="BUSY", match_command="SET")

    # Non-matching command (GET key)
    await toxic.transform(b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n", in_ctx)
    res1 = await toxic.transform(b"$3\r\nbar\r\n", out_ctx)
    assert res1 == b"$3\r\nbar\r\n"

    # Matching command (SET key val)
    await toxic.transform(b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n", in_ctx)
    res2 = await toxic.transform(b"+OK\r\n", out_ctx)
    assert res2 is not None
    assert res2.startswith(b"-BUSY ")


def test_database_faults_factory_registration() -> None:
    pg = create_toxic("pg1", "postgres_fault", attributes={"sqlstate": "40001"})
    assert isinstance(pg, PostgresFaultToxic)
    assert pg.sqlstate == "40001"

    r = create_toxic("r1", "redis_fault", attributes={"error_type": "LOADING"})
    assert isinstance(r, RedisFaultToxic)
    assert r.error_type == "LOADING"
