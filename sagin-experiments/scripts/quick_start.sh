#!/bin/bash
# SAGIN Simulation Quick Start Script
# 提供简单的命令来启动、停止和测试SAGIN仿真系统

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../configs/sagin_topology_config.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_requirements() {
    print_header "检查系统要求"

    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装: $(docker --version)"
    else
        print_error "Docker 未安装"
        exit 1
    fi

    # Check Python3
    if command -v python3 &> /dev/null; then
        print_success "Python3 已安装: $(python3 --version)"
    else
        print_error "Python3 未安装"
        exit 1
    fi

    # Check Python packages
    if python3 -c "import skyfield" 2>/dev/null; then
        print_success "Skyfield 库已安装"
    else
        print_error "Skyfield 库未安装"
        echo "请运行: pip3 install skyfield"
        exit 1
    fi

    # Check if running as root (required for Docker)
    if [ "$EUID" -ne 0 ]; then
        print_error "需要 root 权限运行 Docker"
        echo "请使用 sudo 运行此脚本"
        exit 1
    fi

    print_success "所有要求已满足"
    echo
}

dry_run_test() {
    print_header "运行 Dry-Run 测试"
    print_info "不会创建真实容器或修改网络，仅模拟运行"
    echo

    cd "$SCRIPT_DIR"
    python3 sagin_integration.py \
        --config "$CONFIG_FILE" \
        --dry-run \
        --no-docker \
        --duration 1 \
        --interval 5

    if [ $? -eq 0 ]; then
        print_success "Dry-run 测试完成"
    else
        print_error "Dry-run 测试失败"
        exit 1
    fi
}

start_simulation() {
    local duration=${1:-10}
    local interval=${2:-10}

    print_header "启动 SAGIN 仿真"
    print_info "持续时间: ${duration} 分钟"
    print_info "更新间隔: ${interval} 秒"
    echo

    cd "$SCRIPT_DIR"
    python3 sagin_integration.py \
        --config "$CONFIG_FILE" \
        --duration "$duration" \
        --interval "$interval"
}

start_infinite() {
    local interval=${1:-10}

    print_header "启动无限时长 SAGIN 仿真"
    print_info "更新间隔: ${interval} 秒"
    print_info "按 Ctrl+C 停止仿真"
    echo

    cd "$SCRIPT_DIR"
    python3 sagin_integration.py \
        --config "$CONFIG_FILE" \
        --interval "$interval"
}

cleanup() {
    print_header "清理 Docker 环境"

    cd "$SCRIPT_DIR"
    python3 sagin_integration.py \
        --config "$CONFIG_FILE" \
        --cleanup-only

    if [ $? -eq 0 ]; then
        print_success "清理完成"
    else
        print_error "清理失败"
        exit 1
    fi
}

show_status() {
    print_header "SAGIN 系统状态"

    # Check Docker network
    if docker network ls | grep -q "sagin_net"; then
        print_success "Docker 网络 'sagin_net' 存在"
    else
        print_info "Docker 网络 'sagin_net' 不存在"
    fi

    # Check containers
    echo
    echo "SAGIN 容器状态:"
    docker ps -a --filter "name=sagin_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true

    # Check log file
    echo
    if [ -f "/tmp/sagin_integration.log" ]; then
        print_info "日志文件: /tmp/sagin_integration.log"
        echo "最近10行日志:"
        tail -10 /tmp/sagin_integration.log
    else
        print_info "无日志文件"
    fi
}

run_unit_tests() {
    print_header "运行单元测试"

    echo "1. 测试轨道仿真器..."
    cd "$SCRIPT_DIR"
    python3 sagin_orbit_simulator.py

    echo
    echo "2. 测试网络拓扑管理器..."
    python3 network_topology_manager.py

    print_success "单元测试完成"
}

show_usage() {
    cat << EOF
SAGIN 仿真系统快速启动脚本

用法: sudo ./quick_start.sh [命令] [参数]

命令:
    check           检查系统要求
    test            运行 dry-run 测试（不创建容器）
    unit-test       运行单元测试
    start [分钟] [间隔]   启动仿真（默认: 10分钟, 10秒间隔）
    infinite [间隔]       启动无限时长仿真（默认: 10秒间隔）
    status          显示系统状态
    cleanup         清理 Docker 容器和网络
    help            显示此帮助信息

示例:
    sudo ./quick_start.sh check                  # 检查系统要求
    sudo ./quick_start.sh test                   # 运行测试
    sudo ./quick_start.sh start 5 10             # 运行5分钟，每10秒更新
    sudo ./quick_start.sh infinite 5             # 无限运行，每5秒更新
    sudo ./quick_start.sh status                 # 查看状态
    sudo ./quick_start.sh cleanup                # 清理环境

日志文件: /tmp/sagin_integration.log

EOF
}

# Main script logic
case "${1:-help}" in
    check)
        check_requirements
        ;;
    test)
        check_requirements
        dry_run_test
        ;;
    unit-test)
        run_unit_tests
        ;;
    start)
        check_requirements
        start_simulation "${2:-10}" "${3:-10}"
        ;;
    infinite)
        check_requirements
        start_infinite "${2:-10}"
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "未知命令: $1"
        echo
        show_usage
        exit 1
        ;;
esac
