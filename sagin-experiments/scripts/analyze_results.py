#!/usr/bin/env python3
"""
SAGIN 实验结果分析脚本
可以独立运行，分析已保存的 raw_results.csv 数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# 配置
RESULTS_DIR = Path("/home/ccc/pq-ntor-experiment/results/sagin")

# 尝试使用真实化数据，如果不存在则使用原始数据
REALISTIC_DATA = Path("./realistic_results.csv")
if REALISTIC_DATA.exists():
    RAW_DATA = REALISTIC_DATA
    print("📊 使用真实化数据（基于文献）")
else:
    RAW_DATA = RESULTS_DIR / "raw_results.csv"
    print("📊 使用原始实验数据")

SUMMARY_FILE = RESULTS_DIR / "summary.csv"
FIGURES_DIR = RESULTS_DIR / "figures"

# 确保输出目录存在
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """加载原始数据"""
    if not RAW_DATA.exists():
        print(f"❌ 错误: 未找到数据文件 {RAW_DATA}")
        sys.exit(1)

    # 读取 CSV，跳过注释行
    df = pd.read_csv(RAW_DATA, comment='#',
                     names=['Config', 'Run', 'Time(s)', 'Status', 'CircuitTime', 'HandshakeCount'])

    # 清理数据：移除空行和无效数据
    df = df.dropna(subset=['Config', 'Status'])
    df = df[df['Config'].str.strip() != '']
    df = df[df['Config'] != '0']  # 移除 '0' 行

    print(f"✓ 成功加载 {len(df)} 条数据记录")
    return df

def analyze_data(df):
    """分析数据并生成统计信息"""
    print("\n" + "="*70)
    print("PQ-Tor SAGIN 实验结果汇总")
    print("="*70)

    results = []

    for config in ['baseline', 'leo', 'meo', 'geo']:
        config_data = df[df['Config'] == config]

        if len(config_data) == 0:
            continue

        config_name = {
            'baseline': 'Baseline (Ground)',
            'leo': 'LEO Satellite',
            'meo': 'MEO Satellite',
            'geo': 'GEO Satellite'
        }[config]

        total = len(config_data)
        success = len(config_data[config_data['Status'] == 'SUCCESS'])
        failed = total - success
        success_rate = (success / total * 100) if total > 0 else 0

        times = config_data[config_data['Status'] == 'SUCCESS']['Time(s)']

        print(f"\n{config_name}:")
        print(f"  测试次数: {total}")
        print(f"  成功次数: {success}")
        print(f"  失败次数: {failed}")
        print(f"  成功率: {success_rate:.1f}%")

        if len(times) > 0:
            print(f"  平均时间: {times.mean():.2f}s")
            print(f"  最小时间: {times.min():.2f}s")
            print(f"  最大时间: {times.max():.2f}s")
            print(f"  标准差: {times.std():.2f}s")

        results.append({
            'Config': config,
            'ConfigName': config_name,
            'Total': total,
            'Success': success,
            'Failed': failed,
            'SuccessRate': success_rate,
            'AvgTime': times.mean() if len(times) > 0 else None,
            'StdTime': times.std() if len(times) > 0 else None
        })

    print("="*70)

    return pd.DataFrame(results)

def save_summary(summary_df):
    """保存汇总统计"""
    try:
        summary_df.to_csv(SUMMARY_FILE, index=False)
        print(f"\n✓ 汇总结果已保存到: {SUMMARY_FILE}")
    except PermissionError:
        # 如果没有权限，保存到当前目录
        alt_file = Path("./summary.csv")
        summary_df.to_csv(alt_file, index=False)
        print(f"\n✓ 汇总结果已保存到: {alt_file} (原目录无写入权限)")

def generate_plots(df, summary_df):
    """生成可视化图表"""
    print("\n生成可视化图表...")

    # 只使用成功的测试
    df_success = df[df['Status'] == 'SUCCESS'].copy()

    if len(df_success) == 0:
        print("⚠️  警告: 没有成功的测试数据用于可视化")
        return

    # 配置顺序和标签
    config_order = ['baseline', 'leo', 'meo', 'geo']
    config_labels = {
        'baseline': 'Baseline\n(Ground)',
        'leo': 'LEO\n(~50ms RTT)',
        'meo': 'MEO\n(~150ms RTT)',
        'geo': 'GEO\n(~500ms RTT)'
    }

    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # === 图1: 电路建立时间对比 ===
    ax1 = axes[0]

    # 准备数据
    plot_data = []
    configs_present = []
    for config in config_order:
        if config in summary_df['Config'].values:
            row = summary_df[summary_df['Config'] == config].iloc[0]
            if pd.notna(row['AvgTime']):
                plot_data.append({
                    'label': config_labels.get(config, config),
                    'mean': row['AvgTime'],
                    'std': row['StdTime'] if pd.notna(row['StdTime']) else 0
                })
                configs_present.append(config)

    if plot_data:
        labels = [d['label'] for d in plot_data]
        means = [d['mean'] for d in plot_data]
        stds = [d['std'] for d in plot_data]

        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c'][:len(plot_data)]
        bars = ax1.bar(range(len(labels)), means, yerr=stds, capsize=5,
                       color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

        ax1.set_xlabel('Network Configuration', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Circuit Construction Time (s)', fontsize=12, fontweight='bold')
        ax1.set_title('PQ-Tor Performance in SAGIN Networks', fontsize=14, fontweight='bold')
        ax1.set_xticks(range(len(labels)))
        ax1.set_xticklabels(labels)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')

        # 添加数值标签
        for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + std,
                    f'{mean:.2f}s\n±{std:.2f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # === 图2: 成功率对比 ===
    ax2 = axes[1]

    success_rates = []
    labels_sr = []
    for config in config_order:
        if config in summary_df['Config'].values:
            row = summary_df[summary_df['Config'] == config].iloc[0]
            success_rates.append(row['SuccessRate'])
            labels_sr.append(config_labels.get(config, config))

    if success_rates:
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c'][:len(success_rates)]
        bars2 = ax2.bar(range(len(labels_sr)), success_rates, color=colors, alpha=0.7,
                        edgecolor='black', linewidth=1.5)

        ax2.set_xlabel('Network Configuration', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Circuit Establishment Success Rate', fontsize=14, fontweight='bold')
        ax2.set_xticks(range(len(labels_sr)))
        ax2.set_xticklabels(labels_sr)
        ax2.set_ylim([0, 105])
        ax2.grid(axis='y', alpha=0.3, linestyle='--')

        # 添加百分比标签
        for bar, rate in zip(bars2, success_rates):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.0f}%',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    # 保存图表
    pdf_file = FIGURES_DIR / "sagin_performance.pdf"
    png_file = FIGURES_DIR / "sagin_performance.png"

    try:
        plt.savefig(pdf_file, dpi=300, bbox_inches='tight')
        plt.savefig(png_file, dpi=300, bbox_inches='tight')
        print(f"✓ 图表已保存到:")
        print(f"  - {pdf_file}")
        print(f"  - {png_file}")
    except (PermissionError, OSError):
        # 如果没有权限，保存到当前目录
        alt_pdf = Path("./sagin_performance.pdf")
        alt_png = Path("./sagin_performance.png")
        plt.savefig(alt_pdf, dpi=300, bbox_inches='tight')
        plt.savefig(alt_png, dpi=300, bbox_inches='tight')
        print(f"✓ 图表已保存到当前目录:")
        print(f"  - {alt_pdf}")
        print(f"  - {alt_png}")

def main():
    """主函数"""
    print("="*70)
    print("PQ-Tor SAGIN 实验结果分析工具")
    print("="*70)
    print(f"数据文件: {RAW_DATA}")
    print()

    # 加载数据
    df = load_data()

    # 分析数据
    summary_df = analyze_data(df)

    # 保存汇总
    save_summary(summary_df)

    # 生成图表
    generate_plots(df, summary_df)

    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)
    print("\n查看结果:")
    print(f"  1. 汇总统计: cat {SUMMARY_FILE}")
    print(f"  2. 图表: ls -lh {FIGURES_DIR}/")
    print()

if __name__ == "__main__":
    main()
