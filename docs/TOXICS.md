# Toxic Plugin Reference

Toxics represent chaos rules injected into the data stream between a client and an upstream service. FaultBox includes eight built-in toxic types.

## General Configuration

Every toxic accepts four common attributes:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | string | required | Unique identifier within the proxy pipeline |
| `type` | string | required | Plugin type name (e.g. `latency`, `bandwidth`) |
| `direction` | string | `both` | Target direction: `inbound`, `outbound`, or `both` |
| `toxicity` | float | `1.0` | Probability of applying the toxic (value between `0.0` and `1.0`) |
| `enabled` | boolean | `true` | Whether the toxic actively modifies traffic |

---

## 1. Latency (`latency`)

Adds artificial delays to passing byte chunks.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `latency_ms` | integer | `200` | Base delay in milliseconds |
| `jitter_ms` | integer | `0` | Variance applied to the delay |
| `distribution` | string | `uniform` | Random distribution: `uniform` or `normal` |

### Example

```bash
faultbox toxic add my-proxy lat-1 --type latency --attributes '{"latency_ms": 250, "jitter_ms": 50}'
```

---

## 2. Bandwidth (`bandwidth`)

Throttles stream throughput to a maximum rate using a token bucket rate limiter.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rate_kbps` | integer | `100` | Maximum throughput ceiling in kilobytes per second |

### Example

```bash
faultbox toxic add my-proxy slow-pipe --type bandwidth --attributes '{"rate_kbps": 30}' --direction inbound
```

---

## 3. Reset Peer (`reset_peer`)

Abruptly tears down the TCP connection using `SO_LINGER=0`, issuing an immediate `TCP RST` packet.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `byte_offset` | integer | `0` | Terminate after transmitting this total number of bytes |
| `timeout_ms` | integer | `0` | Delay in milliseconds before terminating the connection |

### Example

```bash
faultbox toxic add my-proxy drop-conn --type reset_peer --attributes '{"byte_offset": 512}'
```

---

## 4. Timeout (`timeout`)

Halts data transmission. If `timeout_ms` is zero, the socket hangs indefinitely until the client times out. If non-zero, it drops packets after the delay.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `timeout_ms` | integer | `0` | Duration to wait before dropping the packet |

### Example

```bash
faultbox toxic add my-proxy blackhole --type timeout --attributes '{"timeout_ms": 1000}'
```

---

## 5. Corrupt (`corrupt`)

Mutates payload contents by modifying random bytes or flipping individual bit flags.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rate` | float | `0.05` | Fraction of payload bytes to modify (e.g. `0.05` is 5%) |
| `mode` | string | `bitflip` | Mutation mode: `bitflip`, `zero`, or `random_byte` |

### Example

```bash
faultbox toxic add my-proxy bit-mangle --type corrupt --attributes '{"rate": 0.1, "mode": "bitflip"}'
```

---

## 6. Slicer (`slicer`)

Splits large chunks into smaller byte slices with micro-delays between transmissions. Useful for testing framing logic and socket reassembly.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `slice_size` | integer | `64` | Maximum byte size per slice |
| `delay_ms` | integer | `10` | Sleep duration between consecutive slice transmissions |

### Example

```bash
faultbox toxic add my-proxy fragmenter --type slicer --attributes '{"slice_size": 16, "delay_ms": 5}'
```

---

## 7. Flapping (`flapping`)

Periodically alternates between healthy operation and failed states to simulate unstable dependencies and test retry policies.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `up_duration_sec` | float | `10.0` | Duration of the operational phase in seconds |
| `down_duration_sec` | float | `5.0` | Duration of the degraded phase in seconds |
| `down_action` | string | `drop` | Failure mode during the down phase: `drop` or `reset` |

### Example

```bash
faultbox toxic add my-proxy flap --type flapping --attributes '{"up_duration_sec": 8.0, "down_duration_sec": 4.0, "down_action": "reset"}'
```

---

## 8. HTTP Error (`http_error`)

Inspects HTTP response streams and substitutes the original status line and body with a synthetic error response.

### Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `status_code` | integer | `500` | HTTP response code (e.g. 429, 500, 502, 503) |
| `status_message` | string | `Internal Server Error` | HTTP status reason string |
| `body` | string | `{"error": "FaultBox Chaos Injected"}` | Response payload string |
| `content_type` | string | `application/json` | Content-Type header value |

### Example

```bash
faultbox toxic add my-proxy rate-limit --type http_error --direction outbound --attributes '{"status_code": 429, "status_message": "Too Many Requests", "body": "{\"error\":\"rate_limited\"}"}'
```
