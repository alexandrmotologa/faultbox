# Python Microservices Resilience Demo

This example shows how to use FaultBox to test backend microservices against real-world database failovers and network latency.

## Prerequisites

1. Run the FaultBox server:
   ```bash
   faultbox server --host 0.0.0.0 --port 8474
   ```

2. Start a PostgreSQL database on `127.0.0.1:5432` or via Docker Compose:
   ```bash
   docker compose -f ../../deploy/docker-compose.chaos.yml up postgres-upstream -d
   ```

## Running the Demo

Run the resilience application:
```bash
python app.py
```

## Running the Automated Chaos Scenario

Execute the declarative chaos scenario with CI assertions:
```bash
faultbox scenario run scenario.yaml
```
