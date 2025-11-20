#!/usr/bin/env python3
"""
PQ-NTOR 卫星轨道集成测试
结合 Skyfield 轨道数据和真实握手性能测试
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from satellite_orbit import SatelliteOrbit

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class PQNTORSatelliteTest:
    """PQ-NTOR 卫星握手性能测试类"""

    def __init__(self):
        """初始化测试环境"""
        self.orbit = SatelliteOrbit()
        self.ground_station_pos = [0, 0, 0]  # 地面站位置 (原点)
        self.base_handshake_us = 49  # 真实C程序测量的握手时间(微秒)

    def calculate_network_delay(self, satellite_pos):
        """
        根据卫星位置计算网络延迟

        Args:
            satellite_pos: [x, y, z] 卫星ENU坐标 (米)

        Returns:
            distance_km: 通信距离 (公里)
            rtt_ms: 往返时延 (毫秒)
        """
        # 计算卫星到地面站的距离
        distance_m = np.sqrt(
            satellite_pos[0]**2 +
            satellite_pos[1]**2 +
            satellite_pos[2]**2
        )
        distance_km = distance_m / 1000

        # 光速传播延迟: c = 300,000 km/s = 300 km/ms
        light_speed_km_per_ms = 300
        rtt_ms = (2 * distance_km) / light_speed_km_per_ms

        return distance_km, rtt_ms

    def calculate_elevation_angle(self, satellite_pos):
        """
        计算卫星仰角

        Args:
            satellite_pos: [x, y, z] 卫星ENU坐标 (米)

        Returns:
            elevation_deg: 仰角 (度)
        """
        horizontal_dist = np.sqrt(satellite_pos[0]**2 + satellite_pos[1]**2)
        elevation_rad = np.arctan2(satellite_pos[2], horizontal_dist)
        return np.degrees(elevation_rad)

    def test_during_window(self, window, num_samples=30):
        """
        在一个通信窗口期间测试握手性能

        Args:
            window: 通信窗口字典 (包含start_time, end_time, duration_minutes)
            num_samples: 采样点数量

        Returns:
            DataFrame: 测试结果数据
        """
        start_time = window['start_time']
        end_time = window['end_time']
        duration_seconds = (end_time - start_time).total_seconds()

        # 生成时间采样点
        time_samples = [
            start_time + timedelta(seconds=i * duration_seconds / (num_samples - 1))
            for i in range(num_samples)
        ]

        results = []

        for sample_time in time_samples:
            # 获取卫星位置
            sat_pos = self.orbit.get_satellite_position_for_env(sample_time)

            # 计算网络参数
            distance_km, rtt_ms = self.calculate_network_delay(sat_pos)
            elevation_deg = self.calculate_elevation_angle(sat_pos)

            # 计算总握手时间 = PQ-NTOR握手 + 网络RTT
            base_handshake_ms = self.base_handshake_us / 1000  # 转换为毫秒
            total_handshake_ms = base_handshake_ms + rtt_ms

            # 计算通信开销 (网络延迟占比)
            overhead_percent = (rtt_ms / total_handshake_ms) * 100

            # 判断通信是否成功 (仰角 > 10度认为可靠)
            success = elevation_deg > 10

            # 记录结果
            results.append({
                'time': sample_time,
                'time_offset_sec': (sample_time - start_time).total_seconds(),
                'distance_km': distance_km,
                'elevation_deg': elevation_deg,
                'rtt_ms': rtt_ms,
                'base_handshake_ms': base_handshake_ms,
                'total_handshake_ms': total_handshake_ms,
                'overhead_percent': overhead_percent,
                'success': success,
                'sat_x_m': sat_pos[0],
                'sat_y_m': sat_pos[1],
                'sat_z_m': sat_pos[2]
            })

        return pd.DataFrame(results)

    def plot_results(self, df, window, save_path='pq_ntor_satellite_test_results.png'):
        """
        绘制测试结果图表

        Args:
            df: 测试结果DataFrame
            window: 通信窗口信息
            save_path: 图表保存路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f'PQ-NTOR 卫星握手性能测试\n'
            f'窗口时间: {window["start_time"].strftime("%H:%M:%S")} - '
            f'{window["end_time"].strftime("%H:%M:%S")} '
            f'(持续 {window["duration_minutes"]:.1f} 分钟)',
            fontsize=14, fontweight='bold'
        )

        # 子图1: 握手时间
        ax1 = axes[0, 0]
        ax1.plot(df['time_offset_sec'], df['total_handshake_ms'],
                 'b-', linewidth=2, label='总握手时间')
        ax1.axhline(y=df['base_handshake_ms'].iloc[0],
                    color='g', linestyle='--', linewidth=1.5,
                    label=f'PQ-NTOR基础握手 ({self.base_handshake_us}μs)')
        ax1.set_xlabel('时间偏移 (秒)', fontsize=11)
        ax1.set_ylabel('握手时间 (毫秒)', fontsize=11)
        ax1.set_title('握手时间变化曲线', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)

        # 子图2: 通信开销
        ax2 = axes[0, 1]
        ax2.plot(df['time_offset_sec'], df['overhead_percent'],
                 'r-', linewidth=2)
        ax2.set_xlabel('时间偏移 (秒)', fontsize=11)
        ax2.set_ylabel('网络延迟占比 (%)', fontsize=11)
        ax2.set_title('通信开销变化曲线', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(df['time_offset_sec'], 0, df['overhead_percent'],
                         alpha=0.2, color='red')

        # 子图3: 距离与仰角
        ax3 = axes[1, 0]
        ax3_twin = ax3.twinx()

        line1 = ax3.plot(df['time_offset_sec'], df['distance_km'],
                         'b-', linewidth=2, label='通信距离')
        ax3.set_xlabel('时间偏移 (秒)', fontsize=11)
        ax3.set_ylabel('距离 (公里)', fontsize=11, color='b')
        ax3.tick_params(axis='y', labelcolor='b')

        line2 = ax3_twin.plot(df['time_offset_sec'], df['elevation_deg'],
                              'orange', linewidth=2, label='仰角')
        ax3_twin.set_ylabel('仰角 (度)', fontsize=11, color='orange')
        ax3_twin.tick_params(axis='y', labelcolor='orange')
        ax3_twin.axhline(y=10, color='red', linestyle='--',
                         linewidth=1, alpha=0.7, label='最低可靠仰角')

        ax3.set_title('轨道参数变化曲线', fontsize=12, fontweight='bold')

        # 合并图例
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left', fontsize=9)
        ax3.grid(True, alpha=0.3)

        # 子图4: 成功率统计
        ax4 = axes[1, 1]
        success_rate = (df['success'].sum() / len(df)) * 100
        categories = ['成功', '失败']
        values = [df['success'].sum(), (~df['success']).sum()]
        colors = ['#4ade80', '#f87171']

        bars = ax4.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_ylabel('采样点数量', fontsize=11)
        ax4.set_title(f'通信成功率: {success_rate:.1f}%',
                      fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')

        # 在柱状图上显示数值
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n✅ 图表已保存: {save_path}")

        return fig

    def run_test(self, start_time=None, duration_minutes=10):
        """
        运行完整测试流程

        Args:
            start_time: 测试开始时间 (默认为当前时间)
            duration_minutes: 测试持续时间 (分钟)
        """
        if start_time is None:
            start_time = datetime.now()

        print("=" * 60)
        print("PQ-NTOR 卫星轨道集成测试")
        print("=" * 60)
        print(f"测试开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"基础握手时间: {self.base_handshake_us} μs (C程序实测)")
        print(f"测试持续时间: {duration_minutes} 分钟")
        print()

        # 模拟通信窗口
        window = {
            'start_time': start_time,
            'end_time': start_time + timedelta(minutes=duration_minutes),
            'duration_minutes': duration_minutes
        }

        print("正在进行握手性能测试...")
        df = self.test_during_window(window, num_samples=30)

        # 统计分析
        print("\n" + "=" * 60)
        print("测试结果统计")
        print("=" * 60)
        print(f"采样点数量: {len(df)}")
        print(f"通信距离范围: {df['distance_km'].min():.2f} - {df['distance_km'].max():.2f} km")
        print(f"仰角范围: {df['elevation_deg'].min():.2f}° - {df['elevation_deg'].max():.2f}°")
        print(f"RTT延迟范围: {df['rtt_ms'].min():.4f} - {df['rtt_ms'].max():.4f} ms")
        print(f"总握手时间范围: {df['total_handshake_ms'].min():.4f} - {df['total_handshake_ms'].max():.4f} ms")
        print(f"平均通信开销: {df['overhead_percent'].mean():.2f}%")
        print(f"通信成功率: {(df['success'].sum() / len(df)) * 100:.1f}%")

        # 保存数据
        csv_path = 'pq_ntor_satellite_test_data.csv'
        df.to_csv(csv_path, index=False)
        print(f"\n✅ 数据已保存: {csv_path}")

        # 绘制图表
        self.plot_results(df, window)

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

        return df


def main():
    """主函数"""
    # 创建测试实例
    tester = PQNTORSatelliteTest()

    # 运行测试 (10分钟窗口)
    results = tester.run_test(duration_minutes=10)

    print("\n提示:")
    print("- 生成的CSV文件包含所有测试数据点")
    print("- 生成的PNG图表展示了握手性能的时间序列变化")
    print("- 可以修改 duration_minutes 参数来测试不同时长的通信窗口")


if __name__ == '__main__':
    main()
