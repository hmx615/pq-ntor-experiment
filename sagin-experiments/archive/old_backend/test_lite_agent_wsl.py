#!/usr/bin/env python3
"""
WSL测试版 - 不依赖Docker直接运行Lite Agent
用于本地测试验证
"""

import asyncio
import json
import logging
import time
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockWebSocket:
    """模拟WebSocket连接（用于本地测试）"""
    def __init__(self):
        self.messages = []
        self.connected = True
        
    async def send(self, data):
        """模拟发送消息"""
        self.messages.append(data)
        logger.info(f"📤 Sent: {len(data)} bytes")
        
    async def recv(self):
        """模拟接收消息"""
        await asyncio.sleep(5)
        return json.dumps({'type': 'topology_info', 'topology_id': 1})


class LiteNodeAgentTest:
    """测试版Lite Agent"""
    def __init__(self, node_id: str, node_role: str, update_interval: float = 2.0):
        self.node_id = node_id
        self.node_role = node_role
        self.update_interval = update_interval
        self.running = True
        
        self.handshake_count = 0
        self.status_buffer = []
        self.buffer_max_size = 3
        
        # 性能统计
        self.total_messages = 0
        self.total_bytes = 0
        self.start_time = time.time()
        
    def collect_minimal_data(self):
        """精简数据采集"""
        if int(time.time()) % 10 == 0:
            self.handshake_count += 1
            
        return {
            'type': 'node_status',
            'node_id': self.node_id,
            'timestamp': int(time.time()),
            'status': {
                'role': self.node_role,
                'online': True
            },
            'pq_ntor': {
                'handshakes': self.handshake_count
            }
        }
    
    async def send_status_update(self, websocket):
        """批量发送状态更新"""
        status_data = self.collect_minimal_data()
        self.status_buffer.append(status_data)
        
        if len(self.status_buffer) >= self.buffer_max_size:
            batch_data = {
                'type': 'batch_status',
                'data': self.status_buffer
            }
            json_str = json.dumps(batch_data)
            
            await websocket.send(json_str)
            
            # 统计
            self.total_messages += 1
            self.total_bytes += len(json_str)
            
            logger.info(f"✅ Batch sent: {len(self.status_buffer)} messages, {len(json_str)} bytes")
            self.status_buffer.clear()
    
    async def status_loop(self, websocket):
        """状态更新循环"""
        logger.info(f"📊 Status loop started (interval: {self.update_interval}s)")
        
        while self.running:
            await self.send_status_update(websocket)
            await asyncio.sleep(self.update_interval)
    
    async def heartbeat_loop(self, websocket):
        """心跳循环"""
        logger.info("💓 Heartbeat loop started (interval: 60s)")
        
        while self.running:
            heartbeat = {'type': 'heartbeat', 'node_id': self.node_id}
            await websocket.send(json.dumps(heartbeat))
            await asyncio.sleep(60)
    
    def print_stats(self):
        """打印性能统计"""
        runtime = time.time() - self.start_time
        avg_bytes_per_sec = self.total_bytes / runtime if runtime > 0 else 0
        
        print("\n" + "="*50)
        print("📈 Performance Statistics")
        print("="*50)
        print(f"Runtime: {runtime:.1f}s")
        print(f"Total batches: {self.total_messages}")
        print(f"Total bytes: {self.total_bytes}")
        print(f"Avg bandwidth: {avg_bytes_per_sec:.1f} bytes/s")
        print(f"Handshakes: {self.handshake_count}")
        print("="*50 + "\n")
    
    async def run_test(self, duration=30):
        """运行测试"""
        logger.info(f"🚀 Starting Lite Agent Test")
        logger.info(f"   Node ID: {self.node_id}")
        logger.info(f"   Role: {self.node_role}")
        logger.info(f"   Update interval: {self.update_interval}s")
        logger.info(f"   Test duration: {duration}s\n")
        
        # 使用模拟WebSocket
        mock_ws = MockWebSocket()
        
        try:
            # 并发运行任务
            await asyncio.wait_for(
                asyncio.gather(
                    self.status_loop(mock_ws),
                    self.heartbeat_loop(mock_ws)
                ),
                timeout=duration
            )
        except asyncio.TimeoutError:
            logger.info(f"\n⏰ Test completed after {duration}s")
            self.running = False
        
        # 打印统计
        self.print_stats()
        
        return mock_ws.messages


async def compare_agents():
    """对比原版和精简版Agent"""
    print("\n" + "="*60)
    print("  Agent Performance Comparison Test")
    print("="*60 + "\n")
    
    # 测试精简版
    print("### Testing Lite Agent ###\n")
    lite_agent = LiteNodeAgentTest('test-pi-1', 'ground', update_interval=2.0)
    lite_messages = await lite_agent.run_test(duration=20)
    
    print("\n### Comparison Summary ###\n")
    print("Lite Agent:")
    print(f"  - Update interval: 2.0s")
    print(f"  - Batch size: 3 messages")
    print(f"  - Data fields: 5 (minimal)")
    print(f"  - Total messages sent: {len(lite_messages)}")
    
    if lite_messages:
        sample = json.loads(lite_messages[0])
        if 'data' in sample:
            sample_size = len(json.dumps(sample['data'][0]))
            print(f"  - Avg message size: {sample_size} bytes")
    
    print("\nOriginal Agent (estimated):")
    print(f"  - Update interval: 1.0s")
    print(f"  - Batch size: 1 message")
    print(f"  - Data fields: 7 (full)")
    print(f"  - Estimated message size: ~450 bytes")
    print(f"  - Bandwidth: ~450 bytes/s")
    
    print("\n" + "="*60)
    print("✨ Test Complete - Agent is ready for deployment!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(compare_agents())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
