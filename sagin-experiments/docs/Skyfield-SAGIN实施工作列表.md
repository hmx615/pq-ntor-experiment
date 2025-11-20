# Skyfield-SAGIN 实施工作列表

**创建日期**: 2025-11-12
**项目目标**: 使用Skyfield在飞腾派上实现SAGIN网络仿真，结合PQ-NTOR进行性能测试
**预计周期**: 2-3周
**优先级**: 高

---

## 📋 项目概述

### 目标

在飞腾派硬件上使用Skyfield库实现SAGIN（Space-Air-Ground Integrated Network）网络仿真，测试PQ-NTOR协议在不同类型链路上的性能表现。

### 网络拓扑

```
拓扑结构（7个节点）:
┌─────────────────────────────────────────────────────────────┐
│                  Space Layer (太空层)                        │
│                                                              │
│         Satellite-1 (卫星1)  ←─→  Satellite-2 (卫星2)       │
│              ↓                         ↓                     │
└──────────────┼─────────────────────────┼─────────────────────┘
               │                         │
               │    星地链路              │
               ↓                         ↓
┌──────────────┼─────────────────────────┼─────────────────────┐
│              │     Air Layer (空中层)   │                     │
│              │                         │                     │
│         Aircraft-1 (飞机1)  ←─→  Aircraft-2 (飞机2)         │
│              ↓                         ↓                     │
└──────────────┼─────────────────────────┼─────────────────────┘
               │                         │
               │    空地链路              │
               ↓                         ↓
┌──────────────┴─────────────────────────┴─────────────────────┐
│                Ground Layer (地面层)                          │
│                                                              │
│    GS-Beijing (北京)  GS-London (伦敦)  GS-NewYork (纽约)   │
│         ↕                  ↕                  ↕              │
│      Client            Server             Client             │
└─────────────────────────────────────────────────────────────┘

总计节点: 7个
- 2 卫星 (Space)
- 2 飞机 (Air)
- 3 地面站 (Ground)
```

### 测试链路类型

| 链路类型 | 端点 | 数量 | 特性 |
|---------|------|------|------|
| **星间链路 (ISL)** | Sat-1 ↔ Sat-2 | 1 | 高延迟、动态变化 |
| **星地链路 (SGLink)** | Sat ↔ GS | 6 (2×3) | 可见性约束、高延迟 |
| **星空链路 (SALink)** | Sat ↔ Aircraft | 4 (2×2) | 可见性约束、中延迟 |
| **空地链路 (AGLink)** | Aircraft ↔ GS | 6 (2×3) | 低延迟、稳定 |
| **地面链路 (GLink)** | GS ↔ GS | 3 | 基准对照、最低延迟 |

### 实验目标

1. **动态拓扑仿真**: 基于Skyfield实时计算节点位置和链路状态
2. **PQ-NTOR性能测试**: 测试后量子Tor在不同链路上的性能
3. **性能对比分析**:
   - PQ-NTOR vs 传统Ntor
   - 不同链路类型的性能差异
   - 动态切换对性能的影响

---

## 🗂️ 工作任务分解

### Phase 1: 环境准备与基础开发 (Week 1, Days 1-7)

#### Task 1.1: 飞腾派环境配置 ⏱️ 0.5天

**负责人**: -
**优先级**: P0 (阻塞性)
**依赖**: 无

**子任务**:
- [ ] 1.1.1 在飞腾派上安装Skyfield及依赖
  ```bash
  pip3 install skyfield numpy scipy matplotlib astropy jplephem sgp4
  ```
- [ ] 1.1.2 下载星历表数据
  ```bash
  python3 -c "from skyfield.api import load; load('de421.bsp')"
  ```
- [ ] 1.1.3 下载TLE数据（Starlink LEO示例）
  ```bash
  wget -O tle_starlink.txt \
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
  ```
- [ ] 1.1.4 验证Skyfield基本功能
  ```bash
  python3 test_skyfield_basic.py
  ```

**验收标准**:
- ✅ Skyfield能成功导入
- ✅ 能正确计算ISS位置
- ✅ TLE数据正常加载
- ✅ 内存占用<200MB

**预期产出**:
- `test_skyfield_basic.py` - 基础功能测试脚本

---

#### Task 1.2: SAGIN拓扑配置文件 ⏱️ 0.5天

**负责人**: -
**优先级**: P0
**依赖**: Task 1.1

**子任务**:
- [ ] 1.2.1 创建卫星配置（2颗）
  - Sat-1: LEO卫星（高度550km，Starlink轨道）
  - Sat-2: MEO卫星（高度8000km，O3b轨道）
- [ ] 1.2.2 创建飞机配置（2架）
  - Aircraft-1: 北京-伦敦航线（高度10km，速度250m/s）
  - Aircraft-2: 伦敦-纽约航线（高度10km，速度250m/s）
- [ ] 1.2.3 创建地面站配置（3个）
  - GS-Beijing: 北京 (39.9°N, 116.4°E)
  - GS-London: 伦敦 (51.5°N, 0.1°W)
  - GS-NewYork: 纽约 (40.7°N, 74.0°W)
- [ ] 1.2.4 定义链路可见性参数
  - 最小仰角: 10°（卫星-地面站）
  - 最大距离: 10,000km（星间链路）
  - 飞机通信半径: 500km

**验收标准**:
- ✅ 配置文件格式正确（JSON）
- ✅ 包含所有7个节点
- ✅ TLE数据有效
- ✅ 航线参数合理

**预期产出**:
- `sagin_topology_config.json` - 完整拓扑配置

**配置文件示例**:
```json
{
  "satellites": {
    "Sat-1": {
      "type": "LEO",
      "altitude_km": 550,
      "line1": "1 44713U 19074A   ...",
      "line2": "2 44713  53.0542 ...",
      "frequency_ghz": 12.5
    },
    "Sat-2": {
      "type": "MEO",
      "altitude_km": 8000,
      "line1": "1 12345U ...",
      "line2": "2 12345  50.0000 ...",
      "frequency_ghz": 18.5
    }
  },
  "aircraft": {
    "Aircraft-1": {
      "route": "Beijing-London",
      "cruise_altitude_km": 10,
      "cruise_speed_m_s": 250,
      "start_lat": 39.9,
      "start_lon": 116.4,
      "end_lat": 51.5,
      "end_lon": -0.1
    },
    "Aircraft-2": {
      "route": "London-NewYork",
      "cruise_altitude_km": 10,
      "cruise_speed_m_s": 250,
      "start_lat": 51.5,
      "start_lon": -0.1,
      "end_lat": 40.7,
      "end_lon": -74.0
    }
  },
  "ground_stations": {
    "GS-Beijing": {
      "latitude": 39.9,
      "longitude": 116.4,
      "elevation_m": 50,
      "min_elevation_deg": 10
    },
    "GS-London": {
      "latitude": 51.5,
      "longitude": -0.1,
      "elevation_m": 25,
      "min_elevation_deg": 10
    },
    "GS-NewYork": {
      "latitude": 40.7,
      "longitude": -74.0,
      "elevation_m": 10,
      "min_elevation_deg": 10
    }
  },
  "link_constraints": {
    "max_isl_distance_km": 10000,
    "min_elevation_deg": 10,
    "aircraft_comm_radius_km": 500
  }
}
```

---

#### Task 1.3: 核心轨道仿真器开发 ⏱️ 2天

**负责人**: -
**优先级**: P0
**依赖**: Task 1.1, 1.2

**子任务**:
- [ ] 1.3.1 实现SAGINOrbitSimulator类
  - 卫星位置计算（Skyfield SGP4）
  - 飞机轨迹仿真（大圆航线+恒速）
  - 地面站位置管理
- [ ] 1.3.2 实现链路可见性检查
  - `check_sat_gs_visibility()` - 卫星-地面站
  - `check_sat_sat_visibility()` - 星间链路
  - `check_sat_aircraft_visibility()` - 卫星-飞机
  - `check_aircraft_gs_visibility()` - 飞机-地面站
- [ ] 1.3.3 实现链路延迟计算
  - 距离计算（大地测量学）
  - 传播延迟（光速300,000km/s）
  - 多普勒频移（可选）
- [ ] 1.3.4 实现实时仿真主循环
  - 每10秒更新一次拓扑
  - 回调接口设计
  - 拓扑变化检测

**验收标准**:
- ✅ 卫星位置精度<1km（与在线工具对比）
- ✅ 飞机轨迹平滑连续
- ✅ 可见性判断正确（与仰角计算一致）
- ✅ 延迟计算合理（距离/光速）
- ✅ 实时仿真稳定运行>1小时

**预期产出**:
- `sagin_orbit_simulator.py` (~500行)
- `test_orbit_simulator.py` - 单元测试

**关键代码接口**:
```python
class SAGINOrbitSimulator:
    def get_satellite_position(self, sat_name, time_utc=None) -> dict
    def get_aircraft_position(self, aircraft_name, time_utc=None) -> dict
    def check_visibility(self, node1, node2, time_utc=None) -> dict
    def calculate_link_delay(self, node1, node2, time_utc=None) -> dict
    def get_network_topology(self, time_utc=None) -> dict
    def run_realtime_simulation(self, callback, interval_sec=10)
```

---

#### Task 1.4: Docker网络拓扑管理器 ⏱️ 1.5天

**负责人**: -
**优先级**: P0
**依赖**: Task 1.3

**子任务**:
- [ ] 1.4.1 设计Docker容器架构
  - 7个容器（2 Sat + 2 Aircraft + 3 GS）
  - 网络命名和IP分配
  - 容器资源限制
- [ ] 1.4.2 实现NetworkTopologyManager类
  - `update_link_delay()` - 使用tc netem
  - `enable_link()` / `disable_link()` - 使用iptables
  - `apply_topology_update()` - 批量更新
- [ ] 1.4.3 实现拓扑同步机制
  - 监听轨道仿真器回调
  - 计算拓扑差异
  - 增量更新网络配置
- [ ] 1.4.4 创建Docker Compose配置
  - 定义所有容器
  - 配置网络桥接
  - 挂载卷和环境变量

**验收标准**:
- ✅ 7个容器成功启动
- ✅ tc规则正确应用（tcpdump验证）
- ✅ 链路启用/禁用即时生效（<100ms）
- ✅ 拓扑更新不中断现有连接

**预期产出**:
- `network_topology_manager.py` (~300行)
- `docker-compose-sagin.yml`
- `Dockerfile.sagin-node`

**Docker架构示例**:
```yaml
services:
  sat-1:
    container_name: sagin-sat-1
    image: pq-ntor-sagin:latest
    cap_add:
      - NET_ADMIN
    networks:
      sagin_net:
        ipv4_address: 172.20.1.11

  sat-2:
    container_name: sagin-sat-2
    image: pq-ntor-sagin:latest
    cap_add:
      - NET_ADMIN
    networks:
      sagin_net:
        ipv4_address: 172.20.1.12

  aircraft-1:
    container_name: sagin-aircraft-1
    image: pq-ntor-sagin:latest
    cap_add:
      - NET_ADMIN
    networks:
      sagin_net:
        ipv4_address: 172.20.2.21

  # ... (其他5个容器)

networks:
  sagin_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

#### Task 1.5: 端到端集成测试 ⏱️ 1天

**负责人**: -
**优先级**: P1
**依赖**: Task 1.3, 1.4

**子任务**:
- [ ] 1.5.1 集成轨道仿真器与网络管理器
  ```python
  simulator = SAGINOrbitSimulator('sagin_topology_config.json')
  network_mgr = NetworkTopologyManager()
  simulator.run_realtime_simulation(network_mgr.apply_topology_update, 10)
  ```
- [ ] 1.5.2 测试静态拓扑
  - 固定时间点的链路状态
  - 验证延迟和可见性
- [ ] 1.5.3 测试动态拓扑
  - 运行30分钟仿真
  - 观察卫星过顶事件
  - 验证切换机制
- [ ] 1.5.4 性能基准测试
  - CPU占用
  - 内存占用
  - 网络拓扑更新延迟

**验收标准**:
- ✅ 仿真器与网络管理器正确集成
- ✅ 拓扑更新与实际轨道一致
- ✅ CPU占用<5%
- ✅ 内存占用<500MB（含7个容器）
- ✅ 拓扑更新延迟<200ms

**预期产出**:
- `test_integration.py` - 集成测试脚本
- `integration_test_report.md` - 测试报告

---

#### Task 1.6: 可视化工具开发（可选） ⏱️ 1.5天

**负责人**: -
**优先级**: P2（非阻塞）
**依赖**: Task 1.3

**子任务**:
- [ ] 1.6.1 实现2D拓扑可视化
  - 地图投影（Matplotlib Basemap）
  - 节点位置标注
  - 链路连线（有效/失效）
- [ ] 1.6.2 实现实时更新动画
  - 每10秒刷新一次
  - 显示时间戳
  - 显示链路延迟
- [ ] 1.6.3 保存可视化快照
  - PNG图片序列
  - 生成视频（ffmpeg）

**验收标准**:
- ✅ 能清晰显示7个节点位置
- ✅ 链路状态正确（绿色=有效，灰色=失效）
- ✅ 动画流畅（>5 fps）

**预期产出**:
- `topology_visualizer.py` (~200行)
- 示例截图和视频

---

### Phase 2: PQ-NTOR性能测试 (Week 2, Days 8-14)

#### Task 2.1: PQ-NTOR测试脚本适配 ⏱️ 1天

**负责人**: -
**优先级**: P0
**依赖**: Phase 1完成

**子任务**:
- [ ] 2.1.1 修改现有测试脚本
  - 适配7节点拓扑
  - 支持指定源和目标节点
  - 支持多跳路由测试
- [ ] 2.1.2 创建实验场景脚本
  - 场景1: 星间链路（Sat-1 → Sat-2）
  - 场景2: 星地链路（Sat-1 → GS-Beijing）
  - 场景3: 星空地链路（Sat-1 → Aircraft-1 → GS-London）
  - 场景4: 全路径（GS-Beijing → Sat-1 → Sat-2 → GS-NewYork）
- [ ] 2.1.3 实现传统Ntor对照组
  - 部署传统Tor（非PQ）
  - 相同拓扑和链路条件

**验收标准**:
- ✅ 脚本能正确连接指定节点
- ✅ 路由路径可控
- ✅ PQ和非PQ版本可切换

**预期产出**:
- `run_pq_ntor_test.sh` - 测试脚本
- `test_scenarios.json` - 场景配置

---

#### Task 2.2: 链路性能测试 ⏱️ 2天

**负责人**: -
**优先级**: P0
**依赖**: Task 2.1

**子任务**:
- [ ] 2.2.1 星间链路测试（ISL）
  - Sat-1 ↔ Sat-2
  - 测试指标: 电路建立时间、握手时延、吞吐量
  - 重复次数: 50次
  - 测试时长: 1小时（覆盖多个轨道位置）
- [ ] 2.2.2 星地链路测试（SGLink）
  - Sat-1 ↔ GS-Beijing
  - Sat-1 ↔ GS-London
  - Sat-2 ↔ GS-NewYork
  - 每个链路50次测试
- [ ] 2.2.3 星空链路测试（SALink）
  - Sat-1 ↔ Aircraft-1
  - Sat-2 ↔ Aircraft-2
  - 每个链路50次测试
- [ ] 2.2.4 空地链路测试（AGLink）
  - Aircraft-1 ↔ GS-Beijing
  - Aircraft-2 ↔ GS-London
  - 每个链路30次测试
- [ ] 2.2.5 基准地面链路测试（GLink）
  - GS-Beijing ↔ GS-London（光纤）
  - 30次测试作为baseline

**测试指标**:
- Circuit Construction Time (电路建立时间)
- Handshake Latency (握手延迟)
- Cell Transmission Time (单元传输时间)
- Throughput (吞吐量)
- Timeout Rate (超时率)
- Packet Loss Rate (丢包率)

**验收标准**:
- ✅ 每个链路类型至少30次有效测试
- ✅ 数据格式统一（CSV）
- ✅ 包含时间戳和链路状态
- ✅ 测试期间拓扑状态记录完整

**预期产出**:
- `isl_test_results.csv` - 星间链路数据
- `sglink_test_results.csv` - 星地链路数据
- `salink_test_results.csv` - 星空链路数据
- `aglink_test_results.csv` - 空地链路数据
- `glink_baseline_results.csv` - 地面基准数据

---

#### Task 2.3: 动态切换测试 ⏱️ 1天

**负责人**: -
**优先级**: P1
**依赖**: Task 2.2

**子任务**:
- [ ] 2.3.1 卫星过顶场景
  - Client在GS-Beijing
  - Server在GS-NewYork
  - 路径经过Sat-1（从不可见到可见再到不可见）
  - 测试电路在切换时的行为
- [ ] 2.3.2 飞机移动场景
  - Client在Aircraft-1（移动中）
  - Server在GS-London
  - 测试移动节点的性能影响
- [ ] 2.3.3 多跳路由切换
  - 初始路径: GS-Beijing → Sat-1 → GS-London
  - 切换到: GS-Beijing → Aircraft-1 → GS-London
  - 测试路由重建时间和数据连续性

**验收标准**:
- ✅ 记录切换时刻的性能数据
- ✅ 分析切换前后性能差异
- ✅ 统计切换成功率

**预期产出**:
- `handover_test_results.csv`
- `handover_analysis.md`

---

#### Task 2.4: PQ vs 传统Ntor对比测试 ⏱️ 1天

**负责人**: -
**优先级**: P0
**依赖**: Task 2.2

**子任务**:
- [ ] 2.4.1 相同条件下运行传统Ntor测试
  - 使用完全相同的拓扑
  - 使用完全相同的链路条件
  - 每个场景30次重复
- [ ] 2.4.2 数据配对分析
  - 按链路类型配对
  - 按时间窗口配对（确保网络条件相同）
- [ ] 2.4.3 统计显著性检验
  - t-test检验时延差异
  - 计算性能开销百分比

**验收标准**:
- ✅ PQ和传统版本测试数量相同
- ✅ 测试条件对等
- ✅ 统计分析结果显著（p<0.05）

**预期产出**:
- `ntor_traditional_results.csv`
- `pq_vs_traditional_comparison.csv`

---

#### Task 2.5: 压力测试与边界条件 ⏱️ 1天

**负责人**: -
**优先级**: P2
**依赖**: Task 2.2

**子任务**:
- [ ] 2.5.1 高延迟场景
  - GEO卫星模拟（35,786km，~240ms单程延迟）
  - 测试PQ-NTOR在极高延迟下的表现
- [ ] 2.5.2 高丢包场景
  - 模拟恶劣天气（丢包率5%-20%）
  - 测试重传机制
- [ ] 2.5.3 链路抖动场景
  - 延迟变化±50ms
  - 测试稳定性
- [ ] 2.5.4 并发连接测试
  - 同时建立10条电路
  - 测试资源消耗

**验收标准**:
- ✅ 记录边界条件下的性能
- ✅ 识别性能瓶颈
- ✅ 验证协议鲁棒性

**预期产出**:
- `stress_test_results.csv`
- `boundary_conditions_analysis.md`

---

### Phase 3: 数据分析与论文撰写 (Week 3, Days 15-21)

#### Task 3.1: 数据预处理与清洗 ⏱️ 0.5天

**负责人**: -
**优先级**: P0
**依赖**: Phase 2完成

**子任务**:
- [ ] 3.1.1 合并所有CSV数据
- [ ] 3.1.2 数据清洗
  - 移除异常值（3σ原则）
  - 处理缺失值
  - 时间戳标准化
- [ ] 3.1.3 添加元数据
  - 链路类型标签
  - 拓扑状态标签
  - PQ/传统标签

**验收标准**:
- ✅ 数据格式统一
- ✅ 无重复记录
- ✅ 标签完整

**预期产出**:
- `merged_test_results.csv`
- `data_cleaning_report.md`

---

#### Task 3.2: 统计分析 ⏱️ 1天

**负责人**: -
**优先级**: P0
**依赖**: Task 3.1

**子任务**:
- [ ] 3.2.1 描述性统计
  - 每种链路的均值、中位数、标准差
  - 最小值、最大值、百分位数
- [ ] 3.2.2 对比分析
  - PQ vs 传统Ntor（各链路类型）
  - 不同链路类型的性能差异
  - 动态vs静态拓扑的影响
- [ ] 3.2.3 回归分析
  - 延迟与距离的关系
  - 性能与链路类型的关系
- [ ] 3.2.4 统计检验
  - t-test（PQ vs 传统）
  - ANOVA（多组链路对比）

**验收标准**:
- ✅ 统计结果有显著性（p<0.05）
- ✅ 效应量清晰（Cohen's d）
- ✅ 结果可复现

**预期产出**:
- `statistical_analysis.ipynb` - Jupyter notebook
- `statistical_summary.csv`

---

#### Task 3.3: 数据可视化 ⏱️ 1.5天

**负责人**: -
**优先级**: P0
**依赖**: Task 3.2

**子任务**:
- [ ] 3.3.1 创建核心图表（8-10张）
  - **Figure 1**: 电路建立时间对比（PQ vs 传统，按链路分组）
  - **Figure 2**: 握手延迟分布箱型图
  - **Figure 3**: 不同链路类型的性能开销
  - **Figure 4**: 动态拓扑下的性能变化（时间序列）
  - **Figure 5**: 星间链路距离vs延迟散点图
  - **Figure 6**: 切换事件对性能的影响
  - **Figure 7**: 吞吐量对比（PQ vs 传统）
  - **Figure 8**: 综合性能雷达图（多维度对比）
- [ ] 3.3.2 生成出版级PDF
  - 矢量格式（300 DPI）
  - 清晰标注和图例
  - 配色方案统一
- [ ] 3.3.3 创建补充图表
  - 拓扑可视化快照
  - 链路状态时间线

**验收标准**:
- ✅ 所有图表清晰可读
- ✅ 支持LaTeX引用
- ✅ 配色适合黑白打印

**预期产出**:
- `figure1_circuit_time_comparison.pdf`
- `figure2_handshake_distribution.pdf`
- ... (共8-10个PDF文件)
- `figure_generation.py` - 生成脚本

---

#### Task 3.4: 论文Evaluation章节撰写 ⏱️ 2天

**负责人**: -
**优先级**: P0
**依赖**: Task 3.3

**子任务**:
- [ ] 3.4.1 撰写实验设置（Experimental Setup）
  - 硬件平台（飞腾派规格）
  - 网络拓扑（7节点）
  - 轨道仿真（Skyfield）
  - 测试参数
- [ ] 3.4.2 撰写结果部分（Results）
  - 6.2.1 星间链路性能
  - 6.2.2 星地链路性能
  - 6.2.3 混合链路性能
  - 6.2.4 PQ vs 传统对比
  - 6.2.5 动态切换影响
- [ ] 3.4.3 撰写讨论部分（Discussion）
  - 性能开销分析
  - 实用性评估
  - 局限性说明
  - 优化方向
- [ ] 3.4.4 创建表格
  - Table 1: 测试环境参数
  - Table 2: 链路类型特征
  - Table 3: 性能对比摘要

**验收标准**:
- ✅ 符合学术论文规范
- ✅ 逻辑清晰连贯
- ✅ 图表引用正确
- ✅ 结果客观准确

**预期产出**:
- `evaluation_section_draft.tex` (~3000字)
- `evaluation_tables.tex`

---

#### Task 3.5: 技术报告撰写 ⏱️ 1天

**负责人**: -
**优先级**: P1
**依赖**: Task 3.4

**子任务**:
- [ ] 3.5.1 撰写实验报告
  - 实验过程记录
  - 关键发现总结
  - 遇到的问题和解决方案
- [ ] 3.5.2 撰写系统文档
  - 架构说明
  - 部署指南
  - 使用手册
- [ ] 3.5.3 创建实验可复现指南
  - 环境配置步骤
  - 数据获取方法
  - 脚本运行说明

**验收标准**:
- ✅ 文档完整详细
- ✅ 他人可按文档复现
- ✅ 包含故障排除指南

**预期产出**:
- `SAGIN_PQ_NTOR_实验报告.md` (~10,000字)
- `系统部署与使用手册.md` (~5,000字)
- `实验复现指南.md` (~3,000字)

---

### Phase 4: 系统优化与收尾 (可选，Days 22-28)

#### Task 4.1: 性能优化 ⏱️ 2天

**负责人**: -
**优先级**: P2
**依赖**: Phase 3完成

**子任务**:
- [ ] 4.1.1 轨道仿真优化
  - 批量计算（向量化）
  - 缓存机制
  - 预测算法
- [ ] 4.1.2 网络更新优化
  - 增量更新
  - 异步处理
  - 批量操作
- [ ] 4.1.3 资源优化
  - 内存占用优化
  - CPU占用优化

**验收标准**:
- ✅ CPU占用降低30%
- ✅ 内存占用降低20%
- ✅ 拓扑更新延迟降低50%

---

#### Task 4.2: 代码重构与文档 ⏱️ 1.5天

**负责人**: -
**优先级**: P2
**依赖**: Task 4.1

**子任务**:
- [ ] 4.2.1 代码重构
  - 模块化改进
  - 错误处理增强
  - 日志系统完善
- [ ] 4.2.2 代码文档
  - Docstring补充
  - 类型注解
  - 示例代码
- [ ] 4.2.3 单元测试
  - 覆盖率>80%
  - CI/CD集成

**验收标准**:
- ✅ 代码通过pylint检查
- ✅ 测试覆盖率>80%
- ✅ API文档自动生成

---

#### Task 4.3: 演示准备 ⏱️ 1天

**负责人**: -
**优先级**: P2
**依赖**: Phase 3完成

**子任务**:
- [ ] 4.3.1 创建演示PPT
  - 项目背景和目标
  - 系统架构
  - 关键结果
  - 演示视频
- [ ] 4.3.2 准备演示环境
  - 一键启动脚本
  - 演示场景设计
  - 备份方案
- [ ] 4.3.3 录制演示视频
  - 系统运行演示
  - 可视化动画
  - 结果展示

**预期产出**:
- `SAGIN_PQ_NTOR_演示.pptx`
- `demo_video.mp4`
- `quick_start_demo.sh`

---

## 📅 时间表

### 总览（3周）

| Week | 主要任务 | 里程碑 |
|------|---------|--------|
| **Week 1** | 环境配置 + 仿真器开发 + 网络管理器 | M1: 基础系统就绪 |
| **Week 2** | PQ-NTOR性能测试 + 数据收集 | M2: 实验数据完整 |
| **Week 3** | 数据分析 + 可视化 + 论文撰写 | M3: 论文章节完成 |
| **(可选 Week 4)** | 优化 + 重构 + 演示准备 | M4: 系统完善 |

### 详细甘特图

```
Week 1:
Day 1-2:   [===Task 1.1-1.2===][======Task 1.3======]
Day 3-4:   [=========Task 1.3 续========]
Day 5-6:   [=======Task 1.4=======]
Day 7:     [====Task 1.5====]

Week 2:
Day 8:     [===Task 2.1===]
Day 9-10:  [=======Task 2.2=======]
Day 11-12: [====Task 2.2 续====][=Task 2.3=]
Day 13:    [===Task 2.4===]
Day 14:    [===Task 2.5===]

Week 3:
Day 15:    [Task 3.1][====Task 3.2====]
Day 16:    [=======Task 3.3=======]
Day 17:    [====Task 3.3 续====]
Day 18-19: [=======Task 3.4=======]
Day 20:    [===Task 3.5===]
Day 21:    [缓冲/补充]

(可选)
Week 4:
Day 22-23: [=======Task 4.1=======]
Day 24-25: [====Task 4.2====]
Day 26:    [==Task 4.3==]
Day 27-28: [缓冲/备用]
```

---

## 🎯 里程碑与验收标准

### M1: 基础系统就绪 (Day 7)

**标准**:
- ✅ Skyfield环境配置完成
- ✅ 轨道仿真器正常工作
- ✅ Docker网络管理器可用
- ✅ 7节点容器成功启动
- ✅ 端到端集成测试通过

**验收方法**:
```bash
# 运行集成测试
python3 test_integration.py

# 预期输出：
# ✓ 轨道仿真器运行正常
# ✓ 7个容器全部启动
# ✓ 拓扑更新延迟<200ms
# ✓ 内存占用<500MB
# ✓ 所有链路可见性判断正确
```

---

### M2: 实验数据完整 (Day 14)

**标准**:
- ✅ 至少300次有效测试（5种链路×50-60次）
- ✅ PQ和传统Ntor对照组完整
- ✅ 动态切换测试完成
- ✅ 数据格式统一，无缺失

**验收方法**:
```bash
# 检查数据完整性
python3 check_data_completeness.py

# 预期输出：
# ISL测试: 50/50 ✓
# SGLink测试: 150/150 ✓
# SALink测试: 100/100 ✓
# AGLink测试: 180/180 ✓
# GLink基准: 30/30 ✓
# 传统Ntor对照: 300/300 ✓
# 总计: 810条有效记录
```

---

### M3: 论文章节完成 (Day 21)

**标准**:
- ✅ 8-10张出版级图表
- ✅ Evaluation章节草稿（~3000字）
- ✅ 统计分析结果显著（p<0.05）
- ✅ 技术报告完整

**验收方法**:
- 审阅论文草稿
- 检查图表质量
- 验证统计结果
- 确认文档完整性

---

### M4: 系统完善 (Day 28, 可选)

**标准**:
- ✅ 代码测试覆盖率>80%
- ✅ 性能优化达标（CPU降低30%）
- ✅ 文档齐全（部署、使用、复现）
- ✅ 演示材料就绪

---

## 📊 性能指标定义

### 1. Circuit Construction Time (电路建立时间)

**定义**: 从发起电路请求到电路建立完成的总时间

**测量方法**:
```python
start_time = time.time()
circuit = controller.new_circuit()
end_time = time.time()
construction_time = end_time - start_time
```

**单位**: 秒（s）

**预期范围**:
- 地面链路: 0.5-1.5s
- 空地链路: 1.0-2.0s
- 星地链路: 2.0-4.0s
- 星间链路: 3.0-6.0s

---

### 2. Handshake Latency (握手延迟)

**定义**: PQ-NTOR握手协议的RTT（往返时延）

**测量方法**:
```
握手延迟 = CREATE2发送时间 → CREATED2接收时间
```

**单位**: 毫秒（ms）

**预期范围**:
- 地面链路: 10-50ms
- 空地链路: 20-100ms
- 星地链路: 100-300ms
- 星间链路: 150-500ms

---

### 3. Cell Transmission Time (单元传输时间)

**定义**: 单个Tor cell（2048字节）的传输时延

**单位**: 毫秒（ms）

**预期范围**:
- 地面链路: 5-20ms
- 空地链路: 10-50ms
- 星地链路: 50-150ms
- 星间链路: 100-300ms

---

### 4. Throughput (吞吐量)

**定义**: 单位时间内传输的数据量

**测量方法**:
```python
data_size = 10 * 1024 * 1024  # 10 MB
start_time = time.time()
# 传输数据
end_time = time.time()
throughput = data_size / (end_time - start_time)
```

**单位**: Mbps

**预期范围**:
- 地面链路: 50-100 Mbps
- 空地链路: 10-50 Mbps
- 星地链路: 5-20 Mbps
- 星间链路: 1-10 Mbps

---

### 5. Timeout Rate (超时率)

**定义**: 超过90秒未完成的连接占总连接数的百分比

**计算方法**:
```
Timeout Rate = (超时次数 / 总测试次数) × 100%
```

**单位**: %

**预期范围**:
- 地面链路: 0-5%
- 空地链路: 5-10%
- 星地链路: 10-20%
- 星间链路: 15-30%

---

### 6. Performance Overhead (性能开销)

**定义**: PQ-NTOR相对于传统Ntor的性能损失

**计算方法**:
```
Overhead = (PQ_Time - Traditional_Time) / Traditional_Time × 100%
```

**单位**: %

**预期范围**:
- 握手开销: 20-50%（Kyber计算）
- 总体开销: 10-30%
- Cell大小增加: 300%（512B → 2048B）

---

## 🔬 实验场景设计

### 场景1: 单跳星间链路 (ISL)

**路径**: Sat-1 ↔ Sat-2

**特点**:
- 距离: 2000-8000km（动态变化）
- 延迟: 7-27ms（单程）
- 可见性: 持续可见（LEO-MEO）

**测试目标**:
- 测试高动态链路性能
- 验证频繁距离变化的影响

**重复次数**: 50次（覆盖1小时）

---

### 场景2: 单跳星地链路 (SGLink)

**路径**: Sat-1 ↔ GS-Beijing

**特点**:
- 距离: 550-2000km（可见时）
- 延迟: 2-7ms（单程）
- 可见性: 间歇性（每90分钟过顶1次，可见10分钟）

**测试目标**:
- 测试可见性约束下的性能
- 记录卫星过顶事件

**重复次数**: 50次（覆盖多个过顶窗口）

---

### 场景3: 多跳混合链路

**路径**: GS-Beijing → Sat-1 → Aircraft-1 → GS-London

**特点**:
- 3跳混合
- 包含星地、星空、空地链路
- 总延迟: 50-150ms

**测试目标**:
- 测试多跳路由性能
- 验证不同链路类型的组合效应

**重复次数**: 30次

---

### 场景4: 端到端全球通信

**路径**: GS-Beijing → Sat-1 → Sat-2 → GS-NewYork

**特点**:
- 跨越地球1/3周长（~13,000km）
- 包含星间链路
- 总延迟: 100-300ms

**测试目标**:
- 测试全球尺度通信性能
- 对比传统光纤路由

**重复次数**: 30次

---

### 场景5: 动态切换场景

**路径**: GS-Beijing → (动态选择) → GS-London

**切换条件**:
- 初始: Sat-1可见，使用星地链路
- 切换: Sat-1不可见，切换到Aircraft-1（空地链路）

**测试目标**:
- 测试切换机制鲁棒性
- 分析切换对性能的影响

**重复次数**: 20次切换事件

---

## 🛠️ 技术栈

### 核心技术

| 组件 | 技术选型 | 版本 | 用途 |
|-----|---------|------|------|
| **轨道仿真** | Skyfield | 1.48+ | 卫星/飞机位置计算 |
| **容器化** | Docker | 24.0+ | 节点隔离 |
| **网络模拟** | tc netem | - | 延迟/丢包模拟 |
| **编程语言** | Python | 3.8+ | 主要开发语言 |
| **数据处理** | Pandas, NumPy | 最新 | 数据分析 |
| **可视化** | Matplotlib | 3.5+ | 图表生成 |
| **统计分析** | SciPy, Statsmodels | 最新 | 统计检验 |
| **PQ密码学** | Kyber-512 | - | 后量子握手 |

### 开发环境

- **操作系统**: Ubuntu 22.04 ARM64（飞腾派麒麟V10）
- **CPU**: 飞腾FT-2000/4 (4核 @ 2.6-3.0GHz)
- **内存**: 8GB DDR4
- **存储**: 128GB SSD

---

## 📝 数据格式规范

### 测试结果CSV格式

```csv
timestamp,link_type,node1,node2,distance_km,delay_ms,protocol,test_id,circuit_time_s,handshake_latency_ms,cell_time_ms,throughput_mbps,timeout,packet_loss_rate,topology_state
2025-11-15T10:30:00Z,ISL,Sat-1,Sat-2,3245.6,10.8,PQ-NTOR,1,4.523,234.5,89.2,5.6,False,0.02,visible
2025-11-15T10:31:00Z,ISL,Sat-1,Sat-2,3198.2,10.7,PQ-NTOR,2,4.612,241.3,91.1,5.4,False,0.01,visible
...
```

**字段说明**:
- `timestamp`: UTC时间戳（ISO 8601格式）
- `link_type`: 链路类型（ISL/SGLink/SALink/AGLink/GLink）
- `node1`, `node2`: 链路两端节点名称
- `distance_km`: 节点间距离（公里）
- `delay_ms`: 单程传播延迟（毫秒）
- `protocol`: 协议类型（PQ-NTOR/Traditional-NTOR）
- `test_id`: 测试序号
- `circuit_time_s`: 电路建立时间（秒）
- `handshake_latency_ms`: 握手延迟（毫秒）
- `cell_time_ms`: 单元传输时间（毫秒）
- `throughput_mbps`: 吞吐量（Mbps）
- `timeout`: 是否超时（布尔值）
- `packet_loss_rate`: 丢包率（0-1）
- `topology_state`: 拓扑状态（visible/invisible/degraded）

---

## 🚨 风险与缓解措施

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| **Skyfield计算精度不足** | 低 | 中 | 已验证精度<1km，满足需求；增加误差分析章节 |
| **Docker网络性能瓶颈** | 中 | 高 | 使用host网络模式；监控网络开销；设置对照组 |
| **飞腾派性能不足** | 中 | 高 | 优化代码；减少并发容器数；使用性能分析工具 |
| **TLE数据过时** | 低 | 低 | 自动更新脚本；使用近期数据 |
| **拓扑更新延迟过大** | 中 | 中 | 异步处理；批量更新；增量更新 |
| **测试时间过长** | 高 | 中 | 并行测试；减少重复次数（最低30次） |

### 项目风险

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| **时间超期** | 中 | 高 | 设置缓冲时间；优先完成核心任务；砍掉可选功能 |
| **数据质量问题** | 中 | 高 | 严格数据验证；记录元数据；及时备份 |
| **硬件故障** | 低 | 高 | 定期备份；准备备用飞腾派；云端备份数据 |
| **实验不可复现** | 中 | 高 | 详细记录实验参数；固定随机种子；版本控制 |

---

## 📚 参考资源

### Skyfield资源
- 官网: https://rhodesmill.org/skyfield/
- 文档: https://rhodesmill.org/skyfield/api.html
- GitHub: https://github.com/skyfielders/python-skyfield

### TLE数据源
- CelesTrak: https://celestrak.org/
- Space-Track: https://www.space-track.org/

### 相关文献
- Schanzenbach et al. 2019 (PETS): PQ-Tor性能评估
- Apostolopoulos et al. 2020 (NDSS): Tor over LEO卫星
- Handley 2018 (SIGCOMM): Starlink性能数据

---

## 📞 支持与协作

### 需要协助的事项

1. **TLE数据获取**: 需要真实的Starlink/O3b卫星TLE
2. **飞机航线数据**: 需要真实的航班轨迹数据
3. **硬件资源**: 确认飞腾派数量和配置
4. **实验时间**: 确认实验窗口（避免其他实验冲突）

### 定期检查点

- **Week 1 End**: 基础系统演示
- **Week 2 Mid**: 部分实验数据展示
- **Week 2 End**: 完整数据集审查
- **Week 3 Mid**: 图表和初稿审查
- **Week 3 End**: 最终交付

---

## ✅ 检查清单

### 启动前检查 (Day 0)

- [ ] 飞腾派硬件就位（至少1台，推荐2台）
- [ ] 网络环境配置完成（SSH访问、外网连接）
- [ ] PQ-NTOR代码库已更新到最新版本
- [ ] 确认实验时间窗口（至少连续3周）
- [ ] 团队成员角色分工明确
- [ ] 数据存储空间充足（至少50GB）

### Phase 1 完成检查 (Day 7)

- [ ] Skyfield环境测试通过
- [ ] 7节点容器全部正常运行
- [ ] 轨道仿真器实时运行>1小时无崩溃
- [ ] 网络拓扑更新延迟<200ms
- [ ] 可视化工具（可选）正常工作

### Phase 2 完成检查 (Day 14)

- [ ] 每种链路至少30次有效测试
- [ ] PQ和传统Ntor对照组数据量相等
- [ ] 动态切换测试至少20次成功
- [ ] 所有数据CSV格式正确，无缺失
- [ ] 数据已备份到至少2个位置

### Phase 3 完成检查 (Day 21)

- [ ] 8-10张PDF图表生成完毕
- [ ] 统计分析结果通过显著性检验
- [ ] Evaluation章节草稿完成（~3000字）
- [ ] 技术报告完整（~18,000字）
- [ ] 实验可复现指南完成

---

## 🎊 预期成果

### 学术成果

1. **论文章节**: 完整的Evaluation章节（~3000字）
2. **图表**: 8-10张出版级PDF图表
3. **数据集**: 800+条实验数据记录
4. **技术报告**: 详尽的实验报告和系统文档

### 技术成果

1. **SAGIN仿真系统**: 基于Skyfield的完整仿真平台
2. **测试框架**: 可复用的PQ-NTOR性能测试框架
3. **可视化工具**: 实时拓扑可视化（可选）
4. **开源代码**: 完整系统代码（~2000行）

### 创新点

1. **首个ARM平台SAGIN实时仿真**: 使用Skyfield在飞腾派上实现
2. **首个PQ-Tor在SAGIN的性能评估**: 填补文献空白
3. **多层异构网络测试**: 星间、星地、星空、空地链路全覆盖
4. **动态拓扑感知**: 实时轨道仿真驱动网络配置

---

## 📝 工作记录

### 更新日志

| 日期 | 更新内容 | 负责人 |
|-----|---------|--------|
| 2025-11-12 | 创建工作列表初稿 | - |
| - | - | - |

### 问题跟踪

| ID | 问题描述 | 状态 | 解决方案 | 更新时间 |
|----|---------|------|---------|---------|
| - | - | - | - | - |

---

**创建日期**: 2025-11-12
**预计完成日期**: 2025-12-03（3周）
**工作列表版本**: v1.0
**状态**: 待启动

---

**准备就绪，等待启动指令！** 🚀
