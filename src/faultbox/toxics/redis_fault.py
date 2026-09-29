"""Redis RESP protocol-aware toxic: injects synthetic RESP error frames."""

from __future__ import annotations

from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection

REDIS_DEFAULT_ERRORS = {
    "READONLY": "You can't write against a read only replica.",
    "BUSY": "Redis is busy running a script. You can only call SCRIPT KILL or SHUTDOWN NOSAVE.",
    "LOADING": "Redis is loading the dataset in memory",
    "CLUSTERDOWN": "The cluster is down",
    "OOM": "command not allowed when used memory > 'maxmemory'.",
    "WRONGTYPE": "Operation against a key holding the wrong kind of value",
    "ERR": "syntax error or unknown operation",
}


class RedisFaultToxic(BaseToxic):
    """Overrides backend responses with standard Redis RESP error messages (-<TYPE> <msg>\\r\\n)."""

    def __init__(
        self,
        name: str,
        error_type: str = "READONLY",
        message: str = "",
        match_command: str = "",
        direction: ToxicDirection = ToxicDirection.OUTBOUND,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="redis_fault",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.error_type = error_type.upper().strip()
        default_msg = REDIS_DEFAULT_ERRORS.get(self.error_type, "FaultBox chaos injected")
        self.message = message.strip() or default_msg
        self.match_command = match_command.upper().strip()
        self._matched_conns: set[str] = set()

    def _get_conn_key(self, context: StreamContext) -> str:
        return context.client_addr or context.proxy_name

    def build_resp_error(self) -> bytes:
        """Construct standard RESP simple error frame: -<TYPE> <Message>\\r\\n."""
        return f"-{self.error_type} {self.message}\r\n".encode()

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        conn_key = self._get_conn_key(context)

        # Track inbound command if match_command is specified
        if context.direction == ToxicDirection.INBOUND:
            if self.match_command:
                chunk_upper = chunk.upper()
                if self.match_command.encode("utf-8") in chunk_upper:
                    self._matched_conns.add(conn_key)
            return chunk

        # Outbound handling:
        # Check command match if configured
        if self.match_command and conn_key not in self._matched_conns:
            return chunk

        self._matched_conns.discard(conn_key)

        # Intercept and replace response with synthetic RESP error
        return self.build_resp_error()

    async def on_close(self, context: StreamContext) -> None:
        self._matched_conns.discard(self._get_conn_key(context))

    def get_attributes(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "match_command": self.match_command,
        }
