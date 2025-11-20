#!/usr/bin/env python3
"""
SAGIN Real Network Test using PQ-NTOR Client/Relay Programs
基于真实PQ-NTOR client/relay程序的SAGIN网络测试

测试方法：
1. 在容器中启动directory服务器和relay节点
2. 使用真实的client程序构建电路
3. 测量真实的端到端性能
"""

import json
import subprocess
import time
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SAGINRealNetworkTest:
    """SAGIN真实网络测试"""

    def __init__(self, config_file: str, use_pq: bool = True):
        """
        初始化测试

        Args:
            config_file: SAGIN拓扑配置文件
            use_pq: True=PQ-NTOR, False=传统NTOR
        """
        self.config_file = config_file
        self.use_pq = use_pq
        self.config = self._load_config()

        self.network_name = 'sagin_net'
        self.pq_image = 'pq-ntor-sagin:latest'

        self.containers = {}
        self.test_results = []

        self.results_dir = Path('/home/ccc/pq-ntor-experiment/sagin-experiments/results')
        self.results_dir.mkdir(exist_ok=True)

        logger.info(f"SAGIN Real Network Test initialized (PQ={use_pq})")

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _run_command(self, cmd: List[str], check=True, capture_output=True):
        """执行命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            if check:
                raise
            return e

    def _get_node_ip(self, node_name: str) -> str:
        """获取节点IP地址"""
        return self.containers.get(node_name, {}).get('ip', '')

    def setup_network(self):
        """创建Docker网络"""
        logger.info("Setting up Docker network...")

        # 删除旧网络（如果存在）
        self._run_command(['docker', 'network', 'rm', self.network_name], check=False)

        # 创建新网络
        self._run_command([
            'docker', 'network', 'create',
            '--subnet=172.20.0.0/16',
            self.network_name
        ])

        logger.info(f"Created network {self.network_name}")

    def create_containers(self):
        """创建Docker容器"""
        logger.info("Creating PQ-NTOR containers...")

        # 检查镜像是否存在
        logger.info(f"Checking for image {self.pq_image}...")
        result = self._run_command(['docker', 'images', '-q', self.pq_image])
        if not result.stdout.strip():
            logger.error(f"Image {self.pq_image} not found!")
            raise RuntimeError(f"Please build image first: docker build -t {self.pq_image} ...")

        # 获取所有节点
        nodes = []
        for sat_name in self.config.get('satellites', {}):
            nodes.append({'name': sat_name, 'subnet': '1', 'host': '11' if sat_name == 'Sat-1' else '12'})
        for ac_name in self.config.get('aircraft', {}):
            nodes.append({'name': ac_name, 'subnet': '2', 'host': '21' if ac_name == 'Aircraft-1' else '22'})
        for gs_name in self.config.get('ground_stations', {}):
            gs_num = {'GS-Beijing': '31', 'GS-London': '32', 'GS-NewYork': '33'}.get(gs_name, '31')
            nodes.append({'name': gs_name, 'subnet': '3', 'host': gs_num})

        # 创建容器
        for node in nodes:
            container_name = f"sagin_{node['name'].lower()}"
            ip_address = f"172.20.{node['subnet']}.{node['host']}"

            logger.info(f"Creating container {container_name} at {ip_address}...")

            # 删除旧容器（如果存在）
            self._run_command(['docker', 'rm', '-f', container_name], check=False)

            # 创建新容器
            result = self._run_command([
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', self.network_name,
                '--ip', ip_address,
                '--cap-add', 'NET_ADMIN',
                '--privileged',
                self.pq_image,
                '/root/start.sh'
            ])

            container_id = result.stdout.strip()

            self.containers[node['name']] = {
                'container_name': container_name,
                'ip': ip_address,
                'id': container_id
            }

            logger.info(f"Created container {container_name} (ID: {container_id})")

        logger.info(f"Created {len(self.containers)} PQ-NTOR containers")

        # 等待容器启动
        time.sleep(2)

    def start_directory_server(self, node_name='GS-Beijing'):
        """在指定节点启动directory服务器"""
        container_name = f"sagin_{node_name.lower()}"

        logger.info(f"Starting directory server in {container_name}...")

        # 在后台启动directory服务器
        self._run_command([
            'docker', 'exec', '-d', container_name,
            'bash', '-c',
            'cd /root/pq-ntor && ./directory > logs/directory.log 2>&1 &'
        ])

        # 等待服务器启动
        time.sleep(2)

        logger.info(f"Directory server started at {self._get_node_ip(node_name)}:5000")

        return self._get_node_ip(node_name)

    def start_relay_nodes(self, exclude_nodes: List[str] = []):
        """启动relay节点"""
        logger.info("Starting relay nodes...")

        port = 9001
        for node_name in self.containers.keys():
            if node_name in exclude_nodes:
                continue

            container_name = f"sagin_{node_name.lower()}"

            logger.info(f"Starting relay in {container_name} on port {port}...")

            # 在后台启动relay
            self._run_command([
                'docker', 'exec', '-d', container_name,
                'bash', '-c',
                f'cd /root/pq-ntor && ./relay -p {port} > logs/relay_{port}.log 2>&1 &'
            ])

            port += 1

        # 等待所有relay启动
        time.sleep(3)

        logger.info("All relay nodes started")

    def register_nodes_to_directory(self, dir_ip: str, nodes: List[Dict]):
        """
        向directory注册节点

        注意：当前的directory_server实现使用硬编码的节点列表
        这个函数作为占位符，未来可以实现动态注册
        """
        logger.info(f"Nodes will be discovered from directory at {dir_ip}:5000")
        logger.info("Note: Current directory uses hardcoded relay list")
        pass

    def run_circuit_test(self, client_node: str, dir_ip: str, iterations: int = 5) -> Dict:
        """
        运行电路构建测试

        Args:
            client_node: 运行client的节点名称
            dir_ip: directory服务器IP
            iterations: 测试迭代次数

        Returns:
            测试结果字典
        """
        client_container = f"sagin_{client_node.lower()}"

        logger.info(f"Running circuit test from {client_node} (iterations: {iterations})")

        results = []
        success_count = 0

        for i in range(iterations):
            logger.info(f"  Iteration {i+1}/{iterations}...")

            # 运行client程序
            start_time = time.time()

            result = self._run_command([
                'docker', 'exec', client_container,
                '/root/pq-ntor/client',
                '-d', dir_ip,
                '-p', '5000'
            ], check=False)

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # 检查是否成功
            if result.returncode == 0 and 'circuit established' in result.stdout.lower():
                success_count += 1
                results.append(duration_ms)
                logger.info(f"    ✓ Success: {duration_ms:.2f} ms")
            else:
                logger.warning(f"    ✗ Failed")
                logger.debug(f"    Output: {result.stdout[:200]}")

            # 延迟避免连接冲突
            time.sleep(1)

        # 计算统计
        if results:
            return {
                'status': 'success',
                'circuit_time_ms': sum(results) / len(results),
                'min_time_ms': min(results),
                'max_time_ms': max(results),
                'success_rate': (success_count / iterations) * 100,
                'timeout_rate': ((iterations - success_count) / iterations) * 100,
                'iterations': iterations
            }
        else:
            return {
                'status': 'failure',
                'circuit_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'success_rate': 0,
                'timeout_rate': 100,
                'iterations': iterations
            }

    def run_all_scenarios(self, iterations: int = 5):
        """运行测试场景"""
        logger.info("=== Running SAGIN Real Network Test ===")

        # 设置网络
        self.setup_network()

        # 创建容器
        self.create_containers()

        # 启动directory服务器（在GS-Beijing）
        dir_ip = self.start_directory_server('GS-Beijing')

        # 启动relay节点（除了运行directory的节点）
        self.start_relay_nodes(exclude_nodes=['GS-Beijing'])

        # 测试场景：从不同节点发起电路构建
        test_scenarios = [
            {
                'id': 'scenario_1',
                'name': 'Ground to Ground (GS-London)',
                'client_node': 'GS-London',
                'description': '从地面站London构建3跳电路'
            },
            {
                'id': 'scenario_2',
                'name': 'Satellite to Ground (Sat-1)',
                'client_node': 'Sat-1',
                'description': '从卫星Sat-1构建3跳电路'
            },
            {
                'id': 'scenario_3',
                'name': 'Aircraft to Ground (Aircraft-1)',
                'client_node': 'Aircraft-1',
                'description': '从飞机Aircraft-1构建3跳电路'
            }
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n--- Scenario {i}/{len(test_scenarios)} ---")
            logger.info(f"=== {scenario['name']} ===")
            logger.info(f"{scenario['description']}")

            # 运行测试
            results = self.run_circuit_test(
                scenario['client_node'],
                dir_ip,
                iterations
            )

            # 添加场景信息
            results['scenario_id'] = scenario['id']
            results['scenario_name'] = scenario['name']
            results['client_node'] = scenario['client_node']
            results['timestamp'] = datetime.utcnow().isoformat()
            results['use_pq'] = self.use_pq

            self.test_results.append(results)

            logger.info(f"Results: {json.dumps(results, indent=2)}")

            # 场景间等待
            time.sleep(3)

        logger.info("\n=== All scenarios completed ===")

    def save_results(self) -> Path:
        """保存测试结果"""
        if not self.test_results:
            logger.warning("No test results to save")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        protocol = 'pq_ntor_real' if self.use_pq else 'traditional_ntor_real'
        filename = self.results_dir / f'sagin_test_{protocol}_{timestamp}.csv'

        logger.info(f"Saving results to {filename}...")

        fieldnames = [
            'scenario_id', 'scenario_name', 'client_node', 'status',
            'circuit_time_ms', 'min_time_ms', 'max_time_ms',
            'success_rate', 'timeout_rate', 'iterations',
            'timestamp', 'use_pq'
        ]

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.test_results:
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)

        logger.info(f"Results saved to {filename}")

        return filename

    def cleanup(self):
        """清理Docker容器和网络"""
        logger.info("Cleaning up...")

        # 删除容器
        for node_name in self.containers.keys():
            container_name = f"sagin_{node_name.lower()}"
            logger.info(f"Removing container {container_name}...")
            self._run_command(['docker', 'rm', '-f', container_name], check=False)

        # 删除网络
        logger.info(f"Removing network {self.network_name}...")
        self._run_command(['docker', 'network', 'rm', self.network_name], check=False)

        logger.info("Cleanup complete")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='SAGIN Real Network Performance Test')
    parser.add_argument(
        '--config',
        default='/home/ccc/pq-ntor-experiment/sagin-experiments/configs/sagin_topology_config.json',
        help='SAGIN配置文件路径'
    )
    parser.add_argument(
        '--traditional',
        action='store_true',
        help='使用传统NTOR（默认PQ-NTOR）'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=5,
        help='每个场景的迭代次数'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='测试后不清理容器（用于调试）'
    )

    args = parser.parse_args()

    # 创建测试实例
    use_pq = not args.traditional
    tester = SAGINRealNetworkTest(args.config, use_pq=use_pq)

    try:
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

    finally:
        # 清理
        if not args.no_cleanup:
            tester.cleanup()
        else:
            logger.info("Skipping cleanup (--no-cleanup flag set)")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
