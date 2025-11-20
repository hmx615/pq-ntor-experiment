#!/usr/bin/env python3
"""
SAGIN PQ-NTOR Performance Testing Script
Integrates PQ-NTOR with SAGIN simulation environment for performance evaluation
"""

import json
import subprocess
import time
import logging
import signal
import sys
import argparse
import csv
from typing import Dict, List, Tuple
from datetime import datetime
import os
from pathlib import Path

# Import SAGIN components
from sagin_orbit_simulator import SAGINOrbitSimulator
from network_topology_manager import NetworkTopologyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/sagin_pq_ntor_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SAGINPQNTORTest:
    """
    PQ-NTOR performance testing in SAGIN environment
    """

    def __init__(self, config_file: str, use_pq: bool = True, dry_run: bool = False):
        """
        Initialize PQ-NTOR test system

        Args:
            config_file: Path to SAGIN topology configuration
            use_pq: Use PQ-NTOR (True) or traditional NTOR (False)
            dry_run: Dry run mode
        """
        self.config_file = config_file
        self.use_pq = use_pq
        self.dry_run = dry_run
        self.config = self._load_config()

        # Docker settings
        self.network_name = self.config.get('docker_network', {}).get('name', 'sagin_net')
        self.pq_image = 'pq-ntor-sagin:latest'
        self.containers: Dict[str, str] = {}  # node_name -> container_id

        # Test results
        self.test_results = []
        self.current_test_id = 0

        # Components
        self.orbit_simulator = None
        self.network_manager = None

        # Results directory
        self.results_dir = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/results')
        self.results_dir.mkdir(exist_ok=True)

        logger.info(f"SAGIN PQ-NTOR Test initialized (PQ={use_pq}, dry_run={dry_run})")

    def _load_config(self) -> dict:
        """Load configuration file"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Execute a shell command"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(command)}")
            return subprocess.CompletedProcess(command, 0, '', '')

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=check,
                timeout=60
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(command)}")
            raise

    def setup_docker_network(self):
        """Create Docker network"""
        logger.info("Setting up Docker network...")

        # Check if network exists
        result = self._run_command(
            ['docker', 'network', 'ls', '--filter', f'name={self.network_name}', '--format', '{{.Name}}'],
            check=False
        )

        if self.network_name in result.stdout:
            logger.info(f"Network {self.network_name} already exists")
        else:
            network_config = self.config.get('docker_network', {})
            self._run_command([
                'docker', 'network', 'create',
                '--driver', 'bridge',
                '--subnet', network_config.get('subnet', '172.20.0.0/16'),
                '--gateway', network_config.get('gateway', '172.20.0.1'),
                self.network_name
            ])
            logger.info(f"Created network {self.network_name}")

    def create_pq_ntor_containers(self):
        """Create Docker containers with PQ-NTOR"""
        logger.info("Creating PQ-NTOR containers...")

        # Pull/check image
        logger.info(f"Checking for image {self.pq_image}...")
        result = self._run_command(
            ['docker', 'images', '-q', self.pq_image],
            check=False
        )

        if not result.stdout.strip():
            logger.error(f"Image {self.pq_image} not found. Please build it first:")
            logger.error("  cd docker && sudo ./build_pq_ntor_image.sh")
            raise RuntimeError("PQ-NTOR image not found")

        # Create containers for each node
        nodes = self._get_all_nodes()

        for node in nodes:
            container_name = f"sagin_{node['name'].lower()}"
            ip_address = node['ip']

            # Check if container exists
            result = self._run_command(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                check=False
            )

            if container_name in result.stdout:
                logger.info(f"Removing existing container {container_name}...")
                self._run_command(['docker', 'rm', '-f', container_name], check=False)

            # Create container
            logger.info(f"Creating container {container_name} at {ip_address}...")

            cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', self.network_name,
                '--ip', ip_address,
                '--cap-add', 'NET_ADMIN',
                '--privileged',
                self.pq_image
            ]

            result = self._run_command(cmd)

            if not self.dry_run:
                container_id = result.stdout.strip()
                self.containers[node['name']] = container_id
                logger.info(f"Created container {container_name} (ID: {container_id[:12]})")

        logger.info(f"Created {len(nodes)} PQ-NTOR containers")

    def _get_all_nodes(self) -> List[dict]:
        """Get all node configurations"""
        nodes = []

        for sat_name, sat_config in self.config.get('satellites', {}).items():
            nodes.append({
                'name': sat_name,
                'type': 'satellite',
                'ip': sat_config.get('ip'),
                'port': sat_config.get('port'),
                'config': sat_config
            })

        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            nodes.append({
                'name': aircraft_name,
                'type': 'aircraft',
                'ip': aircraft_config.get('ip'),
                'port': aircraft_config.get('port'),
                'config': aircraft_config
            })

        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            nodes.append({
                'name': gs_name,
                'type': 'ground_station',
                'ip': gs_config.get('ip'),
                'port': gs_config.get('port'),
                'config': gs_config
            })

        return nodes

    def initialize_components(self):
        """Initialize orbit simulator and network manager"""
        logger.info("Initializing simulation components...")

        self.orbit_simulator = SAGINOrbitSimulator(self.config_file)
        self.network_manager = NetworkTopologyManager(self.config_file, dry_run=self.dry_run)

        logger.info("Components initialized")

    def start_pq_ntor_nodes(self):
        """Start PQ-NTOR relay nodes in containers"""
        logger.info("Starting PQ-NTOR relay nodes...")

        nodes = self._get_all_nodes()

        for node in nodes:
            container_name = f"sagin_{node['name'].lower()}"
            port = node.get('port', 9001)

            # Start relay in background
            cmd = f"/root/pq-ntor/relay --port {port} --log /root/pq-ntor/logs/{node['name']}.log &"

            logger.info(f"Starting relay in {container_name} on port {port}...")

            self._run_command([
                'docker', 'exec', '-d', container_name,
                'bash', '-c', cmd
            ])

        # Wait for nodes to start
        time.sleep(2)
        logger.info("All PQ-NTOR nodes started")

    def run_performance_test(self, scenario: dict) -> dict:
        """
        Run performance test for a specific scenario

        Args:
            scenario: Test scenario configuration

        Returns:
            Test results dictionary
        """
        self.current_test_id += 1
        scenario_id = scenario.get('id', f'test_{self.current_test_id}')
        scenario_name = scenario.get('name', 'Unknown')
        path = scenario.get('path', [])

        logger.info(f"=== Running Test: {scenario_name} ({scenario_id}) ===")
        logger.info(f"Path: {' -> '.join(path)}")

        if len(path) < 2:
            logger.error("Path must have at least 2 nodes")
            return None

        # Get current topology
        topology = self.orbit_simulator.get_network_topology()

        # Apply network topology
        self.network_manager.apply_topology_update(topology)

        # Wait for network configuration to settle
        time.sleep(1)

        # Run circuit construction test
        results = self._run_circuit_test(path, scenario_id)

        # Add scenario metadata
        results['scenario_id'] = scenario_id
        results['scenario_name'] = scenario_name
        results['path'] = path
        results['timestamp'] = datetime.utcnow().isoformat()
        results['use_pq'] = self.use_pq

        self.test_results.append(results)

        logger.info(f"Test {scenario_name} completed: {results.get('status', 'unknown')}")

        return results

    def _run_circuit_test(self, path: List[str], test_id: str) -> dict:
        """
        Run circuit construction test through the specified path

        Args:
            path: List of node names forming the circuit path
            test_id: Test identifier

        Returns:
            Test results
        """
        # Get first and last node (client and destination)
        client_node = path[0]
        dest_node = path[-1]
        relay_path = path[1:-1]  # Intermediate relays

        client_container = f"sagin_{client_node.lower()}"
        dest_ip = self._get_node_ip(dest_node)

        logger.info(f"Circuit: {client_node} -> {' -> '.join(relay_path)} -> {dest_node}")

        # Build relay list argument
        relay_ips = [self._get_node_ip(relay) for relay in relay_path]
        relay_arg = ','.join(relay_ips)

        # Run benchmark in client container
        start_time = time.time()

        try:
            cmd = [
                'docker', 'exec', client_container,
                '/root/pq-ntor/benchmark_pq_ntor',
                '--hops', str(len(path) - 1),
                '--relays', relay_arg,
                '--dest', dest_ip,
                '--iterations', '10'
            ]

            result = self._run_command(cmd, check=False)

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Parse benchmark output
            if result.returncode == 0:
                # Parse results from stdout
                parsed_results = self._parse_benchmark_output(result.stdout)

                return {
                    'status': 'success',
                    'duration_ms': duration_ms,
                    'circuit_time_ms': parsed_results.get('avg_time_ms', 0),
                    'min_time_ms': parsed_results.get('min_time_ms', 0),
                    'max_time_ms': parsed_results.get('max_time_ms', 0),
                    'success_rate': parsed_results.get('success_rate', 0),
                    'timeout_rate': parsed_results.get('timeout_rate', 0),
                    'iterations': parsed_results.get('iterations', 10)
                }
            else:
                logger.error(f"Benchmark failed: {result.stderr}")
                return {
                    'status': 'failure',
                    'error': result.stderr[:200],
                    'duration_ms': duration_ms
                }

        except Exception as e:
            logger.error(f"Circuit test error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'duration_ms': 0
            }

    def _get_node_ip(self, node_name: str) -> str:
        """Get IP address for a node"""
        # Check satellites
        for sat_name, sat_config in self.config.get('satellites', {}).items():
            if sat_name == node_name:
                return sat_config.get('ip')

        # Check aircraft
        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            if aircraft_name == node_name:
                return aircraft_config.get('ip')

        # Check ground stations
        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            if gs_name == node_name:
                return gs_config.get('ip')

        raise ValueError(f"Unknown node: {node_name}")

    def _parse_benchmark_output(self, output: str) -> dict:
        """Parse benchmark output to extract metrics"""
        results = {
            'avg_time_ms': 0,
            'min_time_ms': 0,
            'max_time_ms': 0,
            'success_rate': 0,
            'timeout_rate': 0,
            'iterations': 0
        }

        # Parse output (format depends on benchmark_pq_ntor output)
        # This is a placeholder - adjust based on actual output format
        for line in output.split('\n'):
            if 'Average' in line or 'avg' in line.lower():
                try:
                    results['avg_time_ms'] = float(line.split(':')[-1].strip().split()[0])
                except:
                    pass
            elif 'Success rate' in line:
                try:
                    results['success_rate'] = float(line.split(':')[-1].strip().rstrip('%'))
                except:
                    pass

        return results

    def run_all_scenarios(self):
        """Run all test scenarios from configuration"""
        logger.info("=== Running All Test Scenarios ===")

        scenarios = self.config.get('test_scenarios', [])

        if not scenarios:
            logger.error("No test scenarios defined in configuration")
            return

        logger.info(f"Found {len(scenarios)} scenarios")

        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"\n--- Scenario {i}/{len(scenarios)} ---")

            # Skip dynamic scenarios for now
            if scenario.get('dynamic', False):
                logger.info(f"Skipping dynamic scenario: {scenario.get('name')}")
                continue

            results = self.run_performance_test(scenario)

            if results:
                logger.info(f"Results: {json.dumps(results, indent=2)}")

            # Wait between tests
            time.sleep(2)

    def save_results(self):
        """Save test results to CSV file"""
        if not self.test_results:
            logger.warning("No test results to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        protocol = 'pq_ntor' if self.use_pq else 'traditional_ntor'
        filename = self.results_dir / f'sagin_test_{protocol}_{timestamp}.csv'

        logger.info(f"Saving results to {filename}...")

        fieldnames = [
            'scenario_id', 'scenario_name', 'path', 'status',
            'circuit_time_ms', 'min_time_ms', 'max_time_ms',
            'success_rate', 'timeout_rate', 'iterations',
            'timestamp', 'use_pq'
        ]

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.test_results:
                row = {field: result.get(field, '') for field in fieldnames}
                row['path'] = ' -> '.join(result.get('path', []))
                writer.writerow(row)

        logger.info(f"Results saved to {filename}")

        return filename

    def cleanup(self):
        """Clean up Docker containers and networks"""
        logger.info("Cleaning up...")

        # Reset network configurations
        if self.network_manager:
            self.network_manager.reset_all_links()

        # Stop and remove containers
        for node_name in self.containers.keys():
            container_name = f"sagin_{node_name.lower()}"
            logger.info(f"Removing container {container_name}...")
            self._run_command(['docker', 'rm', '-f', container_name], check=False)

        # Remove network
        logger.info(f"Removing network {self.network_name}...")
        self._run_command(['docker', 'network', 'rm', self.network_name], check=False)

        logger.info("Cleanup complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='SAGIN PQ-NTOR Performance Test')
    parser.add_argument(
        '--config',
        default='/home/ccc/pq-ntor-experiment/sagin-experiments/configs/sagin_topology_config.json',
        help='Path to SAGIN topology configuration'
    )
    parser.add_argument(
        '--traditional',
        action='store_true',
        help='Use traditional NTOR instead of PQ-NTOR'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no actual tests)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        help='Run specific scenario by ID'
    )
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only perform cleanup and exit'
    )

    args = parser.parse_args()

    # Initialize test system
    use_pq = not args.traditional
    test_system = SAGINPQNTORTest(args.config, use_pq=use_pq, dry_run=args.dry_run)

    try:
        if args.cleanup_only:
            test_system.cleanup()
            return 0

        # Setup environment
        test_system.setup_docker_network()
        test_system.create_pq_ntor_containers()
        test_system.initialize_components()
        test_system.start_pq_ntor_nodes()

        # Run tests
        if args.scenario:
            # Run specific scenario
            scenarios = test_system.config.get('test_scenarios', [])
            scenario = next((s for s in scenarios if s.get('id') == args.scenario), None)

            if scenario:
                test_system.run_performance_test(scenario)
            else:
                logger.error(f"Scenario not found: {args.scenario}")
                return 1
        else:
            # Run all scenarios
            test_system.run_all_scenarios()

        # Save results
        results_file = test_system.save_results()
        logger.info(f"\nResults saved to: {results_file}")

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    finally:
        # Cleanup
        test_system.cleanup()

    logger.info("\nSAGIN PQ-NTOR test complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
