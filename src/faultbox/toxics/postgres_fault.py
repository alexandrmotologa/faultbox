"""PostgreSQL protocol-aware toxic: injects synthetic wire-level ErrorResponse packets."""

from __future__ import annotations

import struct
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection

POSTGRES_SQLSTATE_NAMES = {
    "57P01": "admin_shutdown",
    "57014": "query_canceled",
    "40001": "serialization_failure",
    "40P01": "deadlock_detected",
    "08006": "connection_failure",
    "08001": "sqlclient_unable_to_establish_sqlconnection",
    "23505": "unique_violation",
    "42P01": "undefined_table",
    "53300": "too_many_connections",
}

DEFAULT_MESSAGES = {
    "57P01": "terminating connection due to administrator command",
    "57014": "canceling statement due to user request",
    "40001": "could not serialize access due to concurrent update",
    "40P01": "deadlock detected",
    "08006": "connection to server was lost",
    "08001": "could not connect to server: Connection refused",
    "23505": "duplicate key value violates unique constraint",
    "42P01": "relation does not exist",
    "53300": "sorry, too many clients already",
}


class PostgresFaultToxic(BaseToxic):
    """Overrides backend responses with standard PostgreSQL wire-level ErrorResponse frames."""

    def __init__(
        self,
        name: str,
        sqlstate: str = "57P01",
        message: str = "",
        severity: str = "ERROR",
        detail: str = "FaultBox synthetic chaos injected",
        close_connection: bool = False,
        match_query: str = "",
        send_ready_for_query: bool = True,
        direction: ToxicDirection = ToxicDirection.OUTBOUND,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="postgres_fault",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.sqlstate = sqlstate.strip()
        self.severity = severity.upper()
        self.message = message or DEFAULT_MESSAGES.get(self.sqlstate, "synthetic postgres error")
        self.detail = detail
        self.close_connection = close_connection
        self.match_query = match_query.strip().lower()
        self.send_ready_for_query = send_ready_for_query
        self._matched_conns: set[str] = set()

    def _get_conn_key(self, context: StreamContext) -> str:
        return context.client_addr or context.proxy_name

    def build_error_response(self) -> bytes:
        """Construct PostgreSQL 3.0 wire protocol ErrorResponse packet ('E')."""
        fields = [
            (b"S", self.severity.encode("utf-8")),
            (b"V", self.severity.encode("utf-8")),
            (b"C", self.sqlstate.encode("utf-8")),
            (b"M", self.message.encode("utf-8")),
        ]
        if self.detail:
            fields.append((b"D", self.detail.encode("utf-8")))

        # Field payload: code (1 byte) + null-terminated value
        body = bytearray()
        for code, val in fields:
            body.extend(code)
            body.extend(val)
            body.append(0)
        # End of fields marker (null byte)
        body.append(0)

        # Message length = 4 (length field itself) + len(body)
        length = 4 + len(body)
        packet = bytearray()
        packet.append(ord(b"E"))
        packet.extend(struct.pack("!I", length))
        packet.extend(body)

        # Optionally append ReadyForQuery ('Z') so non-fatal queries don't leave client hanging
        if self.send_ready_for_query and self.sqlstate != "57P01" and not self.close_connection:
            # ReadyForQuery: 'Z' + len 5 (Int32) + status 'I' (idle) or 'E' (error)
            packet.append(ord(b"Z"))
            packet.extend(struct.pack("!I", 5))
            packet.append(ord(b"E"))

        return bytes(packet)

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        conn_key = self._get_conn_key(context)

        # Track inbound queries if match_query is active
        if context.direction == ToxicDirection.INBOUND:
            if self.match_query:
                chunk_lower = chunk.lower()
                if self.match_query.encode("utf-8") in chunk_lower:
                    self._matched_conns.add(conn_key)
            return chunk

        # Outbound handling:
        # If match_query was configured, verify inbound match occurred
        if self.match_query and conn_key not in self._matched_conns:
            return chunk

        # Only inject once per query cycle or first response
        if context.metadata.get("postgres_error_injected"):
            # If close_connection was requested, drop trailing chunks
            if self.close_connection or self.sqlstate == "57P01":
                return None
            return chunk

        context.metadata["postgres_error_injected"] = True
        self._matched_conns.discard(conn_key)

        return self.build_error_response()

    async def on_close(self, context: StreamContext) -> None:
        self._matched_conns.discard(self._get_conn_key(context))

    def get_attributes(self) -> dict[str, Any]:
        return {
            "sqlstate": self.sqlstate,
            "sqlstate_name": POSTGRES_SQLSTATE_NAMES.get(self.sqlstate, "custom_error"),
            "severity": self.severity,
            "message": self.message,
            "detail": self.detail,
            "close_connection": self.close_connection,
            "match_query": self.match_query,
            "send_ready_for_query": self.send_ready_for_query,
        }
