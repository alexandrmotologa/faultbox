# Declarative Scenarios

FaultBox supports declarative YAML scenarios for orchestrating timed chaos sequences. These files allow developers and automated CI pipelines to reproduce complex network failure patterns repeatedly.

## File Structure

A scenario file contains metadata, an optional default target proxy, and an ordered list of phases:

```yaml
name: "slow-3g-simulation"
description: "Throttles throughput and introduces high mobile network latency"
target_proxy: "mobile-api"
phases:
  - time_seconds: 0.0
    action: "add_toxic"
    toxic:
      name: "3g-latency"
      type: "latency"
      attributes:
        latency_ms: 300
        jitter_ms: 50

  - time_seconds: 10.0
    action: "add_toxic"
    toxic:
      name: "3g-bandwidth"
      type: "bandwidth"
      attributes:
        rate_kbps: 45

  - time_seconds: 25.0
    action: "reset"
```

## Phase Actions

The `action` field supports five operations:

### 1. `add_toxic`
Attaches a new toxic to the target proxy pipeline.
Requires a nested `toxic` object containing `name`, `type`, and optional `attributes`.

### 2. `remove_toxic`
Removes a toxic from the pipeline by identifier.
Requires `toxic_name` (or `toxic.name`).

### 3. `reset`
Clears all active toxics from the target proxy pipeline.

### 4. `pause`
Stops the target proxy from accepting new connections.

### 5. `resume`
Restores the target proxy to operational state.

## Executing Scenarios

### Via CLI

Run a scenario locally during application testing:

```bash
faultbox scenario run scenarios/flapping-service.yaml
```

### Combined With `faultbox run`

Launch the proxy listeners and immediately execute a scenario file:

```bash
faultbox run \
  --proxy "app-proxy:9000->127.0.0.1:8080" \
  --scenario scenarios/slow-3g-mobile.yaml
```

### In Continuous Integration (CI)

In a GitHub Actions or GitLab CI job, place FaultBox in the background, run integration tests against the proxy port, and observe how resilience mechanisms respond:

```bash
# 1. Start FaultBox proxy and execute the chaos schedule
faultbox run \
  --proxy "service:9000->service-internal:8000" \
  --scenario scenarios/cascading-failure.yaml \
  --api-port 8474 &

# 2. Execute test suite against localhost:9000
pytest tests/resilience/
```
