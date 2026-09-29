"""Microservice Resilience Demo with FaultBox.

This script demonstrates an application communicating with an upstream database
through a FaultBox chaos proxy, using retry policies and circuit breaker patterns.
"""

from __future__ import annotations

import asyncio
import time

from faultbox.client import FaultBoxClient


async def run_resilience_demo() -> None:
    print("=" * 60)
    print("FaultBox Python Microservice Resilience Demo")
    print("=" * 60)

    # 1. Connect to FaultBox Control Plane
    client = FaultBoxClient(base_url="http://localhost:8474")

    # 2. Register a database proxy (e.g. PostgreSQL)
    proxy_name = "demo-postgres"
    print(f"\n[1] Registering chaos proxy '{proxy_name}'...")
    try:
        await client.create_proxy(
            name=proxy_name,
            listen="127.0.0.1:15432",
            upstream="127.0.0.1:5432",
            protocol="tcp",
        )
        print("    Proxy listening on 127.0.0.1:15432 -> upstream 127.0.0.1:5432")
    except Exception as exc:
        print(f"    Proxy already exists or created: {exc}")

    # 3. Inject a Waveform Latency Toxic (simulating periodic latency spikes)
    print("\n[2] Attaching waveform latency toxic (100ms base + 300ms sine wave)...")
    await client.add_toxic(
        proxy_name=proxy_name,
        name="sine-latency",
        toxic_type="waveform_latency",
        direction="both",
        attributes={
            "base_latency_ms": 100,
            "amplitude_ms": 300,
            "period_sec": 10.0,
            "waveform": "sine",
        },
    )

    # 4. Inject a PostgreSQL Protocol Fault (simulating failover admin_shutdown)
    print("\n[3] Attaching PostgreSQL wire fault (SQLSTATE 57P01 admin shutdown)...")
    await client.add_toxic(
        proxy_name=proxy_name,
        name="pg-failover",
        toxic_type="postgres_fault",
        direction="inbound",
        toxicity=0.3,  # 30% failure rate
        attributes={
            "sqlstate": "57P01",
            "message": "database system is shutting down",
            "severity": "FATAL",
        },
    )

    # 5. Simulate client queries with retry logic
    print("\n[4] Executing 10 client transactions with retry loop...")
    for i in range(1, 11):
        start = time.perf_counter()
        success = False
        attempts = 0

        while attempts < 3 and not success:
            attempts += 1
            try:
                # In real code: asyncpg.connect("127.0.0.1", 15432)
                # Here we simulate network connection to the proxy
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", 15432),
                    timeout=2.0,
                )
                writer.write(b"QSELECT * FROM orders WHERE status = 'pending';\x00")
                await writer.drain()

                # Read response (or simulated fault)
                data = await asyncio.wait_for(reader.read(1024), timeout=2.0)
                writer.close()
                await writer.wait_closed()

                if data.startswith(b"E"):
                    # PostgreSQL ErrorResponse detected
                    raise RuntimeError(
                        f"PostgreSQL Wire Error: {data.decode('latin1', errors='ignore')}"
                    )

                success = True
            except Exception as err:
                if attempts < 3:
                    await asyncio.sleep(0.1 * (2**attempts))  # Exponential backoff
                else:
                    elapsed = (time.perf_counter() - start) * 1000
                    print(
                        f"    Transaction #{i:02d}: FAILED after {attempts} attempts ({elapsed:.1f}ms) -> {err}"
                    )

        if success:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"    Transaction #{i:02d}: SUCCESS in {attempts} attempt(s) ({elapsed:.1f}ms)")

        await asyncio.sleep(0.3)

    # 6. Clean up toxics
    print("\n[5] Resetting proxy toxics...")
    await client.reset_proxy(proxy_name)
    print("    Proxy clean. Chaos test complete.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(run_resilience_demo())
