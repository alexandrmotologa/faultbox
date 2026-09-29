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

## Quality Gates & Resilience SLA Assertions

FaultBox scenarios support automated **Quality Gate Assertions**. You can define SLA thresholds directly in your scenario file. When running via `faultbox scenario run`, FaultBox evaluates every assertion, renders a structured verification report, and exits with code `0` (PASS) or `1` (FAIL), providing an instant pass/fail gate for CI/CD pipelines.

```yaml
name: "resilience-gate"
description: "Injects latency and validates error budgets during chaos"
target_proxy: "api-gateway"

phases:
  - time_seconds: 0.0
    action: "add_toxic"
    toxic:
      name: "controlled-jitter"
      type: "latency"
      attributes:
        latency_ms: 150

  - time_seconds: 5.0
    action: "reset"

assertions:
  - metric: "errors_total"
    operator: "<="
    threshold: 25
    description: "Maximum allowable errors during chaos injection"

  - metric: "error_rate"
    operator: "<"
    threshold: 0.05
    description: "Chaos error rate SLA (< 5%)"

  - metric: "connections_active"
    operator: "=="
    threshold: 0
    description: "All client connections cleanly drained"
```

### Supported Metrics

| Metric | Scope | Description |
|---|---|---|
| `errors_total` | Scenario Delta | Total socket/proxy errors incurred during scenario execution |
| `errors_cumulative` | Cumulative | Lifetime errors recorded on target proxy |
| `error_rate` | Scenario Delta | Ratio of delta errors to delta connections (`0.0` to `1.0`) |
| `bytes_in` / `bytes_out` | Scenario Delta | Total inbound/outbound payload bytes during scenario |
| `bytes_total` | Scenario Delta | Total combined network throughput during scenario |
| `connections_total` | Scenario Delta | Number of new client connections opened during scenario |
| `connections_active` | Point-in-time | Number of active client connections remaining at scenario end |

### Comparison Operators

- `<` / `lt` (Less than)
- `<=` / `le` (Less than or equal)
- `>` / `gt` (Greater than)
- `>=` / `ge` (Greater than or equal)
- `==` / `=` (Equal)
- `!=` / `ne` (Not equal)

## Executing Scenarios

### Via CLI

Run a scenario locally or in CI pipelines:

```bash
faultbox scenario run scenarios/resilience-gate.yaml
```

If any assertion fails or an error occurs during execution, `faultbox scenario run` prints a highlighted Rich SLA table and terminates with **exit code 1**.

### Combined With `faultbox run`

Launch proxy listeners and immediately execute a scenario file:

```bash
faultbox run \
  --proxy "app-proxy:9000->127.0.0.1:8080" \
  --scenario scenarios/slow-3g-mobile.yaml
```

### In Continuous Integration (CI)

In GitHub Actions or GitLab CI, validate system resilience against automated quality gates:

```yaml
# GitHub Actions snippet
- name: Run FaultBox Chaos Quality Gate
  run: |
    faultbox scenario run scenarios/resilience-gate.yaml
```

