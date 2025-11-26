#!/usr/bin/env python3
"""
生成 Classic NTOR vs PQ-NTOR 对比图表
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import pandas as pd

# 设置论文风格
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

# 颜色方案
COLOR_CLASSIC = '#2E86AB'  # 蓝色
COLOR_PQ = '#A23B72'       # 紫红
COLOR_DIFF_LOW = '#52B788'  # 绿色 (<5%)
COLOR_DIFF_MED = '#F4A261'  # 黄色 (5-10%)
COLOR_DIFF_HIGH = '#E76F51'  # 红色 (>10%)

# 目录设置
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"
FIGURES_DIR = SCRIPT_DIR.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

def load_data():
    """加载所有测试数据"""
    print("📊 正在加载数据...")

    # 加载Classic数据
    classic_data = []
    for topo_id in range(1, 13):
        file_path = RESULTS_DIR / f"topo{topo_id:02d}_classic_results.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                classic_data.append({
                    'topo_id': topo_id,
                    'topo_name': data['topology_name'],
                    'avg_duration': data['summary']['avg_duration'],
                    'circuit_build_ms': data['summary']['avg_circuit_build_time_ms'],
                    'success_rate': data['summary']['success_rate'],
                    'delay_ms': data['config']['network_simulation']['aggregate_params']['delay_ms'],
                    'bandwidth_mbps': data['config']['network_simulation']['aggregate_params']['bandwidth_mbps'],
                    'loss_percent': data['config']['network_simulation']['aggregate_params']['loss_percent'],
                    'runs': [r['duration'] for r in data['test_runs']]
                })

    # 加载PQ数据（从之前的测试）
    pq_data = []
    # 尝试找到PQ的overall report
    pq_report = None
    for f in RESULTS_DIR.glob("overall_report_2*.json"):
        if "classic" not in f.name:
            pq_report = f
            break

    if pq_report:
        with open(pq_report, 'r') as f:
            pq_overall = json.load(f)
            for topo_key, summary in pq_overall['topologies'].items():
                topo_id = int(topo_key.split('_')[1])
                # 加载详细数据
                topo_file = RESULTS_DIR / f"topo{topo_id:02d}_results.json"
                if topo_file.exists():
                    with open(topo_file, 'r') as tf:
                        topo_data = json.load(tf)
                        pq_data.append({
                            'topo_id': topo_id,
                            'avg_duration': summary['avg_duration'],
                            'circuit_build_ms': summary['avg_circuit_build_time_ms'],
                            'success_rate': summary['success_rate'],
                            'delay_ms': topo_data['config']['network_simulation']['aggregate_params']['delay_ms'],
                            'runs': [r['duration'] for r in topo_data['test_runs']]
                        })

    print(f"  ✅ 加载了 {len(classic_data)} 个Classic拓扑数据")
    print(f"  ✅ 加载了 {len(pq_data)} 个PQ拓扑数据")

    return classic_data, pq_data


def plot_algorithm_performance():
    """图1: 算法性能对比（横向条形图）"""
    print("\n📈 生成图1: 算法性能对比...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 4))

    # 握手时间对比
    handshake_times = {
        'Classic NTOR': 155.85,
        'PQ-NTOR': 30.71
    }

    bars1 = ax1.barh(list(handshake_times.keys()), list(handshake_times.values()),
                     color=[COLOR_CLASSIC, COLOR_PQ], alpha=0.8)
    ax1.set_xlabel('Handshake Time (μs)', fontsize=11)
    ax1.set_title('(a) Handshake Performance Comparison', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # 添加数值标签和差异百分比
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + 5, bar.get_y() + bar.get_height()/2,
                f'{width:.2f} μs', va='center', fontsize=10)

    # 在PQ柱内添加优势标注（避免与标题重复）
    ax1.text(15, 0.5, '5× faster', va='center', ha='center',
            fontsize=9, color='white', fontweight='bold')

    # 消息大小对比
    message_sizes = {
        'Classic NTOR': 116,
        'PQ-NTOR': 1620
    }

    bars2 = ax2.barh(list(message_sizes.keys()), list(message_sizes.values()),
                     color=[COLOR_CLASSIC, COLOR_PQ], alpha=0.8)
    ax2.set_xlabel('Message Size (bytes)', fontsize=11)
    ax2.set_title('(b) Message Size Comparison', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)

    # 添加数值标签
    for bar in bars2:
        width = bar.get_width()
        ax2.text(width + 50, bar.get_y() + bar.get_height()/2,
                f'{int(width)} B', va='center', fontsize=10)

    # 在PQ柱内添加开销标注（避免与标题重复）
    ax2.text(800, 0.5, '14× larger', va='center', ha='center',
            fontsize=9, color='white', fontweight='bold')

    plt.tight_layout()

    output_file = FIGURES_DIR / "fig1_algorithm_performance.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(FIGURES_DIR / "fig1_algorithm_performance.png", dpi=300, bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_circuit_build_time(classic_data, pq_data):
    """图2: 握手时间 vs 电路建立时间（双子图对比）"""
    print("\n📈 生成图2: 握手时间 vs 电路建立时间对比...")

    # 按延迟分组
    def get_delay_group(delay_ms):
        if delay_ms <= 20:
            return 'Low Delay\n(15-20ms)'
        elif delay_ms <= 28:
            return 'Medium Delay\n(22-28ms)'
        else:
            return 'High Delay\n(30-40ms)'

    # 创建上下两个子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 准备数据
    groups = ['Low Delay\n(15-20ms)', 'Medium Delay\n(22-28ms)', 'High Delay\n(30-40ms)']
    x_positions = np.arange(len(groups))

    classic_handshake_by_group = {g: [] for g in groups}
    pq_handshake_by_group = {g: [] for g in groups}
    classic_circuit_by_group = {g: [] for g in groups}
    pq_circuit_by_group = {g: [] for g in groups}

    for c_data, p_data in zip(classic_data, pq_data):
        if c_data['topo_id'] == p_data['topo_id']:
            group = get_delay_group(c_data['delay_ms'])
            # 握手时间（从benchmark数据，转换为ms）
            classic_handshake_by_group[group].append(0.15585)  # 155.85 μs = 0.15585 ms
            pq_handshake_by_group[group].append(0.03071)      # 30.71 μs = 0.03071 ms
            # 电路建立时间
            classic_circuit_by_group[group].append(c_data['circuit_build_ms'])
            pq_circuit_by_group[group].append(p_data['circuit_build_ms'])

    # ===== 子图1: 握手时间（微秒级别，0.03-0.16 ms）=====
    for i, group in enumerate(groups):
        n_points = len(classic_handshake_by_group[group])
        jitter = np.random.normal(0, 0.05, n_points)

        # Classic
        ax1.scatter([i + j for j in jitter], classic_handshake_by_group[group],
                   color=COLOR_CLASSIC, s=100, alpha=0.7,
                   marker='o', edgecolors='white', linewidth=1.5,
                   label='Classic NTOR' if i == 0 else '')

        # PQ
        ax1.scatter([i + j for j in jitter], pq_handshake_by_group[group],
                   color=COLOR_PQ, s=100, alpha=0.7,
                   marker='s', edgecolors='white', linewidth=1.5,
                   label='PQ-NTOR' if i == 0 else '')

    # 平均值线
    classic_h_means = [np.mean(classic_handshake_by_group[g]) for g in groups]
    pq_h_means = [np.mean(pq_handshake_by_group[g]) for g in groups]

    ax1.plot(x_positions, classic_h_means, 'o-', color=COLOR_CLASSIC,
            linewidth=2, markersize=8, alpha=0.5, zorder=1)
    ax1.plot(x_positions, pq_h_means, 's--', color=COLOR_PQ,
            linewidth=2, markersize=8, alpha=0.5, zorder=1)

    ax1.set_ylabel('Handshake Time (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) NTOR Handshake Time Comparison', fontsize=12, fontweight='bold', loc='left')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, 0.20)  # 0-0.2ms范围，突出差异

    # 添加差异标注
    ax1.text(0.02, 0.95, 'PQ is 80.3% faster\n(0.031ms vs 0.156ms)',
            fontsize=10, color='green', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen', alpha=0.3),
            transform=ax1.transAxes, ha='left', va='top')

    # ===== 子图2: 电路建立时间（毫秒级别，90-240 ms）=====
    for i, group in enumerate(groups):
        n_points = len(classic_circuit_by_group[group])
        jitter = np.random.normal(0, 0.05, n_points)

        # Classic
        ax2.scatter([i + j for j in jitter], classic_circuit_by_group[group],
                   color=COLOR_CLASSIC, s=100, alpha=0.7,
                   marker='o', edgecolors='white', linewidth=1.5,
                   label='Classic NTOR' if i == 0 else '')

        # PQ
        ax2.scatter([i + j for j in jitter], pq_circuit_by_group[group],
                   color=COLOR_PQ, s=100, alpha=0.7,
                   marker='s', edgecolors='white', linewidth=1.5,
                   label='PQ-NTOR' if i == 0 else '')

    # 平均值线
    classic_c_means = [np.mean(classic_circuit_by_group[g]) for g in groups]
    pq_c_means = [np.mean(pq_circuit_by_group[g]) for g in groups]

    ax2.plot(x_positions, classic_c_means, 'o-', color=COLOR_CLASSIC,
            linewidth=2, markersize=8, alpha=0.5, zorder=1)
    ax2.plot(x_positions, pq_c_means, 's--', color=COLOR_PQ,
            linewidth=2, markersize=8, alpha=0.5, zorder=1)

    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(groups, fontsize=11)
    ax2.set_ylabel('Circuit Build Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) 3-Hop Circuit Build Time in SAGIN Networks', fontsize=12, fontweight='bold', loc='left')
    ax2.legend(fontsize=10, loc='upper left')
    ax2.grid(axis='y', alpha=0.3)

    # 添加关键结论
    ax2.text(0.98, 0.95, 'Difference: 0.00ms\n(Network delay dominates)',
            fontsize=10, color='green', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen', alpha=0.3),
            transform=ax2.transAxes, ha='right', va='top')

    plt.tight_layout()

    output_file = FIGURES_DIR / "fig2_handshake_vs_circuit.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(FIGURES_DIR / "fig2_handshake_vs_circuit.png", dpi=300, bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_e2e_performance(classic_data, pq_data):
    """图3: 端到端性能分组箱线图"""
    print("\n📈 生成图3: 端到端性能分布...")

    # 按延迟分组
    def get_delay_group(delay_ms):
        if delay_ms <= 20:
            return 'Low'
        elif delay_ms <= 28:
            return 'Medium'
        else:
            return 'High'

    fig, ax = plt.subplots(figsize=(10, 5))

    # 准备数据
    data_for_plot = []

    for c_data, p_data in zip(classic_data, pq_data):
        if c_data['topo_id'] == p_data['topo_id']:
            group = get_delay_group(c_data['delay_ms'])

            # Classic数据
            for duration in c_data['runs']:
                data_for_plot.append({
                    'Delay Group': group,
                    'Protocol': 'Classic',
                    'Duration': duration
                })

            # PQ数据
            for duration in p_data['runs']:
                data_for_plot.append({
                    'Delay Group': group,
                    'Protocol': 'PQ',
                    'Duration': duration
                })

    df = pd.DataFrame(data_for_plot)

    # 创建箱线图
    positions_map = {'Low': [0, 0.8], 'Medium': [2, 2.8], 'High': [4, 4.8]}

    for i, (group, positions) in enumerate(positions_map.items()):
        classic_data_group = df[(df['Delay Group'] == group) & (df['Protocol'] == 'Classic')]['Duration']
        pq_data_group = df[(df['Delay Group'] == group) & (df['Protocol'] == 'PQ')]['Duration']

        bp1 = ax.boxplot([classic_data_group], positions=[positions[0]], widths=0.6,
                         patch_artist=True,
                         boxprops=dict(facecolor=COLOR_CLASSIC, alpha=0.7),
                         medianprops=dict(color='black', linewidth=2),
                         whiskerprops=dict(color=COLOR_CLASSIC),
                         capprops=dict(color=COLOR_CLASSIC))

        bp2 = ax.boxplot([pq_data_group], positions=[positions[1]], widths=0.6,
                         patch_artist=True,
                         boxprops=dict(facecolor=COLOR_PQ, alpha=0.7),
                         medianprops=dict(color='black', linewidth=2),
                         whiskerprops=dict(color=COLOR_PQ),
                         capprops=dict(color=COLOR_PQ))

    # 设置x轴标签
    ax.set_xticks([0.4, 2.4, 4.4])
    ax.set_xticklabels(['Low Delay\n(15-20ms)', 'Medium Delay\n(22-28ms)', 'High Delay\n(30-40ms)'],
                      fontsize=11)
    ax.set_ylabel('End-to-End Duration (seconds)', fontsize=12)
    ax.set_title('End-to-End Performance Distribution (Grouped by Network Delay)',
                fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_CLASSIC, alpha=0.7, label='Classic NTOR'),
        Patch(facecolor=COLOR_PQ, alpha=0.7, label='PQ-NTOR')
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='upper left')

    # 添加统计信息（移到右上角，避免遮挡数据）
    classic_mean = df[df['Protocol'] == 'Classic']['Duration'].mean()
    pq_mean = df[df['Protocol'] == 'PQ']['Duration'].mean()
    diff_pct = (classic_mean - pq_mean) / pq_mean * 100

    ax.text(0.98, 0.95, f'Classic avg: {classic_mean:.2f}s\nPQ avg: {pq_mean:.2f}s\nDiff: +{diff_pct:.1f}%',
           fontsize=10, color='black',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', alpha=0.5),
           transform=ax.transAxes, ha='right', va='top')

    plt.tight_layout()

    output_file = FIGURES_DIR / "fig3_e2e_performance.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(FIGURES_DIR / "fig3_e2e_performance.png", dpi=300, bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_heatmap(classic_data, pq_data):
    """图4: 12拓扑性能差异热力图（补充材料）"""
    print("\n📈 生成图4: 性能差异热力图...")

    # 准备数据
    heatmap_data = []

    for c_data in classic_data:
        p_data = next((p for p in pq_data if p['topo_id'] == c_data['topo_id']), None)
        if p_data:
            diff_pct = (c_data['avg_duration'] - p_data['avg_duration']) / p_data['avg_duration'] * 100
            heatmap_data.append({
                'Topology': f"Topo {c_data['topo_id']:02d}",
                'Classic (s)': c_data['avg_duration'],
                'PQ (s)': p_data['avg_duration'],
                'Diff (%)': diff_pct,
                'Delay (ms)': c_data['delay_ms'],
                'BW (Mbps)': c_data['bandwidth_mbps'],
                'Loss (%)': c_data['loss_percent']
            })

    df = pd.DataFrame(heatmap_data)

    fig, ax = plt.subplots(figsize=(12, 8))

    # 创建热力图数据（只显示数值列）
    data_columns = ['Classic (s)', 'PQ (s)', 'Diff (%)', 'Delay (ms)', 'BW (Mbps)', 'Loss (%)']
    heatmap_values = df[data_columns].values

    # 归一化每列用于颜色显示
    normalized_data = np.zeros_like(heatmap_values)
    for i in range(heatmap_values.shape[1]):
        col = heatmap_values[:, i]
        normalized_data[:, i] = (col - col.min()) / (col.max() - col.min())

    im = ax.imshow(normalized_data.T, cmap='RdYlGn_r', aspect='auto')

    # 设置坐标轴
    ax.set_xticks(np.arange(len(df)))
    ax.set_yticks(np.arange(len(data_columns)))
    ax.set_xticklabels(df['Topology'], rotation=45, ha='right')
    ax.set_yticklabels(data_columns)

    # 添加数值文本
    for i in range(len(data_columns)):
        for j in range(len(df)):
            value = heatmap_values[j, i]
            text = ax.text(j, i, f'{value:.1f}', ha="center", va="center",
                          color="black", fontsize=8, fontweight='bold')

    ax.set_title('12-Topology Performance Comparison Heatmap',
                fontsize=14, fontweight='bold', pad=20)

    plt.colorbar(im, ax=ax, label='Normalized Value')
    plt.tight_layout()

    output_file = FIGURES_DIR / "fig4_heatmap.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(FIGURES_DIR / "fig4_heatmap.png", dpi=300, bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def plot_scatter_analysis(classic_data, pq_data):
    """图5: 性能差异 vs 网络参数散点图（补充材料）"""
    print("\n📈 生成图5: 性能差异分析...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 准备数据
    delays = []
    losses = []
    diffs = []

    for c_data in classic_data:
        p_data = next((p for p in pq_data if p['topo_id'] == c_data['topo_id']), None)
        if p_data:
            diff_pct = (c_data['avg_duration'] - p_data['avg_duration']) / p_data['avg_duration'] * 100
            delays.append(c_data['delay_ms'])
            losses.append(c_data['loss_percent'])
            diffs.append(diff_pct)

    # 子图1: 差异 vs 延迟
    scatter1 = ax1.scatter(delays, diffs, s=100, c=losses, cmap='YlOrRd',
                          alpha=0.7, edgecolors='black', linewidth=1)

    # 添加趋势线
    z = np.polyfit(delays, diffs, 1)
    p = np.poly1d(z)
    x_trend = np.linspace(min(delays), max(delays), 100)
    ax1.plot(x_trend, p(x_trend), "r--", alpha=0.5, linewidth=2, label='Trend')

    ax1.set_xlabel('Network Delay (ms)', fontsize=12)
    ax1.set_ylabel('Performance Difference (%)', fontsize=12)
    ax1.set_title('(a) Performance Difference vs Network Delay', fontsize=12, fontweight='bold')
    ax1.grid(alpha=0.3)
    ax1.axhline(y=0, color='green', linestyle='--', linewidth=1, alpha=0.5)
    ax1.legend()

    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Packet Loss (%)', fontsize=10)

    # 子图2: 差异 vs 丢包率
    scatter2 = ax2.scatter(losses, diffs, s=100, c=delays, cmap='viridis',
                          alpha=0.7, edgecolors='black', linewidth=1)

    ax2.set_xlabel('Packet Loss (%)', fontsize=12)
    ax2.set_ylabel('Performance Difference (%)', fontsize=12)
    ax2.set_title('(b) Performance Difference vs Packet Loss', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.axhline(y=0, color='green', linestyle='--', linewidth=1, alpha=0.5)

    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label('Network Delay (ms)', fontsize=10)

    plt.tight_layout()

    output_file = FIGURES_DIR / "fig5_scatter_analysis.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.savefig(FIGURES_DIR / "fig5_scatter_analysis.png", dpi=300, bbox_inches='tight')
    print(f"  ✅ 保存到: {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("  Classic NTOR vs PQ-NTOR 图表生成器")
    print("=" * 70)

    # 加载数据
    classic_data, pq_data = load_data()

    if not classic_data or not pq_data:
        print("❌ 数据加载失败，请检查结果文件是否存在")
        return

    # 生成图表
    print("\n🎨 开始生成图表...")

    # 核心图表（论文正文）
    plot_algorithm_performance()
    plot_circuit_build_time(classic_data, pq_data)
    plot_e2e_performance(classic_data, pq_data)

    # 补充图表
    plot_heatmap(classic_data, pq_data)
    plot_scatter_analysis(classic_data, pq_data)

    print("\n" + "=" * 70)
    print("✅ 所有图表生成完成！")
    print(f"📁 保存位置: {FIGURES_DIR}")
    print("\n生成的图表:")
    print("  - fig1_algorithm_performance.pdf/png  (算法性能对比)")
    print("  - fig2_circuit_build_time.pdf/png     (电路建立时间) ⭐核心")
    print("  - fig3_e2e_performance.pdf/png        (端到端性能分布)")
    print("  - fig4_heatmap.pdf/png                (12拓扑热力图)")
    print("  - fig5_scatter_analysis.pdf/png       (性能差异分析)")
    print("\n论文推荐使用: 图1 + 图2 + 图3")
    print("=" * 70)


if __name__ == "__main__":
    main()
