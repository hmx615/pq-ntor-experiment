#!/usr/bin/env python3
"""
WebSocket Hub - 中央通信服务
用于飞腾派7（控制台）接收6个节点数据并广播
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import websockets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局状态
class HubState:
    def __init__(self):
        # 连接的客户端（节点和前端）
        self.node_connections: Dict[str, any] = {}
        self.frontend_connections: Set[any] = set()

        # 节点数据缓存
        self.node_data: Dict[str, dict] = {}

        # 当前拓扑
        self.current_topology = 1

        # 统计信息
        self.stats = {
            'total_messages': 0,
            'start_time': datetime.now().isoformat()
        }

hub_state = HubState()


async def handle_node_message(node_id: str, message: dict):
    """处理来自节点的消息"""
    msg_type = message.get('type', 'unknown')

    if msg_type == 'node_status':
        # 更新节点状态
        hub_state.node_data[node_id] = {
            'node_id': node_id,
            'timestamp': datetime.now().isoformat(),
            'status': message.get('status', {}),
            'links': message.get('links', []),
            'pq_ntor': message.get('pq_ntor', {}),
            'traffic': message.get('traffic', {}),
            'topology_id': hub_state.current_topology
        }

        # 广播到所有前端
        await broadcast_to_frontends({
            'type': 'node_update',
            'node_id': node_id,
            'data': hub_state.node_data[node_id]
        })

        logger.debug(f"Updated status for node {node_id}")

    elif msg_type == 'heartbeat':
        # 心跳响应
        return {'type': 'heartbeat_ack', 'timestamp': datetime.now().isoformat()}

    return None


async def handle_frontend_message(websocket, message: dict):
    """处理来自前端的消息"""
    msg_type = message.get('type', 'unknown')

    if msg_type == 'get_all_nodes':
        # 返回所有节点状态
        await websocket.send(json.dumps({
            'type': 'all_nodes',
            'nodes': hub_state.node_data,
            'topology_id': hub_state.current_topology
        }))

    elif msg_type == 'change_topology':
        # 切换拓扑
        new_topology = message.get('topology_id')
        if new_topology and 1 <= new_topology <= 12:
            hub_state.current_topology = new_topology

            # 广播拓扑切换命令到所有节点
            await broadcast_to_nodes({
                'type': 'topology_change',
                'topology_id': new_topology
            })

            # 通知所有前端
            await broadcast_to_frontends({
                'type': 'topology_changed',
                'topology_id': new_topology
            })

            logger.info(f"Topology changed to {new_topology}")

    elif msg_type == 'get_stats':
        # 返回统计信息
        await websocket.send(json.dumps({
            'type': 'stats',
            'data': {
                **hub_state.stats,
                'nodes_online': len(hub_state.node_data),
                'frontends_connected': len(hub_state.frontend_connections),
                'current_topology': hub_state.current_topology
            }
        }))


async def broadcast_to_nodes(message: dict):
    """广播消息到所有节点"""
    if hub_state.node_connections:
        message_json = json.dumps(message)
        await asyncio.gather(
            *[ws.send(message_json) for ws in hub_state.node_connections.values()],
            return_exceptions=True
        )


async def broadcast_to_frontends(message: dict):
    """广播消息到所有前端"""
    if hub_state.frontend_connections:
        message_json = json.dumps(message)
        # 移除已断开的连接
        dead_connections = set()
        for ws in hub_state.frontend_connections:
            try:
                await ws.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                dead_connections.add(ws)

        hub_state.frontend_connections -= dead_connections


async def websocket_handler(websocket):
    """WebSocket连接处理器"""
    client_type = None
    node_id = None

    try:
        # 等待客户端注册消息
        register_msg = await websocket.recv()
        register_data = json.loads(register_msg)

        client_type = register_data.get('client_type')

        if client_type == 'node':
            # 节点连接
            node_id = register_data.get('node_id')
            hub_state.node_connections[node_id] = websocket
            logger.info(f"Node {node_id} connected")

            # 发送当前拓扑
            await websocket.send(json.dumps({
                'type': 'topology_info',
                'topology_id': hub_state.current_topology
            }))

        elif client_type == 'frontend':
            # 前端连接
            hub_state.frontend_connections.add(websocket)
            logger.info(f"Frontend connected (total: {len(hub_state.frontend_connections)})")

            # 发送所有节点数据
            await websocket.send(json.dumps({
                'type': 'all_nodes',
                'nodes': hub_state.node_data,
                'topology_id': hub_state.current_topology
            }))

        else:
            logger.warning(f"Unknown client type: {client_type}")
            await websocket.close()
            return

        # 消息循环
        async for message in websocket:
            hub_state.stats['total_messages'] += 1

            try:
                data = json.loads(message)

                if client_type == 'node':
                    response = await handle_node_message(node_id, data)
                    if response:
                        await websocket.send(json.dumps(response))

                elif client_type == 'frontend':
                    await handle_frontend_message(websocket, data)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_type}: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"{client_type} disconnected")

    finally:
        # 清理连接
        if client_type == 'node' and node_id:
            hub_state.node_connections.pop(node_id, None)
            hub_state.node_data.pop(node_id, None)
            logger.info(f"Node {node_id} disconnected")

        elif client_type == 'frontend':
            hub_state.frontend_connections.discard(websocket)
            logger.info(f"Frontend disconnected (remaining: {len(hub_state.frontend_connections)})")


async def main():
    """主函数"""
    host = '0.0.0.0'
    port = 9000

    logger.info(f"Starting WebSocket Hub on {host}:{port}")

    async with websockets.serve(websocket_handler, host, port):
        logger.info("WebSocket Hub is running")
        await asyncio.Future()  # 永久运行


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket Hub stopped")
