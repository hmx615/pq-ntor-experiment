#!/bin/bash
# SAGIN Phase 2 Quick Start Script
# PQ-NTOR Performance Testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../configs/sagin_topology_config.json"
DOCKER_DIR="${SCRIPT_DIR}/../docker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    print_header "检查 Phase 2 要求"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
    print_success "Docker 已安装"

    # Check Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    print_success "Python3 已安装"

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "需要 root 权限"
        echo "请使用 sudo 运行此脚本"
        exit 1
    fi
    print_success "权限检查通过"

    # Check if PQ-NTOR image exists
    if docker images | grep -q "pq-ntor-sagin"; then
        print_success "PQ-NTOR 镜像已存在"
    else
        print_info "PQ-NTOR 镜像未找到，需要先构建"
        return 1
    fi

    print_success "所有要求已满足"
    echo
    return 0
}

build_image() {
    print_header "构建 PQ-NTOR Docker 镜像"

    if [ ! -f "${DOCKER_DIR}/build_pq_ntor_image.sh" ]; then
        print_error "构建脚本不存在: ${DOCKER_DIR}/build_pq_ntor_image.sh"
        exit 1
    fi

    cd "${DOCKER_DIR}"
    ./build_pq_ntor_image.sh

    if [ $? -eq 0 ]; then
        print_success "镜像构建成功"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

run_pq_test() {
    local scenario=${1:-all}

    print_header "运行 PQ-NTOR 性能测试"
    print_info "场景: ${scenario}"
    echo

    cd "${SCRIPT_DIR}"

    if [ "$scenario" == "all" ]; then
        python3 sagin_pq_ntor_test.py \
            --config "$CONFIG_FILE"
    else
        python3 sagin_pq_ntor_test.py \
            --config "$CONFIG_FILE" \
            --scenario "$scenario"
    fi

    if [ $? -eq 0 ]; then
        print_success "PQ-NTOR 测试完成"
    else
        print_error "PQ-NTOR 测试失败"
        exit 1
    fi
}

run_traditional_test() {
    local scenario=${1:-all}

    print_header "运行传统 NTOR 性能测试"
    print_info "场景: ${scenario}"
    echo

    cd "${SCRIPT_DIR}"

    if [ "$scenario" == "all" ]; then
        python3 sagin_pq_ntor_test.py \
            --config "$CONFIG_FILE" \
            --traditional
    else
        python3 sagin_pq_ntor_test.py \
            --config "$CONFIG_FILE" \
            --traditional \
            --scenario "$scenario"
    fi

    if [ $? -eq 0 ]; then
        print_success "传统 NTOR 测试完成"
    else
        print_error "传统 NTOR 测试失败"
        exit 1
    fi
}

run_comparison() {
    print_header "运行 PQ-NTOR vs 传统 NTOR 对比测试"
    echo

    print_info "第1步: 运行 PQ-NTOR 测试..."
    run_pq_test all

    echo
    print_info "等待 5 秒..."
    sleep 5
    echo

    print_info "第2步: 运行传统 NTOR 测试..."
    run_traditional_test all

    echo
    print_success "对比测试完成"
    print_info "请运行 analyze_results 查看对比结果"
}

analyze_results() {
    print_header "分析测试结果"

    cd "${SCRIPT_DIR}"

    if [ -f "analyze_sagin_results.py" ]; then
        python3 analyze_sagin_results.py
    else
        print_info "结果分析脚本尚未创建"
        print_info "结果文件位于: ../results/"
        ls -lth ../results/sagin_test_*.csv | head -10
    fi
}

cleanup() {
    print_header "清理环境"

    cd "${SCRIPT_DIR}"
    python3 sagin_pq_ntor_test.py --cleanup-only

    if [ $? -eq 0 ]; then
        print_success "清理完成"
    else
        print_error "清理失败"
        exit 1
    fi
}

show_status() {
    print_header "Phase 2 系统状态"

    # Check Docker image
    echo "Docker 镜像:"
    docker images | grep -E "REPOSITORY|pq-ntor-sagin" || echo "  未找到 PQ-NTOR 镜像"

    echo
    echo "容器状态:"
    docker ps -a --filter "name=sagin_" --format "table {{.Names}}\t{{.Status}}" || echo "  无运行中的容器"

    echo
    echo "测试结果:"
    if [ -d "${SCRIPT_DIR}/../results" ]; then
        ls -lth "${SCRIPT_DIR}/../results/sagin_test_"*.csv 2>/dev/null | head -5 || echo "  无测试结果"
    fi

    echo
    echo "日志文件:"
    if [ -f "/tmp/sagin_pq_ntor_test.log" ]; then
        echo "  /tmp/sagin_pq_ntor_test.log (最近10行)"
        tail -10 /tmp/sagin_pq_ntor_test.log
    else
        echo "  无日志文件"
    fi
}

show_usage() {
    cat << EOF
SAGIN Phase 2 快速启动脚本

用法: sudo ./phase2_quick_start.sh [命令] [参数]

命令:
    check               检查系统要求
    build               构建 PQ-NTOR Docker 镜像
    test-pq [场景]      运行 PQ-NTOR 测试（默认: all）
    test-trad [场景]    运行传统 NTOR 测试（默认: all）
    comparison          运行对比测试（PQ vs 传统）
    analyze             分析测试结果
    status              显示系统状态
    cleanup             清理环境
    help                显示此帮助信息

场景选项:
    all                 运行所有场景（默认）
    scenario_1          星间链路 (ISL)
    scenario_2          星地链路
    scenario_3          多跳混合链路
    scenario_4          全球端到端
    scenario_5          动态切换

示例:
    # 完整流程
    sudo ./phase2_quick_start.sh check
    sudo ./phase2_quick_start.sh build
    sudo ./phase2_quick_start.sh comparison

    # 运行特定场景
    sudo ./phase2_quick_start.sh test-pq scenario_1
    sudo ./phase2_quick_start.sh test-trad scenario_2

    # 查看状态和清理
    sudo ./phase2_quick_start.sh status
    sudo ./phase2_quick_start.sh cleanup

日志文件:
    /tmp/sagin_pq_ntor_test.log

EOF
}

# Main script logic
case "${1:-help}" in
    check)
        check_requirements
        ;;
    build)
        check_requirements || true
        build_image
        ;;
    test-pq)
        check_requirements
        run_pq_test "${2:-all}"
        ;;
    test-trad)
        check_requirements
        run_traditional_test "${2:-all}"
        ;;
    comparison)
        check_requirements
        run_comparison
        ;;
    analyze)
        analyze_results
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
