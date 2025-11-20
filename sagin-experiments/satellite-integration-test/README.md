# PQ-NTOR 卫星轨道集成测试

**创建日期**: 2025-11-20
**目的**: 整合 Skyfield 卫星轨道数据与 PQ-NTOR 握手性能测试

---

## 文件说明

### 测试脚本
- **pq_ntor_satellite_test.py** (11 KB)
  主测试脚本，结合卫星轨道数据和 PQ-NTOR 握手时间进行性能分析

### 测试结果数据
- **pq_ntor_satellite_test_data.csv** (6 KB)
  完整测试数据，包含 30 个采样点的详细参数：
  - 时间戳
  - 通信距离 (km)
  - 仰角 (度)
  - RTT 延迟 (ms)
  - 总握手时间 (ms)
  - 通信开销百分比
  - 成功/失败状态
  - 卫星 3D 坐标 (ENU)

### 可视化图表
- **pq_ntor_satellite_test_results.png** (240 KB)
  主测试结果 4 子图：
  1. 握手时间变化曲线
  2. 通信开销变化曲线
  3. 轨道参数变化 (距离 & 仰角)
  4. 通信成功率统计

- **elevation_curve_20250308_1721.png** (137 KB)
  卫星仰角随时间变化曲线 (2025-03-08 17:21 通信窗口)

- **elevation_map_20250308_172645.png** (410 KB)
  区域仰角分布热力图 (60km × 60km 观测区域)

---

## 测试结果概览

### 测试配置
| 参数 | 数值 |
|------|------|
| PQ-NTOR 基础握手时间 | 49 μs (C程序实测) |
| 测试时长 | 10 分钟 |
| 采样点数量 | 30 |
| 测试时间 | 2025-11-20 16:56:50 - 17:06:50 |

### 关键指标
| 指标 | 数值 |
|------|------|
| 通信距离范围 | 11,908.71 - 13,106.74 km |
| 仰角范围 | -74.27° ~ -59.54° |
| 网络 RTT 延迟 | 79.39 - 87.38 ms |
| 总握手时间 | 79.44 - 87.43 ms |
| 平均通信开销 | 99.94% (网络延迟占比) |
| 通信成功率 | 0.0% (仰角未达 10° 阈值) |

### 重要发现

1. **PQ-NTOR 低开销验证**
   - 握手本身仅 49μs，占总时间 0.06%
   - 即使在 13,000 km 距离下，加密握手延迟可忽略不计

2. **网络延迟主导**
   - 卫星通信中，物理传播延迟占 >99.9%
   - RTT ≈ 2 × 距离 / 光速 (300 km/ms)

3. **测试时段分析**
   - 当前测试窗口卫星在地平线以下 (负仰角)
   - 属于不可见期，无法建立通信

---

## 如何使用

### 运行测试
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/satellite-integration-test
python3 pq_ntor_satellite_test.py
```

### 自定义测试参数
编辑脚本 `main()` 函数：
```python
# 修改测试时长 (默认 10 分钟)
results = tester.run_test(duration_minutes=20)

# 指定测试开始时间
from datetime import datetime
start = datetime(2025, 3, 8, 17, 21, 0)  # 使用真实通信窗口
results = tester.run_test(start_time=start, duration_minutes=10)
```

### 数据分析
```python
import pandas as pd

# 读取测试数据
df = pd.read_csv('pq_ntor_satellite_test_data.csv')

# 筛选成功通信的数据点
successful = df[df['success'] == True]

# 计算平均握手时间
avg_handshake = df['total_handshake_ms'].mean()
```

---

## 依赖关系

### Python 依赖
```bash
pip3 install numpy pandas matplotlib skyfield
```

### 关联文件
- **satellite_orbit.py** (位于上级目录)
  提供卫星轨道计算、TLE 数据、通信窗口分析

---

## 后续优化方向

### 1. 使用真实通信窗口
当前测试使用随机时间点，应改为使用 `satellite_orbit.py` 计算的真实通信窗口：

```python
from satellite_orbit import SatelliteOrbit

orbit = SatelliteOrbit()
orbit.analyze_communication_windows()
# 使用输出的窗口时间运行测试
```

### 2. 多轨道位置对比
测试不同轨道位置的性能差异：
- 近地点 vs. 远地点
- 低仰角 vs. 高仰角
- 上升段 vs. 下降段

### 3. 长期统计分析
运行 24 小时测试，覆盖多个轨道周期 (101.13 分钟/周期)

### 4. 真实网络集成
结合 C 程序进行实际网络握手测试：
```bash
# 运行 C 程序握手测试
cd ../../
./pq-ntor-handshake --satellite-mode --distance 12000
```

### 5. 多地面站测试
模拟不同地理位置的地面站，分析覆盖范围

---

## 技术原理

### 总握手时间计算
```
总握手时间 = PQ-NTOR 握手时间 + 网络 RTT

其中:
- PQ-NTOR 握手: 49 μs (固定，C程序实测)
- 网络 RTT = 2 × 卫星距离 / 光速
- 光速 = 300,000 km/s = 300 km/ms
```

### 通信成功判定
```python
success = (elevation_angle > 10°) and (distance < 2000 km)
```
- 最低仰角要求: 10° (避免大气衰减)
- 最大通信距离: 2000 km (典型 LEO 卫星)

### 通信开销计算
```
开销百分比 = (网络 RTT / 总握手时间) × 100%
```

---

## 相关文档

- **Phase2最终总结_学术版.md**: PQ-NTOR 性能基准测试结果
- **飞腾派6+1系统部署指南.md**: 物理设备部署方案
- **6+1系统优化工作小结_2025-11-20_下午.md**: 分布式展示系统优化记录

---

## 版本历史

**v1.0** (2025-11-20)
- 初始版本
- 实现基础卫星轨道 + PQ-NTOR 握手集成测试
- 生成 CSV 数据和 4 子图可视化
- 支持自定义测试时长和采样点数量

---

**联系方式**: 如有问题请查看主项目 README 或提交 issue
