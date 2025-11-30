#!/usr/bin/env python3
"""
test_3hop_12topo.py - Complete 3-hop Circuit Construction Test Across 12 SAGIN Topologies

This script:
1. Starts directory server and relay nodes
2. For each of 12 topologies:
   - Applies TC network parameters
   - Runs circuit construction benchmark (100 iterations)
   - Collects timing data
3. Generates comprehensive results

Usage:
    sudo python3 test_3hop_12topo.py [--iterations 100] [--output results.json]
"""

import subprocess
import time
import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Topology definitions (matching phytium results)
TOPOLOGIES = {
    "topo01": {"rate_mbps": 31.81, "delay_ms": 5.42, "loss_percent": 2.0, "scenario": "Satellite Direct NOMA (Uplink)"},
    "topo02": {"rate_mbps": 8.77, "delay_ms": 5.44, "loss_percent": 2.0, "scenario": "T Cooperative Access (Uplink)"},
    "topo03": {"rate_mbps": 20.53, "delay_ms": 2.73, "loss_percent": 0.1, "scenario": "T User Cooperative NOMA (Uplink)"},
    "topo04": {"rate_mbps": 29.21, "delay_ms": 5.42, "loss_percent": 2.0, "scenario": "Hybrid Direct+Coop (Uplink)"},
    "topo05": {"rate_mbps": 23.03, "delay_ms": 5.43, "loss_percent": 2.0, "scenario": "Multi-layer Tree (Uplink)"},
    "topo06": {"rate_mbps": 29.21, "delay_ms": 5.42, "loss_percent": 0.1, "scenario": "Dual UAV Relay (Uplink)"},
    "topo07": {"rate_mbps": 14.08, "delay_ms": 5.44, "loss_percent": 2.0, "scenario": "Direct NOMA+Coop (Downlink)"},
    "topo08": {"rate_mbps": 8.77, "delay_ms": 5.46, "loss_percent": 2.0, "scenario": "Multi-hop Cooperative (Downlink)"},
    "topo09": {"rate_mbps": 8.77, "delay_ms": 2.72, "loss_percent": 0.5, "scenario": "T User Cooperative (Downlink)"},
    "topo10": {"rate_mbps": 8.77, "delay_ms": 5.44, "loss_percent": 2.0, "scenario": "Hybrid Single-hop Coop (Downlink)"},
    "topo11": {"rate_mbps": 3.60, "delay_ms": 5.44, "loss_percent": 2.0, "scenario": "Hybrid Multi-hop Coop (Downlink)"},
    "topo12": {"rate_mbps": 8.77, "delay_ms": 5.44, "loss_percent": 2.0, "scenario": "Dual Relay Cooperative (Downlink)"},
}

class SystemManager:
    """Manages directory server and relay nodes"""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.directory_proc = None
        self.relay_procs = []

    def start_directory(self, port=5000):
        """Start directory server"""
        print(f"[System] Starting directory server on port {port}...")
        directory_bin = self.base_dir / "directory"

        if not directory_bin.exists():
            print(f"  Warning: {directory_bin} not found, attempting to compile...")
            # Try to compile from source
            return False

        try:
            self.directory_proc = subprocess.Popen(
                [str(directory_bin), str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(1)  # Wait for startup

            if self.directory_proc.poll() is None:
                print("  ✓ Directory server started")
                return True
            else:
                print("  ✗ Directory server failed to start")
                return False
        except Exception as e:
            print(f"  ✗ Failed to start directory: {e}")
            return False

    def start_relays(self, count=3):
        """Start relay nodes (Guard, Middle, Exit)"""
        print(f"[System] Starting {count} relay nodes...")
        relay_bin = self.base_dir / "relay"

        if not relay_bin.exists():
            print(f"  Warning: {relay_bin} not found")
            return False

        base_port = 6000
        relay_types = ["guard", "middle", "exit"]

        for i in range(count):
            port = base_port + i
            relay_type = relay_types[i] if i < len(relay_types) else "middle"

            try:
                proc = subprocess.Popen(
                    [str(relay_bin), str(port), relay_type, "localhost:5000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.relay_procs.append(proc)
                print(f"  ✓ {relay_type.capitalize()} relay started on port {port}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ Failed to start {relay_type} relay: {e}")
                return False

        time.sleep(2)  # Wait for all relays to register
        return True

    def stop_all(self):
        """Stop all processes"""
        print("[System] Stopping all processes...")

        if self.directory_proc:
            self.directory_proc.terminate()
            self.directory_proc.wait(timeout=5)

        for proc in self.relay_procs:
            proc.terminate()
            proc.wait(timeout=5)

        print("  ✓ All processes stopped")

class TCManager:
    """Manages Linux TC (Traffic Control) configuration"""

    def __init__(self, tc_script):
        self.tc_script = Path(tc_script)

    def apply_topology(self, topo_id):
        """Apply TC rules for a topology"""
        params = TOPOLOGIES[topo_id]
        print(f"[TC] Applying {topo_id}: {params['rate_mbps']} Mbps, "
              f"{params['delay_ms']} ms, {params['loss_percent']}% loss")

        try:
            result = subprocess.run(
                ["sudo", str(self.tc_script), topo_id],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("  ✓ TC configured")
                return True
            else:
                print(f"  ✗ TC configuration failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ✗ TC configuration error: {e}")
            return False

    def clear(self):
        """Clear all TC rules"""
        print("[TC] Clearing TC rules...")
        try:
            subprocess.run(
                ["sudo", str(self.tc_script), "clear"],
                capture_output=True,
                timeout=10
            )
            print("  ✓ TC cleared")
        except Exception as e:
            print(f"  ✗ TC clear error: {e}")

class BenchmarkRunner:
    """Runs 3-hop circuit construction benchmark"""

    def __init__(self, benchmark_bin):
        self.benchmark_bin = Path(benchmark_bin)

    def run(self, iterations=100, directory_host="localhost", directory_port=5000):
        """Run benchmark and parse results"""
        print(f"[Benchmark] Running {iterations} iterations...")

        try:
            result = subprocess.run(
                [str(self.benchmark_bin), str(iterations), directory_host, str(directory_port)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                print(f"  ✗ Benchmark failed: {result.stderr}")
                return None

            # Parse JSON output
            output = result.stdout
            json_match = re.search(r'\{[^}]+\}', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                print(f"  ✓ Average: {data['total_ms']:.2f} ms")
                return data
            else:
                print("  ✗ Failed to parse benchmark output")
                return None

        except subprocess.TimeoutExpired:
            print("  ✗ Benchmark timed out")
            return None
        except Exception as e:
            print(f"  ✗ Benchmark error: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Test 3-hop circuit construction across 12 SAGIN topologies")
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per topology (default: 100)")
    parser.add_argument("--output", default="3hop_12topo_results.json", help="Output JSON file")
    parser.add_argument("--base-dir", default="/home/user/pq-ntor-test", help="Base directory for binaries")
    parser.add_argument("--skip-system-start", action="store_true", help="Skip starting directory/relay servers")
    args = parser.parse_args()

    print("=" * 70)
    print("  PQ-NTOR 3-Hop Circuit Construction - 12 SAGIN Topologies")
    print("=" * 70)
    print(f"Iterations per topology: {args.iterations}")
    print(f"Output file: {args.output}")
    print()

    # Initialize managers
    tc_manager = TCManager("./configure_tc.sh")
    benchmark_runner = BenchmarkRunner(f"{args.base_dir}/benchmark_3hop_circuit")

    # Check if benchmark binary exists
    if not benchmark_runner.benchmark_bin.exists():
        print(f"Error: Benchmark binary not found at {benchmark_runner.benchmark_bin}")
        print("Please compile it first with:")
        print(f"  gcc -o {benchmark_runner.benchmark_bin} benchmark_3hop_circuit.c -lm")
        return 1

    # Start system (unless skipped)
    system = None
    if not args.skip_system_start:
        system = SystemManager(args.base_dir)
        if not system.start_directory():
            print("Failed to start directory server")
            return 1

        if not system.start_relays():
            print("Failed to start relay nodes")
            system.stop_all()
            return 1

    # Run tests for all topologies
    results = {}

    try:
        for topo_id in sorted(TOPOLOGIES.keys()):
            print()
            print("=" * 70)
            print(f"  Testing {topo_id}: {TOPOLOGIES[topo_id]['scenario']}")
            print("=" * 70)

            # Apply TC
            if not tc_manager.apply_topology(topo_id):
                print(f"  Skipping {topo_id} due to TC configuration failure")
                continue

            # Wait for TC to stabilize
            time.sleep(2)

            # Run benchmark
            data = benchmark_runner.run(args.iterations)

            if data:
                results[topo_id] = {
                    **TOPOLOGIES[topo_id],
                    **data,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"  Failed to get results for {topo_id}")

            # Small delay between topologies
            time.sleep(1)

    finally:
        # Cleanup
        tc_manager.clear()
        if system:
            system.stop_all()

    # Save results
    print()
    print("=" * 70)
    print("  Saving Results")
    print("=" * 70)

    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to {output_path}")

    # Print summary
    print()
    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"Total topologies tested: {len(results)}/12")

    if results:
        avg_total = sum(r['total_ms'] for r in results.values()) / len(results)
        print(f"Average circuit construction time: {avg_total:.2f} ms")

        min_topo = min(results.items(), key=lambda x: x[1]['total_ms'])
        max_topo = max(results.items(), key=lambda x: x[1]['total_ms'])

        print(f"Fastest: {min_topo[0]} ({min_topo[1]['total_ms']:.2f} ms)")
        print(f"Slowest: {max_topo[0]} ({max_topo[1]['total_ms']:.2f} ms)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
