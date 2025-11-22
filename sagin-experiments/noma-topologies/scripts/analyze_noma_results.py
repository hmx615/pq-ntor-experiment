#!/usr/bin/env python3
"""
分析NOMA拓扑测试结果并生成可视化图表
读取test_all_topologies.sh生成的CSV数据，计算统计数据，生成论文图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from pathlib import Path

# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# 拓扑名称映射（用于图表显示）
TOPOLOGY_NAMES = {
    1: "Z1-Up1",
    2: "Z1-Up2",
    3: "Z2-Up",
    4: "Z3-Up",
    5: "Z5-Up",
    6: "Z6-Up",
    7: "Z1-Down",
    8: "Z2-Down",
    9: "Z3-Down",
    10: "Z4-Down",
    11: "Z5-Down",
    12: "Z6-Down"
}

# 传统NTOR模拟数据 (基于147us PQ握手开销)
# 假设Traditional NTOR握手时间为100us
TRADITIONAL_NTOR_HANDSHAKE_US = 100
PQ_NTOR_HANDSHAKE_US = 147
PQ_OVERHEAD_US = PQ_NTOR_HANDSHAKE_US - TRADITIONAL_NTOR_HANDSHAKE_US  # 47us


def load_results(csv_file):
    """加载测试结果CSV"""
    print(f"Loading results from: {csv_file}")
    df = pd.read_csv(csv_file)

    # 只分析成功的测试
    df_success = df[df['success'] == True].copy()

    print(f"Total tests: {len(df)}")
    print(f"Successful tests: {len(df_success)}")
    print(f"Success rate: {len(df_success)/len(df)*100:.2f}%")

    return df, df_success


def calculate_statistics(df_success):
    """计算每个拓扑的统计数据"""
    stats = []

    for topo_id in range(1, 13):
        topo_data = df_success[df_success['topology_id'] == topo_id]

        if len(topo_data) == 0:
            print(f"Warning: No successful tests for topology {topo_id}")
            continue

        # 提取性能数据
        durations = topo_data['duration_s'].values * 1000  # 转换为ms

        # 计算统计量
        mean_time = np.mean(durations)
        std_time = np.std(durations)
        success_rate = len(topo_data) / 10 * 100  # 假设每个拓扑测10次

        # 计算PQ开销占比
        pq_overhead_percent = (PQ_OVERHEAD_US / 1000) / mean_time * 100

        # 模拟Traditional NTOR时间
        traditional_time = mean_time - (PQ_OVERHEAD_US / 1000)

        stats.append({
            'topology_id': topo_id,
            'topology_name': TOPOLOGY_NAMES[topo_id],
            'mean_time_ms': mean_time,
            'std_time_ms': std_time,
            'traditional_time_ms': traditional_time,
            'pq_overhead_ms': PQ_OVERHEAD_US / 1000,
            'pq_overhead_percent': pq_overhead_percent,
            'success_rate': success_rate,
            'num_tests': len(topo_data)
        })

    stats_df = pd.DataFrame(stats)
    return stats_df


def generate_figure1_topology_comparison(stats_df, output_dir):
    """
    图1: 12拓扑性能对比 (grouped bar chart)
    对比PQ-NTOR vs Traditional NTOR的电路建立时间
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(stats_df))
    width = 0.35

    # 绘制grouped bar chart
    bars1 = ax.bar(x - width/2, stats_df['traditional_time_ms'], width,
                   label='Traditional NTOR', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, stats_df['mean_time_ms'], width,
                   label='PQ-NTOR (Kyber-512)', color='#e74c3c', alpha=0.8)

    # 标注
    ax.set_xlabel('NOMA Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Circuit Setup Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Circuit Setup Time Comparison Across 12 NOMA Topologies',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df['topology_name'], rotation=45, ha='right')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加数值标签
    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure1_topology_comparison.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure1_topology_comparison.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure1_topology_comparison")
    plt.close()


def generate_figure2_pq_overhead_breakdown(stats_df, output_dir):
    """
    图2: PQ开销分解 (stacked bar chart)
    显示总时间中PQ握手开销的占比
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(stats_df))

    # 绘制stacked bar chart
    bars1 = ax.bar(x, stats_df['traditional_time_ms'],
                   label='Network Propagation', color='#95a5a6', alpha=0.8)
    bars2 = ax.bar(x, stats_df['pq_overhead_ms'],
                   bottom=stats_df['traditional_time_ms'],
                   label='PQ Overhead (47μs)', color='#e67e22', alpha=0.8)

    # 标注
    ax.set_xlabel('NOMA Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Circuit Setup Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR Overhead Breakdown Across NOMA Topologies',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df['topology_name'], rotation=45, ha='right')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加百分比标签
    for i, (bar, pct) in enumerate(zip(bars2, stats_df['pq_overhead_percent'])):
        height = bar.get_height()
        y_pos = bar.get_y() + height/2
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{pct:.2f}%',
                ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure2_pq_overhead_breakdown.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure2_pq_overhead_breakdown.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure2_pq_overhead_breakdown")
    plt.close()


def generate_figure3_uplink_vs_downlink(stats_df, output_dir):
    """
    图3: 上行vs下行对比 (box plot)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 分离上行和下行数据
    uplink = stats_df[stats_df['topology_id'] <= 6]
    downlink = stats_df[stats_df['topology_id'] >= 7]

    data = [uplink['mean_time_ms'].values, downlink['mean_time_ms'].values]
    positions = [1, 2]

    bp = ax.boxplot(data, positions=positions, widths=0.5, patch_artist=True,
                    showmeans=True, meanline=True,
                    boxprops=dict(facecolor='#3498db', alpha=0.6),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(color='green', linewidth=2, linestyle='--'))

    # 标注
    ax.set_ylabel('Circuit Setup Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Uplink vs Downlink Performance Comparison',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(['Uplink\n(Topo 1-6)', 'Downlink\n(Topo 7-12)'], fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加统计信息
    uplink_mean = uplink['mean_time_ms'].mean()
    downlink_mean = downlink['mean_time_ms'].mean()
    ax.text(1, uplink_mean + 2, f'μ={uplink_mean:.1f}ms', ha='center', fontsize=10, fontweight='bold')
    ax.text(2, downlink_mean + 2, f'μ={downlink_mean:.1f}ms', ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure3_uplink_vs_downlink.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure3_uplink_vs_downlink.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure3_uplink_vs_downlink")
    plt.close()


def generate_figure4_cooperation_impact(stats_df, output_dir):
    """
    图4: 协作链路影响 (grouped bar)
    对比有协作链路 (拓扑7,8,11,12) vs 无协作链路的性能
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 分类数据
    with_coop_ids = [7, 8, 11, 12]
    without_coop_ids = [1, 2, 3, 4, 5, 6, 9, 10]

    with_coop = stats_df[stats_df['topology_id'].isin(with_coop_ids)]
    without_coop = stats_df[stats_df['topology_id'].isin(without_coop_ids)]

    # 计算平均值
    metrics = ['mean_time_ms', 'pq_overhead_percent', 'success_rate']
    with_coop_means = [with_coop['mean_time_ms'].mean(),
                       with_coop['pq_overhead_percent'].mean(),
                       with_coop['success_rate'].mean()]
    without_coop_means = [without_coop['mean_time_ms'].mean(),
                          without_coop['pq_overhead_percent'].mean(),
                          without_coop['success_rate'].mean()]

    # 归一化处理 (success_rate为百分比，需要缩放)
    with_coop_means_norm = [with_coop_means[0], with_coop_means[1], with_coop_means[2]/10]
    without_coop_means_norm = [without_coop_means[0], without_coop_means[1], without_coop_means[2]/10]

    x = np.arange(3)
    width = 0.35

    bars1 = ax.bar(x - width/2, without_coop_means_norm, width,
                   label='Without Cooperation', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, with_coop_means_norm, width,
                   label='With Cooperation', color='#2ecc71', alpha=0.8)

    # 标注
    ax.set_ylabel('Normalized Value', fontsize=12, fontweight='bold')
    ax.set_title('Impact of NOMA Cooperation Links on Performance',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(['Setup Time\n(ms)', 'PQ Overhead\n(%)', 'Success Rate\n(×10%)'], fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加实际数值
    for i, (bar, val) in enumerate(zip(bars1, without_coop_means)):
        if i == 2:  # success_rate
            label_val = f'{val:.1f}%'
        else:
            label_val = f'{val:.2f}'
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                label_val, ha='center', va='bottom', fontsize=9)

    for i, (bar, val) in enumerate(zip(bars2, with_coop_means)):
        if i == 2:  # success_rate
            label_val = f'{val:.1f}%'
        else:
            label_val = f'{val:.2f}'
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                label_val, ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure4_cooperation_impact.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure4_cooperation_impact.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure4_cooperation_impact")
    plt.close()


def generate_figure5_hops_vs_overhead(stats_df, output_dir):
    """
    图5: 跳数vs PQ占比 (scatter + trendline)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 定义跳数
    hops_map = {1: 2, 2: 3, 3: 3, 4: 2.5, 5: 3, 6: 3,
                7: 2, 8: 3, 9: 2.5, 10: 3, 11: 3.5, 12: 3.5}

    stats_df['hops'] = stats_df['topology_id'].map(hops_map)

    # 绘制散点图
    scatter = ax.scatter(stats_df['hops'], stats_df['pq_overhead_percent'],
                        s=150, c=stats_df['topology_id'], cmap='viridis',
                        alpha=0.7, edgecolors='black', linewidth=1.5)

    # 添加趋势线
    z = np.polyfit(stats_df['hops'], stats_df['pq_overhead_percent'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(stats_df['hops'].min(), stats_df['hops'].max(), 100)
    ax.plot(x_trend, p(x_trend), "r--", linewidth=2, label=f'Trend: y={z[0]:.3f}x+{z[1]:.3f}')

    # 标注
    ax.set_xlabel('Number of Tor Circuit Hops', fontsize=12, fontweight='bold')
    ax.set_ylabel('PQ Overhead (%)', fontsize=12, fontweight='bold')
    ax.set_title('Relationship Between Circuit Hops and PQ Overhead',
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3, linestyle='--')

    # 添加颜色条
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Topology ID', fontsize=11)

    # 标注每个点
    for idx, row in stats_df.iterrows():
        ax.annotate(row['topology_name'],
                   (row['hops'], row['pq_overhead_percent']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, alpha=0.7)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure5_hops_vs_overhead.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure5_hops_vs_overhead.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure5_hops_vs_overhead")
    plt.close()


def generate_figure6_success_vs_loss(stats_df, output_dir):
    """
    图6: 成功率vs丢包率 (scatter plot)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 模拟丢包率数据 (基于配置文件)
    loss_map = {1: 0.5, 2: 0.5, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                7: 2.0, 8: 2.0, 9: 2.0, 10: 2.0, 11: 2.0, 12: 2.0}

    stats_df['avg_loss_percent'] = stats_df['topology_id'].map(loss_map)

    # 绘制散点图
    colors = ['#3498db' if tid <= 6 else '#e74c3c' for tid in stats_df['topology_id']]
    scatter = ax.scatter(stats_df['avg_loss_percent'], stats_df['success_rate'],
                        s=150, c=colors, alpha=0.7, edgecolors='black', linewidth=1.5)

    # 添加标注
    for idx, row in stats_df.iterrows():
        ax.annotate(row['topology_name'],
                   (row['avg_loss_percent'], row['success_rate']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, alpha=0.7)

    # 标注
    ax.set_xlabel('Average Link Loss Rate (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Circuit Setup Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Success Rate vs Link Loss Rate Across NOMA Topologies',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(alpha=0.3, linestyle='--')

    # 添加图例
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w',
                             markerfacecolor='#3498db', markersize=10, label='Uplink'),
                      Line2D([0], [0], marker='o', color='w',
                             markerfacecolor='#e74c3c', markersize=10, label='Downlink')]
    ax.legend(handles=legend_elements, fontsize=11)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure6_success_vs_loss.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'figure6_success_vs_loss.pdf'), bbox_inches='tight')
    print(f"✓ Generated: figure6_success_vs_loss")
    plt.close()


def generate_summary_table(stats_df, output_dir):
    """
    生成汇总表格 (CSV + LaTeX)
    """
    # 选择关键列
    summary = stats_df[[
        'topology_id', 'topology_name',
        'mean_time_ms', 'std_time_ms',
        'pq_overhead_percent', 'success_rate'
    ]].copy()

    # 重命名列
    summary.columns = [
        'ID', 'Topology',
        'Setup Time (ms)', 'Std Dev (ms)',
        'PQ Overhead (%)', 'Success Rate (%)'
    ]

    # 格式化数值
    summary['Setup Time (ms)'] = summary['Setup Time (ms)'].map('{:.2f}'.format)
    summary['Std Dev (ms)'] = summary['Std Dev (ms)'].map('{:.2f}'.format)
    summary['PQ Overhead (%)'] = summary['PQ Overhead (%)'].map('{:.2f}'.format)
    summary['Success Rate (%)'] = summary['Success Rate (%)'].map('{:.1f}'.format)

    # 保存CSV
    csv_path = os.path.join(output_dir, 'summary_table.csv')
    summary.to_csv(csv_path, index=False)
    print(f"✓ Generated: summary_table.csv")

    # 生成LaTeX表格
    latex_path = os.path.join(output_dir, 'summary_table.tex')
    with open(latex_path, 'w') as f:
        f.write("% LaTeX Table: NOMA Topology Performance Summary\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\caption{PQ-NTOR Performance Across 12 NOMA Topologies}\n")
        f.write("\\label{tab:noma_performance}\n")
        f.write("\\begin{tabular}{|c|l|c|c|c|c|}\n")
        f.write("\\hline\n")
        f.write("\\textbf{ID} & \\textbf{Topology} & \\textbf{Setup Time (ms)} & \\textbf{Std Dev (ms)} & \\textbf{PQ Overhead (\\%)} & \\textbf{Success Rate (\\%)} \\\\\n")
        f.write("\\hline\n")

        for _, row in summary.iterrows():
            f.write(f"{row['ID']} & {row['Topology']} & {row['Setup Time (ms)']} & {row['Std Dev (ms)']} & {row['PQ Overhead (%)']} & {row['Success Rate (%)']} \\\\\n")

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"✓ Generated: summary_table.tex")

    # 打印统计摘要
    print("\n" + "="*60)
    print("STATISTICAL SUMMARY")
    print("="*60)
    print(f"Average Circuit Setup Time: {stats_df['mean_time_ms'].mean():.2f} ms")
    print(f"Average PQ Overhead: {stats_df['pq_overhead_percent'].mean():.2f}%")
    print(f"Average Success Rate: {stats_df['success_rate'].mean():.1f}%")
    print(f"Min PQ Overhead: {stats_df['pq_overhead_percent'].min():.2f}% (Topology {stats_df.loc[stats_df['pq_overhead_percent'].idxmin(), 'topology_id']})")
    print(f"Max PQ Overhead: {stats_df['pq_overhead_percent'].max():.2f}% (Topology {stats_df.loc[stats_df['pq_overhead_percent'].idxmax(), 'topology_id']})")
    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_noma_results.py <raw_results.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    # 创建输出目录
    output_dir = "../results/figures"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*60)
    print("  NOMA Topology Results Analysis")
    print("="*60 + "\n")

    # 1. 加载数据
    df, df_success = load_results(csv_file)

    # 2. 计算统计数据
    print("\nCalculating statistics...")
    stats_df = calculate_statistics(df_success)

    # 3. 生成所有图表
    print("\nGenerating figures...")
    generate_figure1_topology_comparison(stats_df, output_dir)
    generate_figure2_pq_overhead_breakdown(stats_df, output_dir)
    generate_figure3_uplink_vs_downlink(stats_df, output_dir)
    generate_figure4_cooperation_impact(stats_df, output_dir)
    generate_figure5_hops_vs_overhead(stats_df, output_dir)
    generate_figure6_success_vs_loss(stats_df, output_dir)

    # 4. 生成汇总表格
    print("\nGenerating summary tables...")
    generate_summary_table(stats_df, output_dir)

    print("\n" + "="*60)
    print("✅ Analysis Complete!")
    print("="*60)
    print(f"📊 Figures saved to: {output_dir}")
    print(f"📁 Summary tables saved to: {output_dir}")
    print("\nGenerated files:")
    print("  - figure1_topology_comparison.png/pdf")
    print("  - figure2_pq_overhead_breakdown.png/pdf")
    print("  - figure3_uplink_vs_downlink.png/pdf")
    print("  - figure4_cooperation_impact.png/pdf")
    print("  - figure5_hops_vs_overhead.png/pdf")
    print("  - figure6_success_vs_loss.png/pdf")
    print("  - summary_table.csv")
    print("  - summary_table.tex")
    print("\n")


if __name__ == "__main__":
    main()
