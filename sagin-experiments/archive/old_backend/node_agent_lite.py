#!/usr/bin/env python3
"""
Node Agent Lite - 精简版节点数据采集Agent
优化用于飞腾派性能受限环境
"""

import asyncio
import json
import logging
import os
import time
import websockets

# 精简日志配置
logging.basicConfig(
    level=logging.WARNING,  # 降低日志级别
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiteNodeAgent:
    def __init__(self, node_id: str, node_role: str, hub_url: str, update_interval: float = 2.0):
        self.node_id = node_id
        self.node_role = node_role
        self.hub_url = hub_url
        self.websocket = None
        self.running = True
        self.update_interval = update_interval  # 可配置更新间隔

        # 精简状态
        self.handshake_count = 0
        self.current_topology = 1

        # 批量发送缓冲区
        self.status_buffer = []
        self.buffer_max_size = 3  # 累积3条消息后批量发送

    async def connect_to_hub(self):
        """连接到WebSocket Hub"""
        try:
            self.websocket = await websockets.connect(self.hub_url)

            # 注册节点
            await self.websocket.send(json.dumps({
                'client_type': 'node',
                'node_id': self.node_id,
                'node_role': self.node_role
            }))

            logger.info(f"Node {self.node_id} connected")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def collect_minimal_data(self):
        """只采集必要数据 - 精简版"""
        # 模拟握手（降低频率）
        if int(time.time()) % 10 == 0:  # 每10秒可能握手一次
            self.handshake_count += 1

        return {
            'type': 'node_status',
            'node_id': self.node_id,
            'timestamp': int(time.time()),  # 使用时间戳而不是ISO格式
            'status': {
                'role': self.node_role,
                'online': True
            },
            'pq_ntor': {
                'handshakes': self.handshake_count
            }
        }

    async def send_status_update(self):
        """发送状态更新（批量模式）"""
        if not self.websocket:
            return

        # 收集数据
        status_data = self.collect_minimal_data()
        self.status_buffer.append(status_data)

        # 达到缓冲区大小后批量发送
        if len(self.status_buffer) >= self.buffer_max_size:
            try:
                batch_data = {
                    'type': 'batch_status',
                    'data': self.status_buffer
                }
                await self.websocket.send(json.dumps(batch_data))
                self.status_buffer.clear()

            except Exception as e:
                logger.error(f"Send failed: {e}")
                self.status_buffer.clear()

    async def handle_hub_messages(self):
        """处理来自Hub的消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'topology_change':
                    self.current_topology = data.get('topology_id')
                    logger.info(f"Topology changed to {self.current_topology}")

                elif msg_type == 'topology_info':
                    self.current_topology = data.get('topology_id')

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed")
            self.websocket = None

    async def heartbeat_loop(self):
        """心跳循环（降低频率）"""
        while self.running:
            if self.websocket:
                try:
                    await self.websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'node_id': self.node_id
                    }))
                except:
                    self.websocket = None

            await asyncio.sleep(60)  # 60秒心跳（原30秒）

    async def status_loop(self):
        """状态更新循环"""
        while self.running:
            await self.send_status_update()
            await asyncio.sleep(self.update_interval)

    async def run(self):
        """主运行循环"""
        logger.info(f"Starting Lite Node Agent: {self.node_id}")

        while self.running:
            if not self.websocket:
                if not await self.connect_to_hub():
                    await asyncio.sleep(5)
                    continue

            try:
                # 并发运行所有任务
                await asyncio.gather(
                    self.handle_hub_messages(),
                    self.heartbeat_loop(),
                    self.status_loop()
                )
            except Exception as e:
                logger.error(f"Error in run loop: {e}")
                self.websocket = None
                await asyncio.sleep(5)


async def main():
    # 从环境变量读取配置
    node_id = os.getenv('NODE_ID', 'unknown')
    node_role = os.getenv('NODE_ROLE', 'ground')
    hub_url = os.getenv('HUB_URL', 'ws://192.168.100.17:9000')
    update_interval = float(os.getenv('UPDATE_INTERVAL', '2.0'))

    # 创建并运行Agent
    agent = LiteNodeAgent(node_id, node_role, hub_url, update_interval)

    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        agent.running = False


if __name__ == "__main__":
    asyncio.run(main())
