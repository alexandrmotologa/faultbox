# Architecture

FaultBox intercepts raw TCP socket traffic between client applications and upstream target services. This document outlines the connection lifecycle, toxic pipeline mechanics, and socket termination protocols.

## System Overview

FaultBox separates connection management into three decoupled layers:

1. **Proxy Listener**: An asynchronous TCP server bound to a local port.
2. **Bidirectional Pipe**: A streaming bridge pairing client and upstream sockets.
3. **Toxic Pipeline**: An ordered sequence of transformations applied to byte chunks.

```
+---------------+        +----------------------+        +-------------------+
|               |  TCP   |   FaultBox Listener  |  TCP   |                   |
| Client Socket | <----> |  (BidirectionalPipe) | <----> |  Upstream Service |
|               |        +----------------------+        |                   |
+---------------+                   |                    +-------------------+
                                    v
                         +----------------------+
                         |    Toxic Pipeline    |
                         |  - Latency           |
                         |  - Bandwidth Limit   |
                         |  - Bit Corrupt       |
                         |  - HTTP Error        |
                         +----------------------+
```

## Connection Lifecycle

When a client initiates a connection to a FaultBox listening port:

1. The listener invokes `asyncio.open_connection` to reach the configured upstream host and port.
2. If the upstream service is unreachable, FaultBox immediately terminates the client socket and logs an error in its traffic statistics.
3. If the upstream connection succeeds, FaultBox instantiates a `BidirectionalPipe` and starts two asynchronous tasks:
   - **Inbound Task**: Reads from the client socket, applies inbound toxics, and writes to the upstream socket.
   - **Outbound Task**: Reads from the upstream socket, applies outbound toxics, and writes to the client socket.
4. When either stream reaches end-of-file (EOF) or an unrecoverable socket error occurs, FaultBox cancels the opposing task, closes both writers, and decrements its active connection counter.

## Pipeline Mechanics

The toxic pipeline holds an ordered list of `BaseToxic` instances. Each toxic exposes a `transform` method with the following signature:

```python
async def transform(self, chunk: bytes, context: StreamContext) -> bytes | list[bytes] | None
```

The pipeline executes transformations in order:

- If a toxic returns a `bytes` object, the modified bytes pass to the subsequent toxic in the chain.
- If a toxic returns a `list[bytes]` (such as `SlicerToxic`), FaultBox processes each slice through downstream toxics and flushes them to the destination socket.
- If a toxic returns `None` (such as packet drop or timeout), processing for that chunk halts immediately and no bytes reach the destination socket.
- If a toxic raises `ConnectionResetError` (such as `ResetPeerToxic`), the pipe catches the exception, configures `SO_LINGER`, and terminates the socket.

## Socket Termination Protocol

Standard TCP closures send a `FIN` packet, allowing the operating system to flush buffered data gracefully. To simulate network hardware failures or abrupt process crashes, FaultBox can force a hard `TCP RST` using the `SO_LINGER` socket option:

```python
import socket
import struct

linger = struct.pack("ii", 1, 0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
sock.close()
```

Setting `l_onoff=1` and `l_linger=0` discards unsent buffer contents and transmits an immediate `RST` flag to the peer.

## Control Plane Isolation

The REST control plane runs as an independent `uvicorn` instance within the same `asyncio` event loop. API operations modify in-memory proxy pipelines using thread-safe asynchronous locks. Modifying or clearing toxics takes effect immediately on subsequent socket reads without needing to restart active listeners.
