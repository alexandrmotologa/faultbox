# Python Client SDK & Pytest Integration

FaultBox provides synchronous and asynchronous Python clients for programmatic chaos injection in test suites and automation scripts.

## Installation

The client is included with the `faultbox` package:

```bash
pip install faultbox
```

## Quick Example (Synchronous)

```python
from faultbox.client import FaultBoxClient

client = FaultBoxClient("http://127.0.0.1:8474")

# Add a 200ms latency toxic only for the duration of this block
with client.toxic("redis-proxy", "latency", latency_ms=200):
    response = redis_client.get("user:123")
    assert response is not None

# Outside the block, the proxy returns to pristine state automatically
```

## Context Managers

### 1. Scoped Disruption: `client.toxic(...)`

Injects a toxic on block entry and cleans it up upon exiting the block, even if an assertion or exception is raised:

```python
with client.toxic(
    proxy="order-service",
    toxic_type="http_error",
    status_code=503,
    status_message="Service Unavailable",
):
    # Verify circuit breaker opens
    with pytest.raises(ServiceUnavailableError):
        order_client.place_order(order_data)
```

### 2. Ephemeral Test Proxy: `client.temporary_proxy(...)`

Registers a proxy for the duration of a test and destroys it on exit:

```python
with client.temporary_proxy("test-db", "9432", "127.0.0.1:5432") as proxy:
    run_database_resilience_test(f"127.0.0.1:{proxy['listen'].split(':')[-1]}")
```

### 3. Connection Freeze: `client.paused(...)`

Temporarily rejects new connections to test connection retry loops and failover logic:

```python
with client.paused("rabbitmq-proxy"):
    # Verify message producer queues messages locally
    producer.send_message({"task": "process_image"})
```

## Asynchronous Client

For codebases using `asyncio` or `pytest-asyncio`:

```python
import pytest
from faultbox.client import AsyncFaultBoxClient


@pytest.mark.asyncio
async def test_async_service_retry():
    async with AsyncFaultBoxClient("http://127.0.0.1:8474") as client:
        async with client.toxic("http-api", "bandwidth", rate_kbps=20):
            response = await fetch_large_dataset()
            assert response.status == 200
```

## Pytest Fixture Plugin

FaultBox automatically registers a Pytest plugin entrypoint when installed. The fixtures `faultbox_client` and `async_faultbox_client` are available in any test file:

```python
def test_cache_miss_fallback(faultbox_client):
    with faultbox_client.toxic("cache-proxy", "timeout", timeout_ms=500):
        val = my_service.fetch_with_fallback("key-1")
        assert val == "fallback_value"
```

Configure the control plane URL by setting the `FAULTBOX_API_URL` environment variable if not using the default `http://127.0.0.1:8474`.
