#!/usr/bin/env python3
"""
SAGIN Network Topology Manager - Simplified Version (without tc netem)
Uses only iptables for link control (no delay simulation)

适用于飞腾派等TC模块不可用的环境
"""

import json
import subprocess
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleNetworkTopologyManager:
    """Simplified network manager without tc dependencies"""

    def __init__(self, config_file: str, dry_run: bool = False):
        self.config_file = config_file
        self.dry_run = dry_run
        self.config = self._load_config()
        self.node_containers: Dict[str, str] = {}
        self.node_ips: Dict[str, str] = {}
        self._initialize_node_mappings()

        logger.info(f"简化版网络管理器已初始化 (dry_run={dry_run})")
        logger.info(f"管理 {len(self.node_ips)} 个节点")
        logger.info("注意: 此版本仅使用iptables控制链路，不模拟延迟")

    def _load_config(self) -> dict:
        """加载SAGIN拓扑配置"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _initialize_node_mappings(self):
        """初始化节点映射"""
        # 卫星节点
        for sat_name, sat_config in self.config.get('satellites', {}).items():
            container_name = f"sagin_{sat_name.lower()}"
            self.node_containers[sat_name] = container_name
            self.node_ips[sat_name] = sat_config.get('ip')

        # 飞行器节点
        for aircraft_name, aircraft_config in self.config.get('aircraft', {}).items():
            container_name = f"sagin_{aircraft_name.lower()}"
            self.node_containers[aircraft_name] = container_name
            self.node_ips[aircraft_name] = aircraft_config.get('ip')

        # 地面站节点
        for gs_name, gs_config in self.config.get('ground_stations', {}).items():
            container_name = f"sagin_{gs_name.lower()}"
            self.node_containers[gs_name] = container_name
            self.node_ips[gs_name] = gs_config.get('ip')

        logger.info(f"节点映射: {list(self.node_containers.keys())}")

    def _run_command(self, command: List[str], container: str = None) -> bool:
        """执行命令（可选在容器内执行）"""
        if container:
            full_command = ['docker', 'exec', container] + command
        else:
            full_command = command

        if self.dry_run:
            logger.info(f"[DRY RUN] {' '.join(full_command)}")
            return True

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"命令执行错误: {e}")
            return False

    def enable_link(self, source: str, destination: str):
        """
        启用链路（移除iptables DROP规则）

        Args:
            source: 源节点名称
            destination: 目标节点名称
        """
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            logger.warning(f"无法启用链路 {source}->{destination}: 缺少映射")
            return False

        # 移除DROP规则（可能不存在，这是正常的）
        command = ['iptables', '-D', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
        self._run_command(command, container)

        logger.info(f"已启用链路 {source} -> {destination}")
        return True

    def disable_link(self, source: str, destination: str):
        """
        禁用链路（添加iptables DROP规则）

        Args:
            source: 源节点名称
            destination: 目标节点名称
        """
        container = self.node_containers.get(source)
        dest_ip = self.node_ips.get(destination)

        if not container or not dest_ip:
            logger.warning(f"无法禁用链路 {source}->{destination}: 缺少映射")
            return False

        # 添加DROP规则
        command = ['iptables', '-A', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
        success = self._run_command(command, container)

        if success:
            logger.info(f"已禁用链路 {source} -> {destination}")
        else:
            logger.warning(f"禁用链路失败 {source} -> {destination}")

        return success

    def get_node_info(self):
        """获取节点信息"""
        return {
            'total_nodes': len(self.node_ips),
            'nodes': list(self.node_ips.keys()),
            'containers': self.node_containers,
            'ips': self.node_ips
        }

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 network_topology_manager_simple.py <config.json>")
        print("\n示例:")
        print("  python3 network_topology_manager_simple.py ../sagin_topology_config.json")
        print("\n说明:")
        print("  此简化版仅使用iptables控制链路启用/禁用")
        print("  不模拟延迟/抖动（tc netem不可用时的备选方案）")
        print("  适用于飞腾派等内核不支持TC的环境")
        sys.exit(1)

    config_file = sys.argv[1]

    print("="*60)
    print("SAGIN简化版网络管理器")
    print("="*60)

    manager = SimpleNetworkTopologyManager(config_file, dry_run=False)

    info = manager.get_node_info()
    print(f"\n✓ 初始化完成")
    print(f"  节点总数: {info['total_nodes']}")
    print(f"  节点列表: {', '.join(info['nodes'])}")

    print("\n✓ 功能说明:")
    print("  - 链路启用/禁用: iptables控制")
    print("  - 延迟模拟: 在仿真脚本中计算（不使用tc）")
    print("  - 适用场景: 飞腾派、嵌入式设备")

    print("\n" + "="*60)
