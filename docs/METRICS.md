# Prometheus Metrics & Observability

FaultBox exposes real-time operational telemetry formatted for Prometheus scrapers at `GET /metrics`.

## Endpoint

```http
GET /metrics
```

**Content-Type**: `text/plain; version=0.0.4; charset=utf-8`

## Metrics Reference

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `faultbox_bytes_total` | counter | `proxy`, `direction` | Total data volume transferred (`inbound` or `outbound`) |
| `faultbox_connections_active` | gauge | `proxy` | Number of currently open TCP sockets |
| `faultbox_connections_total` | counter | `proxy` | Lifetime total of connections accepted |
| `faultbox_errors_total` | counter | `proxy` | Socket and pipeline exceptions encountered |
| `faultbox_throughput_kbps` | gauge | `proxy`, `direction` | Rolling throughput in kilobytes per second |
| `faultbox_proxy_enabled` | gauge | `proxy` | Current operational state (`1` active, `0` paused) |
| `faultbox_toxics_configured` | gauge | `proxy` | Total count of toxics attached to the proxy pipeline |

## Example Output

```text
# HELP faultbox_bytes_total Total bytes transferred by proxy and direction.
# TYPE faultbox_bytes_total counter
faultbox_bytes_total{proxy="redis-chaos",direction="inbound"} 1048576
faultbox_bytes_total{proxy="redis-chaos",direction="outbound"} 2097152

# HELP faultbox_connections_active Number of currently active TCP connections.
# TYPE faultbox_connections_active gauge
faultbox_connections_active{proxy="redis-chaos"} 4

# HELP faultbox_throughput_kbps Rolling throughput calculation in kilobytes per second.
# TYPE faultbox_throughput_kbps gauge
faultbox_throughput_kbps{proxy="redis-chaos",direction="inbound"} 124.50
faultbox_throughput_kbps{proxy="redis-chaos",direction="outbound"} 248.10

# HELP faultbox_toxics_configured Number of toxics attached to the proxy pipeline.
# TYPE faultbox_toxics_configured gauge
faultbox_toxics_configured{proxy="redis-chaos"} 2
```

## Prometheus Configuration

Add FaultBox as a scrape target in your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "faultbox"
    scrape_interval: 5s
    static_configs:
      - targets: ["127.0.0.1:8474"]
```
