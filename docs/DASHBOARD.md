# Embedded Web UI Dashboard

FaultBox includes an embedded single-page browser dashboard served directly by the FastAPI control plane. It provides real-time cluster traffic gauges, proxy controls, and interactive toxic management without installing extra dependencies.

## Accessing the Dashboard

When FaultBox is running with the control plane enabled:

```bash
faultbox run --proxy "redis:9000->127.0.0.1:6379" --api --api-port 8474
```

Open your web browser and navigate to:

```
http://127.0.0.1:8474/
```

Or:

```
http://127.0.0.1:8474/ui
```

## Features

### 1. Cluster Traffic KPIs
The top metric cards aggregate cluster-wide statistics in real time:
- **Active Proxies**: Total count of registered proxy listening routes.
- **Active Connections**: Total open TCP sockets currently transferring data.
- **Throughput In / Out**: Real-time throughput rates measured in KB/s.
- **Total Errors**: Cumulative count of socket resets and upstream connection failures.

### 2. Live Telemetry Streaming
The dashboard establishes a WebSocket connection to `/ws/telemetry` upon loading. Proxy states, throughput figures, and toxic badges refresh every second. If WebSockets are blocked or disconnected, the dashboard switches to an HTTP polling fallback.

### 3. Interactive Proxy Management
- **New Proxy**: Create proxy listening routes by specifying name, local port, and upstream destination.
- **Pause / Resume**: Freeze socket acceptance without terminating the FaultBox process.
- **Reset**: Remove all active toxics on a proxy with a single click to restore pristine conditions.
- **Delete**: Shut down and unregister proxies dynamically.

### 4. Direct Toxic Injection
Click **+ Toxic** on any proxy to open the toxic attachment modal:
- Choose from all nine toxic plugins (Latency, Waveform Latency, Bandwidth, Reset Peer, Timeout, Corrupt, Slicer, Flapping, HTTP Error).
- Configure target direction (`inbound`, `outbound`, or `both`).
- Adjust toxicity probability (from `0.0` to `1.0`).
- Pre-filled JSON attribute templates ensure quick parameter modification.
- Individual toxics can be disabled or deleted directly from the active badges list.
