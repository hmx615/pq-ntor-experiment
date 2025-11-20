#!/usr/bin/env python3
"""
SAGIN Network Topology Manager
Applies real-time network topology changes to Docker containers based on orbit simulation
Uses tc netem for delay/jitter and iptables for link enable/disable
"""

import json
import subprocess
import time
import logging
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LinkState:
    """Represents the state of a network link"""
    source: str
    destination: str
    enabled: bool
    delay_ms: float
    distance_km: float
    bandwidth_mbps: int = 100
    jitter_ms: float = 0.0
    loss_percent: float = 0.0


class NetworkTopologyManager:
    """
    Manages Docker container network topology based on SAGIN orbit simulation
    """

    def __init__(self, config_file: str, dry_run: bool = False):
        """
        Initialize the network topology manager

        Args:
            config_file: Path to SAGIN topology configuration JSON
            dry_run: If True, only log commands without executing
        """
        self.config_file = config_file
        self.dry_run = dry_run
        self.config = self._load_config()

        # Current network state
        self.current_links: Dict[Tuple[str, str], LinkState] = {}

        # Node to container mapping
        self.node_containers: Dict[str, str] = {}

        # Node to IP mapping
        self.node_ips: Dict[str, str] = {}

        # Statistics
        self.update_count = 0
        self.link_changes = 0

        # Initialize node mappings
        self._initialize_node_mappings()

        logger.info(f"Network Topology Manager initialized (dry_run={dry_run})")
        logger.info(f"Managing {len(self.node_ips)} nodes across {len(self.current_links)} potential links")

    def _load_config(self) -> dict:
        """Load SAGIN topology configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _initialize_node_mappings(self):
        """Initialize node-to-container and node-to-IP mappings"""
        # Map satellites
        for sat_name, sat_config in self.config.get('satellites', {}).items():
            container_name = f"sagin_{sat_name.lower()}"
            self.node_containers[sat_name] = container_name
            self.node_ips[sat_name] = sat_config.get('ip')

        # Map aircraft
        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            container_name = f"sagin_{aircraft_name.lower()}"
            self.node_containers[aircraft_name] = container_name
            self.node_ips[aircraft_name] = aircraft_config.get('ip')

        # Map ground stations
        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            container_name = f"sagin_{gs_name.lower()}"
            self.node_containers[gs_name] = container_name
            self.node_ips[gs_name] = gs_config.get('ip')

        logger.info(f"Initialized mappings for nodes: {list(self.node_containers.keys())}")

    def _run_command(self, command: List[str], container: str = None) -> bool:
        """
        Execute a shell command (in container if specified)

        Args:
            command: Command to execute
            container: Container name (if running command in container)

        Returns:
            True if successful, False otherwise
        """
        if container:
            # Run command inside Docker container
            full_command = ['docker', 'exec', container] + command
        else:
            full_command = command

        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(full_command)}")
            return True

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.warning(f"Command failed: {' '.join(full_command)}")
                logger.warning(f"Error: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(full_command)}")
            return False
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False

    def update_link_delay(self, source: str, destination: str, delay_ms: float,
                         jitter_ms: float = 0.0, bandwidth_mbps: int = 100):
        """
        Update link delay using tc netem

        Args:
            source: Source node name
            destination: Destination node name
            delay_ms: One-way delay in milliseconds
            jitter_ms: Delay jitter in milliseconds
            bandwidth_mbps: Bandwidth limit in Mbps
        """
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            logger.warning(f"Cannot update delay for {source}->{destination}: missing mapping")
            return False

        # Clear existing tc rules for this destination
        self._clear_tc_rules(container, dest_ip)

        # Add new tc netem rule
        # tc qdisc add dev eth0 root handle 1: htb default 12
        # tc class add dev eth0 parent 1: classid 1:1 htb rate <bandwidth>mbit
        # tc filter add dev eth0 protocol ip parent 1:0 prio 1 u32 match ip dst <dest_ip> flowid 1:1
        # tc qdisc add dev eth0 parent 1:1 handle 10: netem delay <delay>ms <jitter>ms

        commands = [
            # Create HTB qdisc
            ['tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'handle', '1:', 'htb', 'default', '12'],

            # Create traffic class with bandwidth limit
            ['tc', 'class', 'add', 'dev', 'eth0', 'parent', '1:', 'classid', '1:1',
             'htb', 'rate', f'{bandwidth_mbps}mbit'],

            # Filter traffic to destination
            ['tc', 'filter', 'add', 'dev', 'eth0', 'protocol', 'ip', 'parent', '1:0',
             'prio', '1', 'u32', 'match', 'ip', 'dst', dest_ip, 'flowid', '1:1'],

            # Add netem delay
            ['tc', 'qdisc', 'add', 'dev', 'eth0', 'parent', '1:1', 'handle', '10:',
             'netem', 'delay', f'{delay_ms}ms']
        ]

        # Add jitter if specified
        if jitter_ms > 0:
            commands[-1].extend([f'{jitter_ms}ms'])

        success = True
        for cmd in commands:
            if not self._run_command(cmd, container):
                success = False
                break

        if success:
            logger.debug(f"Updated delay {source}->{destination}: {delay_ms}ms")

        return success

    def _clear_tc_rules(self, container: str, dest_ip: str = None):
        """Clear tc rules for a container"""
        # Simply delete the root qdisc (this removes all rules)
        self._run_command(['tc', 'qdisc', 'del', 'dev', 'eth0', 'root'], container)

    def enable_link(self, source: str, destination: str):
        """
        Enable a network link using iptables

        Args:
            source: Source node name
            destination: Destination node name
        """
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            logger.warning(f"Cannot enable link {source}->{destination}: missing mapping")
            return False

        # Remove any DROP rules for this destination
        command = [
            'iptables', '-D', 'OUTPUT',
            '-d', dest_ip,
            '-j', 'DROP'
        ]

        # Try to delete (may not exist, that's okay)
        self._run_command(command, container)

        logger.debug(f"Enabled link {source}->{destination}")
        return True

    def disable_link(self, source: str, destination: str):
        """
        Disable a network link using iptables

        Args:
            source: Source node name
            destination: Destination node name
        """
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            logger.warning(f"Cannot disable link {source}->{destination}: missing mapping")
            return False

        # Add DROP rule for this destination
        command = [
            'iptables', '-A', 'OUTPUT',
            '-d', dest_ip,
            '-j', 'DROP'
        ]

        success = self._run_command(command, container)

        if success:
            logger.debug(f"Disabled link {source}->{destination}")

        return success

    def apply_topology_update(self, topology: dict):
        """
        Apply topology update from orbit simulator

        Args:
            topology: Topology dictionary from SAGINOrbitSimulator.get_network_topology()
        """
        self.update_count += 1
        timestamp = topology.get('timestamp', datetime.utcnow().isoformat())

        logger.info(f"=== Topology Update #{self.update_count} at {timestamp} ===")

        # Extract link visibility information
        links = topology.get('links', {})

        new_link_states: Dict[Tuple[str, str], LinkState] = {}

        # Process each link
        # Get all node names for parsing
        all_node_names = list(self.node_containers.keys())

        for link_key, link_info in links.items():
            # Parse link key "NodeA-NodeB"
            # Node names may contain hyphens (e.g., "GS-Beijing")
            # Find which node name the link starts with
            source = None
            destination = None

            for node_name in all_node_names:
                if link_key.startswith(node_name + '-'):
                    source = node_name
                    destination = link_key[len(node_name) + 1:]  # Skip the hyphen
                    break

            if not source or destination not in all_node_names:
                logger.warning(f"Could not parse link: {link_key}")
                continue

            # Create link state
            link_state = LinkState(
                source=source,
                destination=destination,
                enabled=link_info.get('visible', False),
                delay_ms=link_info.get('delay_ms', 0.0),
                distance_km=link_info.get('distance_km', 0.0),
                bandwidth_mbps=100  # Default, could be from config
            )

            new_link_states[(source, destination)] = link_state

        # Calculate changes
        changes = self._calculate_topology_changes(new_link_states)

        # Apply changes
        self._apply_changes(changes)

        # Update current state
        self.current_links = new_link_states

        logger.info(f"Applied {len(changes['enabled'])} link enables, "
                   f"{len(changes['disabled'])} link disables, "
                   f"{len(changes['updated'])} link updates")

    def _calculate_topology_changes(self, new_states: Dict[Tuple[str, str], LinkState]) -> dict:
        """
        Calculate differences between current and new topology

        Returns:
            Dictionary with 'enabled', 'disabled', 'updated' link lists
        """
        changes = {
            'enabled': [],   # Links that became visible
            'disabled': [],  # Links that became invisible
            'updated': []    # Links with delay changes
        }

        # Check for new/enabled links
        for link_key, new_state in new_states.items():
            old_state = self.current_links.get(link_key)

            if old_state is None:
                # New link
                if new_state.enabled:
                    changes['enabled'].append(new_state)
            else:
                # Existing link
                if new_state.enabled and not old_state.enabled:
                    # Link became visible
                    changes['enabled'].append(new_state)
                elif not new_state.enabled and old_state.enabled:
                    # Link became invisible
                    changes['disabled'].append(new_state)
                elif new_state.enabled and old_state.enabled:
                    # Check if delay changed significantly (>5ms difference)
                    if abs(new_state.delay_ms - old_state.delay_ms) > 5.0:
                        changes['updated'].append(new_state)

        # Check for removed links
        for link_key, old_state in self.current_links.items():
            if link_key not in new_states and old_state.enabled:
                changes['disabled'].append(old_state)

        return changes

    def _apply_changes(self, changes: dict):
        """Apply the calculated topology changes"""
        # Disable links first
        for link in changes['disabled']:
            self.disable_link(link.source, link.destination)
            self.link_changes += 1

        # Enable and configure new links
        for link in changes['enabled']:
            self.enable_link(link.source, link.destination)
            self.update_link_delay(
                link.source,
                link.destination,
                link.delay_ms,
                bandwidth_mbps=link.bandwidth_mbps
            )
            self.link_changes += 1

        # Update existing links
        for link in changes['updated']:
            self.update_link_delay(
                link.source,
                link.destination,
                link.delay_ms,
                bandwidth_mbps=link.bandwidth_mbps
            )

    def get_statistics(self) -> dict:
        """Get manager statistics"""
        active_links = sum(1 for link in self.current_links.values() if link.enabled)

        return {
            'update_count': self.update_count,
            'link_changes': self.link_changes,
            'active_links': active_links,
            'total_links': len(self.current_links)
        }

    def reset_all_links(self):
        """Reset all network configuration (cleanup)"""
        logger.info("Resetting all network configurations...")

        for node_name, container in self.node_containers.items():
            # Clear tc rules
            self._clear_tc_rules(container)

            # Flush iptables OUTPUT chain
            self._run_command(['iptables', '-F', 'OUTPUT'], container)

        self.current_links.clear()
        logger.info("All links reset")


def test_network_manager():
    """Test the network topology manager with simulated data"""
    import sys
    import os

    # Add parent directory to path to import orbit simulator
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from sagin_orbit_simulator import SAGINOrbitSimulator

    config_file = '/home/ccc/pq-ntor-experiment/sagin-experiments/configs/sagin_topology_config.json'

    print("=== Testing Network Topology Manager ===\n")

    # Initialize managers
    print("1. Initializing orbit simulator...")
    orbit_sim = SAGINOrbitSimulator(config_file)

    print("2. Initializing network topology manager (dry-run mode)...")
    network_mgr = NetworkTopologyManager(config_file, dry_run=True)

    print("\n3. Getting current network topology...")
    topology = orbit_sim.get_network_topology()

    print(f"\n4. Network snapshot:")
    print(f"   Timestamp: {topology['timestamp']}")
    print(f"   Nodes: {topology['node_count']}")
    print(f"   Links: {len(topology['links'])}")
    print(f"   Visible links: {topology['visible_link_count']}")

    print("\n5. Applying topology to network manager...")
    network_mgr.apply_topology_update(topology)

    print("\n6. Manager statistics:")
    stats = network_mgr.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n7. Simulating 3 topology updates...")
    for i in range(3):
        time.sleep(2)
        print(f"\n   Update {i+1}:")
        topology = orbit_sim.get_network_topology()
        network_mgr.apply_topology_update(topology)

        stats = network_mgr.get_statistics()
        print(f"   Active links: {stats['active_links']}/{stats['total_links']}")

    print("\n8. Resetting all links...")
    network_mgr.reset_all_links()

    print("\n=== Test Complete ===")


if __name__ == '__main__':
    # Run test
    test_network_manager()
