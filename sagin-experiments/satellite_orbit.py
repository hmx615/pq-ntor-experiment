import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, wgs84, EarthSatellite, utc
from skyfield.elementslib import osculating_elements_of
import matplotlib.pyplot as plt

class SatelliteOrbit:
    def __init__(self):
        # 地球参数
        self.earth_radius = 6378.137  # 地球半径(km)
        self.earth_mu = 3.986004418e5  # 地球引力常数(km³/s²)
        
        # 卫星轨道参数
        self.a = 7190.14  # 半长轴(km) - 对应高度约800km
        self.e = 0.001  # 偏心率
        self.i = np.radians(49.974)  # 轨道倾角(弧度)
        self.omega = np.radians(79.787)  # 近地点幅角(弧度)
        self.Omega = np.radians(305.816)  # 升交点赤经(弧度)
        self.M0 = np.radians(280.463)  # 初始平近点角(弧度)
        
        # 初始历元
        self.epoch = datetime(2025, 3, 9, 0, 0, 0, tzinfo=utc)
        
        # 地面区域参数
        self.region_corner_lat = 17.9043
        self.region_corner_lon = 47.1306
        self.region_width = 60.0  # km
        self.region_height = 60.0  # km
        
        # 计算区域中心
        self.region_center_lat = self.region_corner_lat + (0.5 * self.region_height) / 111.0
        self.region_center_lon = self.region_corner_lon + (0.5 * self.region_width) / (111.0 * np.cos(np.radians(self.region_center_lat)))
        
        # 使用区域中心作为观测点
        self.observer_lat = self.region_center_lat
        self.observer_lon = self.region_center_lon
        
        # 1. 首先设置Skyfield对象
        self._setup_skyfield()
        
        # 2. 计算通信窗口，并选择最佳窗口
        self.best_window = self.select_best_overhead_window()
        
        # 3. 修改：不移动观测区域，保持(0,0)为原点
        # self.set_observation_region()  # 注释掉或删除此行
        
        # 4. 先分析区域中心点的通信窗口
        print("\n首先分析区域中心点的通信窗口...")
        center_windows = self.analyze_center_visibility(min_elevation=10.0)
        
        # 5. 分析整个区域的通信窗口
        if len(center_windows) > 0:
            # 找到最佳中心窗口时间点进行仰角分布可视化
            best_center_window = max(center_windows, key=lambda w: w['duration'])
            best_time = best_center_window['start_time'] + timedelta(seconds=best_center_window['duration']/2)
            print(f"\n在中心点最佳可见时间 {best_time} 可视化仰角分布...")
            self.visualize_elevation_map(best_time)
            
            # 使用中心窗口的时间范围分析激活小区
            print("\n使用中心窗口时间范围分析激活小区...")
            active_windows = self.analyze_region_visibility(
                min_elevation=10.0, 
                active_cells_only=True,
                start_time=best_center_window['start_time'] - timedelta(minutes=1),
                end_time=best_center_window['end_time'] + timedelta(minutes=1)
            )
            
            # 分析窗口内的仰角变化
            self.analyze_elevation_during_window(best_center_window)
        else:
            # 如果中心点没有窗口，尝试分析更大范围的时间
            print("\n中心点没有找到通信窗口，尝试整个时间范围...")
            self.analyze_region_visibility(min_elevation=10.0, active_cells_only=True)
    
    def _setup_skyfield(self):
        """设置Skyfield对象，用于通信窗口计算"""
        # 计算轨道周期(分钟)和平均运动(每天圈数)
        period_seconds = 2 * np.pi * np.sqrt(self.a**3 / self.earth_mu)
        period_minutes = period_seconds / 60
        mean_motion = 1440 / period_minutes  # 每天圈数
        
        print(f"轨道信息: 半长轴={self.a}km, 高度≈{self.a-self.earth_radius:.1f}km")
        print(f"轨道周期: {period_minutes:.2f}分钟, 平均运动: {mean_motion:.4f}圈/天")
        
        self.line1 = f'1 57795U 23135D   25067.76655111  .00000709  00000-0  38421-3 0  9996'
        self.line2 = f'2 57795  49.9742 310.5414 0014096  75.8315 284.4162 14.22760140 78354'
        
        print("使用以下TLE数据:")
        print(self.line1)
        print(self.line2)
        
        # 加载时间尺度和创建卫星、观测点
        self.ts = load.timescale()
        self.satellite = EarthSatellite(self.line1, self.line2, name='Simulation', ts=self.ts)
        self.observer = wgs84.latlon(self.region_center_lat, self.region_center_lon)
        
        # 验证TLE是否对应预期轨道
        t = self.ts.from_datetime(self.epoch)
        geocentric = self.satellite.at(t)
        elements = osculating_elements_of(geocentric)
        print(f"\nTLE验证 - 实际轨道参数:")
        print(f"半长轴: {elements.semi_major_axis.km:.2f} km")
        print(f"偏心率: {elements.eccentricity:.6f}")
        print(f"轨道倾角: {elements.inclination.degrees:.2f} 度")
        print(f"观测点: 纬度={self.region_center_lat:.4f}, 经度={self.region_center_lon:.4f}")
    
    # def calculate_position(self, time):
    #     """计算指定时间的卫星位置(通过Skyfield)"""
    #     # 如果时间没有时区信息，添加UTC时区
    #     if time.tzinfo is None:
    #         time = time.replace(tzinfo=utc)
            
    #     # 使用Skyfield计算位置
    #     t = self.ts.from_datetime(time)
    #     geocentric = self.satellite.at(t)
        
    #     # 获取ECI坐标(km)
    #     position = geocentric.position.km
    #     x_eci, y_eci, z_eci = position
        
    #     return x_eci, y_eci, z_eci
    
    def calculate_communication_windows(self, duration_hours=24, step_seconds=60):
        """计算卫星与目标区域的通信窗口(通过Skyfield)"""
        windows = []
        
        # 设置时间范围
        start_time = self.epoch
        end_time = start_time + timedelta(hours=duration_hours)
        
        print(f"计算从 {start_time} 到 {end_time} 的通信窗口...")
        
        # 使用Skyfield的find_events方法找出升降事件
        t0 = self.ts.from_datetime(start_time)
        t1 = self.ts.from_datetime(end_time)
        times, events = self.satellite.find_events(self.observer, t0, t1, altitude_degrees=5.0)
        
        if len(times) > 0:
            # 处理Skyfield找到的事件
            current_window = {'start': None, 'end': None, 'max_elevation_time': None}
            
            for time, event in zip(times, events):
                event_name = ['升起', '最高点', '落下'][event]
                dt = time.utc_datetime()
                print(f"{dt} - {event_name}")
                
                if event == 0:  # 升起
                    current_window['start'] = dt
                elif event == 1:  # 最高点
                    current_window['max_elevation_time'] = dt
                elif event == 2:  # 落下
                    if current_window['start'] is not None:
                        current_window['end'] = dt
                        duration = (current_window['end'] - current_window['start']).total_seconds()
                        print(f"通信窗口: {current_window['start']} 到 {current_window['end']}, 持续时间: {duration:.2f} 秒")
                        windows.append(current_window.copy())
                        current_window = {'start': None, 'end': None, 'max_elevation_time': None}
        
        return windows
    
    def get_satellite_position_for_env(self, time):
        """获取卫星位置，用于Envir.py中的通信性能计算"""
        # 如果时间没有时区信息，添加UTC时区
        if time.tzinfo is None:
            time = time.replace(tzinfo=utc)
            
        # 计算卫星在地心坐标系中的位置
        t = self.ts.from_datetime(time)
        geocentric = self.satellite.at(t)
        
        # 计算相对于观测点的位置
        topocentric = geocentric - self.observer.at(t)
        alt, az, distance = topocentric.altaz()
        
        # 转换为ENU坐标(东北天)
        e = distance.km * np.sin(np.radians(az.degrees)) * np.cos(np.radians(alt.degrees))
        n = distance.km * np.cos(np.radians(az.degrees)) * np.cos(np.radians(alt.degrees)) 
        u = distance.km * np.sin(np.radians(alt.degrees))
        
        # 转换为米作为单位
        return [e * 1000, n * 1000, u * 1000]  # 返回[x, y, z]，单位米

    def select_best_overhead_window(self):
        """选择最佳过顶窗口（高度角最大的窗口）"""
        windows = self.calculate_communication_windows()
        
        # 找出每个窗口的最大高度角
        max_elevations = []
        for window in windows:
            t = self.ts.from_datetime(window['start'])
            difference = self.satellite - self.observer
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            max_elevations.append(alt.degrees)
        
        # 选择高度角最大的窗口
        best_window_index = np.argmax(max_elevations)
        return windows[best_window_index]

  


    def set_observation_region(self):
        """设置观测区域为卫星最佳过顶点下方的区域"""
        # 找到高度角最大的窗口和时刻
        windows = self.calculate_communication_windows()
        max_elevation = -1
        best_window = None
        best_time = None
        
        for window in windows:
            # 使用窗口的最高点时刻
            if window['max_elevation_time'] is not None:
                t = self.ts.from_datetime(window['max_elevation_time'])
                difference = self.satellite - self.observer
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees > max_elevation:
                    max_elevation = alt.degrees
                    best_window = window
                    best_time = window['max_elevation_time']
        
        # 保存最佳窗口信息
        self.best_window = best_window
        
        # 获取该时刻的卫星地面投影点
        t = self.ts.from_datetime(best_time)
        geocentric = self.satellite.at(t)
        subpoint = geocentric.subpoint()
        
        # 设置60km×60km的观测区域，以地面投影点为中心
        self.region_center_lat = subpoint.latitude.degrees
        self.region_center_lon = subpoint.longitude.degrees
        
        # 计算区域边界
        lat_delta = 30.0 / 111.0  # 30km
        lon_delta = 30.0 / (111.0 * np.cos(np.radians(self.region_center_lat)))
        
        self.region_corner_lat = self.region_center_lat - lat_delta
        self.region_corner_lon = self.region_center_lon - lon_delta
        
        print(f"\n设置观测区域:")
        print(f"最佳观测时刻: {best_time}")
        print(f"最大高度角: {max_elevation:.2f}度")
        print(f"区域中心点: 纬度={self.region_center_lat:.4f}, 经度={self.region_center_lon:.4f}")
        print(f"区域左下角: 纬度={self.region_corner_lat:.4f}, 经度={self.region_corner_lon:.4f}")
        
        # 关键修改: 更新observer以使用新的区域中心
        # self.observer = wgs84.latlon(self.region_center_lat, self.region_center_lon)

    def analyze_region_visibility(self, min_elevation=10.0, active_cells_only=False, start_time=None, end_time=None):
        """
        分析整个区域（所有或激活小区）与卫星的通信窗口
        参数:
            min_elevation: 最小仰角要求（度）
            active_cells_only: 是否只分析激活的小区
            start_time: 自定义分析开始时间
            end_time: 自定义分析结束时间
        """
        print(f"\n===== 分析区域的卫星通信窗口 =====")
        print(f"最小仰角要求: {min_elevation}°")
        
        # 获取Envir.py中定义的小区中心坐标
        cell_centers_enu = []
        # 从Envir.py中复制小区布局信息
        R = 15000  # 波束半径15km
        distance = 1.7 * R
        
        # 按Envir.py中的小区布局生成坐标
        # 第1行 (顶部3个)
        cell_centers_enu.append((-distance, distance*1.8))
        cell_centers_enu.append((0, distance*1.8))
        cell_centers_enu.append((distance, distance*1.8))
        
        # 第2行 (中上4个)
        cell_centers_enu.append((-distance*1.5, distance*0.9))
        cell_centers_enu.append((-distance/2, distance*0.9))
        cell_centers_enu.append((distance/2, distance*0.9))
        cell_centers_enu.append((distance*1.5, distance*0.9))
        
        # 第3行 (中下3个)
        cell_centers_enu.append((-distance, 0))
        cell_centers_enu.append((0, 0))  # 中心点
        cell_centers_enu.append((distance, 0))
        
        # 第4行 (底部2个)
        cell_centers_enu.append((-distance/2, -distance*0.9))
        cell_centers_enu.append((distance/2, -distance*0.9))
        
        # 只保留激活的小区中心
        if active_cells_only:
            # 假设激活的小区为1, 6, 11 (对应索引0, 5, 10)
            active_indices = [0, 5, 10]
            cell_centers_enu = [cell_centers_enu[i] for i in active_indices]
            print(f"仅分析 {len(cell_centers_enu)} 个激活小区中心 (索引 {active_indices})")
        
        # 设置时间范围
        if start_time is None:
            start_time = self.epoch - timedelta(hours=24)
        if end_time is None:
            end_time = self.epoch + timedelta(hours=24)
        
        print(f"分析时间范围: {start_time} 到 {end_time}")
        
        # 以较小的步长采样卫星位置
        time_step = timedelta(seconds=30)  # 增大步长提高速度
        current_time = start_time
        
        # 用于存储通信窗口的变量
        communication_start = None
        was_communicating = False
        communication_windows = []
        
        print("\n开始分析每个时刻的通信状态...\n")
        
        while current_time <= end_time:
            # 获取卫星位置
            satellite_pos = self.get_satellite_position_for_env(current_time)
            
            # 检查区域中每个小区中心的仰角
            min_cell_elevation = 90.0  # 初始化为最大可能值
            
            for cell_center in cell_centers_enu:
                # 计算从小区中心到卫星的向量
                dx = satellite_pos[0] - cell_center[0]
                dy = satellite_pos[1] - cell_center[1]
                dz = satellite_pos[2]  # Z轴是高度
                
                # 计算水平距离和仰角
                horizontal_distance = np.sqrt(dx*dx + dy*dy)
                elevation_angle = np.degrees(np.arctan2(dz, horizontal_distance))
                
                # 更新区域内最小仰角
                if elevation_angle < min_cell_elevation:
                    min_cell_elevation = elevation_angle
            
            # 检查是否满足最小仰角要求
            is_communicating = min_cell_elevation >= min_elevation
            
            # 通信状态变化检测
            if is_communicating and not was_communicating:
                # 通信开始
                communication_start = current_time
                print(f"通信开始: {current_time}, 最小仰角: {min_cell_elevation:.2f}°")
                print(f"卫星位置: [{satellite_pos[0]:.2f}, {satellite_pos[1]:.2f}, {satellite_pos[2]:.2f}] m")
            elif not is_communicating and was_communicating:
                # 通信结束
                duration = (current_time - communication_start).total_seconds()
                print(f"通信结束: {current_time}, 持续: {duration:.1f}秒 ({duration/60:.1f}分钟)")
                print(f"卫星位置: [{satellite_pos[0]:.2f}, {satellite_pos[1]:.2f}, {satellite_pos[2]:.2f}] m\n")
                
                # 记录此通信窗口
                window = {
                    'start_time': communication_start,
                    'end_time': current_time,
                    'duration': duration,
                    'start_position': self.get_satellite_position_for_env(communication_start),
                    'end_position': satellite_pos
                }
                communication_windows.append(window)
                communication_start = None
            
            # 更新通信状态
            was_communicating = is_communicating
            
            # 增加时间
            current_time += time_step
        
        # 如果结束时仍在通信，记录最后一个窗口
        if was_communicating:
            duration = (current_time - communication_start).total_seconds()
            window = {
                'start_time': communication_start,
                'end_time': current_time,
                'duration': duration,
                'start_position': self.get_satellite_position_for_env(communication_start),
                'end_position': self.get_satellite_position_for_env(current_time)
            }
            communication_windows.append(window)
            
            print(f"通信持续到分析结束: {current_time}, 持续: {duration:.1f}秒 ({duration/60:.1f}分钟)")
            print(f"卫星位置: [{window['end_position'][0]:.2f}, {window['end_position'][1]:.2f}, {window['end_position'][2]:.2f}] m\n")
        
        # 打印通信窗口总结
        if not communication_windows:
            print("在分析时间段内没有找到满足仰角要求的通信窗口")
        else:
            print("\n===== 通信窗口总结 =====")
            print(f"找到 {len(communication_windows)} 个通信窗口:")
            
            for i, window in enumerate(communication_windows):
                print(f"\n窗口 {i+1}:")
                print(f"开始时间: {window['start_time']}")
                print(f"结束时间: {window['end_time']}")
                print(f"持续时间: {window['duration']:.1f} 秒 ({window['duration']/60:.1f} 分钟)")
                print(f"开始位置: [{window['start_position'][0]:.2f}, {window['start_position'][1]:.2f}, {window['start_position'][2]:.2f}] m")
                print(f"结束位置: [{window['end_position'][0]:.2f}, {window['end_position'][1]:.2f}, {window['end_position'][2]:.2f}] m")
                
                # 显示该窗口是否适合当前仿真
                suitable = 600 <= window['duration'] <= 1800  # 10-30分钟
                print(f"适合仿真: {'是' if suitable else '否'}")
        
        # 保存通信窗口，供其他方法使用
        self.communication_windows_by_region = communication_windows
        return communication_windows

    # 
    def print_custom_time_slots(self):
        """打印特定时间段的卫星位置信息"""
        # 检查是否有通信窗口
        if hasattr(self, 'communication_windows_by_region') and self.communication_windows_by_region:
            # 使用找到的最佳通信窗口
            best_window = max(self.communication_windows_by_region, key=lambda w: w['duration'])
            
            # 设置时间范围为找到的窗口
            start_time = best_window['start_time']
            end_time = best_window['end_time']
            
            print(f"\n使用找到的最佳通信窗口: 从 {start_time} 到 {end_time}, 持续 {best_window['duration']/60:.1f} 分钟")
        else:
            # 使用原来的特定时间段
            start_time = datetime(2025, 3, 9, 17, 2, 10, tzinfo=utc)
            end_time = datetime(2025, 3, 9, 17, 2, 40, tzinfo=utc)
            print(f"\n使用默认时间段: 从 {start_time} 到 {end_time}")
        
        # 计算持续时间并分成30个时间槽
        duration_seconds = (end_time - start_time).total_seconds()
        slots = 30
        slot_seconds = duration_seconds / slots
        
        print(f"\n=== 特定时间段的卫星位置 ({start_time} 到 {end_time}) ===")
        print(f"总持续时间: {duration_seconds}秒, 分为{slots}个时间槽, 每个槽{slot_seconds}秒")
        
        for i in range(slots):
            # 计算时间槽开始时间
            slot_time = start_time + timedelta(seconds=i * slot_seconds)
            
            # 计算时间槽开始时的卫星位置
            pos = self.get_satellite_position_for_env(slot_time)
            distance = np.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2) / 1000
            elevation = np.degrees(np.arcsin(pos[2] / np.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)))
            
            print(f"\n时间槽 {i+1}: {slot_time}")
            print(f"  卫星ENU坐标 = [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}] (米)")
            print(f"  与观测点距离: {distance:.2f} km")
            print(f"  高度角: {elevation:.2f} 度")
            
            # 计算20毫秒后的卫星位置
            delay_time = slot_time + timedelta(milliseconds=20)
            pos_delay = self.get_satellite_position_for_env(delay_time)
            
            print(f"  延迟20ms后ENU坐标 = [{pos_delay[0]:.2f}, {pos_delay[1]:.2f}, {pos_delay[2]:.2f}] (米)")
            
            # 计算位置变化
            dx = pos_delay[0] - pos[0]
            dy = pos_delay[1] - pos[1]
            dz = pos_delay[2] - pos[2]
            
            print(f"  20ms内位置变化: [{dx:.2f}, {dy:.2f}, {dz:.2f}] (米)")
        
        # 生成用于Envir.py的卫星位置列表
        print("\n\n用于Envir.py的卫星位置列表：")
        print("self.satellite_positions = [")
        for i in range(slots):
            slot_time = start_time + timedelta(seconds=i * slot_seconds)
            pos = self.get_satellite_position_for_env(slot_time)
            print(f"    [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}],  # 时间槽{i+1}")
        print("]")
        
        # 生成延迟20ms的位置列表
        print("\nself.satellite_next_positions = [")
        for i in range(slots):
            slot_time = start_time + timedelta(seconds=i * slot_seconds)
            delay_time = slot_time + timedelta(milliseconds=20)
            pos = self.get_satellite_position_for_env(delay_time)
            print(f"    [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}],  # 时间槽{i+1}")
        print("]")

    def analyze_center_visibility(self, min_elevation=10.0):
        """分析区域中心点的卫星通信窗口"""
        print(f"\n===== 分析区域中心点(0,0)的卫星通信窗口 =====")
        print(f"最小仰角要求: {min_elevation}°")
        
        # 设置时间范围，更宽泛以确保捕获完整通信窗口
        start_time = self.epoch - timedelta(hours=24)
        end_time = self.epoch + timedelta(hours=24)
        time_step = timedelta(seconds=30)  # 增大步长提高速度
        current_time = start_time
        
        # 跟踪通信窗口
        communication_windows = []
        communication_start = None
        was_communicating = False
        center_elevations = []  # 记录中心点的仰角变化
        
        while current_time <= end_time:
            satellite_pos = self.get_satellite_position_for_env(current_time)
            
            # 计算中心点(0,0)的仰角
            dx = satellite_pos[0]  # 中心点是(0,0)
            dy = satellite_pos[1]
            dz = satellite_pos[2]
            
            horizontal_distance = np.sqrt(dx*dx + dy*dy)
            elevation_angle = np.degrees(np.arctan2(dz, horizontal_distance))
            
            # 记录仰角数据用于后续分析
            center_elevations.append((current_time, elevation_angle))
            
            is_communicating = elevation_angle >= min_elevation
            
            # 记录通信窗口
            if is_communicating and not was_communicating:
                communication_start = current_time
                print(f"中心点通信开始: {current_time}, 仰角: {elevation_angle:.2f}°")
                print(f"卫星位置: [{satellite_pos[0]:.2f}, {satellite_pos[1]:.2f}, {satellite_pos[2]:.2f}] m")
            elif not is_communicating and was_communicating:
                duration = (current_time - communication_start).total_seconds()
                print(f"中心点通信结束: {current_time}, 持续: {duration:.1f}秒 ({duration/60:.1f}分钟)")
                print(f"卫星位置: [{satellite_pos[0]:.2f}, {satellite_pos[1]:.2f}, {satellite_pos[2]:.2f}] m\n")
                communication_windows.append({
                    'start_time': communication_start,
                    'end_time': current_time,
                    'duration': duration,
                    'start_position': self.get_satellite_position_for_env(communication_start),
                    'end_position': satellite_pos
                })
                communication_start = None
            
            was_communicating = is_communicating
            current_time += time_step
        
        # 处理最后一个窗口
        if was_communicating:
            duration = (current_time - communication_start).total_seconds()
            print(f"中心点通信持续到分析结束: {current_time}, 持续: {duration:.1f}秒 ({duration/60:.1f}分钟)")
            print(f"卫星位置: [{satellite_pos[0]:.2f}, {satellite_pos[1]:.2f}, {satellite_pos[2]:.2f}] m\n")
            communication_windows.append({
                'start_time': communication_start,
                'end_time': current_time,
                'duration': duration,
                'start_position': self.get_satellite_position_for_env(communication_start),
                'end_position': satellite_pos
            })
        
        # 打印结果摘要
        if communication_windows:
            print(f"\n找到 {len(communication_windows)} 个中心点通信窗口")
            for i, window in enumerate(communication_windows):
                print(f"窗口 {i+1}: 开始于 {window['start_time']}, 持续 {window['duration']:.1f} 秒 ({window['duration']/60:.1f} 分钟)")
                
                # 如果窗口持续时间适合仿真，标记出来
                if 600 <= window['duration'] <= 1800:  # 10-30分钟
                    print(f"  ** 适合仿真的窗口 **")
                    print(f"  开始位置: [{window['start_position'][0]:.2f}, {window['start_position'][1]:.2f}, {window['start_position'][2]:.2f}] m")
                    print(f"  结束位置: [{window['end_position'][0]:.2f}, {window['end_position'][1]:.2f}, {window['end_position'][2]:.2f}] m")
        else:
            print("中心点没有找到满足仰角要求的通信窗口")
            
            # 如果没有找到窗口，显示最大仰角时刻
            if center_elevations:
                max_elevation_time, max_elevation = max(center_elevations, key=lambda x: x[1])
                print(f"中心点最大仰角: {max_elevation:.2f}° 发生在 {max_elevation_time}")
        
        return communication_windows

    def visualize_elevation_map(self, timestamp):
        """可视化特定时刻区域内的仰角分布"""
        # 获取卫星位置
        satellite_pos = self.get_satellite_position_for_env(timestamp)
        
        # 设置中文字体 - 解决中文显示问题
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用黑体显示中文
        plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
        
        # 创建网格 - 缩小范围以更好地显示小区区域
        x = np.linspace(-45000, 45000, 100)  
        y = np.linspace(-45000, 45000, 100)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)
        
        # 计算每个点的仰角
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                dx = satellite_pos[0] - X[i,j]
                dy = satellite_pos[1] - Y[i,j]
                dz = satellite_pos[2]
                horizontal_distance = np.sqrt(dx*dx + dy*dy)
                Z[i,j] = np.degrees(np.arctan2(dz, horizontal_distance))
        
        # 绘制仰角热图
        plt.figure(figsize=(12, 10))
        elevation_map = plt.contourf(X, Y, Z, levels=20, cmap='jet')
        cbar = plt.colorbar(elevation_map, label='仰角 (度)')
        cbar.ax.tick_params(labelsize=10)  # 调整colorbar标签大小
        
        # 绘制小区中心
        R = 15000
        distance = 1.7 * R
        cell_centers = [
            (-distance, distance*1.8), (0, distance*1.8), (distance, distance*1.8),
            (-distance*1.5, distance*0.9), (-distance/2, distance*0.9), 
            (distance/2, distance*0.9), (distance*1.5, distance*0.9),
            (-distance, 0), (0, 0), (distance, 0),
            (-distance/2, -distance*0.9), (distance/2, -distance*0.9)
        ]
        
        # 激活的小区
        active_indices = [0, 5, 10]  # 假设激活的小区为1, 6, 11
        
        # 绘制小区边界圆 - 更清晰地展示小区范围
        for i, (cx, cy) in enumerate(cell_centers):
            if i in active_indices:
                # 绘制激活小区的圆
                circle = plt.Circle((cx, cy), R, fill=False, edgecolor='red', linewidth=2)
                plt.gca().add_patch(circle)
                plt.plot(cx, cy, 'wo', markersize=8, markeredgecolor='r')
                plt.text(cx, cy, f'C{i+1}', color='white', fontweight='bold', fontsize=12)
            else:
                # 绘制非激活小区的圆
                circle = plt.Circle((cx, cy), R, fill=False, edgecolor='white', linewidth=1, alpha=0.7) 
                plt.gca().add_patch(circle)
                plt.plot(cx, cy, 'wo', markersize=5, alpha=0.7)
                plt.text(cx, cy, f'C{i+1}', color='white', alpha=0.7, fontsize=10)
        
        # 手动绘制常用仰角值的等高线 - 避免'No contour levels'警告
        min_angle = np.min(Z)
        max_angle = np.max(Z)
        print(f"区域仰角范围: {min_angle:.1f}° - {max_angle:.1f}°")
        
        # 只绘制在数据范围内的等高线
        contour_levels = [angle for angle in [5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 75.0] if min_angle <= angle <= max_angle]
        if contour_levels:
            plt.contour(X, Y, Z, levels=contour_levels, colors='k', linewidths=1.0)
            plt.clabel(plt.contour(X, Y, Z, levels=contour_levels, colors='k', linewidths=0.5), 
                      inline=True, fontsize=9, fmt='%.0f°')
        
        # 添加卫星投影点
        sat_proj_x = satellite_pos[0]
        sat_proj_y = satellite_pos[1]
        plt.plot(sat_proj_x, sat_proj_y, 'rx', markersize=12)
        plt.text(sat_proj_x + 2000, sat_proj_y + 2000, '卫星星下点', color='r', fontweight='bold', fontsize=12)
        
        # 计算中心点仰角 - 添加详细信息
        center_elevation = np.degrees(np.arctan2(satellite_pos[2], 
                                               np.sqrt(satellite_pos[0]**2 + satellite_pos[1]**2)))
        
        # 标题和轴标签
        plt.title(f'区域仰角分布 ({timestamp})\n'
                  f'卫星高度: {satellite_pos[2]/1000:.1f} km, 中心点仰角: {center_elevation:.2f}°', 
                  fontsize=14)
        plt.xlabel('X (m)', fontsize=12)
        plt.ylabel('Y (m)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        
        # 缩小显示范围以聚焦在小区区域 - 调整此处可改变显示的区域大小
        margin = 1.2 * distance * 1.8  # 略大于小区布局
        plt.xlim(-margin, margin)
        plt.ylim(-margin, margin)
        
        # 保存并显示图像
        filename = f'elevation_map_{timestamp.strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"图像已保存为: {filename}")
        plt.show()

    def analyze_elevation_during_window(self, window):
        """分析整个通信窗口期间的仰角变化"""
        start_time = window['start_time']
        end_time = window['end_time']
        duration = window['duration']
        
        # 创建时间点
        num_points = 20  # 采样点数量
        time_step = duration / (num_points - 1)
        
        times = []
        elevations = []
        
        # 计算每个时间点的仰角
        print("\n分析通信窗口内的仰角变化:")
        print(f"窗口开始: {start_time}, 结束: {end_time}, 持续: {duration/60:.1f}分钟")
        
        for i in range(num_points):
            current_time = start_time + timedelta(seconds=i * time_step)
            pos = self.get_satellite_position_for_env(current_time)
            
            # 计算中心点仰角
            center_elevation = np.degrees(np.arctan2(pos[2], np.sqrt(pos[0]**2 + pos[1]**2)))
            
            times.append(current_time)
            elevations.append(center_elevation)
            
            # 输出几个关键点
            if i == 0 or i == num_points//2 or i == num_points-1:
                print(f"时间: {current_time}, 仰角: {center_elevation:.2f}°")
        
        # 绘制仰角变化曲线
        plt.figure(figsize=(10, 6))
        time_minutes = [(t - start_time).total_seconds()/60 for t in times]
        plt.plot(time_minutes, elevations, 'b-', linewidth=2)
        plt.scatter(time_minutes, elevations, color='red', s=30)
        
        plt.title(f'通信窗口内的仰角变化 ({start_time.strftime("%Y-%m-%d %H:%M")} 至 {end_time.strftime("%H:%M")})')
        plt.xlabel('窗口内时间 (分钟)')
        plt.ylabel('仰角 (度)')
        plt.grid(True)
        plt.axhline(y=5.0, color='r', linestyle='--', label='最小仰角要求 (10°)')
        plt.legend()
        
        # 显示最大仰角
        max_idx = np.argmax(elevations)
        max_elev = elevations[max_idx]
        max_time = times[max_idx]
        plt.annotate(f'最大仰角: {max_elev:.2f}°',
                    xy=(time_minutes[max_idx], max_elev),
                    xytext=(time_minutes[max_idx]-1, max_elev+5),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
        
        plt.savefig(f'elevation_curve_{start_time.strftime("%Y%m%d_%H%M")}.png', dpi=300)
        print(f"仰角曲线图已保存")
        plt.show()
        
        return times, elevations

#测试代码
if __name__ == "__main__":
    orbit = SatelliteOrbit()
    
    # 打印自定义时间槽
    orbit.print_custom_time_slots() 