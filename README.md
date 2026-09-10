# FaultBox

FaultBox is a programmable network and protocol chaos injection proxy written in Python 3.12. It sits between client applications and upstream services such as databases, message brokers, and HTTP APIs to simulate network degradation, timeouts, rate limits, data corruption, and protocol errors.

## Why FaultBox

Distributed systems fail in unexpected ways. Networks drop packets, latency spikes without warning, and connections hang half-open. Testing how client code and circuit breakers handle these conditions is difficult when using basic mocks because mocks do not exercise operating system socket behavior.

FaultBox runs as a standalone process or Docker container. You point your application to the FaultBox listening port, and FaultBox forwards traffic to the real upstream service while applying configured chaos rules.

## Core Features

- Asynchronous TCP proxy built on Python `asyncio`.
- Bidirectional toxic chains: apply disruptions to incoming client requests, outgoing upstream responses, or both.
- Eight built-in toxic types:
  - Latency: adds configurable delays with optional jitter.
  - Bandwidth: throttles throughput using a token bucket rate limiter.
  - Reset Peer: abruptly terminates TCP connections with `SO_LINGER` set to 0.
  - Timeout: halts data transmission and leaves connections hanging.
  - Corrupt: mutates random payload bytes or bit values.
  - Slicer: breaks large payloads into small fragments with micro-delays.
  - Flapping: alternates between healthy and broken states on a fixed schedule.
  - HTTP Error: intercepts HTTP responses and overrides status codes (429, 500, 502, 503, 504).
- REST control plane: manage proxies, toxics, and metrics at runtime via HTTP endpoints.
- Terminal dashboard: live terminal interface using Rich to observe traffic and toggle toxics.
- Declarative scenarios: automate timed chaos experiments using YAML scenario files in CI/CD pipelines.

## Quickstart

### Installation

```bash
pip install faultbox
```

Or install from source with uv:

```bash
git clone https://github.com/alexandrmotologa/faultbox.git
cd faultbox
uv venv --python 3.12
uv pip install -e ".[dev]"
```

### Basic Usage

Start a proxy that listens on port 9000 and forwards traffic to an upstream Redis server on port 6379:

```bash
faultbox run --proxy "redis-test:9000->127.0.0.1:6379" --api --api-port 8474
```

Inject 250ms of latency with 50ms jitter on incoming requests:

```bash
faultbox toxic add redis-test latency --type latency --attributes '{"latency_ms": 250, "jitter_ms": 50}' --direction inbound
```

Clear all active toxics to restore normal traffic:

```bash
faultbox proxy reset redis-test
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md): Proxy design, pipeline mechanics, and socket management.
- [Toxic Reference](docs/TOXICS.md): Complete list of toxic attributes and configuration options.
- [Scenarios](docs/SCENARIOS.md): Declarative YAML chaos test syntax and CI/CD integration.
- [REST API](docs/API.md): Control plane endpoint specifications with request and response examples.

## License

MIT License. See [LICENSE](LICENSE) for details.
