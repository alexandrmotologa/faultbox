"""Bidirectional streaming pipe between client and upstream sockets."""

from __future__ import annotations

import asyncio
import socket
import struct
from typing import TYPE_CHECKING

from faultbox.toxics.base import StreamContext, ToxicDirection

if TYPE_CHECKING:
    from faultbox.core.pipeline import ToxicPipeline
    from faultbox.core.stats import TrafficStats


class BidirectionalPipe:
    """Streams data bidirectionally between client and upstream through a toxic pipeline."""

    def __init__(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
        upstream_reader: asyncio.StreamReader,
        upstream_writer: asyncio.StreamWriter,
        pipeline: ToxicPipeline,
        stats: TrafficStats,
        proxy_name: str,
        buffer_size: int = 65536,
    ) -> None:
        self.client_reader = client_reader
        self.client_writer = client_writer
        self.upstream_reader = upstream_reader
        self.upstream_writer = upstream_writer
        self.pipeline = pipeline
        self.stats = stats
        self.proxy_name = proxy_name
        self.buffer_size = buffer_size

        client_peer = client_writer.get_extra_info("peername")
        upstream_peer = upstream_writer.get_extra_info("peername")
        self.client_addr = f"{client_peer[0]}:{client_peer[1]}" if client_peer else "unknown"
        self.upstream_addr = (
            f"{upstream_peer[0]}:{upstream_peer[1]}" if upstream_peer else "unknown"
        )

        self._inbound_context = StreamContext(
            proxy_name=proxy_name,
            direction=ToxicDirection.INBOUND,
            client_addr=self.client_addr,
            upstream_addr=self.upstream_addr,
        )
        self._outbound_context = StreamContext(
            proxy_name=proxy_name,
            direction=ToxicDirection.OUTBOUND,
            client_addr=self.client_addr,
            upstream_addr=self.upstream_addr,
        )

        self._tasks: list[asyncio.Task[None]] = []
        self._is_closed = False

    async def run(self) -> None:
        """Start bidirectional forwarding tasks and wait until completion or error."""
        self.stats.record_connection_open()

        await self.pipeline.notify_connect(self._inbound_context)
        await self.pipeline.notify_connect(self._outbound_context)

        inbound_task = asyncio.create_task(
            self._forward(
                self.client_reader,
                self.upstream_writer,
                self._inbound_context,
                is_inbound=True,
            ),
            name=f"{self.proxy_name}-inbound-{self.client_addr}",
        )
        outbound_task = asyncio.create_task(
            self._forward(
                self.upstream_reader,
                self.client_writer,
                self._outbound_context,
                is_inbound=False,
            ),
            name=f"{self.proxy_name}-outbound-{self.client_addr}",
        )
        self._tasks = [inbound_task, outbound_task]

        try:
            done, pending = await asyncio.wait(
                self._tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        finally:
            await self.close()

    async def _forward(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        context: StreamContext,
        is_inbound: bool,
    ) -> None:
        """Stream chunks from reader to writer via the toxic pipeline."""
        try:
            while not reader.at_eof() and not self._is_closed:
                chunk = await reader.read(self.buffer_size)
                if not chunk:
                    break

                context.bytes_streamed += len(chunk)
                if is_inbound:
                    self.stats.record_bytes_in(len(chunk))
                else:
                    self.stats.record_bytes_out(len(chunk))

                # Pass chunk through toxic pipeline
                transformed = await self.pipeline.process(chunk, context)

                if transformed is not None:
                    if isinstance(transformed, list):
                        for sub_chunk in transformed:
                            if sub_chunk:
                                writer.write(sub_chunk)
                                await writer.drain()
                    elif len(transformed) > 0:
                        writer.write(transformed)
                        await writer.drain()

        except ConnectionResetError:
            self.stats.record_error()
            self._force_rst(writer)
            raise
        except (asyncio.CancelledError, BrokenPipeError, ConnectionAbortedError):
            pass
        except Exception:
            self.stats.record_error()
            raise

    def _force_rst(self, writer: asyncio.StreamWriter) -> None:
        """Force TCP RST by configuring SO_LINGER to zero before closing."""
        sock = writer.get_extra_info("socket")
        if sock is not None:
            try:
                linger = struct.pack("ii", 1, 0)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
            except Exception:
                pass

    async def close(self) -> None:
        """Close both sides of the pipe and notify toxics."""
        if self._is_closed:
            return
        self._is_closed = True

        for task in self._tasks:
            if not task.done():
                task.cancel()

        await self.pipeline.notify_close(self._inbound_context)
        await self.pipeline.notify_close(self._outbound_context)

        for writer in (self.client_writer, self.upstream_writer):
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception:
                pass

        self.stats.record_connection_close()
