#!/usr/bin/env python3
"""
综合可视化：Phase 1 密码学原语 + Phase 2 文献对比 + Phase 3 SAGIN拓扑分析
支持三种协议：Classic NTOR、PQ-NTOR、Hybrid NTOR
生成单独的PDF文件，保存到figure文件夹
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages
import os

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# 颜色方案 - 三种协议
COLOR_CLASSIC = '#3498db'  # 蓝色 - Classic NTOR
COLOR_PQ = '#e74c3c'       # 红色 - PQ-NTOR
COLOR_HYBRID = '#2ecc71'   # 绿色 - Hybrid NTOR
COLOR_OVERHEAD = '#f39c12' # 橙色 - 开销
COLOR_LITERATURE = '#95a5a6'  # 灰色 - 文献

# ============================================================================
# Phase 1: 密码学原语基准测试数据
# ============================================================================

PHASE1_CSV_PATH = '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase1_crypto_benchmarks.csv'

# ============================================================================
# Phase 2: 文献对比数据
# ============================================================================

PHASE2_DATA = {
    'Platform': ['Intel x86\n(Tor)', 'Hardware\nResearch', 'Raspberry\nPi 4', 'Phytium Pi\n(Ours)'],
    'Classic_NTOR_min': [100, 20, 60, 60],
    'Classic_NTOR_max': [150, 30, 100, 100],
    'PQ_NTOR_min': [650, 100, 263, 181.64],
    'PQ_NTOR_max': [650, 200, 263, 181.64],
    'Overhead_min': [4.3, 3.3, 2.6, 1.8],
    'Overhead_max': [6.5, 10.0, 4.4, 3.0],
    'Source': ['arXiv\n2025/479', 'Hardware\nImpl.', 'MDPI\n2023', 'This\nWork']
}

# ============================================================================
# Phase 1 图表生成函数
# ============================================================================

def create_phase1_fig1_crypto_performance(output_dir='.'):
    """Phase 1 - 图1: 密码学原语性能对比柱状图"""

    df = pd.read_csv(PHASE1_CSV_PATH)

    fig, ax = plt.subplots(figsize=(12, 7))

    operations = df['Operation'].tolist()
    means = df['Mean_us'].tolist()
    stds = df['StdDev_us'].tolist()

    # 为不同类型的操作使用不同颜色
    colors = []
    for op in operations:
        if 'Kyber' in op:
            colors.append(COLOR_PQ)  # Kyber操作用红色
        else:
            colors.append(COLOR_CLASSIC)  # HKDF/HMAC用蓝色

    x = np.arange(len(operations))
    bars = ax.bar(x, means, yerr=stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')

    # 添加数值标签
    for i, (mean, std) in enumerate(zip(means, stds)):
        ax.text(i, mean + std + 0.5, f'{mean:.2f} µs',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Cryptographic Operation', fontsize=13, fontweight='bold')
    ax.set_ylabel('Execution Time (µs)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 1: Cryptographic Primitives Performance (Phytium Pi)',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(operations, rotation=30, ha='right', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_PQ, alpha=0.8, label='ML-KEM (Kyber) Operations'),
        Patch(facecolor=COLOR_CLASSIC, alpha=0.8, label='Symmetric Operations')
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='upper right')

    # 设置Y轴范围
    ax.set_ylim([0, max(means) * 1.3])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase1_fig1_crypto_performance.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 1 图1: {output_file}")
    plt.close()


def create_phase1_fig2_crypto_breakdown(output_dir='.'):
    """Phase 1 - 图2: 密码学操作时间分解饼图"""

    df = pd.read_csv(PHASE1_CSV_PATH)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 左图：Kyber操作分解
    kyber_ops = df[df['Operation'].str.contains('Kyber')]
    kyber_labels = [op.replace('Kyber-512 ', '') for op in kyber_ops['Operation']]
    kyber_values = kyber_ops['Mean_us'].tolist()

    colors_kyber = ['#e74c3c', '#c0392b', '#a93226']
    wedges1, texts1, autotexts1 = ax1.pie(kyber_values, labels=kyber_labels, autopct='%1.1f%%',
                                          colors=colors_kyber, startangle=90,
                                          explode=(0.05, 0.05, 0.05))
    ax1.set_title('ML-KEM-512 (Kyber) Operations\nTotal: {:.2f} µs'.format(sum(kyber_values)),
                  fontsize=12, fontweight='bold')

    # 右图：对称操作分解
    sym_ops = df[~df['Operation'].str.contains('Kyber')]
    sym_labels = sym_ops['Operation'].tolist()
    sym_values = sym_ops['Mean_us'].tolist()

    colors_sym = ['#3498db', '#2980b9']
    wedges2, texts2, autotexts2 = ax2.pie(sym_values, labels=sym_labels, autopct='%1.1f%%',
                                          colors=colors_sym, startangle=90,
                                          explode=(0.05, 0.05))
    ax2.set_title('Symmetric Operations\nTotal: {:.2f} µs'.format(sum(sym_values)),
                  fontsize=12, fontweight='bold')

    # 设置自动文本样式
    for autotext in autotexts1 + autotexts2:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')

    plt.suptitle('Phase 1: Cryptographic Operation Time Breakdown',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase1_fig2_crypto_breakdown.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 1 图2: {output_file}")
    plt.close()


def create_phase1_fig3_crypto_statistics(output_dir='.'):
    """Phase 1 - 图3: 统计信息表格"""

    df = pd.read_csv(PHASE1_CSV_PATH)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('off')

    # 创建表格数据
    table_data = []
    table_data.append(['Operation', 'Mean (µs)', 'Std Dev', 'Min', 'Max', 'P95', 'P99', '95% CI'])

    for _, row in df.iterrows():
        ci = f"[{row['CI_Lower']:.2f}, {row['CI_Upper']:.2f}]"
        table_data.append([
            row['Operation'],
            f"{row['Mean_us']:.2f}",
            f"{row['StdDev_us']:.2f}",
            f"{row['Min_us']:.2f}",
            f"{row['Max_us']:.2f}",
            f"{row['P95_us']:.2f}",
            f"{row['P99_us']:.2f}",
            ci
        ])

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # 设置表头样式
    for i in range(8):
        cell = table[(0, i)]
        cell.set_facecolor('#34495e')
        cell.set_text_props(weight='bold', color='white', fontsize=11)

    # Kyber行用红色背景
    for row_idx in [1, 2, 3]:
        for col_idx in range(8):
            cell = table[(row_idx, col_idx)]
            cell.set_facecolor('#ffe6e6')

    # 对称操作行用蓝色背景
    for row_idx in [4, 5]:
        for col_idx in range(8):
            cell = table[(row_idx, col_idx)]
            cell.set_facecolor('#e6f2ff')

    ax.set_title('Phase 1: Cryptographic Primitives Statistics (1000 iterations)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase1_fig3_crypto_statistics.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 1 图3: {output_file}")
    plt.close()


# ============================================================================
# Phase 2 图表生成函数
# ============================================================================

def create_phase2_fig1_handshake_comparison(output_dir='.'):
    """Phase 2 - 图1: 握手时间对比"""

    fig, ax = plt.subplots(figsize=(12, 7))
    df = pd.DataFrame(PHASE2_DATA)
    x = np.arange(len(df))
    width = 0.35

    # Classic NTOR
    classic_mean = (df['Classic_NTOR_min'] + df['Classic_NTOR_max']) / 2
    classic_err = (df['Classic_NTOR_max'] - df['Classic_NTOR_min']) / 2

    bars1 = ax.bar(x - width/2, classic_mean, width,
                    yerr=classic_err, capsize=5,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)

    # PQ-NTOR
    pq_mean = (df['PQ_NTOR_min'] + df['PQ_NTOR_max']) / 2
    pq_err = (df['PQ_NTOR_max'] - df['PQ_NTOR_min']) / 2

    bars2 = ax.bar(x + width/2, pq_mean, width,
                    yerr=pq_err, capsize=5,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # 添加数值标签
    for i, (c_mean, p_mean) in enumerate(zip(classic_mean, pq_mean)):
        ax.text(i - width/2, c_mean + classic_err.iloc[i] + 20,
                f'{c_mean:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(i + width/2, p_mean + pq_err.iloc[i] + 20,
                f'{p_mean:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Platform', fontsize=13, fontweight='bold')
    ax.set_ylabel('Handshake Time (µs)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 2: Handshake Performance Comparison (Literature vs Our Work)',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Platform'], fontsize=11)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, max(pq_mean + pq_err) * 1.15])

    # 添加数据源注释
    for i, source in enumerate(df['Source']):
        ax.text(i, -50, source, ha='center', va='top',
                fontsize=9, style='italic', color='gray')

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase2_fig1_handshake_comparison.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 2 图1: {output_file}")
    plt.close()


def create_phase2_fig2_overhead_comparison(output_dir='.'):
    """Phase 2 - 图2: PQ开销倍数对比"""

    fig, ax = plt.subplots(figsize=(10, 6))
    df = pd.DataFrame(PHASE2_DATA)
    x = np.arange(len(df))
    width = 0.7

    overhead_mean = (df['Overhead_min'] + df['Overhead_max']) / 2
    overhead_err = (df['Overhead_max'] - df['Overhead_min']) / 2

    bars = ax.bar(x, overhead_mean, width,
                   yerr=overhead_err, capsize=5,
                   color=COLOR_OVERHEAD, alpha=0.8)

    # 突出显示我们的结果
    bars[-1].set_color(COLOR_PQ)
    bars[-1].set_alpha(1.0)
    bars[-1].set_edgecolor('darkred')
    bars[-1].set_linewidth(2)

    # 添加数值标签
    for i, (o_mean, o_err) in enumerate(zip(overhead_mean, overhead_err)):
        label = f'{o_mean:.1f}×'
        if i == len(overhead_mean) - 1:  # 我们的数据
            ax.text(i, o_mean + o_err + 0.3, label,
                    ha='center', va='bottom', fontsize=12, fontweight='bold', color='darkred')
        else:
            ax.text(i, o_mean + o_err + 0.3, label,
                    ha='center', va='bottom', fontsize=11)

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, label='Baseline (1.0×)')
    ax.set_xlabel('Platform', fontsize=13, fontweight='bold')
    ax.set_ylabel('PQ-NTOR Overhead (×)', fontsize=13, fontweight='bold')
    ax.set_title('PQ-NTOR Relative Overhead Comparison', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Platform'], fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, max(overhead_mean + overhead_err) * 1.15])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase2_fig2_overhead_comparison.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 2 图2: {output_file}")
    plt.close()


def create_phase2_fig3_summary_table(output_dir='.'):
    """Phase 2 - 图3: 性能汇总表"""

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')

    df = pd.DataFrame(PHASE2_DATA)

    # 创建表格数据
    table_data = []
    table_data.append(['Platform', 'Classic (µs)', 'PQ (µs)', 'Overhead', 'Source'])

    for i, row in df.iterrows():
        platform = row['Platform'].replace('\n', ' ')
        classic_range = f"{row['Classic_NTOR_min']:.0f}-{row['Classic_NTOR_max']:.0f}"
        if row['PQ_NTOR_min'] == row['PQ_NTOR_max']:
            pq_value = f"{row['PQ_NTOR_min']:.1f}"
        else:
            pq_value = f"{row['PQ_NTOR_min']:.0f}-{row['PQ_NTOR_max']:.0f}"
        overhead_range = f"{row['Overhead_min']:.1f}-{row['Overhead_max']:.1f}×"
        source = row['Source'].replace('\n', ' ')

        table_data.append([platform, classic_range, pq_value, overhead_range, source])

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 3)

    # 设置表头样式
    for i in range(5):
        cell = table[(0, i)]
        cell.set_facecolor('#34495e')
        cell.set_text_props(weight='bold', color='white', fontsize=12)

    # 突出显示我们的数据行
    for i in range(5):
        cell = table[(4, i)]  # 最后一行
        cell.set_facecolor('#ffe6e6')
        cell.set_text_props(weight='bold')

    ax.set_title('Phase 2: Performance Summary Table', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase2_fig3_summary_table.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 2 图3: {output_file}")
    plt.close()


# ============================================================================
# Phase 3 图表生成函数 - 支持三种协议
# ============================================================================

def load_phase3_data(csv_path):
    """加载并处理Phase 3数据，支持三种协议"""
    df = pd.read_csv(csv_path)

    classic_data = df[df['Protocol'].str.contains('Classic')].sort_values('Topology').reset_index(drop=True)
    pq_data = df[df['Protocol'].str.contains('PQ-NTOR')].sort_values('Topology').reset_index(drop=True)
    hybrid_data = df[df['Protocol'].str.contains('Hybrid')].sort_values('Topology').reset_index(drop=True)

    # 创建合并的数据框
    merged = pq_data.copy()
    merged['Classic_CBT_ms'] = classic_data['Total_CBT_ms'].values
    merged['Classic_Network_Ratio'] = classic_data['Network_Ratio'].values
    merged['Hybrid_CBT_ms'] = hybrid_data['Total_CBT_ms'].values
    merged['Hybrid_Network_Ratio'] = hybrid_data['Network_Ratio'].values

    # 计算开销
    merged['PQ_Overhead'] = merged['Total_CBT_ms'] / merged['Classic_CBT_ms']
    merged['PQ_Overhead_Abs'] = merged['Total_CBT_ms'] - merged['Classic_CBT_ms']
    merged['Hybrid_Overhead'] = merged['Hybrid_CBT_ms'] / merged['Classic_CBT_ms']
    merged['Hybrid_Overhead_Abs'] = merged['Hybrid_CBT_ms'] - merged['Classic_CBT_ms']

    return merged


def create_phase3_fig1_cbt_comparison(csv_path, output_dir='.'):
    """Phase 3 - 图1: 三种协议端到端CBT对比"""

    merged = load_phase3_data(csv_path)
    # 按PQ-NTOR的总CBT降序排序
    sorted_data = merged.sort_values('Total_CBT_ms', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(16, 8))

    x = np.arange(len(sorted_data))
    width = 0.25

    # 三种协议的柱状图
    bars1 = ax.bar(x - width, sorted_data['Classic_CBT_ms'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax.bar(x, sorted_data['Total_CBT_ms'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)
    bars3 = ax.bar(x + width, sorted_data['Hybrid_CBT_ms'], width,
                    label='Hybrid NTOR', color=COLOR_HYBRID, alpha=0.8)

    # 添加网络参数注释
    for i, row in sorted_data.iterrows():
        bw = row['Bandwidth_Mbps']
        delay = row['Link_Delay_ms']
        loss = row['Loss_Percent']

        max_cbt = max(row['Classic_CBT_ms'], row['Total_CBT_ms'], row['Hybrid_CBT_ms'])

        if bw > 25:
            color = 'green'
        elif bw > 10:
            color = 'orange'
        else:
            color = 'red'

        ax.text(i, max_cbt + 1.5,
                f'{bw:.1f}Mbps\n{delay:.1f}ms\n{loss:.1f}%loss',
                ha='center', va='bottom', fontsize=7, color=color, fontweight='bold')

    ax.set_xlabel('SAGIN Topology (Sorted by PQ-NTOR CBT)', fontsize=13, fontweight='bold')
    ax.set_ylabel('End-to-End CBT (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3: Circuit Build Time Comparison - Three Protocols',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_data['Topology'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 30])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig1_cbt_comparison.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图1: {output_file}")
    plt.close()


def create_phase3_fig2_overhead_ratio(csv_path, output_dir='.'):
    """Phase 3 - 图2: 开销倍数（双Y轴折线+柱状图）- 三条折线"""

    merged = load_phase3_data(csv_path)

    # 分离上行和下行拓扑
    uplink_data = merged[merged['Topology'].str.extract(r'(\d+)')[0].astype(int).between(1, 6)].copy()
    downlink_data = merged[merged['Topology'].str.extract(r'(\d+)')[0].astype(int).between(7, 12)].copy()

    # 分别按PQ_Overhead降序排列
    uplink_sorted = uplink_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)
    downlink_sorted = downlink_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    # 合并为新的数据顺序：左半边上行(0-5)，右半边下行(6-11)
    sorted_data = pd.concat([uplink_sorted, downlink_sorted], ignore_index=True)

    new_x = np.arange(len(sorted_data))

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # 区域背景
    ax1.axvspan(-0.5, 5.5, alpha=0.08, color='orange', zorder=0)
    ax1.axvspan(5.5, 11.5, alpha=0.08, color='blue', zorder=0)
    ax1.axvline(5.5, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, zorder=1)

    # 柱状图：Classic NTOR CBT作为基准
    width = 0.6
    bars = ax1.bar(new_x, sorted_data['Classic_CBT_ms'], width,
                   color=COLOR_CLASSIC, alpha=0.4, label='Classic NTOR CBT (baseline)')

    ax1.set_xlabel('SAGIN Topology (Left: Uplink | Right: Downlink)',
                   fontsize=12, fontweight='bold')
    ax1.set_ylabel('Classic NTOR CBT (ms)', fontsize=12, fontweight='bold', color=COLOR_CLASSIC)
    ax1.tick_params(axis='y', labelcolor=COLOR_CLASSIC)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_ylim([0, 25])  # 设置左Y轴上限为25ms

    # 右Y轴: 开销倍数（三条折线）
    ax2 = ax1.twinx()

    # PQ-NTOR开销折线
    line_pq = ax2.plot(new_x, sorted_data['PQ_Overhead'], color=COLOR_PQ, marker='o',
                       linewidth=2.5, markersize=8, label='PQ-NTOR Overhead', alpha=0.9)

    # Hybrid NTOR开销折线
    line_hybrid = ax2.plot(new_x, sorted_data['Hybrid_Overhead'], color=COLOR_HYBRID, marker='s',
                          linewidth=2.5, markersize=8, label='Hybrid NTOR Overhead', alpha=0.9)

    # 在折线上标注数值
    for i in range(len(sorted_data)):
        pq_oh = sorted_data['PQ_Overhead'].iloc[i]
        hybrid_oh = sorted_data['Hybrid_Overhead'].iloc[i]

        # PQ-NTOR标注
        ax2.text(i, pq_oh + 0.02, f'{pq_oh:.3f}×',
                ha='center', va='bottom', fontsize=8, color=COLOR_PQ, fontweight='bold')

        # Hybrid NTOR标注（在下方）
        ax2.text(i, hybrid_oh - 0.02, f'{hybrid_oh:.3f}×',
                ha='center', va='top', fontsize=8, color=COLOR_HYBRID, fontweight='bold')

    ax2.set_ylabel('Overhead (×)', fontsize=12, fontweight='bold')
    ax2.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    # 设置Y轴范围
    max_overhead = max(sorted_data['PQ_Overhead'].max(), sorted_data['Hybrid_Overhead'].max())
    ax2.set_ylim([0.95, max_overhead * 1.15])

    ax1.set_title('Phase 3: Protocol Overhead Comparison (Uplink Left | Downlink Right)',
                  fontsize=13, fontweight='bold', pad=15)
    ax1.set_xticks(new_x)
    ax1.set_xticklabels(sorted_data['Topology'], rotation=45, ha='right', fontsize=9)

    # 合并图例
    from matplotlib.patches import Patch
    legend_uplink = Patch(facecolor='orange', alpha=0.08, label='Uplink Zone (topo01-06)')
    legend_downlink = Patch(facecolor='blue', alpha=0.08, label='Downlink Zone (topo07-12)')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    all_handles = [legend_uplink, legend_downlink] + lines1 + lines2
    all_labels = ['Uplink Zone', 'Downlink Zone'] + labels1 + labels2
    ax1.legend(all_handles, all_labels, fontsize=10, loc='upper center', ncol=3)

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig2_overhead_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图2: {output_file}")
    plt.close()


def create_phase3_fig3_absolute_overhead(csv_path, output_dir='.'):
    """Phase 3 - 图3: 绝对开销对比（三种协议）"""

    merged = load_phase3_data(csv_path)
    sorted_data = merged.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_data))
    width = 0.35

    # PQ-NTOR绝对开销
    bars1 = ax.bar(x - width/2, sorted_data['PQ_Overhead_Abs'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # Hybrid NTOR绝对开销
    bars2 = ax.bar(x + width/2, sorted_data['Hybrid_Overhead_Abs'], width,
                    label='Hybrid NTOR', color=COLOR_HYBRID, alpha=0.8)

    # 添加数值标签
    for i in range(len(sorted_data)):
        pq_abs = sorted_data['PQ_Overhead_Abs'].iloc[i]
        hybrid_abs = sorted_data['Hybrid_Overhead_Abs'].iloc[i]

        ax.text(i - width/2, pq_abs + 0.1, f'+{pq_abs:.2f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=COLOR_PQ)
        ax.text(i + width/2, hybrid_abs + 0.1, f'+{hybrid_abs:.2f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=COLOR_HYBRID)

    ax.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Absolute Overhead (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Phase 3: Absolute Time Overhead vs Classic NTOR', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_data['Topology'], rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig3_absolute_overhead.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图3: {output_file}")
    plt.close()


def create_phase3_fig4_cbt_breakdown(csv_path, output_dir='.'):
    """Phase 3 - 图4: CBT组成堆叠图"""

    merged = load_phase3_data(csv_path)
    sorted_data = merged.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_data))
    width = 0.7

    crypto_cbt = sorted_data['Crypto_CBT_ms']
    network_delay = sorted_data['Network_Delay_ms']
    transmission = sorted_data['Transmission_Delay_ms']
    retrans = sorted_data['Retransmission_Delay_ms']

    ax.bar(x, crypto_cbt, width, label='Cryptographic Computation',
           color=COLOR_PQ, alpha=0.9)
    ax.bar(x, network_delay, width, bottom=crypto_cbt,
           label='Network Propagation Delay', color='#95a5a6', alpha=0.8)
    bottom = crypto_cbt + network_delay
    ax.bar(x, transmission, width, bottom=bottom,
           label='Transmission Delay', color='#3498db', alpha=0.7)
    bottom += transmission
    ax.bar(x, retrans, width, bottom=bottom,
           label='Retransmission Delay', color=COLOR_OVERHEAD, alpha=0.7)

    ax.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR CBT Breakdown by Component', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_data['Topology'], rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 30])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig4_cbt_breakdown.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图4: {output_file}")
    plt.close()


def create_phase3_fig5_network_ratio(csv_path, output_dir='.'):
    """Phase 3 - 图5: 网络延迟占比（三种协议）"""

    merged = load_phase3_data(csv_path)
    sorted_data = merged.sort_values('Network_Ratio', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_data))
    width = 0.25

    bars1 = ax.bar(x - width, sorted_data['Classic_Network_Ratio'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax.bar(x, sorted_data['Network_Ratio'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)
    bars3 = ax.bar(x + width, sorted_data['Hybrid_Network_Ratio'], width,
                    label='Hybrid NTOR', color=COLOR_HYBRID, alpha=0.8)

    # 添加数值标签
    for i in range(len(sorted_data)):
        classic_r = sorted_data['Classic_Network_Ratio'].iloc[i]
        pq_r = sorted_data['Network_Ratio'].iloc[i]
        hybrid_r = sorted_data['Hybrid_Network_Ratio'].iloc[i]

        ax.text(i - width, classic_r + 0.5, f"{classic_r:.1f}%",
                ha='center', va='bottom', fontsize=7)
        ax.text(i, pq_r + 0.5, f"{pq_r:.1f}%",
                ha='center', va='bottom', fontsize=7)
        ax.text(i + width, hybrid_r + 0.5, f"{hybrid_r:.1f}%",
                ha='center', va='bottom', fontsize=7)

    ax.set_xlabel('SAGIN Topology (Sorted by PQ-NTOR Network Ratio)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Network Delay Ratio (%)', fontsize=12, fontweight='bold')
    ax.set_title('Network Delay Dominance - Three Protocols', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_data['Topology'], rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([90, 102])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig5_network_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图5: {output_file}")
    plt.close()


def create_phase3_fig6_overhead_vs_bandwidth(csv_path, output_dir='.'):
    """Phase 3 - 图6: 开销 vs 带宽（三种协议）"""

    merged = load_phase3_data(csv_path)

    fig, ax = plt.subplots(figsize=(12, 8))

    # PQ-NTOR散点
    scatter_pq = ax.scatter(merged['Bandwidth_Mbps'], merged['PQ_Overhead'],
                           s=200, c=COLOR_PQ, alpha=0.7, edgecolors='black',
                           linewidth=1.5, label='PQ-NTOR', marker='o')

    # Hybrid NTOR散点
    scatter_hybrid = ax.scatter(merged['Bandwidth_Mbps'], merged['Hybrid_Overhead'],
                               s=200, c=COLOR_HYBRID, alpha=0.7, edgecolors='black',
                               linewidth=1.5, label='Hybrid NTOR', marker='s')

    # 标注拓扑名称
    for i, row in merged.iterrows():
        ax.annotate(row['Topology'],
                   (row['Bandwidth_Mbps'], row['PQ_Overhead']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=7, color=COLOR_PQ)
        ax.annotate(row['Topology'],
                   (row['Bandwidth_Mbps'], row['Hybrid_Overhead']),
                   xytext=(5, -10), textcoords='offset points',
                   fontsize=7, color=COLOR_HYBRID)

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline')

    ax.set_xlabel('Bandwidth (Mbps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('Protocol Overhead vs Bandwidth', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xscale('log')
    ax.set_xticks([10, 15, 20, 25, 30, 40, 50, 70])
    ax.set_xticklabels(['10', '15', '20', '25', '30', '40', '50', '70'])
    ax.set_xlim([8, 80])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig6_overhead_vs_bandwidth.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图6: {output_file}")
    plt.close()


def create_phase3_fig7_overhead_vs_delay(csv_path, output_dir='.'):
    """Phase 3 - 图7: 开销 vs 延迟（三种协议）"""

    merged = load_phase3_data(csv_path)

    fig, ax = plt.subplots(figsize=(12, 8))

    # PQ-NTOR散点
    scatter_pq = ax.scatter(merged['Link_Delay_ms'], merged['PQ_Overhead'],
                           s=200, c=COLOR_PQ, alpha=0.7, edgecolors='black',
                           linewidth=1.5, label='PQ-NTOR', marker='o')

    # Hybrid NTOR散点
    scatter_hybrid = ax.scatter(merged['Link_Delay_ms'], merged['Hybrid_Overhead'],
                               s=200, c=COLOR_HYBRID, alpha=0.7, edgecolors='black',
                               linewidth=1.5, label='Hybrid NTOR', marker='s')

    # 标注拓扑名称
    for i, row in merged.iterrows():
        ax.annotate(row['Topology'],
                   (row['Link_Delay_ms'], row['PQ_Overhead']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=7, color=COLOR_PQ)
        ax.annotate(row['Topology'],
                   (row['Link_Delay_ms'], row['Hybrid_Overhead']),
                   xytext=(5, -10), textcoords='offset points',
                   fontsize=7, color=COLOR_HYBRID)

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline')

    ax.set_xlabel('Link Delay (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('Protocol Overhead vs Link Delay', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig7_overhead_vs_delay.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图7: {output_file}")
    plt.close()


def create_phase3_fig8_bandwidth_category(csv_path, output_dir='.'):
    """Phase 3 - 图8: 按带宽分类汇总（三种协议）"""

    merged = load_phase3_data(csv_path)

    fig, ax = plt.subplots(figsize=(12, 7))

    high_bw = merged[merged['Bandwidth_Mbps'] > 25]
    mid_bw = merged[(merged['Bandwidth_Mbps'] > 10) & (merged['Bandwidth_Mbps'] <= 25)]
    low_bw = merged[merged['Bandwidth_Mbps'] <= 10]

    categories = ['High BW\n(>25 Mbps)', 'Mid BW\n(10-25 Mbps)', 'Low BW\n(<10 Mbps)']

    pq_means = [high_bw['PQ_Overhead'].mean() if len(high_bw) > 0 else 0,
                mid_bw['PQ_Overhead'].mean() if len(mid_bw) > 0 else 0,
                low_bw['PQ_Overhead'].mean() if len(low_bw) > 0 else 0]

    hybrid_means = [high_bw['Hybrid_Overhead'].mean() if len(high_bw) > 0 else 0,
                   mid_bw['Hybrid_Overhead'].mean() if len(mid_bw) > 0 else 0,
                   low_bw['Hybrid_Overhead'].mean() if len(low_bw) > 0 else 0]

    counts = [len(high_bw), len(mid_bw), len(low_bw)]

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax.bar(x - width/2, pq_means, width, label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)
    bars2 = ax.bar(x + width/2, hybrid_means, width, label='Hybrid NTOR', color=COLOR_HYBRID, alpha=0.8)

    for i, (pq_m, hybrid_m, count) in enumerate(zip(pq_means, hybrid_means, counts)):
        ax.text(i - width/2, pq_m + 0.01, f'{pq_m:.3f}×',
               ha='center', va='bottom', fontsize=10, fontweight='bold', color=COLOR_PQ)
        ax.text(i + width/2, hybrid_m + 0.01, f'{hybrid_m:.3f}×',
               ha='center', va='bottom', fontsize=10, fontweight='bold', color=COLOR_HYBRID)
        ax.text(i, max(pq_m, hybrid_m) + 0.04, f'(n={count})',
               ha='center', va='bottom', fontsize=9, style='italic')

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline (1.0×)')

    ax.set_ylabel('Average Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('Protocol Overhead by Bandwidth Category', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig8_bandwidth_category.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图8: {output_file}")
    plt.close()


def create_phase3_fig9_best_worst_scenarios(csv_path, output_dir='.'):
    """Phase 3 - 图9: 最佳/最差场景对比（三种协议）"""

    merged = load_phase3_data(csv_path)
    sorted_data = merged.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 8))

    # 最差3个和最佳3个
    best_3 = sorted_data.tail(3)[::-1]  # 反转顺序
    worst_3 = sorted_data.head(3)

    combined = pd.concat([worst_3, best_3]).reset_index(drop=True)

    y = np.arange(len(combined))
    height = 0.35

    # PQ-NTOR
    bars1 = ax.barh(y - height/2, combined['PQ_Overhead'], height,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # Hybrid NTOR
    bars2 = ax.barh(y + height/2, combined['Hybrid_Overhead'], height,
                    label='Hybrid NTOR', color=COLOR_HYBRID, alpha=0.8)

    # 添加数值标签
    for i, row in combined.iterrows():
        ax.text(row['PQ_Overhead'] + 0.01, i - height/2,
               f"{row['PQ_Overhead']:.3f}× (+{row['PQ_Overhead_Abs']:.2f}ms)",
               va='center', fontsize=9, fontweight='bold', color=COLOR_PQ)
        ax.text(row['Hybrid_Overhead'] + 0.01, i + height/2,
               f"{row['Hybrid_Overhead']:.3f}× (+{row['Hybrid_Overhead_Abs']:.2f}ms)",
               va='center', fontsize=9, fontweight='bold', color=COLOR_HYBRID)

    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)

    ax.set_yticks(y)
    labels = []
    for _, row in combined.iterrows():
        desc = row['Description'][:15] + '...' if len(row['Description']) > 15 else row['Description']
        labels.append(f"{row['Topology']}\n{desc}")
    ax.set_yticklabels(labels, fontsize=9)

    ax.set_xlabel('Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('Best vs Worst Case Scenarios (by PQ-NTOR Overhead)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # 分隔线
    ax.axhline(y=2.5, color='black', linestyle='-', linewidth=2, alpha=0.5)
    ax.text(1.15, 2.5, 'Worst ↑\nBest ↓', va='center', ha='center',
           fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig9_best_worst_scenarios.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图9: {output_file}")
    plt.close()


def create_phase3_fig10_summary_table(csv_path, output_dir='.'):
    """Phase 3 - 图10: 三协议性能汇总表"""

    merged = load_phase3_data(csv_path)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis('off')

    # 计算统计数据
    stats = {
        'Metric': ['Avg CBT (ms)', 'Std Dev (ms)', 'Min (ms)', 'Max (ms)',
                   'Avg Overhead', 'Network Ratio (%)'],
        'Classic NTOR': [
            f"{merged['Classic_CBT_ms'].mean():.2f}",
            f"{merged['Classic_CBT_ms'].std():.2f}",
            f"{merged['Classic_CBT_ms'].min():.2f}",
            f"{merged['Classic_CBT_ms'].max():.2f}",
            "1.000× (baseline)",
            f"{merged['Classic_Network_Ratio'].mean():.1f}"
        ],
        'PQ-NTOR': [
            f"{merged['Total_CBT_ms'].mean():.2f}",
            f"{merged['Total_CBT_ms'].std():.2f}",
            f"{merged['Total_CBT_ms'].min():.2f}",
            f"{merged['Total_CBT_ms'].max():.2f}",
            f"{merged['PQ_Overhead'].mean():.3f}×",
            f"{merged['Network_Ratio'].mean():.1f}"
        ],
        'Hybrid NTOR': [
            f"{merged['Hybrid_CBT_ms'].mean():.2f}",
            f"{merged['Hybrid_CBT_ms'].std():.2f}",
            f"{merged['Hybrid_CBT_ms'].min():.2f}",
            f"{merged['Hybrid_CBT_ms'].max():.2f}",
            f"{merged['Hybrid_Overhead'].mean():.3f}×",
            f"{merged['Hybrid_Network_Ratio'].mean():.1f}"
        ]
    }

    df_stats = pd.DataFrame(stats)

    table_data = [df_stats.columns.tolist()] + df_stats.values.tolist()

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     bbox=[0.1, 0.1, 0.8, 0.8])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)

    # 设置表头样式
    for i in range(4):
        cell = table[(0, i)]
        cell.set_facecolor('#34495e')
        cell.set_text_props(weight='bold', color='white', fontsize=12)

    # 设置列颜色
    for row_idx in range(1, 7):
        table[(row_idx, 1)].set_facecolor('#e6f2ff')  # Classic蓝色
        table[(row_idx, 2)].set_facecolor('#ffe6e6')  # PQ红色
        table[(row_idx, 3)].set_facecolor('#e6ffe6')  # Hybrid绿色

    ax.set_title('Phase 3: Three-Protocol Performance Summary (12 SAGIN Topologies)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig10_summary_table.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图10: {output_file}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("="*80)
    print("📊 生成单独PDF图表 - Phase 1 + Phase 2 + Phase 3 (三协议)")
    print("="*80)
    print()

    output_dir = '/home/ccc/pq-ntor-experiment/essay'

    # 确保figure目录存在
    os.makedirs(f'{output_dir}/figure', exist_ok=True)

    # Phase 1: 3张图
    print("=" * 80)
    print("Phase 1: 密码学原语基准测试（3张图）")
    print("=" * 80)
    create_phase1_fig1_crypto_performance(output_dir)
    create_phase1_fig2_crypto_breakdown(output_dir)
    create_phase1_fig3_crypto_statistics(output_dir)
    print()

    # Phase 2: 3张图
    print("=" * 80)
    print("Phase 2: 文献对比（3张图）")
    print("=" * 80)
    create_phase2_fig1_handshake_comparison(output_dir)
    create_phase2_fig2_overhead_comparison(output_dir)
    create_phase2_fig3_summary_table(output_dir)
    print()

    # Phase 3: 10张图
    print("=" * 80)
    print("Phase 3: SAGIN拓扑分析 - 三协议（10张图）")
    print("=" * 80)
    csv_path = '/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl/phase3_sagin_cbt_with_network_20251216.csv'

    create_phase3_fig1_cbt_comparison(csv_path, output_dir)
    create_phase3_fig2_overhead_ratio(csv_path, output_dir)
    create_phase3_fig3_absolute_overhead(csv_path, output_dir)
    create_phase3_fig4_cbt_breakdown(csv_path, output_dir)
    create_phase3_fig5_network_ratio(csv_path, output_dir)
    create_phase3_fig6_overhead_vs_bandwidth(csv_path, output_dir)
    create_phase3_fig7_overhead_vs_delay(csv_path, output_dir)
    create_phase3_fig8_bandwidth_category(csv_path, output_dir)
    create_phase3_fig9_best_worst_scenarios(csv_path, output_dir)
    create_phase3_fig10_summary_table(csv_path, output_dir)
    print()

    print("="*80)
    print("✅ 所有PDF图表生成完成!")
    print("="*80)
    print()
    print(f"📁 输出目录: {output_dir}/figure/")
    print()
    print("📊 生成的图表:")
    print("  Phase 1 (3张):")
    print("    - phase1_fig1_crypto_performance.pdf")
    print("    - phase1_fig2_crypto_breakdown.pdf")
    print("    - phase1_fig3_crypto_statistics.pdf")
    print()
    print("  Phase 2 (3张):")
    print("    - phase2_fig1_handshake_comparison.pdf")
    print("    - phase2_fig2_overhead_comparison.pdf")
    print("    - phase2_fig3_summary_table.pdf")
    print()
    print("  Phase 3 (10张) - 支持 Classic/PQ/Hybrid NTOR:")
    print("    - phase3_fig1_cbt_comparison.pdf")
    print("    - phase3_fig2_overhead_ratio.pdf (折线+柱状, 三条折线)")
    print("    - phase3_fig3_absolute_overhead.pdf")
    print("    - phase3_fig4_cbt_breakdown.pdf")
    print("    - phase3_fig5_network_ratio.pdf")
    print("    - phase3_fig6_overhead_vs_bandwidth.pdf")
    print("    - phase3_fig7_overhead_vs_delay.pdf")
    print("    - phase3_fig8_bandwidth_category.pdf")
    print("    - phase3_fig9_best_worst_scenarios.pdf")
    print("    - phase3_fig10_summary_table.pdf")
    print()
    print("总计: 16张PDF图表")
    print()

if __name__ == '__main__':
    main()
