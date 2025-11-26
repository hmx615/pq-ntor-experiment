#!/usr/bin/env python3
"""
PQ-NTOR测试结果分析脚本
读取测试结果JSON，生成统计报告和可视化图表

作者: Claude Code
日期: 2025-11-24
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import statistics

# 配置
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"
OUTPUT_DIR = SCRIPT_DIR.parent / "results" / "analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_topology_results(topo_id):
    """加载单个拓扑的测试结果"""
    result_file = RESULTS_DIR / f"topo{topo_id:02d}_results.json"

    if not result_file.exists():
        return None

    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_single_topology(topo_id):
    """分析单个拓扑的测试结果"""
    data = load_topology_results(topo_id)

    if not data:
        return None

    test_runs = data.get('test_runs', [])
    if not test_runs:
        return None

    # 统计指标
    total_runs = len(test_runs)
    successful_runs = [r for r in test_runs if r.get('success', False)]
    success_count = len(successful_runs)
    success_rate = success_count / total_runs * 100 if total_runs > 0 else 0

    # 计算性能指标（仅成功的测试）
    durations = [r['duration'] for r in successful_runs if 'duration' in r]

    analysis = {
        'topology_id': topo_id,
        'topology_name': data.get('topology_name', f'Topo {topo_id}'),
        'total_runs': total_runs,
        'success_count': success_count,
        'success_rate': success_rate,
        'network_params': data.get('config', {}).get('network_simulation', {}).get('aggregate_params', {})
    }

    if durations:
        analysis['duration_stats'] = {
            'mean': statistics.mean(durations),
            'median': statistics.median(durations),
            'stdev': statistics.stdev(durations) if len(durations) > 1 else 0,
            'min': min(durations),
            'max': max(durations)
        }

    # TODO: 解析PQ-NTOR特有指标（从日志中）
    # analysis['pq_handshake_time_us'] = ...
    # analysis['circuit_build_time_ms'] = ...

    return analysis


def analyze_all_topologies():
    """分析所有拓扑的测试结果"""
    print("=" * 70)
    print("  📊 PQ-NTOR测试结果分析")
    print("=" * 70)

    all_analyses = {}

    for topo_id in range(1, 13):
        print(f"\n分析拓扑 {topo_id:02d}...")
        analysis = analyze_single_topology(topo_id)

        if analysis:
            all_analyses[topo_id] = analysis
            print(f"  拓扑名称: {analysis['topology_name']}")
            print(f"  成功率: {analysis['success_rate']:.1f}% ({analysis['success_count']}/{analysis['total_runs']})")

            if 'duration_stats' in analysis:
                stats = analysis['duration_stats']
                print(f"  平均耗时: {stats['mean']:.2f}秒 (中位数: {stats['median']:.2f}秒)")
                print(f"  耗时范围: {stats['min']:.2f} - {stats['max']:.2f}秒")

            net = analysis['network_params']
            print(f"  网络参数: 延迟={net.get('delay_ms')}ms, "
                  f"带宽={net.get('bandwidth_mbps')}Mbps, "
                  f"丢包率={net.get('loss_percent')}%")
        else:
            print(f"  ⚠️  未找到测试结果")

    # 生成对比报告
    generate_comparison_report(all_analyses)

    return all_analyses


def generate_comparison_report(all_analyses):
    """生成拓扑对比报告"""
    if not all_analyses:
        print("\n⚠️  没有可分析的数据")
        return

    print("\n" + "=" * 70)
    print("  📈 拓扑对比报告")
    print("=" * 70)

    # 生成Markdown表格
    report_file = OUTPUT_DIR / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# PQ-NTOR 12拓扑对比报告\n\n")
        f.write(f"**生成时间**: {datetime.now().isoformat()}\n\n")

        f.write("## 测试结果汇总\n\n")
        f.write("| 拓扑ID | 拓扑名称 | 成功率 | 平均耗时(s) | 延迟(ms) | 带宽(Mbps) | 丢包率(%) |\n")
        f.write("|--------|----------|--------|-------------|----------|------------|----------|\n")

        for topo_id in sorted(all_analyses.keys()):
            analysis = all_analyses[topo_id]
            name = analysis['topology_name']
            success_rate = analysis['success_rate']

            duration_mean = "-"
            if 'duration_stats' in analysis:
                duration_mean = f"{analysis['duration_stats']['mean']:.2f}"

            net = analysis['network_params']
            delay = net.get('delay_ms', '-')
            bw = net.get('bandwidth_mbps', '-')
            loss = net.get('loss_percent', '-')

            f.write(f"| {topo_id:02d} | {name} | {success_rate:.1f}% | {duration_mean} | "
                    f"{delay} | {bw} | {loss} |\n")

        # 分组统计
        f.write("\n## 分组统计\n\n")

        uplink_topos = [a for tid, a in all_analyses.items() if tid <= 6]
        downlink_topos = [a for tid, a in all_analyses.items() if tid > 6]

        if uplink_topos:
            avg_success_uplink = sum(a['success_rate'] for a in uplink_topos) / len(uplink_topos)
            f.write(f"**上行拓扑 (1-6)**: 平均成功率 {avg_success_uplink:.1f}%\n\n")

        if downlink_topos:
            avg_success_downlink = sum(a['success_rate'] for a in downlink_topos) / len(downlink_topos)
            f.write(f"**下行拓扑 (7-12)**: 平均成功率 {avg_success_downlink:.1f}%\n\n")

    print(f"\n✅ 对比报告已生成: {report_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分析PQ-NTOR测试结果')
    parser.add_argument('--topo', type=int, metavar='ID',
                        help='分析单个拓扑 (1-12)')

    args = parser.parse_args()

    if args.topo:
        # 分析单个拓扑
        if not (1 <= args.topo <= 12):
            print("❌ 拓扑ID必须在1-12之间")
            sys.exit(1)

        analysis = analyze_single_topology(args.topo)
        if analysis:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 未找到拓扑 {args.topo} 的测试结果")
            sys.exit(1)
    else:
        # 分析所有拓扑
        analyze_all_topologies()


if __name__ == "__main__":
    main()
