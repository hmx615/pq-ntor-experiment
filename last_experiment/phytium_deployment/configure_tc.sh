#!/bin/bash
# configure_tc.sh - Configure Linux TC (Traffic Control) for SAGIN network simulation
#
# This script simulates network conditions for 12 SAGIN topologies
# using tc (traffic control) on the loopback interface
#
# WARNING: Requires root/sudo privileges
# Usage: sudo ./configure_tc.sh <topology_id>
#        sudo ./configure_tc.sh clear

set -e

INTERFACE="lo"  # Loopback interface for single-machine testing

# Topology definitions (matching phytium_12topo_results.json)
declare -A TOPOLOGIES

# Uplink scenarios (topo01-06)
TOPOLOGIES[topo01]="rate=31.81mbit delay=2.71ms loss=2.0%"
TOPOLOGIES[topo02]="rate=8.77mbit delay=2.72ms loss=2.0%"
TOPOLOGIES[topo03]="rate=20.53mbit delay=1.365ms loss=0.1%"
TOPOLOGIES[topo04]="rate=29.21mbit delay=2.71ms loss=2.0%"
TOPOLOGIES[topo05]="rate=23.03mbit delay=2.715ms loss=2.0%"
TOPOLOGIES[topo06]="rate=29.21mbit delay=2.71ms loss=0.1%"

# Downlink scenarios (topo07-12)
TOPOLOGIES[topo07]="rate=14.08mbit delay=2.72ms loss=2.0%"
TOPOLOGIES[topo08]="rate=8.77mbit delay=2.73ms loss=2.0%"
TOPOLOGIES[topo09]="rate=8.77mbit delay=1.36ms loss=0.5%"
TOPOLOGIES[topo10]="rate=8.77mbit delay=2.72ms loss=2.0%"
TOPOLOGIES[topo11]="rate=3.60mbit delay=2.72ms loss=2.0%"
TOPOLOGIES[topo12]="rate=8.77mbit delay=2.72ms loss=2.0%"

# Function to clear all TC rules
clear_tc() {
    echo "Clearing TC rules on $INTERFACE..."
    tc qdisc del dev $INTERFACE root 2>/dev/null || true
    echo "✓ TC rules cleared"
}

# Function to apply TC rules for a topology
apply_tc() {
    local topo=$1
    local params=${TOPOLOGIES[$topo]}

    if [ -z "$params" ]; then
        echo "Error: Unknown topology '$topo'"
        echo "Valid topologies: ${!TOPOLOGIES[@]}"
        exit 1
    fi

    # Parse parameters
    local rate=$(echo "$params" | grep -oP 'rate=\K[0-9.]+mbit')
    local delay=$(echo "$params" | grep -oP 'delay=\K[0-9.]+ms')
    local loss=$(echo "$params" | grep -oP 'loss=\K[0-9.]+')

    echo "Configuring TC for $topo..."
    echo "  Rate:  ${rate}mbit"
    echo "  Delay: ${delay}ms"
    echo "  Loss:  ${loss}%"

    # Clear existing rules
    clear_tc

    # Apply new rules using netem
    # Note: delay is divided by 2 because packets traverse loopback twice (client->server->client)
    local half_delay=$(echo "$delay / 2" | bc -l)

    tc qdisc add dev $INTERFACE root netem \
        rate ${rate}mbit \
        delay ${half_delay}ms 0.1ms \
        loss ${loss}% \
        limit 1000

    echo "✓ TC configured for $topo"
}

# Function to show current TC configuration
show_tc() {
    echo "Current TC configuration on $INTERFACE:"
    tc qdisc show dev $INTERFACE
}

# Main
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges"
    echo "Usage: sudo $0 <topology_id|clear|show>"
    exit 1
fi

case "$1" in
    clear)
        clear_tc
        ;;
    show)
        show_tc
        ;;
    topo0[1-9]|topo1[0-2])
        apply_tc "$1"
        show_tc
        ;;
    "")
        echo "Usage: sudo $0 <topology_id|clear|show>"
        echo ""
        echo "Available topologies:"
        for topo in $(echo "${!TOPOLOGIES[@]}" | tr ' ' '\n' | sort); do
            echo "  $topo: ${TOPOLOGIES[$topo]}"
        done
        echo ""
        echo "Examples:"
        echo "  sudo $0 topo01       # Apply topo01 settings"
        echo "  sudo $0 clear        # Clear all TC rules"
        echo "  sudo $0 show         # Show current TC settings"
        exit 1
        ;;
    *)
        echo "Error: Unknown command '$1'"
        exit 1
        ;;
esac
