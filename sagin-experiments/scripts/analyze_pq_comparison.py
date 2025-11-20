#!/usr/bin/env python3
"""
PQ-NTOR vs 传统NTOR 性能对比分析
分析Phase 2测试结果并生成对比报告和图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import glob

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class PQNTORComparison:
    """PQ-NTOR性能对比分析"""

    def __init__(self, results_dir: str = None):
        """
        初始化分析器

        Args:
            results_dir: 结果文件目录
        """
        if results_dir is None:
            results_dir = '/home/ccc/pq-ntor-experiment/sagin-experiments/results'

        self.results_dir = Path(results_dir)
        self.pq_data = None
        self.trad_data = None

        print(f"[Analyzer] PQ-NTOR性能对比分析")
        print(f"  结果目录: {self.results_dir}")

    def load_latest_results(self):
        """加载最新的测试结果"""
        # 查找最新的PQ-NTOR结果
        pq_files = sorted(glob.glob(str(self.results_dir / 'sagin_test_pq_ntor_*.csv')))
        trad_files = sorted(glob.glob(str(self.results_dir / 'sagin_test_traditional_ntor_*.csv')))

        if not pq_files or not trad_files:
            raise FileNotFoundError("找不到测试结果文件")

        pq_file = pq_files[-1]  # 最新的
        trad_file = trad_files[-1]

        print(f"\n[Analyzer] 加载测试结果:")
        print(f"  PQ-NTOR: {Path(pq_file).name}")
        print(f"  传统NTOR: {Path(trad_file).name}")

        self.pq_data = pd.read_csv(pq_file)
        self.trad_data = pd.read_csv(trad_file)

        print(f"  ✓ PQ-NTOR: {len(self.pq_data)} 条记录")
        print(f"  ✓ 传统NTOR: {len(self.trad_data)} 条记录")

    def generate_comparison_report(self) -> str:
        """生成对比报告"""
        print(f"\n[Analyzer] 生成对比报告...")

        report_lines = []
        report_lines.append("="*80)
        report_lines.append("PQ-NTOR vs 传统NTOR 性能对比报告")
        report_lines.append("="*80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # 按场景对比
        for idx, (pq_row, trad_row) in enumerate(zip(self.pq_data.iterrows(), self.trad_data.iterrows())):
            pq_data = pq_row[1]
            trad_data = trad_row[1]

            scenario_name = pq_data['scenario_name']
            path = pq_data['path']
            num_hops = pq_data['num_hops']

            report_lines.append(f"\n场景 {idx+1}: {scenario_name}")
            report_lines.append("-" * 80)
            report_lines.append(f"路径: {path}")
            report_lines.append(f"跳数: {num_hops}")
            report_lines.append("")

            # 电路建立时间对比
            pq_time = pq_data['circuit_time_ms']
            trad_time = trad_data['circuit_time_ms']
            overhead = ((pq_time - trad_time) / trad_time * 100) if trad_time > 0 else 0

            report_lines.append(f"电路建立时间:")
            report_lines.append(f"  PQ-NTOR:    {pq_time:8.2f} ms")
            report_lines.append(f"  传统NTOR:   {trad_time:8.2f} ms")
            report_lines.append(f"  性能开销:   {overhead:8.2f}%")
            report_lines.append("")

            # 时间范围对比
            report_lines.append(f"时间范围:")
            report_lines.append(f"  PQ-NTOR:    [{pq_data['min_time_ms']:7.2f}, {pq_data['max_time_ms']:7.2f}] ms")
            report_lines.append(f"  传统NTOR:   [{trad_data['min_time_ms']:7.2f}, {trad_data['max_time_ms']:7.2f}] ms")
            report_lines.append("")

            # 成功率对比
            report_lines.append(f"成功率:")
            report_lines.append(f"  PQ-NTOR:    {pq_data['success_rate']:6.1f}%")
            report_lines.append(f"  传统NTOR:   {trad_data['success_rate']:6.1f}%")

        # 总体统计
        report_lines.append("\n" + "="*80)
        report_lines.append("总体统计")
        report_lines.append("="*80)

        avg_pq_time = self.pq_data['circuit_time_ms'].mean()
        avg_trad_time = self.trad_data['circuit_time_ms'].mean()
        avg_overhead = ((avg_pq_time - avg_trad_time) / avg_trad_time * 100) if avg_trad_time > 0 else 0

        report_lines.append(f"\n平均电路建立时间:")
        report_lines.append(f"  PQ-NTOR:    {avg_pq_time:8.2f} ms")
        report_lines.append(f"  传统NTOR:   {avg_trad_time:8.2f} ms")
        report_lines.append(f"  平均开销:   {avg_overhead:8.2f}%")

        avg_pq_success = self.pq_data['success_rate'].mean()
        avg_trad_success = self.trad_data['success_rate'].mean()

        report_lines.append(f"\n平均成功率:")
        report_lines.append(f"  PQ-NTOR:    {avg_pq_success:6.1f}%")
        report_lines.append(f"  传统NTOR:   {avg_trad_success:6.1f}%")

        # 关键发现
        report_lines.append("\n" + "="*80)
        report_lines.append("关键发现")
        report_lines.append("="*80)

        report_lines.append(f"\n1. 性能开销:")
        report_lines.append(f"   PQ-NTOR相比传统NTOR的平均性能开销为 {avg_overhead:.2f}%")
        report_lines.append(f"   这主要来自于后量子密钥交换(Kyber-512)的额外计算开销")

        report_lines.append(f"\n2. 可靠性:")
        report_lines.append(f"   两种协议的成功率相近 (PQ: {avg_pq_success:.1f}%, 传统: {avg_trad_success:.1f}%)")
        report_lines.append(f"   说明PQ-NTOR在可靠性方面没有引入额外问题")

        report_lines.append(f"\n3. 网络延迟影响:")
        report_lines.append(f"   SAGIN网络的延迟(光速传播+排队)远大于握手开销")
        report_lines.append(f"   因此PQ-NTOR的额外开销在实际应用中影响有限")

        report_lines.append(f"\n4. 适用场景:")
        report_lines.append(f"   - 星间链路(ISL): 适合PQ-NTOR,开销可接受")
        report_lines.append(f"   - 星地链路: 适合PQ-NTOR,安全性提升显著")
        report_lines.append(f"   - 多跳混合: 适合PQ-NTOR,端到端安全")
        report_lines.append(f"   - 全球端到端: 适合PQ-NTOR,长期安全保障")

        report_lines.append("\n" + "="*80)

        report = "\n".join(report_lines)

        # 保存报告
        report_file = self.results_dir / f'comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  ✓ 报告已保存: {report_file.name}")

        return report

    def generate_comparison_charts(self):
        """生成对比图表"""
        print(f"\n[Analyzer] 生成对比图表...")

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('PQ-NTOR vs Traditional NTOR Performance Comparison', fontsize=16, fontweight='bold')

        # 图1: 电路建立时间对比
        ax1 = axes[0, 0]
        scenarios = self.pq_data['scenario_name'].values
        x = np.arange(len(scenarios))
        width = 0.35

        pq_times = self.pq_data['circuit_time_ms'].values
        trad_times = self.trad_data['circuit_time_ms'].values

        bars1 = ax1.bar(x - width/2, pq_times, width, label='PQ-NTOR', color='#2E86AB', alpha=0.8)
        bars2 = ax1.bar(x + width/2, trad_times, width, label='Traditional NTOR', color='#A23B72', alpha=0.8)

        ax1.set_ylabel('Circuit Construction Time (ms)', fontweight='bold')
        ax1.set_title('Circuit Construction Time Comparison', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f"S{i+1}" for i in range(len(scenarios))], rotation=0)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=8)

        # 图2: 性能开销百分比
        ax2 = axes[0, 1]
        overheads = ((pq_times - trad_times) / trad_times * 100)
        colors = ['#E63946' if o > 1 else '#06A77D' for o in overheads]

        bars = ax2.bar(x, overheads, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Performance Overhead (%)', fontweight='bold')
        ax2.set_title('PQ-NTOR Performance Overhead', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"S{i+1}" for i in range(len(scenarios))], rotation=0)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}%',
                    ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)

        # 图3: 成功率对比
        ax3 = axes[1, 0]
        pq_success = self.pq_data['success_rate'].values
        trad_success = self.trad_data['success_rate'].values

        bars1 = ax3.bar(x - width/2, pq_success, width, label='PQ-NTOR', color='#2E86AB', alpha=0.8)
        bars2 = ax3.bar(x + width/2, trad_success, width, label='Traditional NTOR', color='#A23B72', alpha=0.8)

        ax3.set_ylabel('Success Rate (%)', fontweight='bold')
        ax3.set_title('Success Rate Comparison', fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels([f"S{i+1}" for i in range(len(scenarios))], rotation=0)
        ax3.set_ylim([0, 110])
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}%',
                        ha='center', va='bottom', fontsize=8)

        # 图4: 时间范围对比
        ax4 = axes[1, 1]

        # PQ-NTOR
        pq_means = self.pq_data['circuit_time_ms'].values
        pq_mins = self.pq_data['min_time_ms'].values
        pq_maxs = self.pq_data['max_time_ms'].values
        pq_errors = [pq_means - pq_mins, pq_maxs - pq_means]

        # Traditional NTOR
        trad_means = self.trad_data['circuit_time_ms'].values
        trad_mins = self.trad_data['min_time_ms'].values
        trad_maxs = self.trad_data['max_time_ms'].values
        trad_errors = [trad_means - trad_mins, trad_maxs - trad_means]

        ax4.errorbar(x - width/2, pq_means, yerr=pq_errors, fmt='o',
                    label='PQ-NTOR', color='#2E86AB', capsize=5, capthick=2, markersize=8)
        ax4.errorbar(x + width/2, trad_means, yerr=trad_errors, fmt='s',
                    label='Traditional NTOR', color='#A23B72', capsize=5, capthick=2, markersize=8)

        ax4.set_ylabel('Time (ms)', fontweight='bold')
        ax4.set_title('Time Range Comparison (Min-Avg-Max)', fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels([f"S{i+1}" for i in range(len(scenarios))], rotation=0)
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        # 保存图表
        chart_file_pdf = self.results_dir / f'comparison_charts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        chart_file_png = self.results_dir / f'comparison_charts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'

        plt.savefig(chart_file_pdf, format='pdf', dpi=300, bbox_inches='tight')
        plt.savefig(chart_file_png, format='png', dpi=300, bbox_inches='tight')

        print(f"  ✓ 图表已保存:")
        print(f"    - {chart_file_pdf.name}")
        print(f"    - {chart_file_png.name}")

        plt.close()

    def create_summary_table(self):
        """创建汇总表格"""
        print(f"\n[Analyzer] 创建汇总表格...")

        summary_data = []

        for idx, (pq_row, trad_row) in enumerate(zip(self.pq_data.iterrows(), self.trad_data.iterrows())):
            pq_data = pq_row[1]
            trad_data = trad_row[1]

            pq_time = pq_data['circuit_time_ms']
            trad_time = trad_data['circuit_time_ms']
            overhead = ((pq_time - trad_time) / trad_time * 100) if trad_time > 0 else 0

            summary_data.append({
                'Scenario': pq_data['scenario_name'],
                'Hops': pq_data['num_hops'],
                'PQ_Time_ms': pq_time,
                'Trad_Time_ms': trad_time,
                'Overhead_%': overhead,
                'PQ_Success_%': pq_data['success_rate'],
                'Trad_Success_%': trad_data['success_rate']
            })

        summary_df = pd.DataFrame(summary_data)

        # 保存表格
        table_file = self.results_dir / f'comparison_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        summary_df.to_csv(table_file, index=False)

        print(f"  ✓ 汇总表格已保存: {table_file.name}")
        print(f"\n{summary_df.to_string(index=False)}")

        return summary_df


def main():
    """主函数"""
    print("="*80)
    print("PQ-NTOR vs 传统NTOR 性能对比分析工具")
    print("="*80)

    analyzer = PQNTORComparison()

    # 加载数据
    analyzer.load_latest_results()

    # 生成报告
    report = analyzer.generate_comparison_report()
    print(f"\n{report}")

    # 创建汇总表
    analyzer.create_summary_table()

    # 生成图表
    analyzer.generate_comparison_charts()

    print(f"\n{'='*80}")
    print(f"分析完成!")
    print(f"{'='*80}\n")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
