#!/usr/bin/env python3
"""
Simulated PQ-NTOR Performance Test for SAGIN
基于真实PQ-NTOR握手性能数据 + SAGIN网络延迟模型
当Docker不可用时的替代测试方案
"""

import json
import random
import csv
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 设置随机种子以保证可重现性
random.seed(42)
np.random.seed(42)


class SimulatedPQNTORTest:
    """基于仿真的PQ-NTOR性能测试"""

    def __init__(self, config_file: str, use_pq: bool = True):
        """
        初始化仿真测试

        Args:
            config_file: SAGIN拓扑配置文件
            use_pq: True=PQ-NTOR, False=传统NTOR
        """
        self.config_file = config_file
        self.use_pq = use_pq
        self.config = self._load_config()

        # PQ-NTOR握手性能（基于实际benchmark数据）
        # 来源: /home/ccc/pq-ntor-experiment/c/benchmark测试结果
        self.pq_handshake_time_ms = 0.049  # 49微秒 = 0.049毫秒
        self.traditional_handshake_time_ms = 0.030  # 30微秒估算

        # 结果存储
        self.test_results = []
        self.results_dir = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/results')
        self.results_dir.mkdir(exist_ok=True)

        print(f"[SimTest] 初始化仿真测试")
        print(f"  协议: {'PQ-NTOR' if use_pq else '传统NTOR'}")
        print(f"  握手延迟: {self.pq_handshake_time_ms if use_pq else self.traditional_handshake_time_ms} ms")

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def calculate_link_delay(self, node1: str, node2: str) -> float:
        """
        计算两节点间的链路延迟
        基于SAGIN配置中的距离和延迟约束
        """
        # 获取节点类型
        type1 = self._get_node_type(node1)
        type2 = self._get_node_type(node2)

        # 根据链路类型确定延迟
        link_type = self._determine_link_type(type1, type2)
        constraints = self.config['link_constraints'].get(link_type, {})

        # 基本延迟（光速传播）
        typical_distance_km = constraints.get('typical_distance_km', 1000)
        base_delay_ms = typical_distance_km / 300.0  # 光速 300,000 km/s

        # 添加处理和排队延迟（1-5ms）
        processing_delay_ms = random.uniform(1.0, 5.0)

        # 添加抖动
        jitter_ms = random.gauss(0, 2.0)

        total_delay_ms = base_delay_ms + processing_delay_ms + jitter_ms
        return max(0.1, total_delay_ms)  # 最小0.1ms

    def _get_node_type(self, node_name: str) -> str:
        """获取节点类型"""
        if node_name in self.config.get('satellites', {}):
            return 'satellite'
        elif node_name in self.config.get('aircraft', {}):
            return 'aircraft'
        elif node_name in self.config.get('ground_stations', {}):
            return 'ground_station'
        return 'unknown'

    def _determine_link_type(self, type1: str, type2: str) -> str:
        """确定链路类型"""
        types = sorted([type1, type2])

        if types == ['satellite', 'satellite']:
            return 'ISL'
        elif 'satellite' in types and 'ground_station' in types:
            return 'SGLink'
        elif 'satellite' in types and 'aircraft' in types:
            return 'SALink'
        elif 'aircraft' in types and 'ground_station' in types:
            return 'AGLink'
        elif types == ['ground_station', 'ground_station']:
            return 'GLink'
        return 'Unknown'

    def simulate_circuit_construction(self, path: List[str], iterations: int = 10) -> Dict:
        """
        仿真电路建立过程

        Args:
            path: 节点路径列表
            iterations: 测试迭代次数

        Returns:
            测试结果字典
        """
        results = []
        success_count = 0
        timeout_count = 0

        # 计算路径中的跳数
        num_hops = len(path) - 1

        # 每一跳的握手时间
        handshake_time = self.pq_handshake_time_ms if self.use_pq else self.traditional_handshake_time_ms

        for i in range(iterations):
            # 计算总延迟
            total_delay_ms = 0

            # 每一跳的延迟
            for j in range(num_hops):
                link_delay = self.calculate_link_delay(path[j], path[j+1])
                total_delay_ms += link_delay

                # 握手时间（每一跳都需要握手）
                total_delay_ms += handshake_time

                # 往返时间（RTT）
                total_delay_ms += link_delay

            # 添加端到端处理延迟
            end_to_end_processing = random.uniform(5.0, 15.0)
            total_delay_ms += end_to_end_processing

            # 模拟成功率（基于跳数和链路质量）
            # 更多跳数 = 更高的失败概率
            success_probability = 0.98 ** num_hops  # 每跳98%成功率

            if random.random() < success_probability:
                success_count += 1
                results.append(total_delay_ms)
            else:
                # 失败的情况（超时）
                timeout_count += 1
                results.append(90000)  # 90秒超时

        # 统计成功的测试
        successful_results = [r for r in results if r < 90000]

        if successful_results:
            return {
                'status': 'success',
                'circuit_time_ms': np.mean(successful_results),
                'min_time_ms': np.min(successful_results),
                'max_time_ms': np.max(successful_results),
                'std_dev_ms': np.std(successful_results),
                'success_rate': (success_count / iterations) * 100,
                'timeout_rate': (timeout_count / iterations) * 100,
                'iterations': iterations
            }
        else:
            return {
                'status': 'failure',
                'circuit_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'std_dev_ms': 0,
                'success_rate': 0,
                'timeout_rate': 100,
                'iterations': iterations
            }

    def run_all_scenarios(self, iterations: int = 10):
        """运行所有测试场景"""
        print(f"\n[SimTest] 运行所有测试场景 (迭代次数: {iterations})")

        scenarios = self.config.get('test_scenarios', [])

        for i, scenario in enumerate(scenarios, 1):
            scenario_id = scenario.get('id')
            scenario_name = scenario.get('name')
            path = scenario.get('path', [])

            # 跳过动态场景
            if scenario.get('dynamic', False):
                print(f"\n[{i}/{len(scenarios)}] 跳过动态场景: {scenario_name}")
                continue

            print(f"\n[{i}/{len(scenarios)}] 测试场景: {scenario_name}")
            print(f"  路径: {' -> '.join(path)}")
            print(f"  跳数: {len(path) - 1}")

            # 运行仿真测试
            results = self.simulate_circuit_construction(path, iterations)

            # 添加场景信息
            results['scenario_id'] = scenario_id
            results['scenario_name'] = scenario_name
            results['path'] = path
            results['num_hops'] = len(path) - 1
            results['timestamp'] = datetime.utcnow().isoformat()
            results['use_pq'] = self.use_pq

            self.test_results.append(results)

            # 打印结果
            print(f"  ✓ 电路建立时间: {results['circuit_time_ms']:.2f} ms")
            print(f"  ✓ 时间范围: [{results['min_time_ms']:.2f}, {results['max_time_ms']:.2f}] ms")
            print(f"  ✓ 成功率: {results['success_rate']:.1f}%")

        print(f"\n[SimTest] 所有场景测试完成")

    def save_results(self) -> Path:
        """保存测试结果到CSV"""
        if not self.test_results:
            print("[SimTest] 警告: 没有测试结果可保存")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        protocol = 'pq_ntor' if self.use_pq else 'traditional_ntor'
        filename = self.results_dir / f'sagin_test_{protocol}_{timestamp}.csv'

        print(f"\n[SimTest] 保存结果到: {filename}")

        fieldnames = [
            'scenario_id', 'scenario_name', 'path', 'num_hops', 'status',
            'circuit_time_ms', 'min_time_ms', 'max_time_ms', 'std_dev_ms',
            'success_rate', 'timeout_rate', 'iterations',
            'timestamp', 'use_pq'
        ]

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.test_results:
                row = {field: result.get(field, '') for field in fieldnames}
                row['path'] = ' -> '.join(result.get('path', []))
                writer.writerow(row)

        print(f"[SimTest] ✓ 结果已保存 ({len(self.test_results)} 条记录)")
        return filename


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='仿真PQ-NTOR性能测试')
    parser.add_argument('--config', default='../configs/sagin_topology_config.json',
                       help='SAGIN配置文件路径')
    parser.add_argument('--traditional', action='store_true',
                       help='使用传统NTOR（默认PQ-NTOR）')
    parser.add_argument('--iterations', type=int, default=10,
                       help='每个场景的迭代次数')

    args = parser.parse_args()

    # 创建测试实例
    use_pq = not args.traditional
    tester = SimulatedPQNTORTest(args.config, use_pq=use_pq)

    # 运行测试
    tester.run_all_scenarios(iterations=args.iterations)

    # 保存结果
    result_file = tester.save_results()

    if result_file:
        print(f"\n{'='*60}")
        print(f"测试完成!")
        print(f"协议: {'PQ-NTOR' if use_pq else '传统NTOR'}")
        print(f"结果文件: {result_file}")
        print(f"{'='*60}\n")

        return 0
    else:
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
