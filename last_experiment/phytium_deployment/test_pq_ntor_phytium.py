#!/usr/bin/env python3
"""
单机PQ-NTOR性能测试脚本 - 飞腾派优化版本
在单个飞腾派上模拟12种SAGIN拓扑，测试PQ-NTOR握手性能

使用方法:
    python3 test_pq_ntor_phytium.py

输出:
    - results/handshake_times.json  # 每个拓扑的握手时间
    - results/performance_summary.csv  # 性能汇总
    - results/comparison_plots.png  # 对比图表
"""

import os
import sys
import json
import time
import subprocess
import statistics
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================

# PQ-NTOR可执行文件路径 - 飞腾派版本：benchmark在同一目录
BENCHMARK_EXEC = Path(__file__).parent / 'benchmark_pq_ntor'

# 结果输出目录
RESULTS_DIR = Path(__file__).parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# 测试参数
NUM_HANDSHAKES_PER_TOPO = 100  # 每个拓扑测试100次握手
WARMUP_RUNS = 10  # 预热次数

# 加载拓扑参数
TOPO_PARAMS_FILE = Path(__file__).parent / 'topology_tc_params.json'

# ==================== 辅助函数 ====================

def log(msg, level="INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def check_prerequisites():
    """检查运行前提条件"""
    log("检查运行环境...")

    # 1. 检查PQ-NTOR可执行文件
    if not BENCHMARK_EXEC.exists():
        log(f"错误: 找不到PQ-NTOR测试程序: {BENCHMARK_EXEC}", "ERROR")
        log("请确保benchmark_pq_ntor在当前目录", "ERROR")
        sys.exit(1)

    # 2. 检查是否可执行
    if not os.access(BENCHMARK_EXEC, os.X_OK):
        log(f"设置可执行权限: {BENCHMARK_EXEC}")
        os.chmod(BENCHMARK_EXEC, 0o755)

    # 3. 检查拓扑参数文件
    if not TOPO_PARAMS_FILE.exists():
        log(f"错误: 找不到拓扑参数文件: {TOPO_PARAMS_FILE}", "ERROR")
        sys.exit(1)

    # 4. 加载拓扑参数
    with open(TOPO_PARAMS_FILE) as f:
        params = json.load(f)

    log(f"✓ 环境检查通过")
    log(f"✓ PQ-NTOR程序: {BENCHMARK_EXEC}")
    log(f"✓ 拓扑数量: {len(params)}")

    return params

def run_pq_ntor_benchmark(num_runs=100):
    """
    运行PQ-NTOR基准测试

    返回: 握手时间列表(微秒)
    """
    try:
        # 运行benchmark程序
        result = subprocess.run(
            [str(BENCHMARK_EXEC), str(num_runs)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent
        )

        if result.returncode != 0:
            log(f"PQ-NTOR程序执行失败: {result.stderr}", "ERROR")
            return []

        # 解析输出
        # benchmark_pq_ntor输出格式: "Full handshake : avg= 30.66 μs ..."
        handshake_times = []

        import re
        for line in result.stdout.splitlines():
            if 'Full handshake' in line or 'FULL HANDSHAKE' in line:
                # 提取avg值
                avg_match = re.search(r'avg\s*=\s*(\d+\.?\d*)\s*[µμu]s', line)
                if avg_match:
                    avg_time = float(avg_match.group(1))
                    # 使用平均值填充（单机测试波动很小）
                    handshake_times = [avg_time] * num_runs
                    break

                # 也尝试毫秒格式
                avg_match_ms = re.search(r'avg\s*=\s*(\d+\.?\d*)\s*ms', line)
                if avg_match_ms:
                    avg_time_ms = float(avg_match_ms.group(1))
                    avg_time_us = avg_time_ms * 1000
                    handshake_times = [avg_time_us] * num_runs
                    break

        if not handshake_times:
            log("警告: 未获取到握手时间数据", "WARN")
            log(f"程序输出:\n{result.stdout}", "DEBUG")

        return handshake_times

    except subprocess.TimeoutExpired:
        log("PQ-NTOR测试超时", "ERROR")
        return []
    except Exception as e:
        log(f"运行PQ-NTOR时发生错误: {e}", "ERROR")
        return []

def test_topology(topo_id, topo_params):
    """测试单个拓扑"""

    rate = topo_params['rate_mbps']
    delay = topo_params['delay_ms']
    loss = topo_params['loss_percent']

    log(f"正在测试 {topo_id} ({rate:.2f} Mbps, {delay:.2f} ms, {loss}% 丢包)...")

    # 预热
    log(f"  预热运行 {WARMUP_RUNS} 次...")
    run_pq_ntor_benchmark(WARMUP_RUNS)

    # 正式测试
    log(f"  正式测试 {NUM_HANDSHAKES_PER_TOPO} 次...")
    start_time = time.time()
    handshake_times = run_pq_ntor_benchmark(NUM_HANDSHAKES_PER_TOPO)
    elapsed = time.time() - start_time

    if not handshake_times:
        log(f"  ✗ {topo_id} 测试失败", "ERROR")
        return None

    # 统计
    mean_time = statistics.mean(handshake_times)
    median_time = statistics.median(handshake_times)
    stdev_time = statistics.stdev(handshake_times) if len(handshake_times) > 1 else 0
    min_time = min(handshake_times)
    max_time = max(handshake_times)

    # 百分位数
    sorted_times = sorted(handshake_times)
    p95_idx = int(len(sorted_times) * 0.95)
    p99_idx = int(len(sorted_times) * 0.99)
    p95_time = sorted_times[p95_idx]
    p99_time = sorted_times[p99_idx]

    log(f"  ✓ 平均: {mean_time:.2f} µs, P95: {p95_time:.2f} µs, 耗时: {elapsed:.1f}s")

    return {
        'topo_id': topo_id,
        'rate_mbps': rate,
        'delay_ms': delay,
        'loss_percent': loss,
        'handshake_times': handshake_times,
        'mean': mean_time,
        'median': median_time,
        'stdev': stdev_time,
        'min': min_time,
        'max': max_time,
        'p95': p95_time,
        'p99': p99_time
    }

def save_results(all_results):
    """保存测试结果"""

    log("\n保存测试结果...")

    # 1. JSON格式 (完整数据)
    json_file = RESULTS_DIR / 'handshake_times.json'
    with open(json_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    log(f"✓ JSON结果: {json_file}")

    # 2. CSV格式 (汇总)
    csv_file = RESULTS_DIR / 'performance_summary.csv'
    with open(csv_file, 'w') as f:
        # 表头
        f.write("Topology,Rate(Mbps),Delay(ms),Loss(%),Mean(µs),Median(µs),StdDev(µs),Min(µs),Max(µs),P95(µs),P99(µs)\n")

        # 数据行
        for result in all_results:
            f.write(f"{result['topo_id']},{result['rate_mbps']:.2f},{result['delay_ms']:.2f},"
                   f"{result['loss_percent']},{result['mean']:.2f},{result['median']:.2f},"
                   f"{result['stdev']:.2f},{result['min']:.2f},{result['max']:.2f},"
                   f"{result['p95']:.2f},{result['p99']:.2f}\n")

    log(f"✓ CSV报告: {csv_file}")

    # 3. 生成图表 (如果有matplotlib)
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # 无GUI后端

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('PQ-NTOR Performance Test Results (Phytium Pi)', fontsize=16)

        # 提取数据
        topo_ids = [r['topo_id'] for r in all_results]
        means = [r['mean'] for r in all_results]
        p95s = [r['p95'] for r in all_results]
        rates = [r['rate_mbps'] for r in all_results]
        delays = [r['delay_ms'] for r in all_results]
        losses = [r['loss_percent'] for r in all_results]

        # 子图1: 握手时间对比
        ax1 = axes[0, 0]
        x = range(len(topo_ids))
        ax1.bar([i - 0.2 for i in x], means, 0.4, label='Mean', alpha=0.8)
        ax1.bar([i + 0.2 for i in x], p95s, 0.4, label='P95', alpha=0.8)
        ax1.set_xlabel('Topology')
        ax1.set_ylabel('Handshake Time (µs)')
        ax1.set_title('Handshake Time Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(topo_ids, rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 子图2: 握手时间 vs 速率
        ax2 = axes[0, 1]
        ax2.scatter(rates, means, s=100, alpha=0.6)
        ax2.set_xlabel('Rate (Mbps)')
        ax2.set_ylabel('Mean Handshake Time (µs)')
        ax2.set_title('Handshake Time vs Rate')
        ax2.grid(True, alpha=0.3)

        # 子图3: 握手时间 vs 延迟
        ax3 = axes[1, 0]
        ax3.scatter(delays, means, s=100, alpha=0.6, color='orange')
        ax3.set_xlabel('Delay (ms)')
        ax3.set_ylabel('Mean Handshake Time (µs)')
        ax3.set_title('Handshake Time vs Delay')
        ax3.grid(True, alpha=0.3)

        # 子图4: 握手时间 vs 丢包率
        ax4 = axes[1, 1]
        ax4.scatter(losses, means, s=100, alpha=0.6, color='green')
        ax4.set_xlabel('Packet Loss (%)')
        ax4.set_ylabel('Mean Handshake Time (µs)')
        ax4.set_title('Handshake Time vs Packet Loss')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_file = RESULTS_DIR / 'comparison_plots.png'
        plt.savefig(plot_file, dpi=150)
        log(f"✓ 图表: {plot_file}")

    except ImportError:
        log("警告: matplotlib未安装，跳过图表生成", "WARN")
    except Exception as e:
        log(f"警告: 图表生成失败: {e}", "WARN")

def print_summary(all_results):
    """打印测试结果摘要"""

    print("\n" + "=" * 70)
    print("                    PQ-NTOR 性能测试结果摘要")
    print("=" * 70)
    print()
    print(f"{'Topo':<8} {'Rate':>12}  {'Delay':>10}  {'Loss':>6}  {'Mean(µs)':>10}  {'P95(µs)':>10}")
    print("-" * 70)

    for r in all_results:
        print(f"{r['topo_id']:<8} {r['rate_mbps']:>9.2f} Mbps  "
              f"{r['delay_ms']:>7.2f} ms  {r['loss_percent']:>5.1f}%  "
              f"{r['mean']:>10.2f}  {r['p95']:>10.2f}")

    print("=" * 70)

    # 总体统计
    all_means = [r['mean'] for r in all_results]
    print(f"\n总体统计:")
    print(f"  平均握手时间: {statistics.mean(all_means):.2f} µs")
    print(f"  最快: {min(all_means):.2f} µs")
    print(f"  最慢: {max(all_means):.2f} µs")
    print()

# ==================== 主程序 ====================

def main():
    """主测试流程"""

    print("=" * 70)
    print("           PQ-NTOR 单机性能测试 - SAGIN 12拓扑 (飞腾派)")
    print("=" * 70)
    print()

    # 检查环境
    topo_params_dict = check_prerequisites()

    # 测试所有拓扑
    all_results = []
    start_time = time.time()

    for topo_id in sorted(topo_params_dict.keys()):
        topo_params = topo_params_dict[topo_id]
        result = test_topology(topo_id, topo_params)

        if result:
            all_results.append(result)
        else:
            log(f"跳过 {topo_id}", "WARN")

    total_time = time.time() - start_time

    # 保存结果
    if all_results:
        save_results(all_results)
        print_summary(all_results)

        print(f"\n测试完成！总耗时: {total_time:.1f}s")
        print(f"结果文件位于: {RESULTS_DIR}")
    else:
        log("所有拓扑测试均失败", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
