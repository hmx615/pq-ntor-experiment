#!/usr/bin/env python3
"""
SAGIN Integration Script
Orchestrates the complete SAGIN simulation environment:
- Docker container management
- Orbit simulation
- Network topology updates
- Performance monitoring
"""

import json
import subprocess
import time
import logging
import signal
import sys
import argparse
from typing import Dict, List
from datetime import datetime
import os

# Import our modules
from sagin_orbit_simulator import SAGINOrbitSimulator
from network_topology_manager import NetworkTopologyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/sagin_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SAGINIntegration:
    """
    Integrates orbit simulator, network topology manager, and Docker containers
    """

    def __init__(self, config_file: str, dry_run: bool = False):
        """
        Initialize SAGIN integration system

        Args:
            config_file: Path to SAGIN topology configuration
            dry_run: If True, don't actually create containers or modify network
        """
        self.config_file = config_file
        self.dry_run = dry_run
        self.config = self._load_config()

        # Components
        self.orbit_simulator = None
        self.network_manager = None

        # Docker state
        self.containers: Dict[str, str] = {}  # node_name -> container_id
        self.network_name = self.config.get('docker_network', {}).get('name', 'sagin_net')

        # Simulation state
        self.running = False
        self.iteration = 0

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"SAGIN Integration initialized (dry_run={dry_run})")

    def _load_config(self) -> dict:
        """Load configuration file"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Execute a shell command

        Args:
            command: Command to execute
            check: Raise exception on non-zero exit code

        Returns:
            CompletedProcess object
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(command)}")
            return subprocess.CompletedProcess(command, 0, '', '')

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            raise

    def setup_docker_network(self):
        """Create Docker network for SAGIN nodes"""
        logger.info("Setting up Docker network...")

        network_config = self.config.get('docker_network', {})
        subnet = network_config.get('subnet', '172.20.0.0/16')
        gateway = network_config.get('gateway', '172.20.0.1')

        # Check if network already exists
        result = self._run_command(
            ['docker', 'network', 'ls', '--filter', f'name={self.network_name}', '--format', '{{.Name}}'],
            check=False
        )

        if self.network_name in result.stdout:
            logger.info(f"Network {self.network_name} already exists")
        else:
            # Create network
            self._run_command([
                'docker', 'network', 'create',
                '--driver', 'bridge',
                '--subnet', subnet,
                '--gateway', gateway,
                self.network_name
            ])
            logger.info(f"Created network {self.network_name}")

    def create_containers(self):
        """Create Docker containers for all SAGIN nodes"""
        logger.info("Creating Docker containers...")

        # Base image (Ubuntu with network tools)
        base_image = 'ubuntu:22.04'

        # Ensure base image exists
        logger.info(f"Pulling base image {base_image}...")
        self._run_command(['docker', 'pull', base_image])

        # Create containers for each node
        nodes = []

        # Add satellites
        for sat_name, sat_config in self.config.get('satellites', {}).items():
            nodes.append({
                'name': sat_name,
                'type': 'satellite',
                'ip': sat_config.get('ip'),
                'config': sat_config
            })

        # Add aircraft
        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            nodes.append({
                'name': aircraft_name,
                'type': 'aircraft',
                'ip': aircraft_config.get('ip'),
                'config': aircraft_config
            })

        # Add ground stations
        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            nodes.append({
                'name': gs_name,
                'type': 'ground_station',
                'ip': gs_config.get('ip'),
                'config': gs_config
            })

        # Create each container
        for node in nodes:
            container_name = f"sagin_{node['name'].lower()}"
            ip_address = node['ip']

            # Check if container already exists
            result = self._run_command(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                check=False
            )

            if container_name in result.stdout:
                logger.info(f"Container {container_name} already exists, removing...")
                self._run_command(['docker', 'rm', '-f', container_name], check=False)

            # Create container
            logger.info(f"Creating container {container_name} at {ip_address}...")

            cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', self.network_name,
                '--ip', ip_address,
                '--cap-add', 'NET_ADMIN',  # Required for tc and iptables
                '--privileged',  # Required for network modifications
                base_image,
                'sleep', 'infinity'  # Keep container running
            ]

            result = self._run_command(cmd)

            if not self.dry_run:
                container_id = result.stdout.strip()
                self.containers[node['name']] = container_id
                logger.info(f"Created container {container_name} (ID: {container_id[:12]})")

                # Install network tools in container
                self._run_command([
                    'docker', 'exec', container_name,
                    'apt-get', 'update'
                ], check=False)

                self._run_command([
                    'docker', 'exec', container_name,
                    'apt-get', 'install', '-y', 'iproute2', 'iptables', 'iputils-ping', 'net-tools'
                ], check=False)

        logger.info(f"Created {len(nodes)} containers")

    def initialize_components(self):
        """Initialize orbit simulator and network manager"""
        logger.info("Initializing simulation components...")

        # Initialize orbit simulator
        self.orbit_simulator = SAGINOrbitSimulator(self.config_file)
        logger.info("Orbit simulator initialized")

        # Initialize network topology manager
        self.network_manager = NetworkTopologyManager(self.config_file, dry_run=self.dry_run)
        logger.info("Network topology manager initialized")

    def topology_update_callback(self, topology: dict):
        """
        Callback for topology updates from orbit simulator

        Args:
            topology: Network topology snapshot
        """
        self.iteration += 1

        timestamp = topology.get('timestamp', 'unknown')
        visible_links = topology.get('visible_link_count', 0)
        total_links = len(topology.get('links', {}))

        logger.info(f"=== Iteration {self.iteration} at {timestamp} ===")
        logger.info(f"Visible links: {visible_links}/{total_links}")

        # Apply topology update to network
        self.network_manager.apply_topology_update(topology)

        # Get statistics
        stats = self.network_manager.get_statistics()
        logger.info(f"Network updates: {stats['update_count']}, "
                   f"Link changes: {stats['link_changes']}, "
                   f"Active links: {stats['active_links']}/{stats['total_links']}")

    def run_simulation(self, duration_min: int = None, interval_sec: int = 10):
        """
        Run the SAGIN simulation

        Args:
            duration_min: Simulation duration in minutes (None = infinite)
            interval_sec: Topology update interval in seconds
        """
        logger.info("=" * 60)
        logger.info("Starting SAGIN Simulation")
        logger.info("=" * 60)
        logger.info(f"Update interval: {interval_sec} seconds")
        logger.info(f"Duration: {duration_min if duration_min else 'Infinite'} minutes")

        self.running = True

        try:
            # Run orbit simulator with network manager callback
            self.orbit_simulator.run_realtime_simulation(
                update_callback=self.topology_update_callback,
                interval_sec=interval_sec,
                duration_min=duration_min
            )
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
        finally:
            self.running = False

    def cleanup(self):
        """Clean up Docker containers and networks"""
        logger.info("Cleaning up...")

        # Reset network configurations
        if self.network_manager:
            self.network_manager.reset_all_links()

        # Stop and remove containers
        for node_name, container_id in self.containers.items():
            container_name = f"sagin_{node_name.lower()}"
            logger.info(f"Removing container {container_name}...")
            self._run_command(['docker', 'rm', '-f', container_name], check=False)

        # Remove network
        logger.info(f"Removing network {self.network_name}...")
        self._run_command(['docker', 'network', 'rm', self.network_name], check=False)

        logger.info("Cleanup complete")

    def get_status(self) -> dict:
        """Get current simulation status"""
        return {
            'running': self.running,
            'iteration': self.iteration,
            'containers': len(self.containers),
            'network_stats': self.network_manager.get_statistics() if self.network_manager else {}
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='SAGIN Integration System')
    parser.add_argument(
        '--config',
        default='/home/ccc/pq-ntor-experiment/sagin-experiments/configs/sagin_topology_config.json',
        help='Path to SAGIN topology configuration file'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Simulation duration in minutes (default: infinite)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Topology update interval in seconds (default: 10)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no Docker containers or network changes)'
    )
    parser.add_argument(
        '--no-docker',
        action='store_true',
        help='Skip Docker setup (only run simulation)'
    )
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only perform cleanup and exit'
    )

    args = parser.parse_args()

    # Initialize integration system
    integration = SAGINIntegration(args.config, dry_run=args.dry_run)

    try:
        if args.cleanup_only:
            # Just cleanup and exit
            integration.cleanup()
            return

        if not args.no_docker:
            # Setup Docker environment
            integration.setup_docker_network()
            integration.create_containers()

        # Initialize simulation components
        integration.initialize_components()

        # Run simulation
        integration.run_simulation(
            duration_min=args.duration,
            interval_sec=args.interval
        )

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    finally:
        if not args.no_docker:
            # Cleanup
            integration.cleanup()

    logger.info("SAGIN simulation complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
