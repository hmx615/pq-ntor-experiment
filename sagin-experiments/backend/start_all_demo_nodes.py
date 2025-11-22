#!/usr/bin/env python3
"""
启动6+1演示系统
- Pi-0: 控制面板 (不需要Agent，只需前端)
- Pi-1 到 Pi-6: 6个地球节点
"""

import asyncio
import json
import logging
import time
import websockets
import random
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)


class DemoAgent:
    def __init__(self, node_id: str, node_role: str, hub_url: str):
        self.node_id = node_id
        self.node_role = node_role
        self.hub_url = hub_url
        self.websocket = None
        self.running = True
        self.handshake_count = 0
        self.topology_id = 1
        self.logger = logging.getLogger(node_id)

        # 为不同节点设置不同的位置
        positions = {
            'pi-1': {'lat': 39.9, 'lon': 116.4, 'city': '北京'},
            'pi-2': {'lat': 31.2, 'lon': 121.5, 'city': '上海'},
            'pi-3': {'lat': 22.5, 'lon': 114.1, 'city': '深圳'},
            'pi-4': {'lat': 30.6, 'lon': 104.1, 'city': '成都'},
            'pi-5': {'lat': 34.3, 'lon': 108.9, 'city': '西安'},
            'pi-6': {'lat': 45.8, 'lon': 126.5, 'city': '哈尔滨'}
        }
        self.position = positions.get(node_id, {'lat': 0, 'lon': 0, 'city': 'Unknown'})

    async def connect_to_hub(self):
        """连接到WebSocket Hub"""
        try:
            self.websocket = await websockets.connect(self.hub_url)
            self.logger.info(f"✅ Connected to Hub")

            # 注册节点
            await self.websocket.send(json.dumps({
                'client_type': 'node',
                'node_id': self.node_id,
                'node_role': self.node_role
            }))
            self.logger.info(f"📝 Registered as {self.node_role} at {self.position['city']}")

        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
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
                'altitude': 0.0,
                'latitude': self.position['lat'],
                'longitude': self.position['lon'],
                'city': self.position['city']
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
            ],
            'traffic': {
                'rx_bytes': random.randint(1000, 5000),
                'tx_bytes': random.randint(1000, 5000)
            }
        }

    async def status_loop(self):
        """状态更新循环"""
        while self.running:
            try:
                status_data = self.generate_demo_data()
                await self.websocket.send(json.dumps(status_data))
                self.logger.debug(f"📤 Status sent: handshakes={self.handshake_count}")
                await asyncio.sleep(2.0)
            except Exception as e:
                self.logger.error(f"❌ Error in status loop: {e}")
                break

    async def heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                heartbeat = {'type': 'heartbeat', 'node_id': self.node_id}
                await self.websocket.send(json.dumps(heartbeat))
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"❌ Heartbeat error: {e}")
                break

    async def run(self):
        """主运行循环"""
        self.logger.info(f"🚀 Starting {self.node_id}")
        await self.connect_to_hub()

        try:
            await asyncio.gather(
                self.status_loop(),
                self.heartbeat_loop()
            )
        except KeyboardInterrupt:
            self.logger.info("⏹️  Stopping...")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()


async def run_all_nodes():
    """启动所有6个地球节点"""
    nodes = []

    print("=" * 60)
    print("🌍 启动 6+1 SAGIN演示系统")
    print("=" * 60)
    print()
    print("系统架构:")
    print("  Pi-0 (控制面板): http://localhost:8080/control-panel/index.html")
    print("  Pi-1~6 (地球节点): 各自独立显示屏")
    print()
    print("启动节点:")

    for i in range(1, 7):
        node_id = f'pi-{i}'
        agent = DemoAgent(node_id, 'ground', 'ws://localhost:9000')
        nodes.append(agent)
        print(f"  - {node_id}: 准备就绪")

    print()
    print("🔄 开始运行...")
    print("=" * 60)
    print()

    # 并发运行所有节点
    await asyncio.gather(*[node.run() for node in nodes])


if __name__ == '__main__':
    try:
        asyncio.run(run_all_nodes())
    except KeyboardInterrupt:
        print("\n\n👋 所有演示节点已停止")
        sys.exit(0)
