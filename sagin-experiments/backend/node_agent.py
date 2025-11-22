#!/usr/bin/env python3
"""
Node Agent - 节点数据采集Agent
运行在每个节点飞腾派上，监控Docker容器并发送数据到WebSocket Hub
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime
import websockets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NodeAgent:
    def __init__(self, node_id: str, node_role: str, hub_url: str):
        self.node_id = node_id
        self.node_role = node_role  # satellite, aircraft, ground
        self.hub_url = hub_url
        self.websocket = None
        self.current_topology = 1
        self.running = True

        # 模拟数据（后续可替换为真实Docker监控）
        self.handshake_count = 0
        self.current_traffic_up = 0  # 当前上行速率
        self.current_traffic_down = 0  # 当前下行速率

    async def connect_to_hub(self):
        """连接到WebSocket Hub"""
        try:
            self.websocket = await websockets.connect(self.hub_url)

            # 注册为节点
            await self.websocket.send(json.dumps({
                'client_type': 'node',
                'node_id': self.node_id,
                'node_role': self.node_role
            }))

            logger.info(f"Node {self.node_id} connected to Hub")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Hub: {e}")
            return False

    async def send_status_update(self):
        """发送状态更新到Hub"""
        if not self.websocket:
            return

        # 模拟实时流量速率（KB/s）
        # 根据节点类型设置不同的流量范围
        if self.node_role == 'satellite':
            # 卫星节点：较高流量
            self.current_traffic_up = random.randint(50, 150)
            self.current_traffic_down = random.randint(80, 200)
        elif self.node_role == 'aircraft':
            # 空中节点：中等流量
            self.current_traffic_up = random.randint(30, 100)
            self.current_traffic_down = random.randint(40, 120)
        else:
            # 地面节点：较低流量
            self.current_traffic_up = random.randint(10, 60)
            self.current_traffic_down = random.randint(15, 80)

        # 模拟握手
        if random.random() < 0.1:  # 10%概率进行握手
            self.handshake_count += 1

        # 获取节点配置
        node_config = self.get_node_config()

        # 构造状态数据
        status_data = {
            'type': 'node_status',
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat(),
            'status': {
                'role': self.node_role,
                'altitude': node_config['altitude'],
                'ip': node_config['ip'],
                'container_ip': node_config['container_ip'],
                'online': True
            },
            'links': self.get_active_links(),
            'pq_ntor': {
                'handshakes': self.handshake_count,
                'avg_time_ms': round(random.uniform(2.0, 3.0), 2),
                'circuit_status': 'active'
            },
            'traffic': {
                'up_kbps': self.current_traffic_up,
                'down_kbps': self.current_traffic_down
            }
        }

        try:
            await self.websocket.send(json.dumps(status_data))
            logger.debug(f"Sent status update for {self.node_id}")

        except Exception as e:
            logger.error(f"Failed to send status: {e}")

    def get_node_config(self) -> dict:
        """获取节点配置信息"""
        # 节点IP配置（基于node_id）
        node_ips = {
            'SAT': {'ip': '192.168.100.11', 'container_ip': '172.20.0.11', 'altitude': 0.15},
            'SR': {'ip': '192.168.100.12', 'container_ip': '172.20.0.12', 'altitude': 0.05},
            'S1R2': {'ip': '192.168.100.13', 'container_ip': '172.20.0.13', 'altitude': 0.05},
            'S1': {'ip': '192.168.100.14', 'container_ip': '172.20.0.14', 'altitude': 0.0},
            'S2': {'ip': '192.168.100.15', 'container_ip': '172.20.0.15', 'altitude': 0.0},
            'T': {'ip': '192.168.100.16', 'container_ip': '172.20.0.16', 'altitude': 0.0},
        }

        return node_ips.get(self.node_id, {
            'ip': '192.168.100.99',
            'container_ip': '172.20.0.99',
            'altitude': 0.0
        })

    def get_active_links(self) -> list:
        """获取当前拓扑下的活跃链路"""
        # 这里简化处理，返回模拟链路数据
        # 实际应该根据current_topology和node_id返回真实链路

        links = []

        # 示例：卫星节点在拓扑1的链路
        if self.node_id == 'SAT' and self.current_topology == 1:
            links = [
                {
                    'target': 'S1',
                    'rssi': 'high',
                    'delay_ms': 10,
                    'bandwidth_mbps': 50,
                    'packet_loss': 0.5,
                    'active': True
                },
                {
                    'target': 'S2',
                    'rssi': 'low',
                    'delay_ms': 30,
                    'bandwidth_mbps': 20,
                    'packet_loss': 2.0,
                    'active': True
                }
            ]

        return links

    async def handle_hub_messages(self):
        """处理来自Hub的消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'topology_change':
                    new_topology = data.get('topology_id')
                    logger.info(f"Topology changed to {new_topology}")
                    self.current_topology = new_topology

                    # 这里应该执行Docker容器切换等操作
                    # await self.switch_topology(new_topology)

                elif msg_type == 'topology_info':
                    self.current_topology = data.get('topology_id')
                    logger.info(f"Current topology: {self.current_topology}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to Hub closed")
            self.websocket = None

    async def heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            if self.websocket:
                try:
                    await self.websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'node_id': self.node_id
                    }))
                except Exception as e:
                    logger.error(f"Heartbeat failed: {e}")
                    self.websocket = None

            await asyncio.sleep(30)  # 每30秒心跳

    async def status_update_loop(self):
        """状态更新循环"""
        while self.running:
            if self.websocket:
                await self.send_status_update()
            await asyncio.sleep(1)  # 每秒更新

    async def run(self):
        """运行Agent主循环"""
        while self.running:
            if not self.websocket:
                success = await self.connect_to_hub()
                if not success:
                    await asyncio.sleep(5)  # 重连等待
                    continue

            # 启动任务
            tasks = [
                asyncio.create_task(self.handle_hub_messages()),
                asyncio.create_task(self.heartbeat_loop()),
                asyncio.create_task(self.status_update_loop())
            ]

            # 等待任务完成（通常由于断线）
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # 取消未完成的任务
            for task in pending:
                task.cancel()

            logger.warning("Connection lost, reconnecting...")
            await asyncio.sleep(2)

    def stop(self):
        """停止Agent"""
        self.running = False


async def main():
    """主函数"""
    # 从环境变量获取配置
    node_id = os.environ.get('NODE_ID', 'SAT')
    node_role = os.environ.get('NODE_ROLE', 'satellite')
    hub_url = os.environ.get('HUB_URL', 'ws://192.168.100.17:9000')

    logger.info(f"Starting Node Agent: {node_id} ({node_role})")
    logger.info(f"Hub URL: {hub_url}")

    agent = NodeAgent(node_id, node_role, hub_url)

    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Node Agent stopped")
        agent.stop()


if __name__ == '__main__':
    asyncio.run(main())
