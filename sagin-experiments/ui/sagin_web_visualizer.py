#!/usr/bin/env python3
"""
SAGIN卫星网络可视化 - Web版本
使用Flask提供Web界面，通过浏览器访问
"""

from flask import Flask, render_template, jsonify
import math
import time
from datetime import datetime
import json

app = Flask(__name__)

# Canvas尺寸（与HTML一致）
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 800
EARTH_CENTER_X = CANVAS_WIDTH / 2   # 500
EARTH_CENTER_Y = CANVAS_HEIGHT / 2  # 400

# 轨道半径（从地球中心计算）
ORBIT_RADIUS = {
    'satellite': 280,   # 卫星LEO轨道
    'aircraft': 180,    # 飞行器层
    'ground': 110       # 地面站（地球表面）
}

# 网络拓扑配置
NODES = {
    'Sat-1': {
        'type': 'satellite',
        'orbit_angle': 0,           # 初始角度
        'orbit_radius': ORBIT_RADIUS['satellite'],
        'orbit_speed': 0.5,         # 度/秒
        'color': '#00ff00'
    },
    'Sat-2': {
        'type': 'satellite',
        'orbit_angle': 180,         # 相反方向
        'orbit_radius': ORBIT_RADIUS['satellite'],
        'orbit_speed': 0.5,
        'color': '#00ff00'
    },
    'Aircraft-1': {
        'type': 'aircraft',
        'orbit_angle': 45,
        'orbit_radius': ORBIT_RADIUS['aircraft'],
        'orbit_speed': 1.0,         # 飞行器更快
        'color': '#ffaa00'
    },
    'Aircraft-2': {
        'type': 'aircraft',
        'orbit_angle': 225,
        'orbit_radius': ORBIT_RADIUS['aircraft'],
        'orbit_speed': 1.0,
        'color': '#ffaa00'
    },
    'GS-Beijing': {
        'type': 'ground',
        'fixed_angle': 60,          # 固定角度（东亚位置）
        'radius': ORBIT_RADIUS['ground'],
        'color': '#ff0000'
    },
    'GS-London': {
        'type': 'ground',
        'fixed_angle': 150,         # 欧洲位置
        'radius': ORBIT_RADIUS['ground'],
        'color': '#ff0000'
    },
    'GS-NewYork': {
        'type': 'ground',
        'fixed_angle': 240,         # 美洲位置
        'radius': ORBIT_RADIUS['ground'],
        'color': '#ff0000'
    },
}

# 链路配置
LINKS = [
    {'from': 'Sat-1', 'to': 'Sat-2', 'type': 'ISL', 'delay': 10},
    {'from': 'Sat-1', 'to': 'Aircraft-1', 'type': 'SA', 'delay': 7},
    {'from': 'Sat-1', 'to': 'GS-Beijing', 'type': 'SG', 'delay': 5},
    {'from': 'Sat-2', 'to': 'Aircraft-2', 'type': 'SA', 'delay': 7},
    {'from': 'Sat-2', 'to': 'GS-London', 'type': 'SG', 'delay': 5},
    {'from': 'Aircraft-1', 'to': 'GS-Beijing', 'type': 'AG', 'delay': 3},
    {'from': 'Aircraft-1', 'to': 'GS-London', 'type': 'AG', 'delay': 3},
]

# 模拟统计数据
stats = {
    'handshakes': 0,
    'circuits': 0,
    'avg_delay_us': 49,
    'data_transferred_mb': 0
}

start_time = time.time()

def calculate_node_position(node_name, current_time):
    """计算节点当前位置（严格在轨道上）"""
    node = NODES[node_name]

    if node['type'] in ['satellite', 'aircraft']:
        # 运动节点：卫星和飞行器
        # 计算当前角度 = 初始角度 + 速度 * 时间
        angle = (node['orbit_angle'] + node['orbit_speed'] * current_time) % 360
        angle_rad = math.radians(angle)

        # 严格根据轨道半径计算位置（从地球中心）
        x = EARTH_CENTER_X + node['orbit_radius'] * math.cos(angle_rad)
        y = EARTH_CENTER_Y + node['orbit_radius'] * math.sin(angle_rad)

        return {'x': x, 'y': y, 'angle': angle}
    else:
        # 地面站：固定位置
        angle_rad = math.radians(node['fixed_angle'])
        x = EARTH_CENTER_X + node['radius'] * math.cos(angle_rad)
        y = EARTH_CENTER_Y + node['radius'] * math.sin(angle_rad)

        return {'x': x, 'y': y, 'angle': node['fixed_angle']}

def check_link_visibility(from_node, to_node, current_time):
    """检查链路是否可见"""
    from_pos = calculate_node_position(from_node, current_time)
    to_pos = calculate_node_position(to_node, current_time)

    # ISL（星间链路）总是可见
    if NODES[from_node]['type'] == 'satellite' and NODES[to_node]['type'] == 'satellite':
        return True

    # 其他链路：根据角度差判断可见性
    # 两个节点角度差小于150度则可见
    angle_diff = abs(from_pos['angle'] - to_pos['angle'])
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    # 可见性阈值
    return angle_diff < 150

@app.route('/')
def index():
    """主页"""
    return render_template('sagin_visualizer.html')

@app.route('/api/topology')
def get_topology():
    """获取当前网络拓扑数据"""
    current_time = time.time() - start_time

    # 计算所有节点位置
    nodes_data = {}
    for node_name, node_info in NODES.items():
        pos = calculate_node_position(node_name, current_time)
        nodes_data[node_name] = {
            'x': pos['x'],
            'y': pos['y'],
            'type': node_info['type'],
            'color': node_info['color']
        }

    # 计算所有链路状态
    links_data = []
    for link in LINKS:
        is_visible = check_link_visibility(link['from'], link['to'], current_time)
        links_data.append({
            'from': link['from'],
            'to': link['to'],
            'type': link['type'],
            'delay': link['delay'],
            'active': is_visible
        })

    # 更新统计（模拟）
    global stats
    stats['handshakes'] = int(current_time / 2)  # 每2秒一次握手
    stats['circuits'] = min(3, int(current_time / 10))
    stats['data_transferred_mb'] = round(current_time * 0.05, 2)

    return jsonify({
        'nodes': nodes_data,
        'links': links_data,
        'stats': stats,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    return jsonify(stats)

if __name__ == '__main__':
    print("="*60)
    print("SAGIN卫星网络可视化 Web服务器")
    print("="*60)
    print("\n启动Web服务器...")
    print("\n访问方式:")
    print("  本地访问: http://localhost:5000")
    print("  局域网访问: http://192.168.5.110:5000")
    print("\n按 Ctrl+C 停止服务器")
    print("="*60)

    app.run(host='0.0.0.0', port=5000, debug=False)
