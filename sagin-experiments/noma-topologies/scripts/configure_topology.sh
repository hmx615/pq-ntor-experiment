#!/bin/bash
##############################################################################
# 配置NOMA拓扑的网络参数
# 使用Linux tc/netem模拟不同链路的延迟、带宽、丢包率
##############################################################################

set -e

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
    echo "Usage: $0 <topology_config.json>"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

# 解析JSON配置 (需要jq)
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it first."
    echo "  sudo apt-get install jq"
    exit 1
fi

TOPO_ID=$(jq -r '.topology_id' "$CONFIG_FILE")
TOPO_NAME=$(jq -r '.name' "$CONFIG_FILE")
TOTAL_DELAY=$(jq -r '.expected_performance.total_delay_ms' "$CONFIG_FILE")
BANDWIDTH=$(jq -r '.expected_performance.bottleneck_bw_mbps' "$CONFIG_FILE")

echo "=========================================="
echo "Configuring Topology $TOPO_ID: $TOPO_NAME"
echo "=========================================="

# 清除现有tc规则
echo "[1/3] Cleaning existing tc rules..."
sudo tc qdisc del dev lo root 2>/dev/null || true
sleep 0.5

# 配置基于拓扑的网络参数
echo "[2/3] Applying network parameters..."

# 提取链路信息
NUM_LINKS=$(jq '.links | length' "$CONFIG_FILE")

if [ "$NUM_LINKS" -eq 0 ]; then
    echo "Warning: No links defined in config, using default parameters"
    # 使用总体延迟和带宽
    sudo tc qdisc add dev lo root netem \
        delay ${TOTAL_DELAY}ms 2ms \
        rate ${BANDWIDTH}mbit \
        loss 0.5%
else
    # 使用第一个链路的参数 (简化版)
    # 实际应该为每个链路单独配置，但这需要更复杂的网络拓扑
    LINK_DELAY=$(jq -r '.links[0].delay_ms' "$CONFIG_FILE")
    LINK_BW=$(jq -r '.links[0].bandwidth_mbps' "$CONFIG_FILE")
    LINK_LOSS=$(jq -r '.links[0].loss_percent' "$CONFIG_FILE")

    echo "  Delay: ${LINK_DELAY}ms"
    echo "  Bandwidth: ${LINK_BW}mbps"
    echo "  Loss: ${LINK_LOSS}%"

    sudo tc qdisc add dev lo root netem \
        delay ${LINK_DELAY}ms 2ms \
        rate ${LINK_BW}mbit \
        loss ${LINK_LOSS}%
fi

# 验证配置
echo "[3/3] Verifying configuration..."
echo ""
sudo tc qdisc show dev lo

echo ""
echo "✅ Topology $TOPO_ID configured successfully!"
echo "   Expected circuit setup time: ~${TOTAL_DELAY}ms"
echo "   Expected bandwidth: ${BANDWIDTH}Mbps"
echo ""
