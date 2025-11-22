#!/usr/bin/env python3
"""
演示版Agent - 生成模拟数据用于前端展示
"""

import asyncio
import json
import logging
import time
import websockets
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoAgent:
    def __init__(self, node_id: str, node_role: str, hub_url: str):
        self.node_id = node_id
        self.node_role = node_role
        self.hub_url = hub_url
        self.websocket = None
        self.running = True
        self.handshake_count = 0
        self.topology_id = 1

    async def connect_to_hub(self):
        """连接到WebSocket Hub"""
        try:
            self.websocket = await websockets.connect(self.hub_url)
            logger.info(f"✅ Connected to Hub: {self.hub_url}")

            # 注册节点
            await self.websocket.send(json.dumps({
                'client_type': 'node',
                'node_id': self.node_id,
                'node_role': self.node_role
            }))
            logger.info(f"📝 Registered as node: {self.node_id} ({self.node_role})")

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise

    def generate_demo_data(self):
        """生成演示数据"""
        self.handshake_count += random.randint(0, 2)

        return {
            'type': 'node_status',
            'node_id': self.node_id,
            'timestamp': int(time.time()),
            'status': {
                'role': self.node_role,
                'online': True,
                'altitude': 0.0 if self.node_role == 'ground' else random.randint(500, 800),
            },
            'pq_ntor': {
                'handshakes': self.handshake_count,
                'avg_time_us': random.randint(140, 150)
            },
            'links': [
                {
                    'target': 'satellite-1',
                    'delay_ms': round(random.uniform(8.0, 10.0), 2),
                    'bandwidth_mbps': random.randint(50, 100)
                }
            ] if self.node_role == 'ground' else []
        }

    async def status_loop(self):
        """状态更新循环"""
        logger.info("🔄 Starting status update loop (2s interval)")

        while self.running:
            try:
                status_data = self.generate_demo_data()
                await self.websocket.send(json.dumps(status_data))
                logger.info(f"📤 Sent status: handshakes={self.handshake_count}")

                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"❌ Error in status loop: {e}")
                break

    async def heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                heartbeat = {'type': 'heartbeat', 'node_id': self.node_id}
                await self.websocket.send(json.dumps(heartbeat))
                logger.info(f"💓 Heartbeat sent")
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")
                break

    async def run(self):
        """主运行循环"""
        logger.info(f"🚀 Starting Demo Agent: {self.node_id}")

        await self.connect_to_hub()

        try:
            await asyncio.gather(
                self.status_loop(),
                self.heartbeat_loop()
            )
        except KeyboardInterrupt:
            logger.info("⏹️  Stopping agent...")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()


async def main():
    # 创建一个演示节点
    agent = DemoAgent(
        node_id='demo-pi-1',
        node_role='ground',
        hub_url='ws://localhost:9000'
    )

    await agent.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo agent stopped")
