"""gRPC fault toxic: injects synthetic gRPC status codes and error trailers."""

from __future__ import annotations

from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection

GRPC_STATUS_NAMES = {
    0: "OK",
    1: "CANCELLED",
    2: "UNKNOWN",
    3: "INVALID_ARGUMENT",
    4: "DEADLINE_EXCEEDED",
    5: "NOT_FOUND",
    6: "ALREADY_EXISTS",
    7: "PERMISSION_DENIED",
    8: "RESOURCE_EXHAUSTED",
    9: "FAILED_PRECONDITION",
    10: "ABORTED",
    11: "OUT_OF_RANGE",
    12: "UNIMPLEMENTED",
    13: "INTERNAL",
    14: "UNAVAILABLE",
    15: "DATA_LOSS",
    16: "UNAUTHENTICATED",
}


class GrpcFaultToxic(BaseToxic):
    """Overrides responses with synthetic gRPC error trailers."""

    def __init__(
        self,
        name: str,
        grpc_status: int = 14,
        grpc_message: str = "Service Unavailable (faultbox chaos)",
        direction: ToxicDirection = ToxicDirection.OUTBOUND,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="grpc_fault",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.grpc_status = grpc_status if grpc_status in GRPC_STATUS_NAMES else 14
        self.grpc_message = grpc_message

    def _build_trailers_only_response(self) -> bytes:
        """Synthesize a trailers-only gRPC response."""
        resp = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/grpc\r\n"
            f"grpc-status: {self.grpc_status}\r\n"
            f"grpc-message: {self.grpc_message}\r\n"
            "Server: FaultBox/0.1.0\r\n"
            "Connection: close\r\n\r\n"
        )
        return resp.encode()

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        # If already injected on this stream, discard trailing chunks
        if context.metadata.get("grpc_fault_injected"):
            return None

        # Detect HTTP/1.x, gRPC-Web, or first outbound chunk
        if chunk.startswith(b"HTTP/") or b"application/grpc" in chunk:
            context.metadata["grpc_fault_injected"] = True
            return self._build_trailers_only_response()

        # For general outbound responses on a gRPC connection
        if context.direction == ToxicDirection.OUTBOUND and context.bytes_streamed <= len(chunk):
            context.metadata["grpc_fault_injected"] = True
            return self._build_trailers_only_response()

        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "grpc_status": self.grpc_status,
            "status_name": GRPC_STATUS_NAMES.get(self.grpc_status, "UNKNOWN"),
            "grpc_message": self.grpc_message,
        }
