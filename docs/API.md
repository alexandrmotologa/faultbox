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
