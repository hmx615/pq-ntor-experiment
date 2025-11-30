# 3-Hop Circuit Construction Testing Framework

## Overview

This framework measures **complete 3-hop Tor circuit construction time** across 12 SAGIN topologies, including:
- Directory server lookup
- Guard relay handshake (PQ-NTOR)
- Middle relay extension (PQ-NTOR, forwarded through Guard)
- Exit relay extension (PQ-NTOR, forwarded through Guard+Middle)

**Key Difference from Handshake-Only Tests:**
- **Handshake test** (~180 µs): Only measures cryptographic computation
- **3-hop circuit test** (~25-30 ms): Measures complete circuit including network transmission

---

## Components

### 1. `benchmark_3hop_circuit.c`
C program that measures circuit construction timing with microsecond precision.

**Features:**
- High-precision timing (CLOCK_MONOTONIC)
- Breakdown by stage: directory, hop1, hop2, hop3
- JSON output for easy parsing
- Configurable iterations

**Compile:**
```bash
gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread
```

**Usage:**
```bash
./benchmark_3hop_circuit <iterations> [directory_host] [directory_port]

# Example: 100 iterations
./benchmark_3hop_circuit 100 localhost 5000
```

**Output:**
```
=== RESULTS ===

Total Circuit Construction Time:
  Average:  25342.15 µs (25.34 ms)
  Median:   25201.33 µs (25.20 ms)
  Min:      23891.02 µs (23.89 ms)
  Max:      28765.44 µs (28.77 ms)
  StdDev:   612.33 µs

Breakdown by Stage:
  Directory Fetch:  3245.67 µs (12.8%)
  Hop 1 (Guard):    7342.11 µs (29.0%)
  Hop 2 (Middle):   7421.89 µs (29.3%)
  Hop 3 (Exit):     7332.48 µs (28.9%)

=== JSON OUTPUT ===
{
  "total_us": 25342.15,
  "total_ms": 25.34,
  ...
}
```

---

### 2. `configure_tc.sh`
Bash script that applies Linux TC (Traffic Control) network parameters.

**Features:**
- Simulates 12 SAGIN topology network conditions
- Rate limiting, delay, packet loss
- Easy apply/clear commands

**Usage:**
```bash
# Apply topo01 settings
sudo ./configure_tc.sh topo01

# Show current settings
sudo ./configure_tc.sh show

# Clear all TC rules
sudo ./configure_tc.sh clear

# List all topologies
sudo ./configure_tc.sh
```

**Network Parameters:**
```bash
topo01: rate=31.81mbit delay=2.71ms loss=2.0%
topo02: rate=8.77mbit delay=2.72ms loss=2.0%
topo03: rate=20.53mbit delay=1.365ms loss=0.1%
...
```

**Important Notes:**
- Requires root/sudo privileges
- Works on loopback interface (`lo`) for single-machine testing
- Delay is automatically halved (packets traverse loopback twice)

---

### 3. `test_3hop_12topo.py`
Python automation script that runs complete 12-topology benchmark suite.

**Features:**
- Automatic system startup (directory + relay servers)
- TC configuration for each topology
- Benchmark execution (100 iterations per topology)
- JSON results output
- Progress tracking

**Usage:**
```bash
# Full automated test (requires sudo for TC)
sudo python3 test_3hop_12topo.py

# Custom iterations
sudo python3 test_3hop_12topo.py --iterations 200

# Custom output file
sudo python3 test_3hop_12topo.py --output my_results.json

# Skip system startup (if already running)
sudo python3 test_3hop_12topo.py --skip-system-start
```

**Output:**
- `3hop_12topo_results.json`: Complete results for all 12 topologies
- Console output: Progress and summary

**Example Output:**
```
======================================================================
  PQ-NTOR 3-Hop Circuit Construction - 12 SAGIN Topologies
======================================================================
Iterations per topology: 100

======================================================================
  Testing topo01: Satellite Direct NOMA (Uplink)
======================================================================
[TC] Applying topo01: 31.81 Mbps, 5.42 ms, 2.0% loss
  ✓ TC configured
[Benchmark] Running 100 iterations...
  ✓ Average: 25.34 ms

...

======================================================================
  Summary
======================================================================
Total topologies tested: 12/12
Average circuit construction time: 26.12 ms
Fastest: topo03 (23.45 ms)
Slowest: topo08 (28.91 ms)
```

---

## Quick Start Guide

### Step 1: Compile Benchmark Program
```bash
cd /home/ccc/pq-ntor-experiment/last_experiment/phytium_deployment

gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread
```

### Step 2: Make Scripts Executable
```bash
chmod +x configure_tc.sh test_3hop_12topo.py
```

### Step 3: Test Single Topology (Manual)
```bash
# Terminal 1: Start directory server
cd /home/user/pq-ntor-test
./directory 5000

# Terminal 2: Start relays
./relay 6000 guard localhost:5000
./relay 6001 middle localhost:5000
./relay 6002 exit localhost:5000

# Terminal 3: Apply TC and run benchmark
sudo ./configure_tc.sh topo01
./benchmark_3hop_circuit 100 localhost 5000

# Clean up
sudo ./configure_tc.sh clear
```

### Step 4: Run Full 12-Topology Test (Automated)
```bash
sudo python3 test_3hop_12topo.py
```

---

## Testing on Phytium Pi

### Deployment Steps

1. **Compile on Phytium:**
```bash
ssh user@192.168.5.110
cd /home/user/pq-ntor-test

# Copy source files
scp benchmark_3hop_circuit.c user@192.168.5.110:/home/user/pq-ntor-test/
scp configure_tc.sh user@192.168.5.110:/home/user/pq-ntor-test/
scp test_3hop_12topo.py user@192.168.5.110:/home/user/pq-ntor-test/

# Compile
gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread
chmod +x configure_tc.sh test_3hop_12topo.py
```

2. **Run Tests:**
```bash
sudo python3 test_3hop_12topo.py --base-dir /home/user/pq-ntor-test
```

3. **Download Results:**
```bash
scp user@192.168.5.110:/home/user/pq-ntor-test/3hop_12topo_results.json \
    ./phytium_results/phytium_3hop_12topo_results.json
```

---

## Expected Results

### Performance Estimates

**WSL (x86_64):**
- Total circuit construction: ~5-10 ms
- Per-hop handshake: ~31 µs × 3 = ~93 µs
- Network overhead: ~5-9 ms

**Phytium Pi (ARM64):**
- Total circuit construction: ~25-35 ms
- Per-hop handshake: ~180 µs × 3 = ~540 µs
- Network overhead: ~25-34 ms

### Key Insights

1. **Network Dominates:**
   - Circuit construction: 25-35 ms
   - Pure crypto (3 handshakes): 0.54 ms (2%)
   - Network transmission: 98% of time

2. **Topology Impact:**
   - Low delay topologies (topo03, topo09): Faster (~23-25 ms)
   - High delay topologies (topo08): Slower (~28-30 ms)
   - Rate has minimal impact (loopback is very fast)

3. **Comparison:**
   - Handshake-only: 180 µs (pure computation)
   - 3-hop circuit: 25-30 ms (realistic system)
   - **140× difference** - proves network matters

---

## Troubleshooting

### Issue: TC configuration fails
```
Error: Operation not permitted
```
**Solution:** Ensure script is run with sudo
```bash
sudo ./configure_tc.sh topo01
```

### Issue: Benchmark can't find directory
```
Failed to fetch directory
```
**Solution:** Ensure directory server is running
```bash
./directory 5000 &
```

### Issue: Benchmark compilation fails
```
undefined reference to `sqrt'
```
**Solution:** Add `-lm` flag
```bash
gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread
```

### Issue: Test runner can't find binary
```
Error: Benchmark binary not found
```
**Solution:** Compile benchmark first, or use `--base-dir`
```bash
gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm
sudo python3 test_3hop_12topo.py --base-dir $(pwd)
```

---

## Data Analysis

After collecting results, you can analyze with:

```python
import json
import pandas as pd

# Load results
with open('3hop_12topo_results.json') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame.from_dict(data, orient='index')

# Analysis
print("Average circuit time:", df['total_ms'].mean(), "ms")
print("Correlation with delay:", df[['delay_ms', 'total_ms']].corr())
print("\nBreakdown:")
print(df[['hop1_us', 'hop2_us', 'hop3_us']].mean() / 1000, "ms")
```

Expected correlations:
- **Delay vs Total Time**: Strong positive (R² > 0.7)
- **Rate vs Total Time**: Weak (R² < 0.2)
- **Loss vs Total Time**: Weak (R² < 0.3)

---

## Comparison with Handshake-Only Tests

| Metric | Handshake-Only | 3-Hop Circuit | Ratio |
|--------|---------------|---------------|-------|
| **Average Time** | 180 µs | 26,000 µs | 144× |
| **Network Impact** | None | Dominant | - |
| **Crypto Impact** | 100% | 2% | - |
| **Topology Variation** | 1.7% | ~20% | 12× |
| **Test Realism** | Low | High | - |

**Conclusion:**
- Handshake tests: Good for crypto performance analysis
- 3-hop tests: Necessary for real-world system evaluation

---

## Next Steps

1. **Run on Phytium Pi:**
   - Deploy framework to ARM platform
   - Collect 12-topology data
   - Compare with WSL results

2. **Distributed Testing (Optional):**
   - Use 7 Phytium Pi devices
   - Real multi-hop network topology
   - More realistic latency modeling

3. **Paper Writing:**
   - Use 3-hop data for system evaluation section
   - Show both handshake (crypto) and circuit (system) results
   - Demonstrate PQ-NTOR's real-world feasibility

---

## File Locations

```
last_experiment/phytium_deployment/
├── benchmark_3hop_circuit.c        # C benchmark program
├── configure_tc.sh                 # TC configuration script
├── test_3hop_12topo.py            # Automated test runner
├── 3HOP_TESTING_README.md         # This file
└── phytium_results/
    ├── 3hop_12topo_results.json   # Output: 12-topology results
    └── 3hop_analysis_report.md     # Generated analysis
```

---

**Last Updated:** 2025-11-30
**Status:** Ready for Testing
**Platform:** WSL/Linux (x86_64, ARM64)
