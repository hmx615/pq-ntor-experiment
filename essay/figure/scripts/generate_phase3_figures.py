#!/usr/bin/env python3
"""
根据Phase 3 CSV数据生成9张论文级别图表
适配简单的phase3_sagin_cbt.csv格式
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
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

# 12拓扑网络参数 (从topology_params.json)
TOPO_PARAMS = {
    'topo01': {'bw': 59.27, 'delay': 5.42, 'loss': 3.0},
    'topo02': {'bw': 16.55, 'delay': 5.42, 'loss': 3.0},
    'topo03': {'bw': 25.19, 'delay': 2.72, 'loss': 1.0},
    'topo04': {'bw': 23.64, 'delay': 5.42, 'loss': 3.0},
    'topo05': {'bw': 25.19, 'delay': 5.43, 'loss': 3.0},
    'topo06': {'bw': 22.91, 'delay': 5.42, 'loss': 1.0},
    'topo07': {'bw': 69.43, 'delay': 5.42, 'loss': 2.0},
    'topo08': {'bw': 38.01, 'delay': 5.43, 'loss': 2.0},
    'topo09': {'bw': 29.84, 'delay': 2.72, 'loss': 0.5},
    'topo10': {'bw': 18.64, 'delay': 5.42, 'loss': 2.0},
    'topo11': {'bw': 9.67, 'delay': 5.43, 'loss': 2.0},
    'topo12': {'bw': 8.73, 'delay': 5.43, 'loss': 2.0},
}

CSV_PATH = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase3_sagin_cbt.csv')
OUTPUT_DIR = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/figures')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_and_prepare_data():
    """加载CSV数据并添加网络参数"""
    df = pd.read_csv(CSV_PATH)

    # 分离Classic和PQ数据
    classic = df[df['Protocol'] == 'Classic NTOR'].sort_values('Topology').reset_index(drop=True)
    pq = df[df['Protocol'] == 'PQ-NTOR'].sort_values('Topology').reset_index(drop=True)

    # 合并数据
    result = pq.copy()
    result['Classic_Mean_ms'] = classic['Mean_ms'].values
    result['PQ_Mean_ms'] = pq['Mean_ms'].values
    result['Overhead_Ratio'] = result['PQ_Mean_ms'] / result['Classic_Mean_ms']
    result['Overhead_Abs_ms'] = result['PQ_Mean_ms'] - result['Classic_Mean_ms']

    # 添加网络参数
    result['Bandwidth_Mbps'] = result['Topology'].map(lambda x: TOPO_PARAMS[x]['bw'])
    result['Delay_ms'] = result['Topology'].map(lambda x: TOPO_PARAMS[x]['delay'])
    result['Loss_Percent'] = result['Topology'].map(lambda x: TOPO_PARAMS[x]['loss'])

    return result

def fig1_cbt_comparison(df):
    """图1: 端到端CBT对比（柱状图）"""
    print("\n生成图1: CBT对比...")

    # 按PQ CBT降序排序
    sorted_df = df.sort_values('PQ_Mean_ms', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_df))
    width = 0.4

    bars1 = ax.bar(x - width/2, sorted_df['Classic_Mean_ms'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, sorted_df['PQ_Mean_ms'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8, edgecolor='black')

    # 添加网络参数注释
    for i, row in sorted_df.iterrows():
        bw = row['Bandwidth_Mbps']
        delay = row['Delay_ms']
        loss = row['Loss_Percent']

        color = 'green' if bw > 25 else ('orange' if bw > 10 else 'red')

        ax.text(i, max(row['Classic_Mean_ms'], row['PQ_Mean_ms']) + 0.02,
                f'{bw:.1f}Mbps\n{delay:.1f}ms\n{loss:.1f}%',
                ha='center', va='bottom', fontsize=7, color=color, fontweight='bold')

    ax.set_xlabel('SAGIN Topology (Sorted by PQ-NTOR CBT)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig1: Circuit Build Time Across 12 SAGIN Topologies',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_df['Topology'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig1_cbt_comparison.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig2_overhead_ratio(df):
    """图2: PQ开销倍数（折线图 - 你说的那张！）"""
    print("\n生成图2: PQ Overhead Ratio 折线图...")

    # 按Overhead Ratio降序排序
    sorted_df = df.sort_values('Overhead_Ratio', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_df))

    # 折线图 + 散点
    line = ax.plot(x, sorted_df['Overhead_Ratio'], 'o-',
                   color=COLOR_PQ, linewidth=2.5, markersize=10,
                   label='PQ/Classic Ratio', alpha=0.8)

    # 添加基准线 (ratio = 1.0)
    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, alpha=0.5, label='Parity (1.0×)')

    # 标注每个点的数值
    for i, row in sorted_df.iterrows():
        ratio = row['Overhead_Ratio']
        ax.text(i, ratio + 0.02, f'{ratio:.2f}×',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('SAGIN Topology (Sorted by Overhead Ratio)', fontsize=13, fontweight='bold')
    ax.set_ylabel('PQ-NTOR / Classic NTOR Ratio', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig2: PQ-NTOR Overhead Ratio Across 12 Topologies',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_df['Topology'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12, loc='upper right')
    ax.grid(alpha=0.3, linestyle='--')

    # 添加统计信息
    avg_ratio = sorted_df['Overhead_Ratio'].mean()
    ax.text(0.02, 0.98, f'Average Ratio: {avg_ratio:.2f}×\nPQ-NTOR is {1/avg_ratio:.2f}× faster!',
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig2_overhead_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig3_absolute_overhead(df):
    """图3: PQ绝对开销（柱状图）"""
    print("\n生成图3: 绝对开销...")

    sorted_df = df.sort_values('Overhead_Ratio', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(sorted_df))

    # 负值开销（PQ更快）
    colors = ['green' if val < 0 else 'red' for val in sorted_df['Overhead_Abs_ms']]
    bars = ax.bar(x, sorted_df['Overhead_Abs_ms'], color=colors, alpha=0.8, edgecolor='black')

    # 数值标注
    for i, (bar, val) in enumerate(zip(bars, sorted_df['Overhead_Abs_ms'])):
        height = bar.get_height()
        ax.text(i, height + (0.01 if height > 0 else -0.01), f'{val:.3f}ms',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

    ax.axhline(y=0, color='black', linewidth=1.5)
    ax.set_xlabel('SAGIN Topology', fontsize=13, fontweight='bold')
    ax.set_ylabel('PQ-NTOR - Classic NTOR (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig3: Absolute Overhead of PQ-NTOR',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_df['Topology'], rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 统计
    avg_overhead = sorted_df['Overhead_Abs_ms'].mean()
    ax.text(0.98, 0.98, f'Avg Overhead: {avg_overhead:.3f}ms\n(Negative = PQ faster)',
            transform=ax.transAxes, ha='right', va='top', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightgreen' if avg_overhead < 0 else 'lightcoral', alpha=0.7))

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig3_absolute_overhead.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig4_cbt_breakdown(df):
    """图4: CBT分解堆叠图"""
    print("\n生成图4: CBT分解...")

    sorted_df = df.sort_values('Overhead_Ratio', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(sorted_df))
    width = 0.4

    # Classic和PQ的CBT堆叠显示
    ax.bar(x - width/2, sorted_df['Classic_Mean_ms'], width,
            label='Classic NTOR CBT', color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')
    ax.bar(x + width/2, sorted_df['PQ_Mean_ms'], width,
            label='PQ-NTOR CBT', color=COLOR_PQ, alpha=0.8, edgecolor='black')

    ax.set_xlabel('SAGIN Topology', fontsize=13, fontweight='bold')
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig4: CBT Breakdown Comparison',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_df['Topology'], rotation=45, ha='right')
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig4_cbt_breakdown.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig5_network_ratio(df):
    """图5: 网络延迟占比"""
    print("\n生成图5: 网络延迟占比...")

    sorted_df = df.sort_values('Overhead_Ratio', ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(sorted_df))

    # 估算网络延迟占比（3跳 * 单跳延迟 / 总CBT）
    sorted_df['Network_Ratio_Classic'] = (3 * sorted_df['Delay_ms']) / sorted_df['Classic_Mean_ms']
    sorted_df['Network_Ratio_PQ'] = (3 * sorted_df['Delay_ms']) / sorted_df['PQ_Mean_ms']

    ax.plot(x, sorted_df['Network_Ratio_Classic'] * 100, 'o-',
            color=COLOR_CLASSIC, linewidth=2, markersize=8, label='Classic NTOR', alpha=0.8)
    ax.plot(x, sorted_df['Network_Ratio_PQ'] * 100, 's--',
            color=COLOR_PQ, linewidth=2, markersize=8, label='PQ-NTOR', alpha=0.8)

    ax.set_xlabel('SAGIN Topology', fontsize=13, fontweight='bold')
    ax.set_ylabel('Network Delay Ratio (%)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig5: Network Delay Contribution to Total CBT',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_df['Topology'], rotation=45, ha='right')
    ax.legend(fontsize=12)
    ax.grid(alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig5_network_ratio.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig6_overhead_vs_bandwidth(df):
    """图6: PQ开销 vs 带宽散点图"""
    print("\n生成图6: Overhead vs 带宽...")

    fig, ax = plt.subplots(figsize=(10, 7))

    scatter = ax.scatter(df['Bandwidth_Mbps'], df['Overhead_Ratio'],
                         s=200, c=df['Delay_ms'], cmap='viridis',
                         alpha=0.7, edgecolors='black', linewidth=1.5)

    # 标注拓扑名称
    for _, row in df.iterrows():
        ax.annotate(row['Topology'], (row['Bandwidth_Mbps'], row['Overhead_Ratio']),
                    fontsize=8, ha='center', va='bottom')

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Bandwidth (Mbps)', fontsize=13, fontweight='bold')
    ax.set_ylabel('PQ/Classic Overhead Ratio', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig6: Overhead Ratio vs Bandwidth',
                  fontsize=14, fontweight='bold', pad=15)
    ax.grid(alpha=0.3, linestyle='--')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Network Delay (ms)', fontsize=11)

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig6_overhead_vs_bandwidth.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig7_overhead_vs_delay(df):
    """图7: PQ开销 vs 延迟散点图"""
    print("\n生成图7: Overhead vs 延迟...")

    fig, ax = plt.subplots(figsize=(10, 7))

    scatter = ax.scatter(df['Delay_ms'], df['Overhead_Ratio'],
                         s=df['Bandwidth_Mbps']*5, c=df['Loss_Percent'],
                         cmap='YlOrRd', alpha=0.7, edgecolors='black', linewidth=1.5)

    # 标注
    for _, row in df.iterrows():
        ax.annotate(row['Topology'], (row['Delay_ms'], row['Overhead_Ratio']),
                    fontsize=8, ha='center', va='bottom')

    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Network Delay (ms)', fontsize=13, fontweight='bold')
    ax.set_ylabel('PQ/Classic Overhead Ratio', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig7: Overhead Ratio vs Delay (Size=BW, Color=Loss)',
                  fontsize=14, fontweight='bold', pad=15)
    ax.grid(alpha=0.3, linestyle='--')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Packet Loss (%)', fontsize=11)

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig7_overhead_vs_delay.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig8_bandwidth_category(df):
    """图8: 按带宽分类汇总"""
    print("\n生成图8: 按带宽分类...")

    # 带宽分类
    df['BW_Category'] = pd.cut(df['Bandwidth_Mbps'],
                                bins=[0, 15, 30, 100],
                                labels=['Low (<15Mbps)', 'Medium (15-30Mbps)', 'High (>30Mbps)'])

    grouped = df.groupby('BW_Category').agg({
        'Overhead_Ratio': 'mean',
        'Classic_Mean_ms': 'mean',
        'PQ_Mean_ms': 'mean'
    }).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(grouped))
    width = 0.35

    bars1 = ax.bar(x - width/2, grouped['Classic_Mean_ms'], width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8)
    bars2 = ax.bar(x + width/2, grouped['PQ_Mean_ms'], width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8)

    ax.set_xlabel('Bandwidth Category', fontsize=13, fontweight='bold')
    ax.set_ylabel('Average CBT (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig8: Performance by Bandwidth Category',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(grouped['BW_Category'])
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 标注ratio
    for i, ratio in enumerate(grouped['Overhead_Ratio']):
        ax.text(i, max(grouped['Classic_Mean_ms'].iloc[i], grouped['PQ_Mean_ms'].iloc[i]) + 0.02,
                f'{ratio:.2f}×', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig8_bandwidth_category.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def fig9_best_worst_scenarios(df):
    """图9: 最佳/最差场景对比"""
    print("\n生成图9: 最佳/最差场景...")

    # 最佳场景（PQ最快的）
    best = df.loc[df['PQ_Mean_ms'].idxmin()]
    # 最差场景（PQ相对最慢的）
    worst = df.loc[df['Overhead_Ratio'].idxmax()]

    scenarios = ['Best Scenario\n' + best['Topology'], 'Worst Scenario\n' + worst['Topology']]
    classic_vals = [best['Classic_Mean_ms'], worst['Classic_Mean_ms']]
    pq_vals = [best['PQ_Mean_ms'], worst['PQ_Mean_ms']]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(scenarios))
    width = 0.35

    bars1 = ax.bar(x - width/2, classic_vals, width,
                    label='Classic NTOR', color=COLOR_CLASSIC, alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, pq_vals, width,
                    label='PQ-NTOR', color=COLOR_PQ, alpha=0.8, edgecolor='black')

    # 数值标注
    for i, (c_val, p_val) in enumerate(zip(classic_vals, pq_vals)):
        ax.text(i - width/2, c_val + 0.01, f'{c_val:.3f}ms',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(i + width/2, p_val + 0.01, f'{p_val:.3f}ms',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Circuit Build Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('Phase 3 Fig9: Best vs Worst Scenarios',
                  fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=11)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加场景信息
    best_info = f"Best: BW={best['Bandwidth_Mbps']:.1f}Mbps, Delay={best['Delay_ms']:.1f}ms\nRatio={best['Overhead_Ratio']:.2f}×"
    worst_info = f"Worst: BW={worst['Bandwidth_Mbps']:.1f}Mbps, Delay={worst['Delay_ms']:.1f}ms\nRatio={worst['Overhead_Ratio']:.2f}×"

    ax.text(0, max(classic_vals + pq_vals) * 0.9, best_info,
            fontsize=9, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.5))
    ax.text(1, max(classic_vals + pq_vals) * 0.9, worst_info,
            fontsize=9, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.5))

    plt.tight_layout()

    output_file = OUTPUT_DIR / 'phase3_fig9_best_worst_scenarios.pdf'
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.png'), dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

def main():
    """主函数"""
    print("=" * 80)
    print("  Phase 3 图表生成器 - 基于最新CSV数据")
    print("=" * 80)
    print()
    print(f"数据源: {CSV_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 80)

    # 加载数据
    print("\n加载数据...")
    df = load_and_prepare_data()
    print(f"✅ 加载了 {len(df)} 个拓扑的数据")

    # 生成9张图
    print("\n开始生成图表...")
    print("-" * 80)

    fig1_cbt_comparison(df)
    fig2_overhead_ratio(df)  # 这就是你说的折线图！
    fig3_absolute_overhead(df)
    fig4_cbt_breakdown(df)
    fig5_network_ratio(df)
    fig6_overhead_vs_bandwidth(df)
    fig7_overhead_vs_delay(df)
    fig8_bandwidth_category(df)
    fig9_best_worst_scenarios(df)

    print()
    print("=" * 80)
    print("✅ 所有Phase 3图表生成完成！")
    print("=" * 80)
    print()
    print("生成的图表:")
    print("  1. phase3_fig1_cbt_comparison.pdf/png       - CBT对比柱状图")
    print("  2. phase3_fig2_overhead_ratio.pdf/png       - Overhead比率折线图 ⭐")
    print("  3. phase3_fig3_absolute_overhead.pdf/png    - 绝对overhead")
    print("  4. phase3_fig4_cbt_breakdown.pdf/png        - CBT分解")
    print("  5. phase3_fig5_network_ratio.pdf/png        - 网络延迟占比")
    print("  6. phase3_fig6_overhead_vs_bandwidth.pdf/png - Overhead vs 带宽")
    print("  7. phase3_fig7_overhead_vs_delay.pdf/png    - Overhead vs 延迟")
    print("  8. phase3_fig8_bandwidth_category.pdf/png   - 带宽分类汇总")
    print("  9. phase3_fig9_best_worst_scenarios.pdf/png - 最佳/最差场景")
    print()

if __name__ == '__main__':
    main()
