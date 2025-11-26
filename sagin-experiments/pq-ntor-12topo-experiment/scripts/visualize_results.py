#!/usr/bin/env python3
"""
PQ-NTOR测试结果可视化脚本
生成性能对比图表

作者: Claude Code
日期: 2025-11-25
"""

import json
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

# 配置
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"
OUTPUT_DIR = SCRIPT_DIR.parent / "results" / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def load_all_results():
    """加载所有拓扑的测试结果"""
    results = {}

    for topo_id in range(1, 13):
        result_file = RESULTS_DIR / f"topo{topo_id:02d}_results.json"

        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results[topo_id] = data

    return results


def extract_metrics(results):
    """提取关键性能指标"""
    metrics = {
        'topo_ids': [],
        'names': [],
        'success_rates': [],
        'avg_durations': [],
        'delays': [],
        'bandwidths': [],
        'loss_rates': []
    }

    for topo_id in sorted(results.keys()):
        data = results[topo_id]

        metrics['topo_ids'].append(topo_id)
        metrics['names'].append(data.get('topology_name', f'Topo {topo_id}'))

        # 成功率
        total = data.get('total_runs', 0)
        success = sum(1 for r in data.get('test_runs', []) if r.get('success', False))
        metrics['success_rates'].append(success / total * 100 if total > 0 else 0)

        # 平均耗时
        durations = [r['duration'] for r in data.get('test_runs', []) if 'duration' in r]
        metrics['avg_durations'].append(np.mean(durations) if durations else 0)

        # 网络参数
        net_params = data.get('config', {}).get('network_simulation', {}).get('aggregate_params', {})
        metrics['delays'].append(net_params.get('delay_ms', 0))
        metrics['bandwidths'].append(net_params.get('bandwidth_mbps', 0))
        metrics['loss_rates'].append(net_params.get('loss_percent', 0))

    return metrics


def plot_success_rate(metrics, output_path):
    """绘制成功率柱状图"""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(metrics['topo_ids']))
    colors = ['#2ecc71' if rate >= 100 else '#e74c3c' for rate in metrics['success_rates']]

    bars = ax.bar(x, metrics['success_rates'], color=colors, alpha=0.8, edgecolor='black')

    ax.set_xlabel('Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR Success Rate Across 12 Topologies', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']], rotation=45)
    ax.set_ylim([0, 105])
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加数值标签
    for i, (bar, rate) in enumerate(zip(bars, metrics['success_rates'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.0f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 成功率图表已保存: {output_path}")


def plot_duration_comparison(metrics, output_path):
    """绘制耗时对比图"""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(metrics['topo_ids']))
    uplink = metrics['avg_durations'][:6]
    downlink = metrics['avg_durations'][6:]

    bars1 = ax.bar(x[:6], uplink, width=0.8, label='Uplink (1-6)',
                   color='#3498db', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x[6:], downlink, width=0.8, label='Downlink (7-12)',
                   color='#e74c3c', alpha=0.8, edgecolor='black')

    ax.set_xlabel('Topology', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Duration (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('PQ-NTOR Average Test Duration Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']], rotation=45)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{height:.1f}s',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 耗时对比图表已保存: {output_path}")


def plot_network_params(metrics, output_path):
    """绘制网络参数对比图"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    x = np.arange(len(metrics['topo_ids']))

    # 延迟
    axes[0].bar(x, metrics['delays'], color='#9b59b6', alpha=0.8, edgecolor='black')
    axes[0].set_xlabel('Topology', fontweight='bold')
    axes[0].set_ylabel('Delay (ms)', fontweight='bold')
    axes[0].set_title('Network Delay', fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']], rotation=45)
    axes[0].grid(axis='y', alpha=0.3, linestyle='--')

    # 带宽
    axes[1].bar(x, metrics['bandwidths'], color='#1abc9c', alpha=0.8, edgecolor='black')
    axes[1].set_xlabel('Topology', fontweight='bold')
    axes[1].set_ylabel('Bandwidth (Mbps)', fontweight='bold')
    axes[1].set_title('Network Bandwidth', fontweight='bold')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']], rotation=45)
    axes[1].grid(axis='y', alpha=0.3, linestyle='--')

    # 丢包率
    axes[2].bar(x, metrics['loss_rates'], color='#e67e22', alpha=0.8, edgecolor='black')
    axes[2].set_xlabel('Topology', fontweight='bold')
    axes[2].set_ylabel('Loss Rate (%)', fontweight='bold')
    axes[2].set_title('Packet Loss Rate', fontweight='bold')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']], rotation=45)
    axes[2].grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 网络参数图表已保存: {output_path}")


def plot_performance_heatmap(metrics, output_path):
    """绘制性能热力图"""
    fig, ax = plt.subplots(figsize=(14, 8))

    # 准备数据矩阵
    data = np.array([
        metrics['success_rates'],
        [d - min(metrics['avg_durations']) for d in metrics['avg_durations']],  # 归一化耗时
        metrics['delays'],
        metrics['bandwidths'],
        metrics['loss_rates']
    ])

    # 归一化到0-100范围
    normalized_data = np.zeros_like(data)
    for i in range(len(data)):
        row = data[i]
        min_val, max_val = row.min(), row.max()
        if max_val > min_val:
            normalized_data[i] = (row - min_val) / (max_val - min_val) * 100
        else:
            normalized_data[i] = 50  # 如果所有值相同，设为50

    im = ax.imshow(normalized_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    # 设置坐标轴
    ax.set_xticks(np.arange(len(metrics['topo_ids'])))
    ax.set_yticks(np.arange(5))
    ax.set_xticklabels([f'T{tid:02d}' for tid in metrics['topo_ids']])
    ax.set_yticklabels(['Success Rate', 'Duration (inv)', 'Delay', 'Bandwidth', 'Loss Rate'])

    # 旋转x轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Normalized Value (0-100)', rotation=270, labelpad=20, fontweight='bold')

    ax.set_title('PQ-NTOR Performance Heatmap', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 性能热力图已保存: {output_path}")


def plot_uplink_vs_downlink(metrics, output_path):
    """绘制上行vs下行对比图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    uplink_durations = metrics['avg_durations'][:6]
    downlink_durations = metrics['avg_durations'][6:]

    categories = ['Uplink\n(Topo 1-6)', 'Downlink\n(Topo 7-12)']
    avg_values = [np.mean(uplink_durations), np.mean(downlink_durations)]
    std_values = [np.std(uplink_durations), np.std(downlink_durations)]

    x = np.arange(len(categories))
    bars = ax.bar(x, avg_values, yerr=std_values, capsize=10,
                   color=['#3498db', '#e74c3c'], alpha=0.8, edgecolor='black', width=0.5)

    ax.set_ylabel('Average Duration (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Uplink vs Downlink Performance Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加数值标签
    for i, (bar, avg, std) in enumerate(zip(bars, avg_values, std_values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.2,
                f'{avg:.2f}s\n(±{std:.2f})',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 上行vs下行对比图已保存: {output_path}")


def generate_summary_chart(metrics, output_path):
    """生成综合统计图"""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 1. 成功率环形图
    ax1 = fig.add_subplot(gs[0, 0])
    success_count = sum(1 for r in metrics['success_rates'] if r >= 100)
    fail_count = len(metrics['success_rates']) - success_count

    colors = ['#2ecc71', '#e74c3c']
    sizes = [success_count, fail_count] if fail_count > 0 else [success_count]
    labels = ['100% Success', 'Failed'] if fail_count > 0 else ['100% Success']

    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors[:len(sizes)],
                                         autopct='%1.1f%%', startangle=90,
                                         textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax1.set_title('Overall Success Rate', fontsize=12, fontweight='bold')

    # 2. 耗时箱线图
    ax2 = fig.add_subplot(gs[0, 1])
    uplink = metrics['avg_durations'][:6]
    downlink = metrics['avg_durations'][6:]

    bp = ax2.boxplot([uplink, downlink], labels=['Uplink', 'Downlink'],
                      patch_artist=True, notch=True)

    for patch, color in zip(bp['boxes'], ['#3498db', '#e74c3c']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.set_ylabel('Duration (seconds)', fontweight='bold')
    ax2.set_title('Duration Distribution', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # 3. 网络参数散点图
    ax3 = fig.add_subplot(gs[1, 0])
    scatter = ax3.scatter(metrics['delays'], metrics['avg_durations'],
                          s=np.array(metrics['bandwidths'])*5,
                          c=metrics['loss_rates'],
                          cmap='YlOrRd', alpha=0.6, edgecolors='black')

    ax3.set_xlabel('Network Delay (ms)', fontweight='bold')
    ax3.set_ylabel('Avg Duration (s)', fontweight='bold')
    ax3.set_title('Delay vs Duration (Size=BW, Color=Loss)', fontsize=12, fontweight='bold')
    ax3.grid(alpha=0.3, linestyle='--')

    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('Loss Rate (%)', rotation=270, labelpad=15)

    # 4. 统计摘要表格
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('tight')
    ax4.axis('off')

    table_data = [
        ['Metric', 'Value'],
        ['Total Tests', f"{len(metrics['topo_ids']) * 10}"],
        ['Success Rate', f"{np.mean(metrics['success_rates']):.1f}%"],
        ['Avg Duration', f"{np.mean(metrics['avg_durations']):.2f}s"],
        ['Duration Std', f"{np.std(metrics['avg_durations']):.2f}s"],
        ['Min Duration', f"{np.min(metrics['avg_durations']):.2f}s"],
        ['Max Duration', f"{np.max(metrics['avg_durations']):.2f}s"],
        ['Avg Delay', f"{np.mean(metrics['delays']):.1f}ms"],
        ['Avg Bandwidth', f"{np.mean(metrics['bandwidths']):.1f}Mbps"],
        ['Avg Loss Rate', f"{np.mean(metrics['loss_rates']):.2f}%"]
    ]

    table = ax4.table(cellText=table_data, cellLoc='left', loc='center',
                      colWidths=[0.5, 0.5])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # 设置表头样式
    for i in range(2):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # 交替行颜色
    for i in range(1, len(table_data)):
        for j in range(2):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')

    ax4.set_title('Statistical Summary', fontsize=12, fontweight='bold', pad=20)

    fig.suptitle('PQ-NTOR 12-Topology Test Summary Dashboard',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 综合统计图已保存: {output_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("  📊 PQ-NTOR测试结果可视化")
    print("=" * 70)
    print()

    # 加载数据
    print("📂 加载测试结果...")
    results = load_all_results()

    if not results:
        print("❌ 未找到测试结果文件")
        return

    print(f"✅ 已加载 {len(results)} 个拓扑的结果")
    print()

    # 提取指标
    print("📈 提取性能指标...")
    metrics = extract_metrics(results)
    print()

    # 生成图表
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("🎨 生成可视化图表...")
    print()

    plot_success_rate(metrics, OUTPUT_DIR / f'success_rate_{timestamp}.png')
    plot_duration_comparison(metrics, OUTPUT_DIR / f'duration_comparison_{timestamp}.png')
    plot_network_params(metrics, OUTPUT_DIR / f'network_params_{timestamp}.png')
    plot_performance_heatmap(metrics, OUTPUT_DIR / f'performance_heatmap_{timestamp}.png')
    plot_uplink_vs_downlink(metrics, OUTPUT_DIR / f'uplink_vs_downlink_{timestamp}.png')
    generate_summary_chart(metrics, OUTPUT_DIR / f'summary_dashboard_{timestamp}.png')

    print()
    print("=" * 70)
    print(f"✅ 所有图表已生成完毕!")
    print(f"📁 保存位置: {OUTPUT_DIR}")
    print("=" * 70)
    print()
    print("生成的图表:")
    print("  1. success_rate_*.png          - 成功率柱状图")
    print("  2. duration_comparison_*.png   - 耗时对比图")
    print("  3. network_params_*.png        - 网络参数对比")
    print("  4. performance_heatmap_*.png   - 性能热力图")
    print("  5. uplink_vs_downlink_*.png    - 上行vs下行对比")
    print("  6. summary_dashboard_*.png     - 综合统计仪表盘 ⭐")
    print()


if __name__ == '__main__':
    main()
