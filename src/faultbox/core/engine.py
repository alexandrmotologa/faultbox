"""High-performance asyncio event loop configuration."""

from __future__ import annotations

import sys


def setup_event_loop() -> str:
    """
    Configure and install the most performant event loop available for the current OS.

    On POSIX platforms (Linux, macOS), attempts to use uvloop (libuv).
    On Windows, uses asyncio default.
    Returns the active engine name ('uvloop' or 'asyncio').
    """
    if sys.platform != "win32":
        try:
            import uvloop  # type: ignore[import-not-found]

            uvloop.install()
            return "uvloop"
        except ImportError:
            pass
    return "asyncio"
