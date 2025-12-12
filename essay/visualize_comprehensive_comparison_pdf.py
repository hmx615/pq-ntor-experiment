#!/usr/bin/env python3
"""
综合可视化：Phase 2文献对比 + Phase 3 SAGIN拓扑分析
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
# 单图生成函数
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
        ax.text(i - width/2, c_mean + classic_err[i] + 20,
                f'{c_mean:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(i + width/2, p_mean + pq_err[i] + 20,
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


def create_phase3_figures(csv_path, output_dir='.'):
    """生成Phase 3的所有单独图表"""

    df = pd.read_csv(csv_path)

    classic_data = df[df['Protocol'].str.contains('Classic')].sort_values('Topology').reset_index(drop=True)
    pq_data = df[df['Protocol'].str.contains('PQ')].sort_values('Topology').reset_index(drop=True)

    # 将Classic数据添加到PQ数据中，确保对应关系
    pq_data['Classic_CBT_ms'] = classic_data['Total_CBT_ms'].values
    pq_data['Classic_Network_Ratio'] = classic_data['Network_Ratio'].values
    pq_data['PQ_Overhead'] = pq_data['Total_CBT_ms'] / pq_data['Classic_CBT_ms']
    pq_data['PQ_Overhead_Abs'] = pq_data['Total_CBT_ms'] - pq_data['Classic_CBT_ms']

    # 图1: 按PQ-NTOR的总CBT降序排序
    sorted_pq_fig1 = pq_data.sort_values('Total_CBT_ms', ascending=False).reset_index(drop=True)

    # 图2及后续: 按PQ开销倍数降序排序
    sorted_pq = pq_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    x = np.arange(len(pq_data))
    width = 0.4

    # 图1: 端到端CBT对比
    create_phase3_fig1_cbt_comparison(sorted_pq_fig1, x, width, output_dir)

    # 图2: PQ开销倍数
    create_phase3_fig2_overhead_ratio(sorted_pq, x, width, output_dir)

    # 图3: PQ绝对开销
    create_phase3_fig3_absolute_overhead(sorted_pq, x, width, output_dir)

    # 图4: CBT组成堆叠图
    create_phase3_fig4_cbt_breakdown(sorted_pq, x, width, output_dir)

    # 图5: 网络延迟占比
    create_phase3_fig5_network_ratio(sorted_pq, x, width, output_dir)

    # 图6: PQ开销 vs 带宽
    create_phase3_fig6_overhead_vs_bandwidth(sorted_pq, output_dir)

    # 图7: PQ开销 vs 延迟
    create_phase3_fig7_overhead_vs_delay(sorted_pq, output_dir)

    # 图8: 按带宽分类汇总
    create_phase3_fig8_bandwidth_category(sorted_pq, output_dir)

    # 图9: 最佳/最差场景对比
    create_phase3_fig9_best_worst_scenarios(sorted_pq, output_dir)


def create_phase3_fig1_cbt_comparison(sorted_pq, x, width, output_dir):
    """Phase 3 - 图1: 端到端CBT对比"""

    fig, ax = plt.subplots(figsize=(14, 7))

    bars1 = ax.bar(x - width/2, sorted_pq['Classic_CBT_ms'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax.bar(x + width/2, sorted_pq['Total_CBT_ms'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    # 添加网络参数注释
    for i, row in sorted_pq.iterrows():
        bw = row['Bandwidth_Mbps']
        delay = row['Link_Delay_ms']
        loss = row['Loss_Percent']

        if bw > 25:
            color = 'green'
        elif bw > 10:
            color = 'orange'
        else:
            color = 'red'

        ax.text(i, max(row['Classic_CBT_ms'], row['Total_CBT_ms']) + 2,
                f'{bw:.1f}Mbps\n{delay:.1f}ms delay\n{loss:.1f}% loss',
                ha='center', va='bottom', fontsize=7, color=color, fontweight='bold')

    ax.set_xlabel('SAGIN Topology (Sorted by PQ-NTOR CBT)', fontsize=13, fontweight='bold')
    ax.set_ylabel('End-to-End CBT (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3: Circuit Build Time Across 12 SAGIN Topologies',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 70])  # 设置纵轴范围到70ms

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig1_cbt_comparison.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图1: {output_file}")
    plt.close()


def create_phase3_fig2_overhead_ratio(sorted_pq, x, width, output_dir):
    """Phase 3 - 图2: PQ开销倍数（双Y轴）- 左半边上行，右半边下行，各自按开销倍率降序排列"""

    # 分离上行和下行拓扑
    uplink_data = sorted_pq[sorted_pq['Topology'].str.extract(r'(\d+)')[0].astype(int).between(1, 6)].copy()
    downlink_data = sorted_pq[sorted_pq['Topology'].str.extract(r'(\d+)')[0].astype(int).between(7, 12)].copy()

    # 分别按PQ_Overhead降序排列
    uplink_sorted = uplink_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)
    downlink_sorted = downlink_data.sort_values('PQ_Overhead', ascending=False).reset_index(drop=True)

    # 合并为新的数据顺序：左半边上行(0-5)，右半边下行(6-11)
    new_sorted_pq = pd.concat([uplink_sorted, downlink_sorted], ignore_index=True)

    # 新的x轴位置
    new_x = range(len(new_sorted_pq))

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 左半边上行区域背景（橙色）
    ax1.axvspan(-0.5, 5.5, alpha=0.08, color='orange', zorder=0)

    # 右半边下行区域背景（蓝色）
    ax1.axvspan(5.5, 11.5, alpha=0.08, color='blue', zorder=0)

    # 中间分隔线
    ax1.axvline(5.5, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, zorder=1)

    # 添加图例标记
    from matplotlib.patches import Patch
    legend_uplink = Patch(facecolor='orange', alpha=0.08, label='Uplink (topo01-06)')
    legend_downlink = Patch(facecolor='blue', alpha=0.08, label='Downlink (topo07-12)')

    # 根据开销倍率设置柱子颜色
    colors = []
    for overhead in new_sorted_pq['PQ_Overhead']:
        if overhead < 1.1:
            colors.append('green')
        elif overhead < 1.5:
            colors.append('orange')
        else:
            colors.append('red')

    # 左Y轴: PQ开销倍数（柱状图）
    bars = ax1.bar(new_x, new_sorted_pq['PQ_Overhead'], width*2, color=colors, alpha=0.7, label='PQ Overhead')

    # 在每个柱子上方标注PQ开销倍数
    for i, overhead in enumerate(new_sorted_pq['PQ_Overhead']):
        ax1.text(i, overhead + 0.05, f'{overhead:.3f}×',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax1.set_xlabel('SAGIN Topology (Left: Uplink by Overhead ↓ | Right: Downlink by Overhead ↓)',
                   fontsize=12, fontweight='bold')
    ax1.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold', color='black')
    ax1.set_ylim([0.9, max(new_sorted_pq['PQ_Overhead']) * 1.2])
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # 右Y轴: Classic NTOR基准值（折线图）
    ax2 = ax1.twinx()
    line = ax2.plot(new_x, new_sorted_pq['Classic_CBT_ms'], color='navy', marker='o', linewidth=2,
                    markersize=6, label='Classic NTOR CBT (Baseline)', alpha=0.8)

    # 在折线标注Classic CBT值
    for i, cbt_value in enumerate(new_sorted_pq['Classic_CBT_ms']):
        # 低值拓扑标注在下方
        if cbt_value < 25:
            ax2.text(i, cbt_value - 1.5, f'{cbt_value:.1f}ms',
                    ha='center', va='top', fontsize=8, color='navy', style='italic', fontweight='bold')
        # 高值拓扑标注在节点上方
        else:
            ax2.text(i, cbt_value + 1.2, f'{cbt_value:.1f}ms',
                    ha='center', va='bottom', fontsize=8, color='navy', style='italic', fontweight='bold')

    ax2.set_ylabel('Classic NTOR CBT (ms)', fontsize=12, fontweight='bold', color='navy')
    ax2.tick_params(axis='y', labelcolor='navy')
    ax2.set_ylim([15, max(new_sorted_pq['Classic_CBT_ms']) * 1.25])

    ax1.set_title('PQ-NTOR Relative Overhead by Topology (Uplink Left | Downlink Right)',
                  fontsize=13, fontweight='bold', pad=15)
    ax1.set_xticks(new_x)
    ax1.set_xticklabels(new_sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)

    # 合并图例，包含背景色块说明
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    all_handles = [legend_uplink, legend_downlink] + lines1 + lines2
    all_labels = ['Uplink Zone', 'Downlink Zone'] + labels1 + labels2
    ax1.legend(all_handles, all_labels, fontsize=10, loc='upper center', ncol=2)

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig2_overhead_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图2 (左上行↓右下行↓): {output_file}")
    plt.close()


def create_phase3_fig3_absolute_overhead(sorted_pq, x, width, output_dir):
    """Phase 3 - 图3: PQ绝对开销"""

    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(x, sorted_pq['PQ_Overhead_Abs'], width*2, color=COLOR_OVERHEAD, alpha=0.8)

    for i, abs_overhead in enumerate(sorted_pq['PQ_Overhead_Abs']):
        ax.text(i, abs_overhead + 0.5, f'+{abs_overhead:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('PQ-NTOR Absolute Overhead (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR Absolute Time Overhead', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, max(sorted_pq['PQ_Overhead_Abs']) * 1.15])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig3_absolute_overhead.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图3: {output_file}")
    plt.close()


def create_phase3_fig4_cbt_breakdown(sorted_pq, x, width, output_dir):
    """Phase 3 - 图4: CBT组成堆叠图"""

    fig, ax = plt.subplots(figsize=(12, 7))

    crypto_cbt = sorted_pq['Crypto_CBT_ms']
    network_delay = sorted_pq['Network_Delay_ms']
    transmission = sorted_pq['Transmission_Delay_ms']
    retrans = sorted_pq['Retransmission_Delay_ms']

    ax.bar(x, crypto_cbt, width*2, label='Cryptographic Computation',
           color=COLOR_PQ, alpha=0.9)
    ax.bar(x, network_delay, width*2, bottom=crypto_cbt,
           label='Network Propagation Delay', color='#95a5a6', alpha=0.8)
    bottom = crypto_cbt + network_delay
    ax.bar(x, transmission, width*2, bottom=bottom,
           label='Transmission Delay', color='#3498db', alpha=0.7)
    bottom += transmission
    ax.bar(x, retrans, width*2, bottom=bottom,
           label='Retransmission Delay', color=COLOR_OVERHEAD, alpha=0.7)

    ax.set_xlabel('SAGIN Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR CBT Breakdown by Component', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_pq['Topology'], rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 70])  # 设置纵轴上限到70ms，避免图例遮挡topo12柱形

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig4_cbt_breakdown.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图4: {output_file}")
    plt.close()


def create_phase3_fig5_network_ratio(sorted_pq, x, width, output_dir):
    """Phase 3 - 图5: 网络延迟占比（按PQ-NTOR从高到低排序）"""

    # 按PQ-NTOR的Network_Ratio从高到低排序
    sorted_by_ratio = sorted_pq.sort_values('Network_Ratio', ascending=False).reset_index(drop=True)
    x_ratio = np.arange(len(sorted_by_ratio))

    fig, ax = plt.subplots(figsize=(12, 6))

    bars1 = ax.bar(x_ratio - width/2, sorted_by_ratio['Classic_Network_Ratio'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax.bar(x_ratio + width/2, sorted_by_ratio['Network_Ratio'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    for i, row in sorted_by_ratio.iterrows():
        ax.text(i - width/2, row['Classic_Network_Ratio'] + 1,
                f"{row['Classic_Network_Ratio']:.0f}%",
                ha='center', va='bottom', fontsize=7)
        ax.text(i + width/2, row['Network_Ratio'] + 1,
                f"{row['Network_Ratio']:.0f}%",
                ha='center', va='bottom', fontsize=7)

    ax.set_xlabel('SAGIN Topology (Sorted by PQ-NTOR Network Ratio)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Network Delay Ratio (%)', fontsize=12, fontweight='bold')
    ax.set_title('Network Delay Dominance', fontsize=13, fontweight='bold')
    ax.set_xticks(x_ratio)
    ax.set_xticklabels(sorted_by_ratio['Topology'], rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 105])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig5_network_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图5: {output_file}")
    plt.close()


def create_phase3_fig6_overhead_vs_bandwidth(sorted_pq, output_dir):
    """Phase 3 - 图6: PQ开销 vs 带宽"""

    fig, ax = plt.subplots(figsize=(10, 7))

    scatter = ax.scatter(sorted_pq['Bandwidth_Mbps'], sorted_pq['PQ_Overhead'],
                        s=200, c=sorted_pq['Link_Delay_ms'], cmap='RdYlGn_r',
                        alpha=0.7, edgecolors='black', linewidth=1.5)

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

    # 设置横轴刻度，覆盖带宽范围 10-50 Mbps
    ax.set_xticks([10, 15, 20, 25, 30, 40, 50])
    ax.set_xticklabels(['10', '15', '20', '25', '30', '40', '50'])
    ax.set_xlim([8, 60])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig6_overhead_vs_bandwidth.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图6: {output_file}")
    plt.close()


def create_phase3_fig7_overhead_vs_delay(sorted_pq, output_dir):
    """Phase 3 - 图7: PQ开销 vs 延迟"""

    fig, ax = plt.subplots(figsize=(10, 7))

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

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig7_overhead_vs_delay.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图7: {output_file}")
    plt.close()


def create_phase3_fig8_bandwidth_category(sorted_pq, output_dir):
    """Phase 3 - 图8: 按带宽分类汇总"""

    fig, ax = plt.subplots(figsize=(10, 6))

    high_bw = sorted_pq[sorted_pq['Bandwidth_Mbps'] > 25]
    mid_bw = sorted_pq[(sorted_pq['Bandwidth_Mbps'] > 10) & (sorted_pq['Bandwidth_Mbps'] <= 25)]
    low_bw = sorted_pq[sorted_pq['Bandwidth_Mbps'] <= 10]

    categories = ['High BW\n(>25 Mbps)', 'Mid BW\n(10-25 Mbps)', 'Low BW\n(<10 Mbps)']
    means = [high_bw['PQ_Overhead'].mean(), mid_bw['PQ_Overhead'].mean(), low_bw['PQ_Overhead'].mean()]
    counts = [len(high_bw), len(mid_bw), len(low_bw)]

    colors_cat = ['green', 'orange', 'red']
    bars = ax.bar(categories, means, color=colors_cat, alpha=0.7, edgecolor='black', linewidth=2)

    for i, (mean, count) in enumerate(zip(means, counts)):
        ax.text(i, mean + 0.05, f'{mean:.2f}×\n(n={count})',
               ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline (1.0×)')

    ax.set_ylabel('Average PQ-NTOR Overhead (×)', fontsize=12, fontweight='bold')
    ax.set_title('PQ Overhead by Bandwidth Category', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0.9, max(means) * 1.15])

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig8_bandwidth_category.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图8: {output_file}")
    plt.close()


def create_phase3_fig9_best_worst_scenarios(sorted_pq, output_dir):
    """Phase 3 - 图9: 最佳/最差场景对比"""

    fig, ax = plt.subplots(figsize=(10, 7))

    best_3 = sorted_pq.head(3)[::-1]
    worst_3 = sorted_pq.tail(3)

    combined = pd.concat([best_3, worst_3]).reset_index(drop=True)
    x = np.arange(len(combined))

    colors_scenario = ['red' if oh > 1.5 else 'orange' if oh > 1.1 else 'green'
                       for oh in combined['PQ_Overhead']]

    bars = ax.barh(x, combined['PQ_Overhead'], color=colors_scenario, alpha=0.8, edgecolor='black')

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

    ax.axhline(y=2.5, color='black', linestyle='-', linewidth=2, alpha=0.5)
    ax.text(1.9, 2.5, 'Best ↑\nWorst ↓', va='center', ha='center',
           fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    plt.tight_layout()

    output_file = f'{output_dir}/figure/phase3_fig9_best_worst_scenarios.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    print(f"✅ Phase 3 图9: {output_file}")
    plt.close()


def main():
    print("="*80)
    print("📊 生成单独PDF图表 - Phase 2 + Phase 3")
    print("="*80)
    print()

    output_dir = '/home/ccc/pq-ntor-experiment/essay'

    # 确保figure目录存在
    os.makedirs(f'{output_dir}/figure', exist_ok=True)

    # Phase 2: 3张图
    print("=" * 80)
    print("Phase 2: 文献对比（3张图）")
    print("=" * 80)
    create_phase2_fig1_handshake_comparison(output_dir)
    create_phase2_fig2_overhead_comparison(output_dir)
    create_phase2_fig3_summary_table(output_dir)
    print()

    # Phase 3: 9张图
    print("=" * 80)
    print("Phase 3: SAGIN拓扑分析（9张图）")
    print("=" * 80)
    # 使用最新的转换后的CSV（2025-12-11 修正版：统一使用2.71ms传播延迟）
    csv_path = '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase3_sagin_cbt_with_network_unified_delay.csv'
    create_phase3_figures(csv_path, output_dir)
    print()

    print("="*80)
    print("✅ 所有PDF图表生成完成!")
    print("="*80)
    print()
    print(f"📁 输出目录: {output_dir}/figure/")
    print()
    print("📊 生成的图表:")
    print("  Phase 2 (3张):")
    print("    - phase2_fig1_handshake_comparison.pdf")
    print("    - phase2_fig2_overhead_comparison.pdf")
    print("    - phase2_fig3_summary_table.pdf")
    print()
    print("  Phase 3 (9张):")
    print("    - phase3_fig1_cbt_comparison.pdf")
    print("    - phase3_fig2_overhead_ratio.pdf")
    print("    - phase3_fig3_absolute_overhead.pdf")
    print("    - phase3_fig4_cbt_breakdown.pdf")
    print("    - phase3_fig5_network_ratio.pdf")
    print("    - phase3_fig6_overhead_vs_bandwidth.pdf")
    print("    - phase3_fig7_overhead_vs_delay.pdf")
    print("    - phase3_fig8_bandwidth_category.pdf")
    print("    - phase3_fig9_best_worst_scenarios.pdf")
    print()
    print("总计: 12张PDF图表")
    print()

if __name__ == '__main__':
    main()
