"""TLS fault toxic: simulates TLS alerts, handshake stalls, and certificate errors."""

from __future__ import annotations

import asyncio
from typing import Any

from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection

# TLS Record Layer content types
TLS_CONTENT_TYPE_HANDSHAKE = 0x16
TLS_CONTENT_TYPE_ALERT = 0x15

# Standard TLS Alert Records (TLS 1.2 / 1.3 frame format: Type, Version, Length, Level, Description)
ALERT_HANDSHAKE_FAILURE = b"\x15\x03\x03\x00\x02\x02\x28"  # Fatal (2), handshake_failure (40)
ALERT_BAD_CERTIFICATE = b"\x15\x03\x03\x00\x02\x02\x2a"  # Fatal (2), bad_certificate (42)
ALERT_ACCESS_DENIED = b"\x15\x03\x03\x00\x02\x02\x31"  # Fatal (2), access_denied (49)


class TlsFaultToxic(BaseToxic):
    """Simulates TLS/SSL handshake failures, alert records, and certificate errors."""

    def __init__(
        self,
        name: str,
        mode: str = "alert_handshake_failure",
        stall_seconds: float = 30.0,
        direction: ToxicDirection = ToxicDirection.BOTH,
        toxicity: float = 1.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            toxic_type="tls_fault",
            direction=direction,
            toxicity=toxicity,
            enabled=enabled,
        )
        self.mode = (
            mode
            if mode
            in (
                "alert_handshake_failure",
                "alert_bad_certificate",
                "alert_access_denied",
                "stall_handshake",
                "corrupt_handshake",
            )
            else "alert_handshake_failure"
        )
        self.stall_seconds = max(0.1, float(stall_seconds))

    def _is_tls_handshake(self, chunk: bytes) -> bool:
        """Check if chunk matches TLS Handshake Record header."""
        return len(chunk) >= 5 and chunk[0] == TLS_CONTENT_TYPE_HANDSHAKE

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        if not chunk:
            return chunk

        if self.mode == "alert_handshake_failure":
            return ALERT_HANDSHAKE_FAILURE

        if self.mode == "alert_bad_certificate":
            return ALERT_BAD_CERTIFICATE

        if self.mode == "alert_access_denied":
            return ALERT_ACCESS_DENIED

        if self.mode == "stall_handshake":
            if self._is_tls_handshake(chunk):
                await asyncio.sleep(self.stall_seconds)
                return None
            return chunk

        if self.mode == "corrupt_handshake":
            if self._is_tls_handshake(chunk) and len(chunk) > 10:
                buf = bytearray(chunk)
                # Invert bytes in the handshake body to invalidate cryptographic signatures
                for i in range(6, min(16, len(buf))):
                    buf[i] ^= 0xFF
                return bytes(buf)
            return chunk

        return chunk

    def get_attributes(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "stall_seconds": self.stall_seconds,
        }
