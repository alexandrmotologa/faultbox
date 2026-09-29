# REST Control Plane API

The FaultBox REST Control Plane runs on port 8474 by default. It provides programmatic management of proxies, toxics, and traffic telemetry.

Interactive OpenAPI documentation is available in your browser at `http://127.0.0.1:8474/docs`.

## Endpoints

### Health Check

```http
GET /healthz
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "FaultBox Control Plane operational"
}
```

---

### List Proxies

```http
GET /proxies
```

**Response (200 OK):**
```json
[
  {
    "name": "redis-proxy",
    "listen": "0.0.0.0:9000",
    "upstream": "127.0.0.1:6379",
    "enabled": true,
    "stats": {
      "bytes_in": 1024,
      "bytes_out": 2048,
      "connections_total": 4,
      "connections_active": 1,
      "errors_total": 0,
      "throughput_in_kbps": 0.25,
      "throughput_out_kbps": 0.50,
      "uptime_seconds": 120.5
    },
    "toxics": []
  }
]
```

---

### Create Proxy

```http
POST /proxies
```

**Request Body:**
```json
{
  "name": "postgres-proxy",
  "listen": "0.0.0.0:9432",
  "upstream": "127.0.0.1:5432"
}
```

**Response (201 Created):**
```json
{
  "name": "postgres-proxy",
  "listen": "0.0.0.0:9432",
  "upstream": "127.0.0.1:5432",
  "enabled": true,
  "stats": { ... },
  "toxics": []
}
```

**cURL Example:**
```bash
curl -X POST http://127.0.0.1:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{"name": "postgres-proxy", "listen": "9432", "upstream": "127.0.0.1:5432"}'
```

---

### Get Proxy Details

```http
GET /proxies/{name}
```

**Response (200 OK):**
Returns the proxy configuration, real-time statistics, and active toxics.

---

### Delete Proxy

```http
DELETE /proxies/{name}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Proxy 'postgres-proxy' deleted."
}
```

---

### Pause / Resume Proxy

```http
POST /proxies/{name}/pause
POST /proxies/{name}/resume
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Proxy 'postgres-proxy' paused."
}
```

---

### Reset Proxy (Clear All Toxics)

```http
POST /proxies/{name}/reset
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "All toxics cleared for proxy 'postgres-proxy'."
}
```

---

### List Toxics on Proxy

```http
GET /proxies/{name}/toxics
```

**Response (200 OK):**
```json
[
  {
    "name": "latency-spike",
    "type": "latency",
    "direction": "inbound",
    "toxicity": 1.0,
    "enabled": true,
    "attributes": {
      "latency_ms": 250,
      "jitter_ms": 25,
      "distribution": "uniform"
    }
  }
]
```

---

### Add Toxic to Proxy

```http
POST /proxies/{name}/toxics
```

**Request Body:**
```json
{
  "name": "latency-spike",
  "type": "latency",
  "direction": "inbound",
  "toxicity": 1.0,
  "attributes": {
    "latency_ms": 250,
    "jitter_ms": 25
  },
  "enabled": true
}
```

**Response (201 Created):**
```json
{
  "name": "latency-spike",
  "type": "latency",
  "direction": "inbound",
  "toxicity": 1.0,
  "enabled": true,
  "attributes": {
    "latency_ms": 250,
    "jitter_ms": 25,
    "distribution": "uniform"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://127.0.0.1:8474/proxies/redis-proxy/toxics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rate-limiter",
    "type": "bandwidth",
    "direction": "both",
    "attributes": { "rate_kbps": 50 }
  }'
```

---

### Remove Toxic from Proxy

```http
DELETE /proxies/{name}/toxics/{toxic_name}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Toxic 'latency-spike' removed."
}
```

---

### Execute Chaos Scenario

```http
POST /scenarios/run
```

**Request Body:**
```json
{
  "yaml_content": "name: test-scenario\ntarget_proxy: order-api\nphases:\n  - time_seconds: 0.0\n    action: add_toxic\n    toxic:\n      name: lat\n      type: latency\n      attributes: { latency_ms: 100 }\nassertions:\n  - metric: errors_total\n    operator: '<='\n    threshold: 0\n"
}
```

**Response (200 OK):**
```json
{
  "name": "test-scenario",
  "total_phases": 1,
  "executed_phases": 1,
  "duration_seconds": 0.15,
  "events": [
    {
      "timestamp": 1727637000.0,
      "time_offset": 0.0,
      "action": "add_toxic",
      "target_proxy": "order-api",
      "success": true,
      "message": "Added toxic 'lat' (latency)"
    }
  ],
  "assertions": [
    {
      "metric": "errors_total",
      "operator": "<=",
      "threshold": 0.0,
      "actual_value": 0.0,
      "passed": true,
      "target_proxy": "order-api",
      "description": "",
      "message": "errors_total actual 0.0 <= threshold 0.0 -> PASS"
    }
  ],
  "assertions_passed": true,
  "success": true
}
```

---

### Export Topology

```http
GET /topology/export
```

**Response (200 OK):**
```json
{
  "version": "1.0",
  "proxies": [
    {
      "name": "web-front",
      "protocol": "tcp",
      "listen": "0.0.0.0:8080",
      "upstream": "127.0.0.1:80",
      "enabled": true,
      "stats": { ... },
      "toxics": [ ... ]
    }
  ]
}
```

---

### Import Topology

```http
POST /topology/import
```

**Request Body:**
```json
{
  "proxies": [
    {
      "name": "web-front",
      "protocol": "tcp",
      "listen": "0.0.0.0:8080",
      "upstream": "127.0.0.1:80",
      "enabled": true,
      "toxics": [
        {
          "name": "lat-toxic",
          "type": "latency",
          "direction": "both",
          "toxicity": 1.0,
          "attributes": { "latency_ms": 100 }
        }
      ]
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Successfully imported topology with 1 proxies."
}
```

---

### Prometheus Metrics

```http
GET /metrics
```

Returns Prometheus standard exposition format metrics for scrapers.

---

### WebSocket Live Telemetry

```http
WS /ws/telemetry
```

Streams real-time JSON snapshots of active proxy configurations and traffic statistics every 1.0s to connected browser clients.

