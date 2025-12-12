#!/usr/bin/env python3
"""
综合可视化：Phase 2文献对比 + Phase 3 SAGIN拓扑分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

# 颜色方案
COLOR_CLASSIC = '#3498db'  # 蓝色
COLOR_PQ = '#e74c3c'       # 红色
COLOR_OVERHEAD = '#f39c12' # 橙色
COLOR_LITERATURE = '#95a5a6'  # 灰色

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
# Phase 3: SAGIN拓扑数据（基于修正的理论计算）
# ============================================================================

def create_phase2_comparison(output_dir='.'):
    """生成Phase 2性能对比图"""

    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    df = pd.DataFrame(PHASE2_DATA)
    x = np.arange(len(df))
    width = 0.35

    # ========================================================================
    # 图1: 握手时间对比（带误差条）
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, :])

    # Classic NTOR
    classic_mean = (df['Classic_NTOR_min'] + df['Classic_NTOR_max']) / 2
    classic_err = (df['Classic_NTOR_max'] - df['Classic_NTOR_min']) / 2

    bars1 = ax1.bar(x - width/2, classic_mean, width,
                    yerr=classic_err, capsize=5,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)

    # PQ-NTOR
    pq_mean = (df['PQ_NTOR_min'] + df['PQ_NTOR_max']) / 2
    pq_err = (df['PQ_NTOR_max'] - df['PQ_NTOR_min']) / 2

    bars2 = ax1.bar(x + width/2, pq_mean, width,
                    yerr=pq_err, capsize=5,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # 添加数值标签
    for i, (c_mean, p_mean) in enumerate(zip(classic_mean, pq_mean)):
        ax1.text(i - width/2, c_mean + classic_err[i] + 20,
                f'{c_mean:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax1.text(i + width/2, p_mean + pq_err[i] + 20,
                f'{p_mean:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax1.set_xlabel('Platform', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Handshake Time (µs)', fontsize=13, fontweight='bold')
    ax1.set_title('Phase 2: Handshake Performance Comparison (Literature vs Our Work)',
                  fontsize=15, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['Platform'], fontsize=11)
    ax1.legend(fontsize=12, loc='upper left')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_ylim([0, max(pq_mean + pq_err) * 1.15])

    # 添加数据源注释
    for i, source in enumerate(df['Source']):
        ax1.text(i, -50, source, ha='center', va='top',
                fontsize=8, style='italic', color='gray')

    # ========================================================================
    # 图2: PQ开销倍数对比
    # ========================================================================
    ax2 = fig.add_subplot(gs[1, 0])

    overhead_mean = (df['Overhead_min'] + df['Overhead_max']) / 2
    overhead_err = (df['Overhead_max'] - df['Overhead_min']) / 2

    bars = ax2.bar(x, overhead_mean, width*2,
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
            ax2.text(i, o_mean + o_err + 0.3, label,
                    ha='center', va='bottom', fontsize=11, fontweight='bold', color='darkred')
        else:
            ax2.text(i, o_mean + o_err + 0.3, label,
                    ha='center', va='bottom', fontsize=10)

    ax2.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Baseline (1.0×)')
    ax2.set_xlabel('Platform', fontsize=12, fontweight='bold')
    ax2.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax2.set_title('PQ-NTOR Relative Overhead', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df['Platform'], fontsize=10)
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim([0, max(overhead_mean + overhead_err) * 1.15])

    # ========================================================================
    # 图3: 性能指标汇总表
    # ========================================================================
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')

    # 创建表格数据
    table_data = []
    table_data.append(['Platform', 'Classic (µs)', 'PQ (µs)', 'Overhead'])

    for i, row in df.iterrows():
        platform = row['Platform'].replace('\n', ' ')
        classic_range = f"{row['Classic_NTOR_min']:.0f}-{row['Classic_NTOR_max']:.0f}"
        if row['PQ_NTOR_min'] == row['PQ_NTOR_max']:
            pq_value = f"{row['PQ_NTOR_min']:.1f}"
        else:
            pq_value = f"{row['PQ_NTOR_min']:.0f}-{row['PQ_NTOR_max']:.0f}"
        overhead_range = f"{row['Overhead_min']:.1f}-{row['Overhead_max']:.1f}×"

        table_data.append([platform, classic_range, pq_value, overhead_range])

    table = ax3.table(cellText=table_data, cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # 设置表头样式
    for i in range(4):
        cell = table[(0, i)]
        cell.set_facecolor('#34495e')
        cell.set_text_props(weight='bold', color='white')

    # 突出显示我们的数据行
    for i in range(4):
        cell = table[(4, i)]  # 最后一行
        cell.set_facecolor('#ffe6e6')
        cell.set_text_props(weight='bold')

    ax3.set_title('Performance Summary', fontsize=13, fontweight='bold', pad=20)

    plt.suptitle('Phase 2: Handshake Performance - Literature vs Our Implementation',
                 fontsize=16, fontweight='bold', y=0.98)

    output_file = f'{output_dir}/phase2_literature_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()


def create_phase3_sagin_visualization(csv_path, output_dir='.'):
    """生成Phase 3 SAGIN拓扑完整分析图"""

    # 读取带网络延迟的完整数据
    df = pd.read_csv(csv_path)

    # 计算PQ相对开销
    classic_data = df[df['Protocol'].str.contains('Classic')].sort_values('Topology').reset_index(drop=True)
    pq_data = df[df['Protocol'].str.contains('PQ')].sort_values('Topology').reset_index(drop=True)

    pq_data['PQ_Overhead'] = pq_data['Total_CBT_ms'] / classic_data['Total_CBT_ms']
    pq_data['PQ_Overhead_Abs'] = pq_data['Total_CBT_ms'] - classic_data['Total_CBT_ms']

    # 按PQ开销从高到低排序
    sorted_pq = pq_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)
    sorted_classic = classic_data.loc[pq_data.sort_values('PQ_Overhead', ascending=False).index].reset_index(drop=True)

    # ========================================================================
    # 创建大图：6个子图
    # ========================================================================
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

    x = np.arange(len(sorted_pq))
    width = 0.4

    # ========================================================================
    # 图1: 端到端CBT对比（按PQ开销降序）
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, :])

    bars1 = ax1.bar(x - width/2, sorted_classic['Total_CBT_ms'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax1.bar(x + width/2, sorted_pq['Total_CBT_ms'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # 添加网络参数注释
    for i, row in sorted_pq.iterrows():
        bw = row['Bandwidth_Mbps']
        delay = row['Link_Delay_ms']
        loss = row['Loss_Percent']

        # 根据带宽分类上色
        if bw > 25:
            color = 'green'
            bw_label = 'High BW'
        elif bw > 10:
            color = 'orange'
            bw_label = 'Mid BW'
        else:
            color = 'red'
            bw_label = 'Low BW'

        ax1.text(i, max(sorted_classic['Total_CBT_ms'].iloc[i],
                       sorted_pq['Total_CBT_ms'].iloc[i]) + 2,
                f'{bw:.1f}Mbps\n{delay:.1f}ms\n{loss:.1f}%',
                ha='center', va='bottom', fontsize=7, color=color, fontweight='bold')

    ax1.set_xlabel('SAGIN Topology (Sorted by PQ Overhead)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('End-to-End CBT (ms)', fontsize=13, fontweight='bold')
    ax1.set_title('Phase 3: Circuit Build Time Across 12 SAGIN Topologies',
                  fontsize=15, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=10)
    ax1.legend(fontsize=12, loc='upper left')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # ========================================================================
    # 图2: PQ开销倍数（降序排列）
    # ========================================================================
    ax2 = fig.add_subplot(gs[1, 0])

    colors = []
    for overhead in sorted_pq['PQ_Overhead']:
        if overhead < 1.1:
            colors.append('green')
        elif overhead < 1.5:
            colors.append('orange')
        else:
            colors.append('red')

    bars = ax2.bar(x, sorted_pq['PQ_Overhead'], width*2, color=colors, alpha=0.8)

    # 添加数值标签
    for i, overhead in enumerate(sorted_pq['PQ_Overhead']):
        ax2.text(i, overhead + 0.05, f'{overhead:.2f}×',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax2.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline (1.0×)')
    ax2.axhline(y=1.5, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='1.5× Threshold')

    ax2.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax2.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax2.set_title('PQ-NTOR Relative Overhead by Topology', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim([0.9, max(sorted_pq['PQ_Overhead']) * 1.1])

    # ========================================================================
    # 图3: PQ绝对开销（ms）
    # ========================================================================
    ax3 = fig.add_subplot(gs[1, 1])

    bars = ax3.bar(x, sorted_pq['PQ_Overhead_Abs'], width*2, color=COLOR_OVERHEAD, alpha=0.8)

    # 添加数值标签
    for i, abs_overhead in enumerate(sorted_pq['PQ_Overhead_Abs']):
        ax3.text(i, abs_overhead + 0.5, f'+{abs_overhead:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax3.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax3.set_ylabel('PQ-NTOR Absolute Overhead (ms)', fontsize=12, fontweight='bold')
    ax3.set_title('PQ-NTOR Absolute Time Overhead', fontsize=13, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    ax3.set_ylim([0, max(sorted_pq['PQ_Overhead_Abs']) * 1.15])

    # ========================================================================
    # 图4: CBT组成堆叠图（PQ-NTOR）
    # ========================================================================
    ax4 = fig.add_subplot(gs[2, 0])

    # 堆叠柱状图
    crypto_cbt = sorted_pq['Crypto_CBT_ms']
    network_delay = sorted_pq['Network_Delay_ms']
    transmission = sorted_pq['Transmission_Delay_ms']
    retrans = sorted_pq['Retransmission_Delay_ms']

    ax4.bar(x, crypto_cbt, width*2, label='Cryptographic Computation',
           color=COLOR_PQ, alpha=0.9)
    ax4.bar(x, network_delay, width*2, bottom=crypto_cbt,
           label='Network Propagation Delay', color='#95a5a6', alpha=0.8)
    bottom = crypto_cbt + network_delay
    ax4.bar(x, transmission, width*2, bottom=bottom,
           label='Transmission Delay', color='#3498db', alpha=0.7)
    bottom += transmission
    ax4.bar(x, retrans, width*2, bottom=bottom,
           label='Retransmission Delay', color=COLOR_OVERHEAD, alpha=0.7)

    ax4.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Circuit Build Time (ms)', fontsize=12, fontweight='bold')
    ax4.set_title('PQ-NTOR CBT Breakdown by Component', fontsize=13, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax4.legend(fontsize=9, loc='upper left')
    ax4.grid(axis='y', alpha=0.3, linestyle='--')

    # ========================================================================
    # 图5: 网络延迟占比（Classic vs PQ）
    # ========================================================================
    ax5 = fig.add_subplot(gs[2, 1])

    bars1 = ax5.bar(x - width/2, sorted_classic['Network_Ratio'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax5.bar(x + width/2, sorted_pq['Network_Ratio'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # 添加数值标签
    for i in range(len(x)):
        ax5.text(i - width/2, sorted_classic['Network_Ratio'].iloc[i] + 1,
                f"{sorted_classic['Network_Ratio'].iloc[i]:.0f}%",
                ha='center', va='bottom', fontsize=7)
        ax5.text(i + width/2, sorted_pq['Network_Ratio'].iloc[i] + 1,
                f"{sorted_pq['Network_Ratio'].iloc[i]:.0f}%",
                ha='center', va='bottom', fontsize=7)

    ax5.axhline(y=50, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='50% Threshold')

    ax5.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Network Delay Ratio (%)', fontsize=12, fontweight='bold')
    ax5.set_title('Network Delay Dominance', fontsize=13, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax5.legend(fontsize=10)
    ax5.grid(axis='y', alpha=0.3, linestyle='--')
    ax5.set_ylim([0, 105])

    plt.suptitle('Phase 3: SAGIN Network Integration Analysis (12 Topologies)',
                 fontsize=16, fontweight='bold', y=0.995)

    output_file = f'{output_dir}/phase3_sagin_comprehensive.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()


def create_phase3_overhead_focus(csv_path, output_dir='.'):
    """专注于PQ开销的详细分析图"""

    df = pd.read_csv(csv_path)

    classic_data = df[df['Protocol'].str.contains('Classic')].sort_values('Topology').reset_index(drop=True)
    pq_data = df[df['Protocol'].str.contains('PQ')].sort_values('Topology').reset_index(drop=True)

    pq_data['PQ_Overhead'] = pq_data['Total_CBT_ms'] / classic_data['Total_CBT_ms']
    pq_data['PQ_Overhead_Abs'] = pq_data['Total_CBT_ms'] - classic_data['Total_CBT_ms']

    # 按PQ开销降序排序
    sorted_pq = pq_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    fig, axes = plt.subplots(2, 2, figsize=(18, 12))

    # ========================================================================
    # 图1: PQ开销 vs 带宽（散点图）
    # ========================================================================
    ax = axes[0, 0]

    scatter = ax.scatter(sorted_pq['Bandwidth_Mbps'], sorted_pq['PQ_Overhead'],
                        s=200, c=sorted_pq['Link_Delay_ms'], cmap='RdYlGn_r',
                        alpha=0.7, edgecolors='black', linewidth=1.5)

    # 添加拓扑标签
    for i, row in sorted_pq.iterrows():
        ax.annotate(row['Topology'],
                   (row['Bandwidth_Mbps'], row['PQ_Overhead']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Link Delay (ms)', fontsize=11)

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axhline(y=1.5, color='orange', linestyle=':', linewidth=1.5, alpha=0.5)

    ax.set_xlabel('Bandwidth (Mbps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('PQ Overhead vs Bandwidth', fontsize=13, fontweight='bold')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xscale('log')

    # ========================================================================
    # 图2: PQ开销 vs 延迟（散点图）
    # ========================================================================
    ax = axes[0, 1]

    scatter = ax.scatter(sorted_pq['Link_Delay_ms'], sorted_pq['PQ_Overhead'],
                        s=200, c=sorted_pq['Bandwidth_Mbps'], cmap='viridis',
                        alpha=0.7, edgecolors='black', linewidth=1.5)

    for i, row in sorted_pq.iterrows():
        ax.annotate(row['Topology'],
                   (row['Link_Delay_ms'], row['PQ_Overhead']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Bandwidth (Mbps)', fontsize=11)

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axhline(y=1.5, color='orange', linestyle=':', linewidth=1.5, alpha=0.5)

    ax.set_xlabel('Link Delay (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('PQ Overhead vs Link Delay', fontsize=13, fontweight='bold')
    ax.grid(alpha=0.3, linestyle='--')

    # ========================================================================
    # 图3: 拓扑分类汇总（按带宽分组）
    # ========================================================================
    ax = axes[1, 0]

    # 按带宽分组
    high_bw = sorted_pq[sorted_pq['Bandwidth_Mbps'] > 25]
    mid_bw = sorted_pq[(sorted_pq['Bandwidth_Mbps'] > 10) & (sorted_pq['Bandwidth_Mbps'] <= 25)]
    low_bw = sorted_pq[sorted_pq['Bandwidth_Mbps'] <= 10]

    categories = ['High BW\n(>25 Mbps)', 'Mid BW\n(10-25 Mbps)', 'Low BW\n(<10 Mbps)']
    means = [high_bw['PQ_Overhead'].mean(), mid_bw['PQ_Overhead'].mean(), low_bw['PQ_Overhead'].mean()]
    counts = [len(high_bw), len(mid_bw), len(low_bw)]

    colors_cat = ['green', 'orange', 'red']
    bars = ax.bar(categories, means, color=colors_cat, alpha=0.7, edgecolor='black', linewidth=2)

    # 添加数值标签
    for i, (mean, count) in enumerate(zip(means, counts)):
        ax.text(i, mean + 0.05, f'{mean:.2f}×\n(n={count})',
               ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline (1.0×)')
    ax.axhline(y=1.5, color='orange', linestyle=':', linewidth=1.5, alpha=0.5, label='1.5× Threshold')

    ax.set_ylabel('Average PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('PQ Overhead by Bandwidth Category', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0.9, max(means) * 1.15])

    # ========================================================================
    # 图4: 最佳/最差场景对比
    # ========================================================================
    ax = axes[1, 1]

    best_3 = sorted_pq.head(3)[::-1]  # 开销最低的3个
    worst_3 = sorted_pq.tail(3)  # 开销最高的3个

    combined = pd.concat([best_3, worst_3]).reset_index(drop=True)
    x = np.arange(len(combined))

    colors_scenario = ['red' if oh > 1.5 else 'orange' if oh > 1.1 else 'green'
                       for oh in combined['PQ_Overhead']]

    bars = ax.barh(x, combined['PQ_Overhead'], color=colors_scenario, alpha=0.8, edgecolor='black')

    # 添加标签
    for i, row in combined.iterrows():
        ax.text(row['PQ_Overhead'] + 0.05, i,
               f"{row['PQ_Overhead']:.2f}× (+{row['PQ_Overhead_Abs']:.1f}ms)",
               va='center', fontsize=10, fontweight='bold')

    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=1.5, color='orange', linestyle=':', linewidth=1.5, alpha=0.5)

    ax.set_yticks(x)
    ax.set_yticklabels([f"{row['Topology']}\n{row['Description'][:20]}..."
                        for _, row in combined.iterrows()], fontsize=9)
    ax.set_xlabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('Best vs Worst Case Scenarios', fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # 添加分隔线
    ax.axhline(y=2.5, color='black', linestyle='-', linewidth=2, alpha=0.5)
    ax.text(1.9, 2.5, 'Best ↑\nWorst ↓', va='center', ha='center',
           fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    plt.suptitle('Phase 3: PQ-NTOR Overhead Analysis - Impact of Network Conditions',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = f'{output_dir}/phase3_overhead_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()


def main():
    print("="*80)
    print("📊 综合可视化：Phase 2 + Phase 3")
    print("="*80)
    print()

    output_dir = '/home/ccc/pq-ntor-experiment/essay'

    # Phase 2: 文献对比
    print("1️⃣ 生成 Phase 2 文献对比图...")
    create_phase2_comparison(output_dir)
    print()

    # Phase 3: SAGIN拓扑分析（使用Phytium数据）
    csv_path = '/home/ccc/pq-ntor-experiment/essay/phase3_results_phytium_20251204_100744/phase3_sagin_cbt_with_network.csv'

    print("2️⃣ 生成 Phase 3 SAGIN综合分析图...")
    create_phase3_sagin_visualization(csv_path, output_dir)
    print()

    print("3️⃣ 生成 Phase 3 PQ开销专项分析图...")
    create_phase3_overhead_focus(csv_path, output_dir)
    print()

    print("="*80)
    print("✅ 所有可视化图表生成完成!")
    print("="*80)
    print()
    print("📁 输出文件:")
    print(f"  1. Phase 2 文献对比: {output_dir}/phase2_literature_comparison.png")
    print(f"  2. Phase 3 SAGIN综合分析: {output_dir}/phase3_sagin_comprehensive.png")
    print(f"  3. Phase 3 PQ开销分析: {output_dir}/phase3_overhead_analysis.png")
    print()

if __name__ == '__main__':
    main()
