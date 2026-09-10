"""HTTP error toxic: intercepts HTTP traffic and injects synthetic status codes."""

from __future__ import annotations

import re
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection

HTTP_RESPONSE_PATTERN = re.compile(rb"^HTTP/\d\.\d\s+\d{3}\s+.*")


class HttpErrorToxic(BaseToxic):
    """Overrides HTTP responses with synthetic status codes like 429, 500, or 503."""

    def __init__(
        self,
        name: str,
        status_code: int = 500,
        status_message: str = "Internal Server Error",
        body: str = '{"error": "FaultBox Chaos Injected"}',
        content_type: str = "application/json",
        direction: ToxicDirection = ToxicDirection.OUTBOUND,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="http_error",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.status_code = status_code
        self.status_message = status_message
        self.body = body
        self.content_type = content_type

    def _build_synthetic_response(self) -> bytes:
        payload_bytes = self.body.encode("utf-8")
        header = (
            f"HTTP/1.1 {self.status_code} {self.status_message}\r\n"
            f"Content-Type: {self.content_type}\r\n"
            f"Content-Length: {len(payload_bytes)}\r\n"
            f"Server: FaultBox/0.1.0\r\n"
            f"Connection: close\r\n\r\n"
        ).encode()
        return header + payload_bytes

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        # If chunk matches HTTP response or starts with HTTP/1.x, override it
        if chunk.startswith(b"HTTP/"):
            return self._build_synthetic_response()

        # If already sent synthetic response on this stream, drop trailing original body chunks
        if context.metadata.get("http_error_injected"):
            return None

        # If first chunk in response doesn't start with HTTP/, still synthesize response
        if context.direction == ToxicDirection.OUTBOUND and context.bytes_streamed <= len(chunk):
            context.metadata["http_error_injected"] = True
            return self._build_synthetic_response()

        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "status_message": self.status_message,
            "body": self.body,
            "content_type": self.content_type,
        }
