#!/bin/bash
#
# configure_tc_netem.sh
# Network emulation configuration for Phase 3 SAGIN testing
#
# Usage:
#   ./configure_tc_netem.sh apply <topology_name>
#   ./configure_tc_netem.sh clear
#   ./configure_tc_netem.sh status
#

set -e

# SAGIN topology parameters (from real NOMA data)
declare -A TOPOLOGIES=(
    ["topo01"]="31.81 5.42 2.0"
    ["topo02"]="8.77 5.44 2.0"
    ["topo03"]="5.69 5.40 2.0"
    ["topo04"]="4.15 5.46 2.0"
    ["topo05"]="16.90 5.38 2.0"
    ["topo06"]="8.77 5.44 2.0"
    ["topo07"]="5.69 5.40 2.0"
    ["topo08"]="4.15 5.46 2.0"
    ["topo09"]="31.81 2.72 0.1"
    ["topo10"]="4.77 2.76 0.1"
    ["topo11"]="3.60 2.74 0.1"
    ["topo12"]="8.77 5.44 2.0"
)

# Network interface (adjust as needed)
INTERFACE="lo"  # Use loopback for single-machine testing

# ========== Functions ==========

function show_usage() {
    echo "Usage:"
    echo "  $0 apply <topology>   - Apply tc/netem configuration for topology"
    echo "  $0 clear              - Clear all tc/netem configuration"
    echo "  $0 status             - Show current tc/netem configuration"
    echo ""
    echo "Available topologies:"
    for topo in "${!TOPOLOGIES[@]}"; do
        IFS=' ' read -r rate delay loss <<< "${TOPOLOGIES[$topo]}"
        echo "  $topo: ${rate} Mbps, ${delay} ms delay, ${loss}% loss"
    done | sort
}

function apply_tc() {
    local topology=$1

    if [[ ! -v "TOPOLOGIES[$topology]" ]]; then
        echo "Error: Unknown topology '$topology'" >&2
        show_usage
        exit 1
    fi

    IFS=' ' read -r rate delay loss <<< "${TOPOLOGIES[$topology]}"

    echo "=========================================="
    echo "Applying tc/netem for $topology"
    echo "=========================================="
    echo "  Rate:  ${rate} Mbps"
    echo "  Delay: ${delay} ms"
    echo "  Loss:  ${loss}%"
    echo "=========================================="

    # Clear existing configuration first
    clear_tc_quiet

    # Apply rate limiting with tbf (Token Bucket Filter)
    rate_kbit=$(echo "$rate * 1024" | bc | cut -d. -f1)
    burst=$(echo "$rate * 128" | bc | cut -d. -f1)k  # 1/8th of rate

    sudo tc qdisc add dev $INTERFACE root handle 1: tbf \
        rate ${rate_kbit}kbit \
        burst $burst \
        latency 50ms

    # Apply delay and packet loss with netem
    sudo tc qdisc add dev $INTERFACE parent 1:1 handle 10: netem \
        delay ${delay}ms \
        loss ${loss}%

    echo ""
    echo "✓ Configuration applied successfully"
    echo ""

    # Show status
    show_status
}

function clear_tc() {
    echo "=========================================="
    echo "Clearing tc/netem configuration"
    echo "=========================================="

    clear_tc_quiet

    echo "✓ Configuration cleared"
    echo ""
}

function clear_tc_quiet() {
    sudo tc qdisc del dev $INTERFACE root 2>/dev/null || true
}

function show_status() {
    echo "=========================================="
    echo "Current tc/netem configuration"
    echo "=========================================="

    if sudo tc qdisc show dev $INTERFACE | grep -q "qdisc"; then
        sudo tc qdisc show dev $INTERFACE
        echo ""
        sudo tc -s qdisc show dev $INTERFACE
    else
        echo "No tc/netem configuration active"
    fi

    echo "=========================================="
}

# ========== Main ==========

if [[ $# -lt 1 ]]; then
    show_usage
    exit 1
fi

command=$1

case "$command" in
    apply)
        if [[ $# -ne 2 ]]; then
            echo "Error: 'apply' requires a topology name" >&2
            show_usage
            exit 1
        fi
        apply_tc "$2"
        ;;

    clear)
        clear_tc
        ;;

    status)
        show_status
        ;;

    *)
        echo "Error: Unknown command '$command'" >&2
        show_usage
        exit 1
        ;;
esac

exit 0
