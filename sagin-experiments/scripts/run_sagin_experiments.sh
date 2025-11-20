#!/bin/bash
# PQ-Tor SAGIN 自动化实验脚本
# 测试PQ-Tor在不同卫星链路条件下的性能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
PROJECT_ROOT="/home/ccc/pq-ntor-experiment"
C_DIR="$PROJECT_ROOT/c"
RESULTS_DIR="$PROJECT_ROOT/results/sagin"
SCRIPT_DIR="$PROJECT_ROOT/sagin-experiments"

# 创建结果目录
mkdir -p "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR/logs"
mkdir -p "$RESULTS_DIR/figures"

# 测试配置
CONFIGS=("baseline" "leo" "meo" "geo")
CONFIG_NAMES=("Baseline (Ground)" "LEO Satellite" "MEO Satellite" "GEO Satellite")
EXPECTED_RTT=(1 50 150 500)

# 测试参数
NUM_RUNS=10         # 每个配置运行次数（增加以观察真实成功率）
TIMEOUT=90          # 客户端超时（秒）- 足够时间完成测试
COOLDOWN=5          # 测试间冷却时间（秒）

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    log_section "检查依赖"

    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_error "需要sudo权限来配置网络"
        echo "请运行: sudo -v"
        exit 1
    fi

    # 检查可执行文件
    if [ ! -f "$C_DIR/directory" ] || [ ! -f "$C_DIR/relay" ] || [ ! -f "$C_DIR/client" ]; then
        log_error "PQ-Tor可执行文件未找到"
        echo "请先编译: cd $C_DIR && make all"
        exit 1
    fi

    # 检查tc命令
    if ! command -v tc &> /dev/null; then
        log_error "tc命令未找到，请安装iproute2"
        echo "Ubuntu/Debian: sudo apt install iproute2"
        exit 1
    fi

    log_success "所有依赖检查通过"
}

# 清理进程
cleanup_processes() {
    log_info "清理后台进程..."
    sudo pkill -9 -f "directory" 2>/dev/null || true
    sudo pkill -9 -f "./relay" 2>/dev/null || true
    sudo pkill -9 -f "./client" 2>/dev/null || true
    sleep 2
    log_info "进程清理完成"
}

# 清理网络配置
cleanup_network() {
    log_info "清理网络配置..."
    sudo "$SCRIPT_DIR/simulate_satellite_link.sh" clean > /dev/null 2>&1 || true
}

# 启动测试网络
start_test_network() {
    log_info "启动测试网络..."

    cd "$C_DIR"

    # 启动directory server
    ./directory > "$RESULTS_DIR/logs/directory.log" 2>&1 &
    DIR_PID=$!
    sleep 1

    if ! ps -p $DIR_PID > /dev/null; then
        log_error "Directory server启动失败"
        return 1
    fi

    # 启动relay节点
    ./relay -r guard -p 6001 > "$RESULTS_DIR/logs/guard.log" 2>&1 &
    GUARD_PID=$!

    ./relay -r middle -p 6002 > "$RESULTS_DIR/logs/middle.log" 2>&1 &
    MIDDLE_PID=$!

    ./relay -r exit -p 6003 > "$RESULTS_DIR/logs/exit.log" 2>&1 &
    EXIT_PID=$!

    sleep 2

    # 检查所有进程是否运行
    if ! ps -p $DIR_PID > /dev/null || \
       ! ps -p $GUARD_PID > /dev/null || \
       ! ps -p $MIDDLE_PID > /dev/null || \
       ! ps -p $EXIT_PID > /dev/null; then
        log_error "部分节点启动失败"
        cleanup_processes
        return 1
    fi

    log_success "测试网络启动成功 (PIDs: $DIR_PID $GUARD_PID $MIDDLE_PID $EXIT_PID)"
    return 0
}

# 停止测试网络
stop_test_network() {
    log_info "停止测试网络..."
    cleanup_processes
}

# 运行单个测试
run_single_test() {
    local config=$1
    local run_number=$2
    local config_name=$3

    log_info "运行测试: $config_name (Run $run_number/$NUM_RUNS)"

    cd "$C_DIR"

    # 记录开始时间
    local start_time=$(date +%s.%N)

    # 运行客户端
    local output_file="$RESULTS_DIR/logs/${config}_run${run_number}.txt"
    timeout $TIMEOUT ./client http://127.0.0.1:8000/ > "$output_file" 2>&1
    local exit_code=$?

    # 记录结束时间
    local end_time=$(date +%s.%N)
    local elapsed=$(echo "$end_time - $start_time" | bc)

    # 分析结果
    local status="UNKNOWN"
    local circuit_time="N/A"
    local handshake_count=0

    if [ $exit_code -eq 0 ]; then
        if grep -q "Test completed successfully" "$output_file"; then
            status="SUCCESS"
            # 尝试提取电路建立时间（如果有的话）
            circuit_time=$(grep -oP 'Circuit.*\K[0-9.]+(?=s)' "$output_file" 2>/dev/null | head -1 || echo "N/A")
        elif grep -q "circuit established" "$output_file"; then
            status="PARTIAL"
        else
            status="FAILED"
        fi
    elif [ $exit_code -eq 124 ]; then
        status="TIMEOUT"
    else
        status="ERROR"
    fi

    # 统计握手次数
    handshake_count=$(grep -c "handshake" "$output_file" 2>/dev/null || echo 0)

    log_info "结果: $status, 耗时: ${elapsed}s"

    echo "$config,$run_number,$elapsed,$status,$circuit_time,$handshake_count" >> "$RESULTS_DIR/raw_results.csv"

    return $([ "$status" = "SUCCESS" ] && echo 0 || echo 1)
}

# 运行配置测试
run_config_tests() {
    local config=$1
    local config_name=$2
    local expected_rtt=$3

    log_section "测试配置: $config_name (预期RTT: ${expected_rtt}ms)"

    # 配置网络
    if [ "$config" != "baseline" ]; then
        log_info "配置卫星链路: $config"
        sudo "$SCRIPT_DIR/simulate_satellite_link.sh" "$config"
        sleep 2

        # 验证配置
        log_info "验证网络配置..."
        sudo "$SCRIPT_DIR/simulate_satellite_link.sh" status
    else
        log_info "使用baseline配置（地面网络）"
    fi

    # 启动测试网络
    if ! start_test_network; then
        log_error "无法启动测试网络，跳过此配置"
        cleanup_network
        return 1
    fi

    # 运行多次测试
    local success_count=0
    for run in $(seq 1 $NUM_RUNS); do
        log_info "===== 开始第 $run/$NUM_RUNS 次测试 ====="
        if run_single_test "$config" "$run" "$config_name"; then
            success_count=$((success_count + 1))
            log_success "第 $run/$NUM_RUNS 次测试成功"
        else
            log_warning "第 $run/$NUM_RUNS 次测试失败"
        fi

        if [ $run -lt $NUM_RUNS ]; then
            log_info "等待3秒后继续下一次测试..."
            sleep 3  # 测试间短暂休息
        fi
    done

    # 停止测试网络
    stop_test_network

    # 清理网络配置
    if [ "$config" != "baseline" ]; then
        cleanup_network
    fi

    log_success "配置 $config_name 测试完成 (成功: $success_count/$NUM_RUNS)"

    # 冷却时间
    if [ "$config" != "geo" ]; then  # 最后一个配置不需要冷却
        log_info "冷却 ${COOLDOWN}s..."
        sleep $COOLDOWN
    fi
}

# 分析结果
analyze_results() {
    log_section "分析实验结果"

    if [ ! -f "$RESULTS_DIR/raw_results.csv" ]; then
        log_error "未找到实验结果文件"
        return 1
    fi

    python3 << 'PYTHON_SCRIPT'
import pandas as pd
import numpy as np
import sys

results_dir = "/home/ccc/pq-ntor-experiment/results/sagin"

try:
    # 读取数据
    df = pd.read_csv(f'{results_dir}/raw_results.csv',
                     names=['Config', 'Run', 'Time(s)', 'Status', 'CircuitTime', 'HandshakeCount'])

    # 按配置分组统计
    print("\n" + "="*70)
    print("PQ-Tor SAGIN 实验结果汇总")
    print("="*70)

    for config in ['baseline', 'leo', 'meo', 'geo']:
        config_data = df[df['Config'] == config]

        if len(config_data) == 0:
            continue

        config_name = {
            'baseline': 'Baseline (Ground)',
            'leo': 'LEO Satellite',
            'meo': 'MEO Satellite',
            'geo': 'GEO Satellite'
        }[config]

        success = len(config_data[config_data['Status'] == 'SUCCESS'])
        total = len(config_data)
        success_rate = (success / total * 100) if total > 0 else 0

        times = config_data[config_data['Status'] == 'SUCCESS']['Time(s)']

        print(f"\n{config_name}:")
        print(f"  测试次数: {total}")
        print(f"  成功次数: {success}")
        print(f"  成功率: {success_rate:.1f}%")

        if len(times) > 0:
            print(f"  平均时间: {times.mean():.2f}s")
            print(f"  最小时间: {times.min():.2f}s")
            print(f"  最大时间: {times.max():.2f}s")
            print(f"  标准差: {times.std():.2f}s")

    print("="*70)

    # 保存汇总结果
    summary = df.groupby('Config').agg({
        'Time(s)': ['count', 'mean', 'std', 'min', 'max'],
        'Status': lambda x: (x == 'SUCCESS').sum()
    }).round(3)

    summary.to_csv(f'{results_dir}/summary.csv')
    print(f"\n✓ 汇总结果已保存到: {results_dir}/summary.csv")

except Exception as e:
    print(f"\n✗ 分析出错: {e}", file=sys.stderr)
    sys.exit(1)

PYTHON_SCRIPT

    local python_exit=$?

    if [ $python_exit -eq 0 ]; then
        log_success "结果分析完成"
    else
        log_error "结果分析失败"
    fi
}

# 生成可视化
generate_plots() {
    log_section "生成可视化图表"

    python3 << 'PYTHON_SCRIPT'
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

results_dir = "/home/ccc/pq-ntor-experiment/results/sagin"

try:
    # 读取数据
    df = pd.read_csv(f'{results_dir}/raw_results.csv',
                     names=['Config', 'Run', 'Time(s)', 'Status', 'CircuitTime', 'HandshakeCount'])

    # 只使用成功的测试
    df_success = df[df['Status'] == 'SUCCESS'].copy()

    if len(df_success) == 0:
        print("警告: 没有成功的测试数据用于可视化")
        sys.exit(0)

    # 配置顺序和名称
    config_order = ['baseline', 'leo', 'meo', 'geo']
    config_labels = {
        'baseline': 'Baseline\n(Ground)',
        'leo': 'LEO\n(~50ms RTT)',
        'meo': 'MEO\n(~150ms RTT)',
        'geo': 'GEO\n(~500ms RTT)'
    }

    # 按配置分组
    grouped = df_success.groupby('Config')['Time(s)'].agg(['mean', 'std', 'count'])
    grouped = grouped.reindex(config_order)

    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 图1: 电路建立时间对比
    ax1 = axes[0]
    configs = [config_labels.get(c, c) for c in grouped.index]
    means = grouped['mean']
    stds = grouped['std']

    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
    bars = ax1.bar(range(len(configs)), means, yerr=stds, capsize=5,
                   color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

    ax1.set_xlabel('Network Configuration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Circuit Construction Time (s)', fontsize=12, fontweight='bold')
    ax1.set_title('PQ-Tor Performance in SAGIN Networks', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(configs)))
    ax1.set_xticklabels(configs)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加数值标签
    for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std,
                f'{mean:.2f}s\n±{std:.2f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 图2: 成功率对比
    ax2 = axes[1]
    success_rates = []
    for config in config_order:
        config_data = df[df['Config'] == config]
        if len(config_data) > 0:
            rate = len(config_data[config_data['Status'] == 'SUCCESS']) / len(config_data) * 100
            success_rates.append(rate)
        else:
            success_rates.append(0)

    bars2 = ax2.bar(range(len(configs)), success_rates, color=colors, alpha=0.7,
                    edgecolor='black', linewidth=1.5)

    ax2.set_xlabel('Network Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Circuit Establishment Success Rate', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(configs)))
    ax2.set_xticklabels(configs)
    ax2.set_ylim([0, 105])
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加百分比标签
    for bar, rate in zip(bars2, success_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.0f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    # 保存图表
    plt.savefig(f'{results_dir}/figures/sagin_performance.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(f'{results_dir}/figures/sagin_performance.png', dpi=300, bbox_inches='tight')

    print(f"✓ 图表已保存到: {results_dir}/figures/")
    print(f"  - sagin_performance.pdf")
    print(f"  - sagin_performance.png")

except Exception as e:
    print(f"✗ 生成图表失败: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_SCRIPT

    local python_exit=$?

    if [ $python_exit -eq 0 ]; then
        log_success "图表生成完成"
    else
        log_warning "图表生成失败（数据可能不足）"
    fi
}

# 主程序
main() {
    log_section "PQ-Tor SAGIN 自动化实验"

    echo "项目目录: $PROJECT_ROOT"
    echo "结果目录: $RESULTS_DIR"
    echo "测试配置: ${#CONFIGS[@]} 种网络配置"
    echo "每配置运行: $NUM_RUNS 次"
    echo ""

    # 检查依赖
    check_dependencies

    # 初始化结果文件
    echo "# Config,Run,Time(s),Status,CircuitTime,HandshakeCount" > "$RESULTS_DIR/raw_results.csv"

    # 清理环境
    cleanup_processes
    cleanup_network

    # 运行所有配置的测试
    for i in "${!CONFIGS[@]}"; do
        run_config_tests "${CONFIGS[$i]}" "${CONFIG_NAMES[$i]}" "${EXPECTED_RTT[$i]}"
    done

    # 最终清理
    cleanup_processes
    cleanup_network

    # 分析结果
    analyze_results

    # 生成可视化
    generate_plots

    log_section "实验完成！"
    echo "结果位置: $RESULTS_DIR"
    echo "  - raw_results.csv    : 原始数据"
    echo "  - summary.csv        : 汇总统计"
    echo "  - figures/           : 可视化图表"
    echo "  - logs/              : 详细日志"
}

# 捕获Ctrl+C
trap 'echo ""; log_warning "实验被中断"; cleanup_processes; cleanup_network; exit 130' INT TERM

# 运行主程序
main

exit 0
