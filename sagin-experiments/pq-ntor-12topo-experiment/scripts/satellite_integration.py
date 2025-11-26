#!/usr/bin/env python3
"""
卫星轨道集成模块
整合satellite_orbit.py，为PQ-NTOR测试提供卫星位置和动态链路参数

作者: Claude Code
日期: 2025-11-24
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# 导入卫星轨道模块
SAGIN_EXP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SAGIN_EXP_DIR))

try:
    from satellite_orbit import SatelliteOrbit
except ImportError as e:
    print(f"❌ 无法导入satellite_orbit模块: {e}")
    print(f"   请确保文件存在: {SAGIN_EXP_DIR}/satellite_orbit.py")
    sys.exit(1)


class SatelliteLinkCalculator:
    """卫星链路参数计算器"""

    def __init__(self, use_static_snapshot=False, snapshot_time=None):
        """
        初始化卫星轨道计算器

        Args:
            use_static_snapshot: 是否使用静态快照（可重复测试）
            snapshot_time: 快照时间（datetime对象），None则使用默认通信窗口中点
        """
        print("🛰️  初始化卫星轨道计算器...")

        # 初始化SatelliteOrbit
        self.orbit = SatelliteOrbit()

        self.use_static_snapshot = use_static_snapshot
        self.snapshot_time = snapshot_time

        if use_static_snapshot:
            if snapshot_time is None:
                # 使用最佳通信窗口的中点作为快照时间
                if hasattr(self.orbit, 'best_window') and self.orbit.best_window:
                    window = self.orbit.best_window
                    duration = (window['end'] - window['start']).total_seconds()
                    self.snapshot_time = window['start'] + timedelta(seconds=duration / 2)
                    print(f"   使用通信窗口中点作为快照: {self.snapshot_time}")
                else:
                    # 使用epoch时间
                    self.snapshot_time = self.orbit.epoch
                    print(f"   使用epoch时间作为快照: {self.snapshot_time}")
            else:
                self.snapshot_time = snapshot_time
                print(f"   使用指定快照时间: {self.snapshot_time}")

            # 计算快照位置
            self.static_position = self.orbit.get_satellite_position_for_env(self.snapshot_time)
            self.static_elevation = self._calculate_elevation(self.static_position)
            self.static_distance = self._calculate_distance(self.static_position)

            print(f"   静态快照参数:")
            print(f"     位置 (ENU): [{self.static_position[0]:.1f}, {self.static_position[1]:.1f}, {self.static_position[2]:.1f}] m")
            print(f"     仰角: {self.static_elevation:.2f}°")
            print(f"     距离: {self.static_distance:.2f} km")

        print("   ✅ 卫星轨道计算器初始化完成")

    def get_satellite_state(self, test_time=None):
        """
        获取卫星状态

        Args:
            test_time: 测试时间（datetime对象），None则使用当前时间或快照时间

        Returns:
            dict: 卫星状态信息
        """
        if self.use_static_snapshot:
            # 使用静态快照
            return {
                'mode': 'static',
                'timestamp': self.snapshot_time.isoformat(),
                'position_enu_m': self.static_position,
                'elevation_deg': self.static_elevation,
                'distance_km': self.static_distance,
                'in_comm_window': self.static_elevation >= 10.0
            }
        else:
            # 动态计算
            if test_time is None:
                test_time = datetime.now(self.orbit.ts.utc)

            position = self.orbit.get_satellite_position_for_env(test_time)
            elevation = self._calculate_elevation(position)
            distance = self._calculate_distance(position)

            return {
                'mode': 'dynamic',
                'timestamp': test_time.isoformat(),
                'position_enu_m': position,
                'elevation_deg': elevation,
                'distance_km': distance,
                'in_comm_window': elevation >= 10.0
            }

    def calculate_propagation_delay(self, test_time=None):
        """
        计算电磁波传播延迟（基于卫星距离）

        Args:
            test_time: 测试时间

        Returns:
            float: 单向传播延迟（毫秒）
        """
        state = self.get_satellite_state(test_time)
        distance_m = state['distance_km'] * 1000

        # 光速: c = 3 * 10^8 m/s
        c = 3.0e8
        delay_seconds = distance_m / c
        delay_ms = delay_seconds * 1000

        return delay_ms

    def adjust_network_params_for_satellite(self, base_params, test_time=None):
        """
        根据卫星位置调整网络参数

        Args:
            base_params: 基础网络参数 dict
            test_time: 测试时间

        Returns:
            dict: 调整后的网络参数
        """
        state = self.get_satellite_state(test_time)

        # 计算传播延迟
        prop_delay_ms = self.calculate_propagation_delay(test_time)

        # 调整参数
        adjusted_params = base_params.copy()

        # 延迟 = 基础延迟 + 传播延迟
        adjusted_params['delay_ms'] = base_params.get('delay_ms', 0) + prop_delay_ms

        # 根据仰角调整丢包率（仰角越低，丢包越高）
        elevation = state['elevation_deg']
        if elevation < 10:
            loss_multiplier = 5.0  # 低仰角，高丢包
        elif elevation < 30:
            loss_multiplier = 2.0
        elif elevation < 60:
            loss_multiplier = 1.2
        else:
            loss_multiplier = 1.0  # 高仰角，正常丢包

        adjusted_params['loss_percent'] = base_params.get('loss_percent', 0) * loss_multiplier

        # 添加卫星状态信息
        adjusted_params['satellite_state'] = state

        return adjusted_params

    def _calculate_elevation(self, position_enu):
        """计算仰角（度）"""
        x, y, z = position_enu
        horizontal_distance = np.sqrt(x**2 + y**2)
        elevation_rad = np.arctan2(z, horizontal_distance)
        return np.degrees(elevation_rad)

    def _calculate_distance(self, position_enu):
        """计算距离（km）"""
        x, y, z = position_enu
        distance_m = np.sqrt(x**2 + y**2 + z**2)
        return distance_m / 1000.0

    def is_in_communication_window(self, test_time=None, min_elevation=10.0):
        """
        检查是否在通信窗口内

        Args:
            test_time: 测试时间
            min_elevation: 最小仰角要求（度）

        Returns:
            bool: 是否在通信窗口内
        """
        state = self.get_satellite_state(test_time)
        return state['elevation_deg'] >= min_elevation

    def get_next_communication_window(self, start_time=None, duration_hours=24):
        """
        获取下一个通信窗口

        Args:
            start_time: 开始搜索时间
            duration_hours: 搜索时长（小时）

        Returns:
            dict: 通信窗口信息，若无则返回None
        """
        if start_time is None:
            start_time = datetime.now(self.orbit.ts.utc)

        # 调用orbit的通信窗口计算
        windows = self.orbit.calculate_communication_windows(
            duration_hours=duration_hours,
            step_seconds=60
        )

        if not windows:
            return None

        # 返回第一个窗口
        return windows[0]

    def generate_test_time_slots(self, num_slots=30, use_comm_window=True):
        """
        生成测试时间槽

        Args:
            num_slots: 时间槽数量
            use_comm_window: 是否使用通信窗口

        Returns:
            list: 时间槽列表 [datetime, ...]
        """
        if use_comm_window:
            # 使用通信窗口
            if hasattr(self.orbit, 'communication_windows_by_region') and self.orbit.communication_windows_by_region:
                windows = self.orbit.communication_windows_by_region
                best_window = max(windows, key=lambda w: w['duration'])
            elif hasattr(self.orbit, 'best_window') and self.orbit.best_window:
                best_window = self.orbit.best_window
            else:
                print("   ⚠️  未找到通信窗口，使用默认时间段")
                return self._generate_default_time_slots(num_slots)

            start_time = best_window['start']
            end_time = best_window['end']
        else:
            # 使用默认时间段
            return self._generate_default_time_slots(num_slots)

        # 均匀分割时间窗口
        duration_seconds = (end_time - start_time).total_seconds()
        slot_duration = duration_seconds / num_slots

        time_slots = []
        for i in range(num_slots):
            slot_time = start_time + timedelta(seconds=i * slot_duration)
            time_slots.append(slot_time)

        return time_slots

    def _generate_default_time_slots(self, num_slots):
        """生成默认时间槽（从epoch开始）"""
        start_time = self.orbit.epoch
        slot_duration = 60  # 60秒间隔

        time_slots = []
        for i in range(num_slots):
            slot_time = start_time + timedelta(seconds=i * slot_duration)
            time_slots.append(slot_time)

        return time_slots


# ==================== 测试代码 ====================
def test_satellite_integration():
    """测试卫星轨道集成模块"""
    print("\n" + "=" * 70)
    print("  🛰️  测试卫星轨道集成模块")
    print("=" * 70)

    # 测试静态模式
    print("\n1️⃣  测试静态快照模式:")
    calc_static = SatelliteLinkCalculator(use_static_snapshot=True)

    state_static = calc_static.get_satellite_state()
    print(f"\n卫星状态:")
    print(f"  模式: {state_static['mode']}")
    print(f"  时间: {state_static['timestamp']}")
    print(f"  位置: [{state_static['position_enu_m'][0]:.1f}, "
          f"{state_static['position_enu_m'][1]:.1f}, "
          f"{state_static['position_enu_m'][2]:.1f}] m")
    print(f"  仰角: {state_static['elevation_deg']:.2f}°")
    print(f"  距离: {state_static['distance_km']:.2f} km")
    print(f"  通信窗口: {'✅ 是' if state_static['in_comm_window'] else '❌ 否'}")

    # 计算传播延迟
    delay = calc_static.calculate_propagation_delay()
    print(f"\n传播延迟: {delay:.3f} ms")

    # 调整网络参数
    base_params = {
        'delay_ms': 20,
        'bandwidth_mbps': 50,
        'loss_percent': 0.5
    }
    adjusted = calc_static.adjust_network_params_for_satellite(base_params)
    print(f"\n网络参数调整:")
    print(f"  基础延迟: {base_params['delay_ms']} ms")
    print(f"  调整后延迟: {adjusted['delay_ms']:.2f} ms")
    print(f"  基础丢包率: {base_params['loss_percent']}%")
    print(f"  调整后丢包率: {adjusted['loss_percent']:.3f}%")

    # 测试动态模式
    print("\n\n2️⃣  测试动态模式:")
    calc_dynamic = SatelliteLinkCalculator(use_static_snapshot=False)

    # 生成测试时间槽
    time_slots = calc_dynamic.generate_test_time_slots(num_slots=5)
    print(f"\n生成 {len(time_slots)} 个测试时间槽:")
    for i, slot_time in enumerate(time_slots):
        state = calc_dynamic.get_satellite_state(slot_time)
        print(f"  槽 {i+1}: {slot_time.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"仰角 {state['elevation_deg']:.2f}°, "
              f"距离 {state['distance_km']:.2f} km")

    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    test_satellite_integration()
