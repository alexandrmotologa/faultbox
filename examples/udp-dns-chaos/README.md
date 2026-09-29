# UDP & Datagram Chaos Testing with FaultBox

This example demonstrates how FaultBox intercepts and injects chaos into connectionless UDP traffic, such as DNS queries, Game server UDP state sync, or Syslog / StatsD collectors.

## Features Covered
- `packet_drop`: Simulating packet loss rates and burst drops.
- `packet_duplicate`: Simulating multi-path network packet duplication.
- `packet_reorder`: Simulating jitter and out-of-order delivery.

## Running the Demo

1. Start FaultBox:
   ```bash
   faultbox server --host 0.0.0.0 --port 8474
   ```

2. Run the UDP test script:
   ```bash
   python dns_chaos_test.py
   ```
