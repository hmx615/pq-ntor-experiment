#!/usr/bin/env python3
"""
SAGIN Orbit Simulator
使用Skyfield进行卫星轨道和飞机轨迹仿真
支持动态网络拓扑计算和链路状态管理
"""

import json
import time
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, EarthSatellite, wgs84
from skyfield import almanac


class SAGINOrbitSimulator:
    """SAGIN网络轨道仿真器"""

    def __init__(self, config_file):
        """
        初始化仿真器

        Args:
            config_file: 配置文件路径 (JSON格式)
        """
        print(f"[Simulator] 初始化SAGIN轨道仿真器...")

        # 加载时间尺度
        self.ts = load.timescale()

        # 存储节点信息
        self.satellites = {}
        self.aircraft = {}
        self.ground_stations = {}
        self.link_constraints = {}
        self.network_params = {}

        # 加载配置
        self.load_config(config_file)

        # 飞机状态（用于轨迹仿真）
        self.aircraft_state = {}
        self.init_aircraft_state()

        print(f"[Simulator] 初始化完成:")
        print(f"  - 卫星: {len(self.satellites)} 颗")
        print(f"  - 飞机: {len(self.aircraft)} 架")
        print(f"  - 地面站: {len(self.ground_stations)} 个")

    def load_config(self, config_file):
        """加载配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 加载卫星
        for sat_name, sat_data in config.get('satellites', {}).items():
            sat = EarthSatellite(
                sat_data['line1'],
                sat_data['line2'],
                sat_name,
                self.ts
            )
            self.satellites[sat_name] = {
                'object': sat,
                'type': sat_data['type'],
                'altitude_km': sat_data['altitude_km'],
                'ip': sat_data['ip'],
                'port': sat_data['port']
            }

        # 加载飞机
        self.aircraft = config.get('aircraft', {})

        # 加载地面站
        for gs_name, gs_data in config.get('ground_stations', {}).items():
            location = wgs84.latlon(
                gs_data['latitude'],
                gs_data['longitude'],
                elevation_m=gs_data['elevation_m']
            )
            self.ground_stations[gs_name] = {
                'location': location,
                'latitude': gs_data['latitude'],
                'longitude': gs_data['longitude'],
                'elevation_m': gs_data['elevation_m'],
                'min_elevation_deg': gs_data['min_elevation_deg'],
                'ip': gs_data['ip'],
                'port': gs_data['port']
            }

        # 加载链路约束
        self.link_constraints = config.get('link_constraints', {})
        self.network_params = config.get('network_parameters', {})

    def init_aircraft_state(self):
        """初始化飞机状态"""
        for aircraft_name, aircraft_data in self.aircraft.items():
            start_loc = aircraft_data['start_location']
            self.aircraft_state[aircraft_name] = {
                'current_lat': start_loc['latitude'],
                'current_lon': start_loc['longitude'],
                'current_alt_km': aircraft_data['cruise_altitude_km'],
                'speed_m_s': aircraft_data['cruise_speed_m_s'],
                'start_time': None,
                'progress': 0.0  # 0.0 = 起点, 1.0 = 终点
            }

    def get_satellite_position(self, sat_name, time_utc=None):
        """
        获取卫星位置

        Args:
            sat_name: 卫星名称
            time_utc: UTC时间（None表示当前时间）

        Returns:
            dict: 位置信息
        """
        if time_utc is None:
            t = self.ts.now()
        else:
            t = self.ts.from_datetime(time_utc)

        sat = self.satellites[sat_name]['object']
        geocentric = sat.at(t)
        subpoint = geocentric.subpoint()

        # 计算速度
        velocity = geocentric.velocity.km_per_s
        speed = np.linalg.norm(velocity)

        return {
            'node_name': sat_name,
            'node_type': 'satellite',
            'latitude': subpoint.latitude.degrees,
            'longitude': subpoint.longitude.degrees,
            'altitude_km': subpoint.elevation.km,
            'velocity_km_s': speed,
            'timestamp': t.utc_iso()
        }

    def get_aircraft_position(self, aircraft_name, time_utc=None):
        """
        获取飞机位置（简化的大圆航线插值）

        Args:
            aircraft_name: 飞机名称
            time_utc: UTC时间

        Returns:
            dict: 位置信息
        """
        if time_utc is None:
            t = self.ts.now()
            time_utc = t.utc_datetime()
        else:
            t = self.ts.from_datetime(time_utc)

        aircraft_data = self.aircraft[aircraft_name]
        state = self.aircraft_state[aircraft_name]

        # 初始化起始时间
        if state['start_time'] is None:
            state['start_time'] = time_utc

        # 计算飞行时间
        elapsed_sec = (time_utc - state['start_time']).total_seconds()

        # 计算起点和终点
        start = aircraft_data['start_location']
        end = aircraft_data['end_location']

        # 简化：使用线性插值（真实应该用大圆航线）
        # 计算总距离（粗略估算）
        lat_diff = end['latitude'] - start['latitude']
        lon_diff = end['longitude'] - start['longitude']
        total_distance_km = np.sqrt(lat_diff**2 + lon_diff**2) * 111  # 1度约111km

        # 计算行进距离
        distance_km = state['speed_m_s'] * elapsed_sec / 1000
        progress = min(distance_km / total_distance_km, 1.0)
        state['progress'] = progress

        # 插值计算当前位置
        current_lat = start['latitude'] + lat_diff * progress
        current_lon = start['longitude'] + lon_diff * progress

        state['current_lat'] = current_lat
        state['current_lon'] = current_lon

        return {
            'node_name': aircraft_name,
            'node_type': 'aircraft',
            'latitude': current_lat,
            'longitude': current_lon,
            'altitude_km': state['current_alt_km'],
            'velocity_km_s': state['speed_m_s'] / 1000,
            'progress': progress,
            'timestamp': t.utc_iso()
        }

    def get_ground_station_position(self, gs_name):
        """
        获取地面站位置（固定）

        Args:
            gs_name: 地面站名称

        Returns:
            dict: 位置信息
        """
        gs = self.ground_stations[gs_name]

        return {
            'node_name': gs_name,
            'node_type': 'ground_station',
            'latitude': gs['latitude'],
            'longitude': gs['longitude'],
            'altitude_km': gs['elevation_m'] / 1000,
            'velocity_km_s': 0.0,
            'timestamp': self.ts.now().utc_iso()
        }

    def calculate_distance(self, pos1, pos2):
        """
        计算两个位置之间的距离（使用球面距离公式）

        Args:
            pos1, pos2: 位置字典（包含lat, lon, altitude_km）

        Returns:
            float: 距离（km）
        """
        # 转换为弧度
        lat1 = np.radians(pos1['latitude'])
        lon1 = np.radians(pos1['longitude'])
        lat2 = np.radians(pos2['latitude'])
        lon2 = np.radians(pos2['longitude'])

        # 地球半径
        R = 6371  # km

        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        horizontal_distance = R * c

        # 考虑高度差
        alt_diff = pos2['altitude_km'] - pos1['altitude_km']
        distance = np.sqrt(horizontal_distance**2 + alt_diff**2)

        return distance

    def check_visibility(self, node1_name, node2_name, time_utc=None):
        """
        检查两个节点之间的可见性

        Args:
            node1_name: 节点1名称
            node2_name: 节点2名称
            time_utc: UTC时间

        Returns:
            dict: 可见性信息
        """
        if time_utc is None:
            t = self.ts.now()
            time_utc = t.utc_datetime()
        else:
            t = self.ts.from_datetime(time_utc)

        # 获取节点位置
        pos1 = self.get_node_position(node1_name, time_utc)
        pos2 = self.get_node_position(node2_name, time_utc)

        # 计算距离
        distance_km = self.calculate_distance(pos1, pos2)

        # 确定链路类型
        link_type = self.get_link_type(pos1['node_type'], pos2['node_type'])

        # 获取链路约束
        constraints = self.link_constraints.get(link_type, {})

        # 检查距离约束
        max_distance = constraints.get('max_distance_km', 10000)
        distance_ok = distance_km <= max_distance

        # 计算仰角（如果涉及地面站）
        elevation_deg = None
        elevation_ok = True

        if pos1['node_type'] == 'ground_station' or pos2['node_type'] == 'ground_station':
            # 简化：只检查最小仰角
            min_elevation = constraints.get('min_elevation_deg', 10)

            # 粗略估算仰角
            if pos1['node_type'] == 'ground_station':
                gs_pos = pos1
                other_pos = pos2
            else:
                gs_pos = pos2
                other_pos = pos1

            # 简化的仰角计算
            alt_diff = other_pos['altitude_km']
            horizontal_dist = distance_km
            elevation_deg = np.degrees(np.arctan2(alt_diff, horizontal_dist))

            elevation_ok = elevation_deg >= min_elevation

        # 计算传播延迟（光速）
        propagation_speed = self.network_params.get('propagation_speed_km_s', 300000)
        delay_ms = (distance_km / propagation_speed) * 1000

        # 判断可见性
        visible = distance_ok and elevation_ok

        return {
            'node1': node1_name,
            'node2': node2_name,
            'visible': visible,
            'distance_km': distance_km,
            'delay_ms': delay_ms,
            'elevation_deg': elevation_deg,
            'link_type': link_type,
            'timestamp': t.utc_iso()
        }

    def get_node_position(self, node_name, time_utc=None):
        """
        获取任意节点的位置

        Args:
            node_name: 节点名称
            time_utc: UTC时间

        Returns:
            dict: 位置信息
        """
        if node_name in self.satellites:
            return self.get_satellite_position(node_name, time_utc)
        elif node_name in self.aircraft:
            return self.get_aircraft_position(node_name, time_utc)
        elif node_name in self.ground_stations:
            return self.get_ground_station_position(node_name)
        else:
            raise ValueError(f"Unknown node: {node_name}")

    def get_link_type(self, type1, type2):
        """确定链路类型"""
        types = sorted([type1, type2])

        if types == ['satellite', 'satellite']:
            return 'inter_satellite_link'
        elif types == ['ground_station', 'satellite']:
            return 'satellite_ground_link'
        elif types == ['aircraft', 'satellite']:
            return 'satellite_aircraft_link'
        elif types == ['aircraft', 'ground_station']:
            return 'aircraft_ground_link'
        else:
            return 'unknown_link'

    def get_network_topology(self, time_utc=None):
        """
        获取完整网络拓扑

        Args:
            time_utc: UTC时间

        Returns:
            dict: 网络拓扑信息
        """
        if time_utc is None:
            t = self.ts.now()
            time_utc = t.utc_datetime()
        else:
            t = self.ts.from_datetime(time_utc)

        # 获取所有节点位置
        positions = {}

        for sat_name in self.satellites:
            positions[sat_name] = self.get_satellite_position(sat_name, time_utc)

        for aircraft_name in self.aircraft:
            positions[aircraft_name] = self.get_aircraft_position(aircraft_name, time_utc)

        for gs_name in self.ground_stations:
            positions[gs_name] = self.get_ground_station_position(gs_name)

        # 计算所有可能的链路
        all_nodes = list(positions.keys())
        links = {}

        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                link_name = f"{node1}-{node2}"
                vis = self.check_visibility(node1, node2, time_utc)
                links[link_name] = vis

        return {
            'timestamp': t.utc_iso(),
            'positions': positions,
            'links': links,
            'node_count': len(positions),
            'visible_link_count': sum(1 for link in links.values() if link['visible'])
        }

    def run_realtime_simulation(self, update_callback, interval_sec=10, duration_min=None):
        """
        实时仿真模式

        Args:
            update_callback: 回调函数，接收网络拓扑更新
            interval_sec: 更新间隔（秒）
            duration_min: 仿真时长（分钟，None表示无限）
        """
        print(f"[Simulator] 启动实时仿真")
        print(f"  - 更新间隔: {interval_sec} 秒")
        print(f"  - 仿真时长: {duration_min if duration_min else '无限'} 分钟")

        start_time = time.time()
        iteration = 0

        try:
            while True:
                iteration += 1

                # 获取当前拓扑
                topology = self.get_network_topology()

                # 调用回调函数
                update_callback(topology)

                # 显示简要信息
                print(f"\n[Iteration {iteration}] {topology['timestamp']}")
                print(f"  可见链路: {topology['visible_link_count']}/{len(topology['links'])}")

                # 检查是否达到时长限制
                if duration_min is not None:
                    elapsed_min = (time.time() - start_time) / 60
                    if elapsed_min >= duration_min:
                        print(f"\n[Simulator] 达到仿真时长 {duration_min} 分钟，停止")
                        break

                # 等待下一次更新
                time.sleep(interval_sec)

        except KeyboardInterrupt:
            print(f"\n[Simulator] 用户中断仿真")

        print(f"[Simulator] 仿真结束，总迭代: {iteration} 次")


def print_topology_summary(topology):
    """打印拓扑摘要（示例回调函数）"""
    print("\n" + "="*60)
    print(f"时间: {topology['timestamp']}")
    print("="*60)

    # 打印节点位置
    print("\n节点位置:")
    for node_name, pos in topology['positions'].items():
        print(f"  {node_name:15s} ({pos['node_type']:15s}): "
              f"({pos['latitude']:7.2f}°, {pos['longitude']:8.2f}°) "
              f"@ {pos['altitude_km']:7.1f} km")

    # 打印可见链路
    print("\n可见链路:")
    for link_name, link in topology['links'].items():
        if link['visible']:
            print(f"  {link_name:30s}: "
                  f"{link['distance_km']:7.1f} km, "
                  f"{link['delay_ms']:6.2f} ms"
                  + (f", 仰角 {link['elevation_deg']:.1f}°"
                     if link['elevation_deg'] is not None else ""))


if __name__ == '__main__':
    import sys

    # 默认配置文件路径
    config_file = '../configs/sagin_topology_config.json'

    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    print("="*60)
    print("SAGIN Orbit Simulator - 测试模式")
    print("="*60)

    # 创建仿真器
    simulator = SAGINOrbitSimulator(config_file)

    # 单次查询测试
    print("\n=== 单次查询测试 ===")
    topology = simulator.get_network_topology()
    print_topology_summary(topology)

    # 检查是否在交互式终端中运行
    import sys
    if sys.stdin.isatty():
        # 询问是否运行实时仿真
        print("\n是否运行实时仿真？(y/n): ", end='')
        try:
            response = input().strip().lower()
        except EOFError:
            response = 'n'

        if response == 'y':
            print("\n=== 启动实时仿真 ===")
            simulator.run_realtime_simulation(
                update_callback=print_topology_summary,
                interval_sec=10,
                duration_min=5  # 运行5分钟
            )
    else:
        print("\n[非交互模式] 跳过实时仿真测试")
