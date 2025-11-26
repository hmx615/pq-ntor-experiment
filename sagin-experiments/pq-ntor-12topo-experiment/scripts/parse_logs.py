#!/usr/bin/env python3
"""
PQ-NTOR日志解析工具
从客户端日志中提取关键性能指标

作者: Claude Code
日期: 2025-11-24
"""

import re
import json
from pathlib import Path
from typing import Dict, Optional


class PQNTORLogParser:
    """PQ-NTOR日志解析器"""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_content = ""

        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                self.log_content = f.read()

    def parse_metrics(self) -> Dict:
        """解析性能指标"""
        metrics = {
            'success': False,
            'circuit_established': False,
            'http_success': False,
            'response_bytes': 0
        }

        # 检查电路是否建立成功
        if '3-hop circuit established!' in self.log_content:
            metrics['circuit_established'] = True

        # 检查HTTP响应
        response_match = re.search(r'Response received \((\d+) bytes\)', self.log_content)
        if response_match:
            metrics['response_bytes'] = int(response_match.group(1))
            metrics['http_success'] = True

        # 检查最终成功标记
        if 'Test completed successfully!' in self.log_content:
            metrics['success'] = True

        # 提取时间戳（如果有）
        # 示例: [Client] 3-hop circuit established in 150ms
        time_patterns = {
            'circuit_build_ms': r'circuit established.*?(\d+)\s*ms',
            'handshake_us': r'handshake.*?(\d+)\s*us',
            'total_rtt_ms': r'RTT.*?(\d+)\s*ms',
        }

        for key, pattern in time_patterns.items():
            match = re.search(pattern, self.log_content, re.IGNORECASE)
            if match:
                metrics[key] = float(match.group(1))

        # 统计关键步骤
        steps = {
            'create2_sent': '[Client] CREATE2 sent successfully' in self.log_content,
            'created2_received': '[Client] Received CREATED2' in self.log_content,
            'first_hop_established': '[Client] First hop established' in self.log_content,
            'extended2_received': '[Client] Received EXTENDED2' in self.log_content,
        }
        metrics['steps'] = steps

        return metrics

    def extract_error_messages(self) -> list:
        """提取错误信息"""
        errors = []
        error_patterns = [
            r'ERROR:.*',
            r'\[Error\].*',
            r'Failed.*',
            r'❌.*'
        ]

        for pattern in error_patterns:
            matches = re.findall(pattern, self.log_content, re.MULTILINE)
            errors.extend(matches)

        return errors


def parse_test_run(topo_id: int, run_id: int, logs_dir: Path) -> Dict:
    """解析单次测试运行的所有日志"""
    result = {
        'topology_id': topo_id,
        'run_id': run_id,
        'timestamp': None,
        'client': {},
        'guard': {},
        'middle': {},
        'exit': {},
        'directory': {}
    }

    # 解析各个节点的日志
    nodes = ['client', 'guard', 'middle', 'exit', 'directory']

    for node in nodes:
        log_file = logs_dir / f"{node}_topo{topo_id:02d}_run{run_id:02d}.log"

        if log_file.exists():
            parser = PQNTORLogParser(log_file)
            metrics = parser.parse_metrics()
            errors = parser.extract_error_messages()

            result[node] = {
                'log_file': str(log_file),
                'log_exists': True,
                'log_size': log_file.stat().st_size,
                'metrics': metrics,
                'errors': errors
            }
        else:
            result[node] = {
                'log_file': str(log_file),
                'log_exists': False
            }

    # 综合判断
    result['overall_success'] = result['client'].get('metrics', {}).get('success', False)

    return result


def analyze_topology_logs(topo_id: int, logs_dir: Path, num_runs: int = 10) -> Dict:
    """分析单个拓扑的所有测试日志"""
    print(f"📄 解析拓扑 {topo_id:02d} 的日志...")

    topology_results = {
        'topology_id': topo_id,
        'num_runs': num_runs,
        'runs': [],
        'summary': {}
    }

    for run_id in range(1, num_runs + 1):
        run_result = parse_test_run(topo_id, run_id, logs_dir)
        topology_results['runs'].append(run_result)

    # 生成汇总统计
    successful_runs = [r for r in topology_results['runs'] if r['overall_success']]

    topology_results['summary'] = {
        'total_runs': num_runs,
        'successful_runs': len(successful_runs),
        'success_rate': len(successful_runs) / num_runs * 100 if num_runs > 0 else 0,
        'failed_runs': num_runs - len(successful_runs)
    }

    # 性能指标统计
    circuit_times = []
    response_sizes = []

    for run in successful_runs:
        client_metrics = run.get('client', {}).get('metrics', {})

        if 'circuit_build_ms' in client_metrics:
            circuit_times.append(client_metrics['circuit_build_ms'])

        if client_metrics.get('response_bytes', 0) > 0:
            response_sizes.append(client_metrics['response_bytes'])

    if circuit_times:
        import statistics
        topology_results['summary']['circuit_build_time'] = {
            'mean': statistics.mean(circuit_times),
            'median': statistics.median(circuit_times),
            'min': min(circuit_times),
            'max': max(circuit_times),
            'stdev': statistics.stdev(circuit_times) if len(circuit_times) > 1 else 0
        }

    if response_sizes:
        import statistics
        topology_results['summary']['response_size'] = {
            'mean': statistics.mean(response_sizes),
            'median': statistics.median(response_sizes)
        }

    return topology_results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='解析PQ-NTOR测试日志')
    parser.add_argument('--topo', type=int, metavar='ID',
                        help='解析单个拓扑 (1-12)')
    parser.add_argument('--logs-dir', type=str,
                        default='../logs',
                        help='日志目录路径')
    parser.add_argument('--output', type=str,
                        help='输出JSON文件路径')

    args = parser.parse_args()

    # 确定日志目录
    script_dir = Path(__file__).parent
    logs_dir = (script_dir / args.logs_dir).resolve()

    if not logs_dir.exists():
        print(f"❌ 日志目录不存在: {logs_dir}")
        return

    print(f"📂 日志目录: {logs_dir}")
    print()

    # 解析日志
    if args.topo:
        # 解析单个拓扑
        result = analyze_topology_logs(args.topo, logs_dir)

        # 输出结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 结果已保存: {output_path}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 解析所有拓扑
        all_results = {}

        for topo_id in range(1, 13):
            result = analyze_topology_logs(topo_id, logs_dir)
            all_results[f"topo{topo_id:02d}"] = result

            summary = result['summary']
            print(f"   成功率: {summary['success_rate']:.1f}% "
                  f"({summary['successful_runs']}/{summary['total_runs']})")
            print()

        # 输出结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"✅ 所有结果已保存: {output_path}")
        else:
            print("\n" + "="*70)
            print("📊 汇总报告")
            print("="*70)

            for topo_id in range(1, 13):
                topo_key = f"topo{topo_id:02d}"
                if topo_key in all_results:
                    summary = all_results[topo_key]['summary']
                    print(f"Topo {topo_id:02d}: {summary['success_rate']:5.1f}% "
                          f"({summary['successful_runs']}/{summary['total_runs']})")


if __name__ == '__main__':
    main()
