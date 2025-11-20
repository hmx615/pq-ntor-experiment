#!/usr/bin/env python3
"""
PQ-Ntor 性能测试数据可视化脚本

读取 benchmark_results.csv 并生成可视化图表
"""

import csv
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import sys
import os

# 使用非交互式后端（服务器环境）
matplotlib.use('Agg')

# 中文字体设置（如果需要）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

def read_benchmark_data(filename):
    """读取 CSV 数据"""
    operations = []
    avg_times = []
    min_times = []
    max_times = []
    median_times = []

    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                operations.append(row['Operation'])
                # CSV 只有 μs 和 ms 列，我们使用 ms 列
                avg_times.append(float(row['Avg(ms)']))
                min_times.append(float(row['Min(ms)']))
                # 从 μs 列转换为 ms
                max_times.append(float(row['Max(μs)']) / 1000.0)
                median_times.append(float(row['Median(μs)']) / 1000.0)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        print("Please run the benchmark first: ./benchmark_pq_ntor")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    return operations, avg_times, min_times, max_times, median_times

def plot_operation_times(operations, avg_times, min_times, max_times, filename='operation_times.png'):
    """绘制各操作时间对比图"""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(operations))
    width = 0.25

    # 绘制柱状图
    bars1 = ax.bar(x - width, min_times, width, label='Min', alpha=0.8, color='#2ecc71')
    bars2 = ax.bar(x, avg_times, width, label='Average', alpha=0.8, color='#3498db')
    bars3 = ax.bar(x + width, max_times, width, label='Max', alpha=0.8, color='#e74c3c')

    # 设置标签和标题
    ax.set_xlabel('Operation', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-Ntor Handshake Performance Breakdown', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(operations, rotation=15, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 添加数值标签
    def autolabel(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=8)

    autolabel(bars2)  # 只标注平均值

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.close()

def plot_handshake_breakdown(operations, avg_times, filename='handshake_breakdown.png'):
    """绘制握手流程时间分解饼图"""
    # 只取前三个步骤（不包括完整握手）
    ops = operations[:3]
    times = avg_times[:3]

    fig, ax = plt.subplots(figsize=(10, 8))

    colors = ['#3498db', '#e74c3c', '#2ecc71']
    explode = (0.05, 0.05, 0.05)

    wedges, texts, autotexts = ax.pie(times, explode=explode, labels=ops,
                                        autopct='%1.1f%%', startangle=90,
                                        colors=colors, textprops={'fontsize': 11})

    # 添加时间标签
    for i, (wedge, autotext) in enumerate(zip(wedges, autotexts)):
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)

    ax.set_title('PQ-Ntor Handshake Time Distribution', fontsize=14, fontweight='bold', pad=20)

    # 添加图例（显示具体时间）
    legend_labels = [f"{op}: {time:.2f} ms" for op, time in zip(ops, times)]
    ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.close()

def plot_comparison_with_ntor(avg_times, filename='ntor_comparison.png'):
    """与原始 Ntor 对比（假设数据）"""
    # 原始 Ntor 预估时间（基于文献）
    # 这些是示例值，可以根据实际情况调整
    ntor_client_create = 0.15   # ms
    ntor_server_reply = 0.20     # ms
    ntor_client_finish = 0.10    # ms
    ntor_full = ntor_client_create + ntor_server_reply + ntor_client_finish

    pq_ntor_full = avg_times[3]  # 完整握手时间

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 子图1: 总时间对比
    protocols = ['Original Ntor\n(Curve25519)', 'PQ-Ntor\n(Kyber512)']
    total_times = [ntor_full, pq_ntor_full]
    colors_bar = ['#95a5a6', '#e74c3c']

    bars = ax1.bar(protocols, total_times, color=colors_bar, alpha=0.8, width=0.6)
    ax1.set_ylabel('Total Handshake Time (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('Total Handshake Time Comparison', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # 添加数值和倍数标签
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f} ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 添加倍数标注
    overhead = pq_ntor_full / ntor_full
    ax1.text(0.5, max(total_times) * 0.6,
            f'{overhead:.1f}× slower',
            ha='center', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    # 子图2: 详细步骤对比
    steps = ['Client\nCreate', 'Server\nReply', 'Client\nFinish']
    ntor_times = [ntor_client_create, ntor_server_reply, ntor_client_finish]
    pq_ntor_times = avg_times[:3]

    x = np.arange(len(steps))
    width = 0.35

    bars1 = ax2.bar(x - width/2, ntor_times, width, label='Original Ntor',
                    color='#95a5a6', alpha=0.8)
    bars2 = ax2.bar(x + width/2, pq_ntor_times, width, label='PQ-Ntor',
                    color='#e74c3c', alpha=0.8)

    ax2.set_ylabel('Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Step-by-Step Comparison', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(steps)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.close()

def plot_overhead_analysis(operations, avg_times, filename='overhead_analysis.png'):
    """通信开销与计算开销综合分析"""
    fig, ax = plt.subplots(figsize=(12, 8))

    # 数据准备
    categories = ['Original Ntor', 'PQ-Ntor (Kyber512)']

    # 通信开销 (bytes)
    comm_overhead = [148, 1620]

    # 计算时间 (ms) - 使用完整握手时间
    comp_time = [0.45, avg_times[3]]  # 原始 Ntor 假设值 vs PQ-Ntor 实测

    # 创建双 Y 轴图
    x = np.arange(len(categories))
    width = 0.35

    ax1 = ax
    color1 = '#3498db'
    ax1.bar(x - width/2, comm_overhead, width, label='Communication (bytes)',
            color=color1, alpha=0.8)
    ax1.set_xlabel('Protocol', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Communication Overhead (bytes)', color=color1,
                   fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)

    # 添加数值标签
    for i, v in enumerate(comm_overhead):
        ax1.text(i - width/2, v, f'{v} B',
                ha='center', va='bottom', fontweight='bold')

    # 第二个 Y 轴
    ax2 = ax1.twinx()
    color2 = '#e74c3c'
    ax2.bar(x + width/2, comp_time, width, label='Computation (ms)',
            color=color2, alpha=0.8)
    ax2.set_ylabel('Computation Time (ms)', color=color2,
                   fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color2)

    # 添加数值标签
    for i, v in enumerate(comp_time):
        ax2.text(i + width/2, v, f'{v:.2f} ms',
                ha='center', va='bottom', fontweight='bold')

    # 标题和图例
    ax1.set_title('PQ-Ntor Overhead Analysis: Communication vs Computation',
                  fontsize=14, fontweight='bold', pad=20)

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    ax1.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.close()

def generate_latex_table(operations, avg_times, median_times, min_times, max_times,
                         filename='performance_table.tex'):
    """生成 LaTeX 格式的性能表格"""
    with open(filename, 'w') as f:
        f.write("% PQ-Ntor Performance Table (LaTeX)\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\caption{PQ-Ntor Handshake Performance (Kyber512)}\n")
        f.write("\\label{tab:pq-ntor-performance}\n")
        f.write("\\begin{tabular}{lrrrr}\n")
        f.write("\\hline\n")
        f.write("Operation & Min (ms) & Avg (ms) & Median (ms) & Max (ms) \\\\\n")
        f.write("\\hline\n")

        for i, op in enumerate(operations):
            # 格式化操作名称
            op_name = op.replace('_', '\\_')
            f.write(f"{op_name} & {min_times[i]:.2f} & {avg_times[i]:.2f} & "
                   f"{median_times[i]:.2f} & {max_times[i]:.2f} \\\\\n")

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"✓ Saved: {filename}")

def main():
    """主函数"""
    print("=" * 70)
    print("PQ-Ntor Performance Data Visualization")
    print("=" * 70)

    # 读取数据
    csv_file = 'benchmark_results.csv'
    if not os.path.exists(csv_file):
        print(f"\nError: {csv_file} not found!")
        print("Please run the benchmark first:")
        print("  cd ~/pq-ntor-experiment/c")
        print("  make benchmark")
        print("  ./benchmark_pq_ntor")
        sys.exit(1)

    print(f"\nReading data from: {csv_file}")
    operations, avg_times, min_times, max_times, median_times = read_benchmark_data(csv_file)

    print(f"Found {len(operations)} operations\n")

    # 生成图表
    print("Generating visualizations...")
    print("-" * 70)

    plot_operation_times(operations, avg_times, min_times, max_times)
    plot_handshake_breakdown(operations, avg_times)
    plot_comparison_with_ntor(avg_times)
    plot_overhead_analysis(operations, avg_times)

    # 生成 LaTeX 表格
    print("\nGenerating LaTeX table...")
    print("-" * 70)
    generate_latex_table(operations, avg_times, median_times, min_times, max_times)

    print("\n" + "=" * 70)
    print("✅ All visualizations generated successfully!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - operation_times.png       : Bar chart of operation times")
    print("  - handshake_breakdown.png   : Pie chart of handshake distribution")
    print("  - ntor_comparison.png       : Comparison with original Ntor")
    print("  - overhead_analysis.png     : Communication vs computation overhead")
    print("  - performance_table.tex     : LaTeX table for paper")
    print("\n")

if __name__ == '__main__':
    main()
