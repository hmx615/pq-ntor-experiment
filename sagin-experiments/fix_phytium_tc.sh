#!/bin/bash
################################################################################
# 飞腾派 TC 模块诊断与修复脚本
# Phytium Pi TC (Traffic Control) Module Diagnostic and Fix Script
#
# 用途: 诊断并修复飞腾派上 "Specified qdisc kind is unknown" 错误
# 版本: v1.0
# 日期: 2025-11-13
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查结果计数
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

################################################################################
# 辅助函数
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASS_COUNT++))
}

print_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARN_COUNT++))
}

print_fail() {
    echo -e "${RED}✗ $1${NC}"
    ((FAIL_COUNT++))
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

################################################################################
# 1. 系统信息检测
################################################################################

check_system_info() {
    print_header "1. 系统信息检测"

    echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "内核版本: $(uname -r)"
    echo "架构: $(uname -m)"

    if [[ $(uname -m) == "aarch64" ]] || [[ $(uname -m) == "arm64" ]]; then
        print_pass "ARM64 架构检测成功"
    else
        print_warn "非 ARM64 架构: $(uname -m)"
    fi

    echo ""
}

################################################################################
# 2. 内核模块检测
################################################################################

check_kernel_modules() {
    print_header "2. 内核模块检测"

    REQUIRED_MODULES=(
        "sch_htb"       # HTB qdisc
        "sch_netem"     # Network Emulator
        "cls_u32"       # U32 classifier
        "sch_tbf"       # Token Bucket Filter
        "sch_prio"      # Priority qdisc
        "sch_ingress"   # Ingress qdisc
    )

    MISSING_MODULES=()

    for module in "${REQUIRED_MODULES[@]}"; do
        if lsmod | grep -q "^$module"; then
            print_pass "$module 已加载"
        elif modprobe -n $module 2>/dev/null; then
            print_warn "$module 未加载（但可用）"
            MISSING_MODULES+=($module)
        else
            print_fail "$module 不可用（需要重新编译内核或安装）"
            MISSING_MODULES+=($module)
        fi
    done

    echo ""

    if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
        print_info "尝试加载缺失的模块..."
        for module in "${MISSING_MODULES[@]}"; do
            if sudo modprobe $module 2>/dev/null; then
                print_pass "成功加载 $module"
            else
                print_fail "无法加载 $module"
            fi
        done
        echo ""
    fi
}

################################################################################
# 3. TC 工具检测
################################################################################

check_tc_tool() {
    print_header "3. TC 工具检测"

    if command -v tc &> /dev/null; then
        TC_VERSION=$(tc -V 2>&1 | head -n1)
        print_pass "tc 工具已安装: $TC_VERSION"

        # 检查 tc 支持的 qdisc 类型
        echo ""
        print_info "tc 支持的 qdisc 类型："
        tc qdisc help 2>&1 | grep -E "qdisc|Usage" | head -n 20
    else
        print_fail "tc 工具未安装"
        print_info "安装命令: sudo apt install iproute2"
    fi

    echo ""
}

################################################################################
# 4. 测试 TC 功能
################################################################################

test_tc_functionality() {
    print_header "4. TC 功能测试"

    # 获取测试网卡
    TEST_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)

    if [ -z "$TEST_INTERFACE" ]; then
        print_fail "无法找到测试网卡"
        echo ""
        return
    fi

    print_info "测试网卡: $TEST_INTERFACE"
    echo ""

    # 测试 1: HTB qdisc
    print_info "测试 HTB qdisc..."
    if sudo tc qdisc add dev $TEST_INTERFACE root handle 1: htb default 10 2>/dev/null; then
        print_pass "HTB qdisc 可用"
        sudo tc qdisc del dev $TEST_INTERFACE root 2>/dev/null
    else
        print_fail "HTB qdisc 不可用"
    fi

    # 测试 2: netem qdisc
    print_info "测试 netem qdisc..."
    if sudo tc qdisc add dev $TEST_INTERFACE root netem delay 10ms 2>/dev/null; then
        print_pass "netem qdisc 可用"
        sudo tc qdisc del dev $TEST_INTERFACE root 2>/dev/null
    else
        print_fail "netem qdisc 不可用"
    fi

    # 测试 3: TBF qdisc
    print_info "测试 TBF qdisc..."
    if sudo tc qdisc add dev $TEST_INTERFACE root tbf rate 100mbit burst 32kbit latency 400ms 2>/dev/null; then
        print_pass "TBF qdisc 可用"
        sudo tc qdisc del dev $TEST_INTERFACE root 2>/dev/null
    else
        print_fail "TBF qdisc 不可用"
    fi

    # 测试 4: U32 classifier
    print_info "测试 U32 classifier..."
    sudo tc qdisc add dev $TEST_INTERFACE root handle 1: htb default 10 2>/dev/null
    if sudo tc filter add dev $TEST_INTERFACE protocol ip parent 1: prio 1 u32 match ip dst 192.168.1.1 flowid 1:1 2>/dev/null; then
        print_pass "U32 classifier 可用"
    else
        print_fail "U32 classifier 不可用"
    fi
    sudo tc qdisc del dev $TEST_INTERFACE root 2>/dev/null

    echo ""
}

################################################################################
# 5. Docker 容器内测试
################################################################################

test_docker_tc() {
    print_header "5. Docker 容器内 TC 测试"

    if ! command -v docker &> /dev/null; then
        print_warn "Docker 未安装，跳过容器测试"
        echo ""
        return
    fi

    # 检查是否有运行中的 SAGIN 容器
    SAGIN_CONTAINERS=$(docker ps --filter "name=sagin_" --format "{{.Names}}" 2>/dev/null)

    if [ -z "$SAGIN_CONTAINERS" ]; then
        print_info "未找到运行中的 SAGIN 容器"
        print_info "创建临时测试容器..."

        # 创建临时测试容器
        if docker run -d --name tc_test --cap-add NET_ADMIN --rm alpine:latest sleep 300 2>/dev/null; then
            print_pass "临时容器创建成功"
            TEST_CONTAINER="tc_test"
        else
            print_fail "无法创建测试容器"
            echo ""
            return
        fi
    else
        TEST_CONTAINER=$(echo "$SAGIN_CONTAINERS" | head -n1)
        print_info "使用现有容器: $TEST_CONTAINER"
    fi

    echo ""

    # 在容器内测试
    print_info "在容器内测试 tc 命令..."

    # 测试 netem
    if docker exec $TEST_CONTAINER tc qdisc add dev eth0 root netem delay 10ms 2>/dev/null; then
        print_pass "容器内 netem 可用"
        docker exec $TEST_CONTAINER tc qdisc del dev eth0 root 2>/dev/null
    else
        print_fail "容器内 netem 不可用"
    fi

    # 测试 htb
    if docker exec $TEST_CONTAINER tc qdisc add dev eth0 root handle 1: htb default 10 2>/dev/null; then
        print_pass "容器内 HTB 可用"
        docker exec $TEST_CONTAINER tc qdisc del dev eth0 root 2>/dev/null
    else
        print_fail "容器内 HTB 不可用"
    fi

    # 清理临时容器
    if [ "$TEST_CONTAINER" == "tc_test" ]; then
        docker stop tc_test >/dev/null 2>&1
        print_info "临时容器已清理"
    fi

    echo ""
}

################################################################################
# 6. 生成修复建议
################################################################################

generate_fix_recommendations() {
    print_header "6. 修复建议"

    if [ $FAIL_COUNT -eq 0 ]; then
        print_pass "所有检查通过！TC 功能完全可用"
        echo ""
        return
    fi

    echo -e "${YELLOW}发现 $FAIL_COUNT 个问题，以下是修复建议：${NC}"
    echo ""

    # 建议 1: 安装 iproute2
    echo -e "${CYAN}1. 确保 iproute2 已安装（包含 tc 工具）：${NC}"
    echo "   sudo apt update"
    echo "   sudo apt install -y iproute2"
    echo ""

    # 建议 2: 加载内核模块
    echo -e "${CYAN}2. 加载必要的内核模块：${NC}"
    echo "   sudo modprobe sch_htb"
    echo "   sudo modprobe sch_netem"
    echo "   sudo modprobe cls_u32"
    echo "   sudo modprobe sch_tbf"
    echo ""

    # 建议 3: 永久加载模块
    echo -e "${CYAN}3. 设置开机自动加载模块（推荐）：${NC}"
    echo "   echo 'sch_htb' | sudo tee -a /etc/modules"
    echo "   echo 'sch_netem' | sudo tee -a /etc/modules"
    echo "   echo 'cls_u32' | sudo tee -a /etc/modules"
    echo "   echo 'sch_tbf' | sudo tee -a /etc/modules"
    echo ""

    # 建议 4: 检查内核配置
    echo -e "${CYAN}4. 如果模块无法加载，检查内核配置：${NC}"
    echo "   zcat /proc/config.gz | grep -E 'CONFIG_NET_SCH|CONFIG_NET_CLS'"
    echo ""
    echo "   需要的配置项："
    echo "   - CONFIG_NET_SCH_HTB=m 或 y"
    echo "   - CONFIG_NET_SCH_NETEM=m 或 y"
    echo "   - CONFIG_NET_CLS_U32=m 或 y"
    echo "   - CONFIG_NET_SCH_TBF=m 或 y"
    echo ""

    # 建议 5: 简化版 SAGIN 网络控制
    echo -e "${CYAN}5. 如果模块仍不可用，使用简化版网络控制：${NC}"
    echo "   创建文件: /home/ccc/pq-ntor-experiment/sagin-experiments/scripts/network_topology_manager_simple.py"
    echo "   使用 iptables + sleep 代替 tc netem"
    echo ""

    # 建议 6: Docker 权限
    echo -e "${CYAN}6. 确保 Docker 容器有 NET_ADMIN 权限：${NC}"
    echo "   docker run --cap-add NET_ADMIN --privileged ..."
    echo ""
}

################################################################################
# 7. 创建简化版网络控制脚本
################################################################################

create_simplified_script() {
    print_header "7. 创建简化版网络控制方案"

    SIMPLE_SCRIPT="/home/ccc/pq-ntor-experiment/sagin-experiments/scripts/network_topology_manager_simple.py"

    cat > "$SIMPLE_SCRIPT" << 'EOFPYTHON'
#!/usr/bin/env python3
"""
SAGIN Network Topology Manager - Simplified Version (without tc netem)
Uses only iptables for link control (no delay simulation)
"""

import json
import subprocess
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleNetworkTopologyManager:
    """Simplified network manager without tc dependencies"""

    def __init__(self, config_file: str, dry_run: bool = False):
        self.config_file = config_file
        self.dry_run = dry_run
        self.config = self._load_config()
        self.node_containers: Dict[str, str] = {}
        self.node_ips: Dict[str, str] = {}
        self._initialize_node_mappings()

    def _load_config(self) -> dict:
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _initialize_node_mappings(self):
        """Initialize node mappings from config"""
        for sat_name, sat_config in self.config.get('satellites', {}).items():
            container_name = f"sagin_{sat_name.lower()}"
            self.node_containers[sat_name] = container_name
            self.node_ips[sat_name] = sat_config.get('ip')

        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            container_name = f"sagin_{aircraft_name.lower()}"
            self.node_containers[aircraft_name] = container_name
            self.node_ips[aircraft_name] = aircraft_config.get('ip')

        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            container_name = f"sagin_{gs_name.lower()}"
            self.node_containers[gs_name] = container_name
            self.node_ips[gs_name] = gs_config.get('ip')

    def _run_command(self, command: List[str], container: str = None) -> bool:
        """Execute command (in container if specified)"""
        if container:
            full_command = ['docker', 'exec', container] + command
        else:
            full_command = command

        if self.dry_run:
            logger.info(f"[DRY RUN] {' '.join(full_command)}")
            return True

        try:
            result = subprocess.run(full_command, capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Command error: {e}")
            return False

    def enable_link(self, source: str, destination: str):
        """Enable link using iptables (remove DROP rule)"""
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            return False

        # Remove DROP rule
        command = ['iptables', '-D', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
        self._run_command(command, container)

        logger.info(f"Enabled link {source} -> {destination}")
        return True

    def disable_link(self, source: str, destination: str):
        """Disable link using iptables (add DROP rule)"""
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            return False

        # Add DROP rule
        command = ['iptables', '-A', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
        self._run_command(command, container)

        logger.info(f"Disabled link {source} -> {destination}")
        return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 network_topology_manager_simple.py <config.json>")
        sys.exit(1)

    manager = SimpleNetworkTopologyManager(sys.argv[1])
    print(f"Initialized simple network manager with {len(manager.node_ips)} nodes")
    print("Note: This version does not simulate delays (tc netem not used)")
EOFPYTHON

    chmod +x "$SIMPLE_SCRIPT"

    if [ -f "$SIMPLE_SCRIPT" ]; then
        print_pass "简化版脚本已创建: $SIMPLE_SCRIPT"
        print_info "此版本仅使用 iptables 控制链路启用/禁用"
        print_warn "不模拟延迟/抖动（tc netem 不可用时的备选方案）"
    else
        print_fail "无法创建简化版脚本"
    fi

    echo ""
}

################################################################################
# 主函数
################################################################################

main() {
    echo ""
    print_header "飞腾派 TC 模块诊断与修复"
    echo ""

    check_system_info
    check_kernel_modules
    check_tc_tool
    test_tc_functionality
    test_docker_tc
    generate_fix_recommendations
    create_simplified_script

    # 总结
    print_header "检测总结"
    echo -e "${GREEN}通过: $PASS_COUNT${NC}"
    echo -e "${YELLOW}警告: $WARN_COUNT${NC}"
    echo -e "${RED}失败: $FAIL_COUNT${NC}"
    echo ""

    # 生成报告
    REPORT_FILE="/tmp/phytium_tc_diagnostic_$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "飞腾派 TC 诊断报告"
        echo "===================="
        echo "时间: $(date)"
        echo "系统: $(uname -a)"
        echo ""
        echo "检测结果: 通过=$PASS_COUNT, 警告=$WARN_COUNT, 失败=$FAIL_COUNT"
    } > "$REPORT_FILE"

    print_info "详细报告已保存: $REPORT_FILE"
    echo ""

    if [ $FAIL_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠ 发现问题，请按照上述修复建议操作${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ 所有检查通过，TC 功能完全可用！${NC}"
        exit 0
    fi
}

# 执行主函数
main
