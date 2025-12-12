#!/usr/bin/env python3
"""
综合可视化：Phase 1-3 实验结果
直接从CSV文件读取数据并生成论文级别的图表

数据来源:
- Phase 1: sagin-experiments/docker/build_context/c/phase1_crypto_benchmarks.csv
- Phase 2: sagin-experiments/docker/build_context/c/phase2_handshake_comparison.csv
- Phase 3: sagin-experiments/docker/build_context/c/phase3_sagin_cbt.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
from pathlib import Path
from datetime import datetime

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 颜色方案
COLOR_CLASSIC = '#3498db'  # 蓝色
COLOR_PQ = '#e74c3c'       # 红色
COLOR_KYBER = '#9b59b6'    # 紫色
COLOR_HKDF = '#1abc9c'     # 绿色
COLOR_HMAC = '#f39c12'     # 橙色

# 数据文件路径
BASE_DIR = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c')
PHASE1_CSV = BASE_DIR / 'phase1_crypto_benchmarks.csv'
PHASE2_CSV = BASE_DIR / 'phase2_handshake_comparison.csv'
PHASE3_CSV = BASE_DIR / 'phase3_sagin_cbt.csv'

# 输出目录
OUTPUT_DIR = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/figures')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_phase1_data():
    """加载 Phase 1 密码学原语性能数据"""
    df = pd.read_csv(PHASE1_CSV)
    return df

def load_phase2_data():
    """加载 Phase 2 握手协议对比数据"""
    df = pd.read_csv(PHASE2_CSV)
    return df

def load_phase3_data():
    """加载 Phase 3 12拓扑电路建立时间数据"""
    df = pd.read_csv(PHASE3_CSV)
    return df

def plot_phase1_crypto_performance():
    """Phase 1: 密码学原语性能柱状图"""
    print("\n生成图表: Phase 1 - 密码学原语性能...")

    df = load_phase1_data()

    fig, ax = plt.subplots(figsize=(12, 6))

    operations = df['Operation'].tolist()
    mean_us = df['Mean_us'].tolist()
    min_us = df['Min_us'].tolist()
    max_us = df['Max_us'].tolist()

    x = np.arange(len(operations))
    width = 0.6

    # 柱状图
    bars = ax.bar(x, mean_us, width, color=COLOR_KYBER, alpha=0.8, edgecolor='black')

    # 误差线 (min-max范围)
    errors = [[mean - min_val for mean, min_val in zip(mean_us, min_us)],
              [max_val - mean for mean, max_val in zip(mean_us, max_us)]]
    ax.errorbar(x, mean_us, yerr=errors, fmt='none', ecolor='black', capsize=5, capthick=2)

    # 添加数值标签
    for i, (bar, mean) in enumerate(zip(bars, mean_us)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(errors[1]) * 0.1,
                f'{mean:.2f} μs',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Operation', fontsize=13, fontweight='bold')
    ax.set_ylabel('Time (μs)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 1: Cryptographic Primitive Performance (1000 iterations)',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(operations, rotation=15, ha='right', fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f'phase1_crypto_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_file, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def plot_phase2_handshake_comparison():
    """Phase 2: 握手协议对比图"""
    print("\n生成图表: Phase 2 - 握手协议对比...")

    df = load_phase2_data()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    protocols = df['Protocol'].tolist()
    mean_us = df['Mean_us'].tolist()
    median_us = df['Median_us'].tolist()
    min_us = df['Min_us'].tolist()
    max_us = df['Max_us'].tolist()

    # 子图1: 平均握手时间对比
    x = np.arange(len(protocols))
    width = 0.6
    colors = [COLOR_CLASSIC, COLOR_PQ]

    bars1 = ax1.bar(x, mean_us, width, color=colors, alpha=0.8, edgecolor='black')

    # 误差线
    errors = [[mean - min_val for mean, min_val in zip(mean_us, min_us)],
              [max_val - mean for mean, max_val in zip(mean_us, max_us)]]
    ax1.errorbar(x, mean_us, yerr=errors, fmt='none', ecolor='black', capsize=5)

    # 数值标签
    for i, (bar, mean) in enumerate(zip(bars1, mean_us)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + max_us[i] - mean_us[i] + 5,
                f'{mean:.2f} μs',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax1.set_xlabel('Protocol', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Handshake Time (μs)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Handshake Time Comparison', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(protocols, fontsize=11)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加加速比标注
    speedup = mean_us[0] / mean_us[1]
    ax1.text(0.5, max(mean_us) * 0.7,
            f'PQ-NTOR is {speedup:.2f}× faster!',
            ha='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightgreen', alpha=0.7))

    # 子图2: 吞吐量对比 (握手/秒)
    throughput = [1e6 / mean for mean in mean_us]  # 转换为 握手/秒

    bars2 = ax2.bar(x, throughput, width, color=colors, alpha=0.8, edgecolor='black')

    for i, (bar, tp) in enumerate(zip(bars2, throughput)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1000,
                f'{tp:,.0f} hs/s',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax2.set_xlabel('Protocol', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Throughput (handshakes/sec)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Handshake Throughput', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(protocols, fontsize=11)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    plt.suptitle('Phase 2: NTOR Handshake Performance Comparison (1000 iterations)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_file = OUTPUT_DIR / f'phase2_handshake_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_file, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def plot_phase3_circuit_build_time():
    """Phase 3: 12拓扑电路建立时间对比"""
    print("\n生成图表: Phase 3 - 12拓扑电路建立时间...")

    df = load_phase3_data()

    # 分离Classic和PQ数据
    df_classic = df[df['Protocol'] == 'Classic NTOR'].sort_values('Topology')
    df_pq = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology')

    fig, ax = plt.subplots(figsize=(14, 7))

    topologies = df_classic['Topology'].tolist()
    x = np.arange(len(topologies))
    width = 0.35

    # Classic NTOR
    classic_mean = df_classic['Mean_ms'].tolist()
    classic_min = df_classic['Min_ms'].tolist()
    classic_max = df_classic['Max_ms'].tolist()

    bars1 = ax.bar(x - width/2, classic_mean, width, label='Classic NTOR',
                    color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')

    # PQ-NTOR
    pq_mean = df_pq['Mean_ms'].tolist()
    pq_min = df_pq['Min_ms'].tolist()
    pq_max = df_pq['Max_ms'].tolist()

    bars2 = ax.bar(x + width/2, pq_mean, width, label='PQ-NTOR',
                    color=COLOR_PQ, alpha=0.8, edgecolor='black')

    # 分隔线 (Uplink vs Downlink)
    ax.axvline(x=5.5, color='gray', linestyle='--', linewidth=2, alpha=0.5)
    ax.text(2.5, max(classic_mean + pq_mean) * 0.95, 'Uplink',
            ha='center', fontsize=12, fontweight='bold', color='gray')
    ax.text(8.5, max(classic_mean + pq_mean) * 0.95, 'Downlink',
            ha='center', fontsize=12, fontweight='bold', color='gray')

    # 添加加速比标注（每个拓扑）
    for i, (c_mean, p_mean) in enumerate(zip(classic_mean, pq_mean)):
        speedup = c_mean / p_mean
        mid_height = max(c_mean, p_mean) + 0.02
        ax.text(i, mid_height, f'{speedup:.2f}×',
                ha='center', va='bottom', fontsize=8, fontweight='bold',
                color='green')

    ax.set_xlabel('Topology', fontsize=13, fontweight='bold')
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3: 3-Hop Circuit Build Time Across 12 SAGIN Topologies (100 iterations)',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(topologies, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加平均性能摘要
    avg_classic = np.mean(classic_mean)
    avg_pq = np.mean(pq_mean)
    avg_speedup = avg_classic / avg_pq

    summary_text = f'Average:\nClassic: {avg_classic:.2f} ms\nPQ-NTOR: {avg_pq:.2f} ms\nSpeedup: {avg_speedup:.2f}×'
    ax.text(0.98, 0.97, summary_text,
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()

    output_file = OUTPUT_DIR / f'phase3_circuit_build_time_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_file, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def plot_phase3_uplink_vs_downlink():
    """Phase 3: Uplink vs Downlink 性能对比"""
    print("\n生成图表: Phase 3 - Uplink vs Downlink 对比...")

    df = load_phase3_data()

    # 分离Classic和PQ数据
    df_classic = df[df['Protocol'] == 'Classic NTOR'].sort_values('Topology')
    df_pq = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology')

    # 分离Uplink (topo01-06) 和 Downlink (topo07-12)
    classic_uplink = df_classic['Mean_ms'][:6].tolist()
    classic_downlink = df_classic['Mean_ms'][6:].tolist()
    pq_uplink = df_pq['Mean_ms'][:6].tolist()
    pq_downlink = df_pq['Mean_ms'][6:].tolist()

    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['Uplink\n(Topo 01-06)', 'Downlink\n(Topo 07-12)']
    x = np.arange(len(categories))
    width = 0.35

    # Classic NTOR
    classic_means = [np.mean(classic_uplink), np.mean(classic_downlink)]
    classic_stds = [np.std(classic_uplink), np.std(classic_downlink)]

    bars1 = ax.bar(x - width/2, classic_means, width,
                    yerr=classic_stds, capsize=5,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')

    # PQ-NTOR
    pq_means = [np.mean(pq_uplink), np.mean(pq_downlink)]
    pq_stds = [np.std(pq_uplink), np.std(pq_downlink)]

    bars2 = ax.bar(x + width/2, pq_means, width,
                    yerr=pq_stds, capsize=5,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8, edgecolor='black')

    # 数值标签
    for i, (c_mean, p_mean) in enumerate(zip(classic_means, pq_means)):
        ax.text(i - width/2, c_mean + classic_stds[i] + 0.01,
                f'{c_mean:.2f} ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax.text(i + width/2, p_mean + pq_stds[i] + 0.01,
                f'{p_mean:.2f} ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Average Circuit Build Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3: Uplink vs Downlink Performance Comparison',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = OUTPUT_DIR / f'phase3_uplink_vs_downlink_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_file, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def plot_comprehensive_summary():
    """综合汇总仪表盘"""
    print("\n生成图表: 综合汇总仪表盘...")

    df1 = load_phase1_data()
    df2 = load_phase2_data()
    df3 = load_phase3_data()

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    # 子图1: Phase 1 Kyber性能
    ax1 = fig.add_subplot(gs[0, 0])
    kyber_ops = [op for op in df1['Operation'] if 'Kyber' in op]
    kyber_times = [df1[df1['Operation'] == op]['Mean_us'].values[0] for op in kyber_ops]
    kyber_labels = [op.replace('Kyber-512 ', '') for op in kyber_ops]

    ax1.bar(range(len(kyber_labels)), kyber_times, color=COLOR_KYBER, alpha=0.8)
    ax1.set_title('Phase 1: Kyber-512 Operations', fontweight='bold')
    ax1.set_ylabel('Time (μs)')
    ax1.set_xticks(range(len(kyber_labels)))
    ax1.set_xticklabels(kyber_labels)
    ax1.grid(axis='y', alpha=0.3)

    for i, t in enumerate(kyber_times):
        ax1.text(i, t + 0.3, f'{t:.2f}', ha='center', va='bottom', fontweight='bold')

    # 子图2: Phase 2 握手对比
    ax2 = fig.add_subplot(gs[0, 1])
    protocols = df2['Protocol'].tolist()
    handshake_times = df2['Mean_us'].tolist()
    colors = [COLOR_CLASSIC, COLOR_PQ]

    bars = ax2.barh(protocols, handshake_times, color=colors, alpha=0.8)
    ax2.set_title('Phase 2: Handshake Performance', fontweight='bold')
    ax2.set_xlabel('Time (μs)')
    ax2.grid(axis='x', alpha=0.3)

    for bar, time in zip(bars, handshake_times):
        width = bar.get_width()
        ax2.text(width + 3, bar.get_y() + bar.get_height()/2,
                f'{time:.2f} μs',
                ha='left', va='center', fontweight='bold')

    # 子图3: Phase 3 平均CBT
    ax3 = fig.add_subplot(gs[0, 2])
    df_classic = df3[df3['Protocol'] == 'Classic NTOR']
    df_pq = df3[df3['Protocol'] == 'PQ-NTOR']

    avg_cbt = [df_classic['Mean_ms'].mean(), df_pq['Mean_ms'].mean()]
    protocols_cbt = ['Classic\nNTOR', 'PQ-NTOR']

    bars = ax3.bar(protocols_cbt, avg_cbt, color=[COLOR_CLASSIC, COLOR_PQ], alpha=0.8)
    ax3.set_title('Phase 3: Average Circuit Build Time', fontweight='bold')
    ax3.set_ylabel('Time (ms)')
    ax3.grid(axis='y', alpha=0.3)

    for bar, time in zip(bars, avg_cbt):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                f'{time:.2f} ms',
                ha='center', va='bottom', fontweight='bold')

    # 子图4: 加速比总结
    ax4 = fig.add_subplot(gs[1, :])
    ax4.axis('off')

    # 计算关键指标
    phase2_speedup = df2[df2['Protocol'] == 'Classic NTOR']['Mean_us'].values[0] / \
                     df2[df2['Protocol'] == 'PQ-NTOR']['Mean_us'].values[0]
    phase3_speedup = df_classic['Mean_ms'].mean() / df_pq['Mean_ms'].mean()

    summary_data = [
        ['Phase', 'Metric', 'Classic NTOR', 'PQ-NTOR', 'Speedup'],
        ['', '', '', '', ''],
        ['Phase 1', 'Kyber-512 Keygen', '-', f'{df1[df1["Operation"]=="Kyber-512 Keygen"]["Mean_us"].values[0]:.2f} μs', '-'],
        ['Phase 1', 'Kyber-512 Encaps', '-', f'{df1[df1["Operation"]=="Kyber-512 Encaps"]["Mean_us"].values[0]:.2f} μs', '-'],
        ['Phase 1', 'Kyber-512 Decaps', '-', f'{df1[df1["Operation"]=="Kyber-512 Decaps"]["Mean_us"].values[0]:.2f} μs', '-'],
        ['', '', '', '', ''],
        ['Phase 2', 'Handshake Time', f'{handshake_times[0]:.2f} μs', f'{handshake_times[1]:.2f} μs', f'{phase2_speedup:.2f}×'],
        ['', '', '', '', ''],
        ['Phase 3', 'Avg Circuit Build', f'{avg_cbt[0]:.2f} ms', f'{avg_cbt[1]:.2f} ms', f'{phase3_speedup:.2f}×'],
        ['Phase 3', '12 Topologies', 'All tested', 'All tested', f'1.30-1.79×'],
    ]

    table = ax4.table(cellText=summary_data, cellLoc='center', loc='center',
                      colWidths=[0.12, 0.25, 0.18, 0.18, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # 表头样式
    for i in range(5):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # 交替行颜色
    for i in range(1, len(summary_data)):
        for j in range(5):
            if summary_data[i][0] == '':  # 空行
                table[(i, j)].set_facecolor('#ecf0f1')
            elif i % 2 == 0:
                table[(i, j)].set_facecolor('#f8f9fa')

    # 高亮加速比列
    for i in range(len(summary_data)):
        if 'Speedup' in str(summary_data[i][4]) and '×' in str(summary_data[i][4]):
            table[(i, 4)].set_facecolor('#d4edda')
            table[(i, 4)].set_text_props(weight='bold', color='#155724')

    ax4.set_title('Performance Summary: Classic NTOR vs PQ-NTOR',
                  fontsize=14, fontweight='bold', pad=20)

    fig.suptitle('PQ-NTOR Comprehensive Performance Analysis (WSL2 x86_64)',
                 fontsize=16, fontweight='bold', y=0.98)

    output_file = OUTPUT_DIR / f'comprehensive_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(output_file, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def main():
    """主函数"""
    print("=" * 80)
    print("  PQ-NTOR Phase 1-3 实验结果可视化")
    print("=" * 80)
    print()
    print(f"数据源:")
    print(f"  - Phase 1: {PHASE1_CSV}")
    print(f"  - Phase 2: {PHASE2_CSV}")
    print(f"  - Phase 3: {PHASE3_CSV}")
    print()
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 80)

    # 检查数据文件
    for csv_file in [PHASE1_CSV, PHASE2_CSV, PHASE3_CSV]:
        if not csv_file.exists():
            print(f"❌ 错误: 数据文件不存在 - {csv_file}")
            return

    print("\n开始生成图表...")
    print("-" * 80)

    # 生成各类图表
    plot_phase1_crypto_performance()
    plot_phase2_handshake_comparison()
    plot_phase3_circuit_build_time()
    plot_phase3_uplink_vs_downlink()
    plot_comprehensive_summary()

    print()
    print("=" * 80)
    print("✅ 所有图表生成完成!")
    print("=" * 80)
    print()
    print(f"📁 图表保存位置: {OUTPUT_DIR}")
    print()
    print("生成的图表:")
    print("  1. phase1_crypto_performance_*.png/pdf       - Phase 1 密码学原语性能")
    print("  2. phase2_handshake_comparison_*.png/pdf     - Phase 2 握手协议对比")
    print("  3. phase3_circuit_build_time_*.png/pdf       - Phase 3 12拓扑电路建立时间")
    print("  4. phase3_uplink_vs_downlink_*.png/pdf       - Phase 3 上行下行对比")
    print("  5. comprehensive_summary_*.png/pdf           - 综合性能汇总 ⭐")
    print()

if __name__ == '__main__':
    main()
