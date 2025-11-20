#!/bin/bash
# 卫星链路仿真脚本
# 使用Linux tc (traffic control) 模拟不同轨道的卫星链路特性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用sudo运行此脚本${NC}"
    echo "用法: sudo $0 {leo|meo|geo|baseline|clean|status}"
    exit 1
fi

# 网络接口（默认使用lo回环，也可指定其他接口）
INTERFACE=${2:-lo}

# 卫星链路参数定义

# LEO (Low Earth Orbit) - 低地球轨道
# 高度: 500-2000 km
# 典型卫星: Starlink, OneWeb
# 真实场景：卫星快速移动导致频繁切换，信号质量波动
LEO_DELAY=25        # 单程延迟 ms (往返50ms)
LEO_JITTER=12       # 抖动 ms (卫星移动、多普勒效应)
LEO_LOSS=3.5        # 丢包率 % (卫星切换、遮挡)
LEO_BW=100mbit      # 带宽限制
LEO_DUPLICATE=0.15  # 重复包率 % (路由重传)

# MEO (Medium Earth Orbit) - 中地球轨道
# 高度: 8,000-20,000 km
# 典型卫星: GPS, Galileo, O3b
# 真实场景：中等距离，信号衰减明显，链路稳定性中等
MEO_DELAY=75        # 单程延迟 ms (往返150ms)
MEO_JITTER=25       # 抖动 ms (信号衰减变化)
MEO_LOSS=6.5        # 丢包率 % (距离远、干扰多)
MEO_BW=50mbit       # 带宽限制
MEO_DUPLICATE=0.25  # 重复包率 % (TCP重传)

# GEO (Geostationary Earth Orbit) - 地球同步轨道
# 高度: ~36,000 km
# 典型卫星: 传统通信卫星、广播卫星
# 真实场景：超远距离，天气影响大，高延迟高丢包
GEO_DELAY=250       # 单程延迟 ms (往返500ms)
GEO_JITTER=40       # 抖动 ms (大气扰动、雨衰)
GEO_LOSS=10.0       # 丢包率 % (极远距离、天气影响)
GEO_BW=10mbit       # 带宽限制
GEO_DUPLICATE=0.4   # 重复包率 % (高延迟导致超时重传)

# Baseline - 地面网络（无额外延迟）
BASELINE_DELAY=0
BASELINE_JITTER=0
BASELINE_LOSS=0
BASELINE_BW=1gbit
BASELINE_DUPLICATE=0

# 函数: 清除现有配置
cleanup() {
    tc qdisc del dev $INTERFACE root 2>/dev/null || true
    echo -e "${GREEN}✓ 已清除 $INTERFACE 的流量控制配置${NC}"
}

# 函数: 应用网络配置
apply_config() {
    local delay=$1
    local jitter=$2
    local loss=$3
    local bw=$4
    local dup=$5
    local name=$6

    # 先清除现有配置
    cleanup

    # 添加新配置
    # 使用netem (network emulation) 模拟网络条件
    tc qdisc add dev $INTERFACE root handle 1: tbf rate $bw burst 32kbit latency 400ms

    # 添加netem延迟、抖动、丢包、重复包
    tc qdisc add dev $INTERFACE parent 1:1 handle 10: netem \
        delay ${delay}ms ${jitter}ms distribution normal \
        loss ${loss}% \
        duplicate ${dup}%

    echo -e "${GREEN}✓ 已配置 $name 卫星链路参数${NC}"
    echo -e "${BLUE}接口: $INTERFACE${NC}"
    echo -e "  延迟: ${delay}ms ± ${jitter}ms (RTT: $((delay*2))ms)"
    echo -e "  丢包率: ${loss}%"
    echo -e "  带宽: $bw"
    echo -e "  重复包: ${dup}%"
}

# 函数: 显示当前状态
show_status() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}当前网络配置状态 (接口: $INTERFACE)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    if tc qdisc show dev $INTERFACE | grep -q "netem"; then
        echo -e "${GREEN}✓ 卫星链路仿真已激活${NC}"
        echo ""
        tc qdisc show dev $INTERFACE
        echo ""
        echo -e "${YELLOW}详细参数:${NC}"
        tc -s qdisc show dev $INTERFACE
    else
        echo -e "${YELLOW}○ 未检测到卫星链路仿真配置${NC}"
        echo -e "  当前使用正常网络配置"
    fi
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
}

# 函数: 测试网络延迟
test_latency() {
    echo -e "${BLUE}测试网络延迟...${NC}"
    echo "发送10个ping包到127.0.0.1:"
    ping -c 10 127.0.0.1 | tail -5
}

# 主程序
case "$1" in
    leo)
        echo -e "${BLUE}配置 LEO (低地球轨道) 卫星链路${NC}"
        apply_config $LEO_DELAY $LEO_JITTER $LEO_LOSS $LEO_BW $LEO_DUPLICATE "LEO"
        echo ""
        show_status
        ;;

    meo)
        echo -e "${BLUE}配置 MEO (中地球轨道) 卫星链路${NC}"
        apply_config $MEO_DELAY $MEO_JITTER $MEO_LOSS $MEO_BW $MEO_DUPLICATE "MEO"
        echo ""
        show_status
        ;;

    geo)
        echo -e "${BLUE}配置 GEO (地球同步轨道) 卫星链路${NC}"
        apply_config $GEO_DELAY $GEO_JITTER $GEO_LOSS $GEO_BW $GEO_DUPLICATE "GEO"
        echo ""
        show_status
        ;;

    baseline)
        echo -e "${BLUE}配置 Baseline (地面网络)${NC}"
        cleanup
        echo -e "${GREEN}✓ 使用正常网络配置（无额外延迟）${NC}"
        ;;

    clean)
        echo -e "${BLUE}清除卫星链路仿真配置${NC}"
        cleanup
        ;;

    status)
        show_status
        ;;

    test)
        show_status
        echo ""
        test_latency
        ;;

    *)
        echo -e "${YELLOW}用法: sudo $0 {leo|meo|geo|baseline|clean|status|test} [interface]${NC}"
        echo ""
        echo "命令说明:"
        echo "  leo       - 配置LEO卫星链路 (RTT ~50ms, 100Mbps)"
        echo "  meo       - 配置MEO卫星链路 (RTT ~150ms, 50Mbps)"
        echo "  geo       - 配置GEO卫星链路 (RTT ~500ms, 10Mbps)"
        echo "  baseline  - 恢复正常地面网络配置"
        echo "  clean     - 清除所有流量控制配置"
        echo "  status    - 显示当前配置状态"
        echo "  test      - 测试当前网络延迟"
        echo ""
        echo "可选参数:"
        echo "  [interface] - 指定网络接口 (默认: lo)"
        echo ""
        echo "示例:"
        echo "  sudo $0 leo          # 在lo接口配置LEO链路"
        echo "  sudo $0 geo eth0     # 在eth0接口配置GEO链路"
        echo "  sudo $0 status       # 查看当前配置"
        echo "  sudo $0 test         # 测试延迟"
        echo "  sudo $0 clean        # 清除配置"
        exit 1
        ;;
esac

exit 0
