#!/usr/bin/env python3
"""
生成包含网络影响的Total_CBT可视化图表
基于最新修正的拓扑参数
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from datetime import datetime

# 设置论文风格
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

# 颜色方案
COLOR_CLASSIC = '#2E86AB'   # 蓝色 - Classic NTOR
COLOR_PQ = '#E63946'        # 红色 - PQ-NTOR
COLOR_HYBRID = '#52B788'    # 绿色 - Hybrid NTOR
COLOR_UPLINK = '#3498db'    # 浅蓝 - 上行
COLOR_DOWNLINK = '#e74c3c'  # 浅红 - 下行

# 目录设置
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"
FIGURES_DIR = SCRIPT_DIR.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

def load_cbt_data():
    """加载Total_CBT数据"""
    csv_file = RESULTS_DIR / "phase3_sagin_cbt_with_network_20251215.csv"

    if not csv_file.exists():
        print(f"❌ 找不到数据文件: {csv_file}")
        return None

    df = pd.read_csv(csv_file)
    print(f"✅ 加载了 {len(df)} 条数据记录")
    return df


def plot_total_cbt_by_topology(df):
    """图1: 12拓扑Total_CBT对比柱状图"""
    print("\n📈 生成图1: 12拓扑Total_CBT对比...")

    fig, ax = plt.subplots(figsize=(14, 6))

    # 获取拓扑列表 (12个拓扑)
    x = np.arange(12)
    width = 0.25

    # 分组数据 - 按拓扑排序
    classic_data = df[df['Protocol'] == 'Classic NTOR'].sort_values('Topology')['Total_CBT_ms'].values
    pq_data = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology')['Total_CBT_ms'].values
    hybrid_data = df[df['Protocol'] == 'Hybrid NTOR'].sort_values('Topology')['Total_CBT_ms'].values

    # 绘制柱状图
    bars1 = ax.bar(x - width, classic_data, width, label='Classic NTOR',
                   color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x, pq_data, width, label='PQ-NTOR',
                   color=COLOR_PQ, alpha=0.8, edgecolor='black')
    bars3 = ax.bar(x + width, hybrid_data, width, label='Hybrid NTOR',
                   color=COLOR_HYBRID, alpha=0.8, edgecolor='black')

    # 添加分隔线（上行/下行）
    ax.axvline(x=5.5, color='gray', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(2.5, ax.get_ylim()[1]*0.95, 'Uplink (Topo 01-06)', ha='center',
            fontsize=11, fontweight='bold', color='#2c3e50')
    ax.text(8.5, ax.get_ylim()[1]*0.95, 'Downlink (Topo 07-12)', ha='center',
            fontsize=11, fontweight='bold', color='#2c3e50')

    ax.set_xlabel('Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Circuit Build Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Total CBT Across 12 SAGIN Topologies (Including Network Delay)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'T{i+1:02d}' for i in range(12)], fontsize=10)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加统计摘要框
    avg_classic = np.mean(classic_data)
    avg_pq = np.mean(pq_data)
    avg_hybrid = np.mean(hybrid_data)

    summary_text = f'Average Total CBT:\n'
    summary_text += f'Classic: {avg_classic:.2f} ms\n'
    summary_text += f'PQ-NTOR: {avg_pq:.2f} ms\n'
    summary_text += f'Hybrid: {avg_hybrid:.2f} ms'

    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = FIGURES_DIR / f"total_cbt_12topo_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / f"total_cbt_12topo_{timestamp}.pdf", format='pdf', bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_uplink_vs_downlink(df):
    """图2: 上行vs下行性能对比（按Zone分组）"""
    print("\n📈 生成图2: 上行vs下行对比...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 提取上行(01-06)和下行(07-12)数据
    uplink_topos = ['topo01', 'topo02', 'topo03', 'topo04', 'topo05', 'topo06']
    downlink_topos = ['topo07', 'topo08', 'topo09', 'topo10', 'topo11', 'topo12']

    # Z1-Z4: 对称设计，下行应该更好
    # Z5-Z6: 非对称设计，上行应该更好

    for protocol_idx, protocol in enumerate(['Classic NTOR', 'PQ-NTOR', 'Hybrid NTOR']):
        protocol_df = df[df['Protocol'] == protocol]

        # 按Zone分组
        zones_symmetric = ['Z1', 'Z2', 'Z3', 'Z4']  # 对称Zone
        zones_asymmetric = ['Z5', 'Z6']  # 非对称Zone

        # Z1-Z4对比
        z1_4_uplink = []
        z1_4_downlink = []
        for i in range(4):
            up_topo = uplink_topos[i]
            down_topo = downlink_topos[i]
            z1_4_uplink.append(protocol_df[protocol_df['Topology'] == up_topo]['Total_CBT_ms'].values[0])
            z1_4_downlink.append(protocol_df[protocol_df['Topology'] == down_topo]['Total_CBT_ms'].values[0])

        # Z5-Z6对比
        z5_6_uplink = []
        z5_6_downlink = []
        for i in range(4, 6):
            up_topo = uplink_topos[i]
            down_topo = downlink_topos[i]
            z5_6_uplink.append(protocol_df[protocol_df['Topology'] == up_topo]['Total_CBT_ms'].values[0])
            z5_6_downlink.append(protocol_df[protocol_df['Topology'] == down_topo]['Total_CBT_ms'].values[0])

    # 子图1: Z1-Z4 对称Zone (下行应该更好)
    ax1 = axes[0]

    # 计算各协议的平均值
    protocols = ['Classic NTOR', 'PQ-NTOR', 'Hybrid NTOR']
    colors = [COLOR_CLASSIC, COLOR_PQ, COLOR_HYBRID]

    x = np.arange(len(protocols))
    width = 0.35

    uplink_means_z14 = []
    downlink_means_z14 = []

    for protocol in protocols:
        protocol_df = df[df['Protocol'] == protocol]
        uplink_vals = [protocol_df[protocol_df['Topology'] == t]['Total_CBT_ms'].values[0] for t in uplink_topos[:4]]
        downlink_vals = [protocol_df[protocol_df['Topology'] == t]['Total_CBT_ms'].values[0] for t in downlink_topos[:4]]
        uplink_means_z14.append(np.mean(uplink_vals))
        downlink_means_z14.append(np.mean(downlink_vals))

    bars1 = ax1.bar(x - width/2, uplink_means_z14, width, label='Uplink (T01-T04)',
                    color=COLOR_UPLINK, alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x + width/2, downlink_means_z14, width, label='Downlink (T07-T10)',
                    color=COLOR_DOWNLINK, alpha=0.8, edgecolor='black')

    # 添加差异标注
    for i, (up, down) in enumerate(zip(uplink_means_z14, downlink_means_z14)):
        diff = up - down
        ax1.annotate(f'{diff:+.2f}ms', xy=(i, max(up, down) + 0.3),
                    ha='center', fontsize=9, fontweight='bold',
                    color='green' if diff > 0 else 'red')

    ax1.set_xlabel('Protocol', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Average Total CBT (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('Z1-Z4 Symmetric Zones\n(Downlink should be better)', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['Classic', 'PQ', 'Hybrid'], fontsize=10)
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # 子图2: Z5-Z6 非对称Zone (上行应该更好)
    ax2 = axes[1]

    uplink_means_z56 = []
    downlink_means_z56 = []

    for protocol in protocols:
        protocol_df = df[df['Protocol'] == protocol]
        uplink_vals = [protocol_df[protocol_df['Topology'] == t]['Total_CBT_ms'].values[0] for t in uplink_topos[4:]]
        downlink_vals = [protocol_df[protocol_df['Topology'] == t]['Total_CBT_ms'].values[0] for t in downlink_topos[4:]]
        uplink_means_z56.append(np.mean(uplink_vals))
        downlink_means_z56.append(np.mean(downlink_vals))

    bars3 = ax2.bar(x - width/2, uplink_means_z56, width, label='Uplink (T05-T06)',
                    color=COLOR_UPLINK, alpha=0.8, edgecolor='black')
    bars4 = ax2.bar(x + width/2, downlink_means_z56, width, label='Downlink (T11-T12)',
                    color=COLOR_DOWNLINK, alpha=0.8, edgecolor='black')

    # 添加差异标注
    for i, (up, down) in enumerate(zip(uplink_means_z56, downlink_means_z56)):
        diff = up - down
        ax2.annotate(f'{diff:+.2f}ms', xy=(i, max(up, down) + 0.3),
                    ha='center', fontsize=9, fontweight='bold',
                    color='green' if diff < 0 else 'red')

    ax2.set_xlabel('Protocol', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Average Total CBT (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('Z5-Z6 Asymmetric Zones\n(Uplink should be better)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Classic', 'PQ', 'Hybrid'], fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = FIGURES_DIR / f"uplink_vs_downlink_zone_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / f"uplink_vs_downlink_zone_{timestamp}.pdf", format='pdf', bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_cbt_breakdown(df):
    """图3: CBT组成分解堆叠图"""
    print("\n📈 生成图3: CBT组成分解...")

    fig, ax = plt.subplots(figsize=(14, 6))

    # 只取PQ-NTOR数据展示分解
    pq_df = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology')

    x = np.arange(len(pq_df))
    width = 0.6

    # 堆叠条形图
    crypto = pq_df['Crypto_CBT_ms'].values
    network = pq_df['Network_Delay_ms'].values
    trans = pq_df['Transmission_Delay_ms'].values
    retrans = pq_df['Retransmission_Delay_ms'].values

    bars1 = ax.bar(x, crypto, width, label='Crypto CBT', color='#9b59b6', alpha=0.8)
    bars2 = ax.bar(x, network, width, bottom=crypto, label='Network Delay', color='#3498db', alpha=0.8)
    bars3 = ax.bar(x, trans, width, bottom=crypto+network, label='Transmission Delay', color='#2ecc71', alpha=0.8)
    bars4 = ax.bar(x, retrans, width, bottom=crypto+network+trans, label='Retransmission', color='#e74c3c', alpha=0.8)

    # 添加分隔线
    ax.axvline(x=5.5, color='gray', linestyle='--', linewidth=2, alpha=0.7)

    ax.set_xlabel('Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR Total CBT Breakdown by Component', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'T{i+1:02d}' for i in range(12)], fontsize=10)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加百分比标注
    network_ratio = pq_df['Network_Ratio'].values
    for i, ratio in enumerate(network_ratio):
        total = crypto[i] + network[i] + trans[i] + retrans[i]
        ax.text(i, total + 0.3, f'{ratio:.1f}%', ha='center', fontsize=8, fontweight='bold')

    ax.text(2.5, ax.get_ylim()[1]*0.92, 'Uplink', ha='center', fontsize=11, fontweight='bold')
    ax.text(8.5, ax.get_ylim()[1]*0.92, 'Downlink', ha='center', fontsize=11, fontweight='bold')

    plt.tight_layout()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = FIGURES_DIR / f"cbt_breakdown_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / f"cbt_breakdown_{timestamp}.pdf", format='pdf', bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_network_dominance(df):
    """图4: 网络延迟占比分析"""
    print("\n📈 生成图4: 网络延迟占比分析...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 子图1: 各协议网络占比柱状图
    protocols = ['Classic NTOR', 'PQ-NTOR', 'Hybrid NTOR']
    colors = [COLOR_CLASSIC, COLOR_PQ, COLOR_HYBRID]

    avg_ratios = []
    for protocol in protocols:
        protocol_df = df[df['Protocol'] == protocol]
        avg_ratios.append(protocol_df['Network_Ratio'].mean())

    bars = ax1.bar(protocols, avg_ratios, color=colors, alpha=0.8, edgecolor='black')

    for bar, ratio in zip(bars, avg_ratios):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{ratio:.1f}%', ha='center', fontsize=11, fontweight='bold')

    ax1.set_ylabel('Network Delay Ratio (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Average Network Delay Ratio by Protocol', fontsize=12, fontweight='bold')
    ax1.set_ylim([95, 100])
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # 子图2: 饼图展示典型拓扑的CBT组成
    # 选择T01 PQ-NTOR作为示例
    sample = df[(df['Topology'] == 'topo01') & (df['Protocol'] == 'PQ-NTOR')].iloc[0]

    sizes = [sample['Crypto_CBT_ms'], sample['Network_Delay_ms'],
             sample['Transmission_Delay_ms'], sample['Retransmission_Delay_ms']]
    labels = ['Crypto\n({:.2f}ms)'.format(sizes[0]),
              'Network\n({:.2f}ms)'.format(sizes[1]),
              'Transmission\n({:.2f}ms)'.format(sizes[2]),
              'Retransmission\n({:.2f}ms)'.format(sizes[3])]
    colors_pie = ['#9b59b6', '#3498db', '#2ecc71', '#e74c3c']
    explode = (0, 0.05, 0, 0)  # 突出网络延迟

    wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors_pie,
                                        autopct='%1.1f%%', explode=explode,
                                        startangle=90, textprops={'fontsize': 9})

    ax2.set_title(f'T01 PQ-NTOR CBT Composition\n(Total: {sample["Total_CBT_ms"]:.2f}ms)',
                 fontsize=12, fontweight='bold')

    plt.tight_layout()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = FIGURES_DIR / f"network_dominance_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / f"network_dominance_{timestamp}.pdf", format='pdf', bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_comprehensive_summary(df):
    """图5: 综合总结图"""
    print("\n📈 生成图5: 综合总结图...")

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    # 1. 各协议平均Total_CBT
    ax1 = fig.add_subplot(gs[0, 0])
    protocols = ['Classic NTOR', 'PQ-NTOR', 'Hybrid NTOR']
    colors = [COLOR_CLASSIC, COLOR_PQ, COLOR_HYBRID]

    means = [df[df['Protocol'] == p]['Total_CBT_ms'].mean() for p in protocols]
    stds = [df[df['Protocol'] == p]['Total_CBT_ms'].std() for p in protocols]

    bars = ax1.bar(range(3), means, yerr=stds, capsize=5, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_xticks(range(3))
    ax1.set_xticklabels(['Classic', 'PQ', 'Hybrid'], fontsize=10)
    ax1.set_ylabel('Total CBT (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('(a) Average Total CBT', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    for i, (m, s) in enumerate(zip(means, stds)):
        ax1.text(i, m + s + 0.3, f'{m:.1f}', ha='center', fontsize=10, fontweight='bold')

    # 2. 上行vs下行对比
    ax2 = fig.add_subplot(gs[0, 1])

    pq_df = df[df['Protocol'] == 'PQ-NTOR']
    uplink_mean = pq_df[pq_df['Topology'].str.contains('0[1-6]')]['Total_CBT_ms'].mean()
    downlink_mean = pq_df[pq_df['Topology'].str.contains('0[7-9]|1[0-2]')]['Total_CBT_ms'].mean()

    bars = ax2.bar(['Uplink\n(T01-06)', 'Downlink\n(T07-12)'],
                   [uplink_mean, downlink_mean],
                   color=[COLOR_UPLINK, COLOR_DOWNLINK], alpha=0.8, edgecolor='black')

    ax2.set_ylabel('PQ-NTOR Total CBT (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('(b) Uplink vs Downlink (PQ-NTOR)', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    for bar in bars:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{bar.get_height():.2f}', ha='center', fontsize=10, fontweight='bold')

    # 3. 网络参数分布
    ax3 = fig.add_subplot(gs[0, 2])

    # 获取唯一的拓扑参数
    unique_topos = df[df['Protocol'] == 'PQ-NTOR'][['Topology', 'Bandwidth_Mbps', 'Loss_Percent']].drop_duplicates()

    scatter = ax3.scatter(unique_topos['Bandwidth_Mbps'], unique_topos['Loss_Percent'],
                         s=100, c=range(12), cmap='viridis', alpha=0.7, edgecolors='black')

    ax3.set_xlabel('Bandwidth (Mbps)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Packet Loss (%)', fontsize=11, fontweight='bold')
    ax3.set_title('(c) Network Parameters Distribution', fontsize=12, fontweight='bold')
    ax3.grid(alpha=0.3)

    # 添加拓扑标签
    for i, row in unique_topos.iterrows():
        ax3.annotate(row['Topology'].replace('topo', 'T'),
                    (row['Bandwidth_Mbps'], row['Loss_Percent']),
                    fontsize=8, ha='center')

    # 4. 各拓扑Total_CBT柱状图
    ax4 = fig.add_subplot(gs[1, :2])

    x = np.arange(12)
    width = 0.25

    classic = df[df['Protocol'] == 'Classic NTOR'].sort_values('Topology')['Total_CBT_ms'].values
    pq = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology')['Total_CBT_ms'].values
    hybrid = df[df['Protocol'] == 'Hybrid NTOR'].sort_values('Topology')['Total_CBT_ms'].values

    ax4.bar(x - width, classic, width, label='Classic', color=COLOR_CLASSIC, alpha=0.8)
    ax4.bar(x, pq, width, label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)
    ax4.bar(x + width, hybrid, width, label='Hybrid', color=COLOR_HYBRID, alpha=0.8)

    ax4.axvline(x=5.5, color='gray', linestyle='--', linewidth=2, alpha=0.7)
    ax4.set_xlabel('Topology', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Total CBT (ms)', fontsize=11, fontweight='bold')
    ax4.set_title('(d) Total CBT Across All Topologies', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([f'T{i+1:02d}' for i in range(12)])
    ax4.legend(fontsize=9, loc='upper left')
    ax4.grid(axis='y', alpha=0.3)

    # 5. 统计摘要表
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')

    # 创建统计表格
    table_data = [
        ['Metric', 'Classic', 'PQ-NTOR', 'Hybrid'],
        ['Avg CBT (ms)', f'{means[0]:.2f}', f'{means[1]:.2f}', f'{means[2]:.2f}'],
        ['Std Dev (ms)', f'{stds[0]:.2f}', f'{stds[1]:.2f}', f'{stds[2]:.2f}'],
        ['Min (ms)', f'{df[df["Protocol"]=="Classic NTOR"]["Total_CBT_ms"].min():.2f}',
                     f'{df[df["Protocol"]=="PQ-NTOR"]["Total_CBT_ms"].min():.2f}',
                     f'{df[df["Protocol"]=="Hybrid NTOR"]["Total_CBT_ms"].min():.2f}'],
        ['Max (ms)', f'{df[df["Protocol"]=="Classic NTOR"]["Total_CBT_ms"].max():.2f}',
                     f'{df[df["Protocol"]=="PQ-NTOR"]["Total_CBT_ms"].max():.2f}',
                     f'{df[df["Protocol"]=="Hybrid NTOR"]["Total_CBT_ms"].max():.2f}'],
        ['Network %', f'{df[df["Protocol"]=="Classic NTOR"]["Network_Ratio"].mean():.1f}',
                      f'{df[df["Protocol"]=="PQ-NTOR"]["Network_Ratio"].mean():.1f}',
                      f'{df[df["Protocol"]=="Hybrid NTOR"]["Network_Ratio"].mean():.1f}'],
    ]

    table = ax5.table(cellText=table_data, cellLoc='center', loc='center',
                      colWidths=[0.3, 0.23, 0.23, 0.23])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2)

    for i in range(4):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    for i in range(1, len(table_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')

    ax5.set_title('(e) Statistical Summary', fontsize=12, fontweight='bold', pad=20)

    fig.suptitle('PQ-NTOR SAGIN Experiment: Comprehensive Performance Analysis',
                 fontsize=16, fontweight='bold', y=0.98)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = FIGURES_DIR / f"comprehensive_summary_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / f"comprehensive_summary_{timestamp}.pdf", format='pdf', bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("  📊 Total CBT可视化图表生成器 (包含网络影响)")
    print("=" * 70)
    print()

    # 加载数据
    df = load_cbt_data()

    if df is None:
        return

    print(f"\n📋 数据概览:")
    print(f"  - 拓扑数: {len(df['Topology'].unique())}")
    print(f"  - 协议数: {len(df['Protocol'].unique())}")
    print(f"  - Total_CBT范围: {df['Total_CBT_ms'].min():.2f} - {df['Total_CBT_ms'].max():.2f} ms")
    print(f"  - 网络占比范围: {df['Network_Ratio'].min():.1f}% - {df['Network_Ratio'].max():.1f}%")

    # 生成图表
    print("\n🎨 开始生成图表...\n")

    plot_total_cbt_by_topology(df)
    plot_uplink_vs_downlink(df)
    plot_cbt_breakdown(df)
    plot_network_dominance(df)
    plot_comprehensive_summary(df)

    print("\n" + "=" * 70)
    print("✅ 所有图表生成完成!")
    print(f"📁 保存位置: {FIGURES_DIR}")
    print("\n生成的图表:")
    print("  1. total_cbt_12topo_*.png/pdf     - 12拓扑Total_CBT对比")
    print("  2. uplink_vs_downlink_zone_*.png/pdf - 上行vs下行Zone对比")
    print("  3. cbt_breakdown_*.png/pdf        - CBT组成分解图")
    print("  4. network_dominance_*.png/pdf    - 网络延迟占比分析")
    print("  5. comprehensive_summary_*.png/pdf - 综合总结图 ⭐")
    print("=" * 70)


if __name__ == '__main__':
    main()
