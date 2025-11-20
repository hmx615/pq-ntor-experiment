# SAGIN 仿真系统使用指南

**版本**: 1.0
**日期**: 2025-11-12
**状态**: ✅ Phase 1 完成

---

## 📋 系统概述

SAGIN (Space-Air-Ground Integrated Network) 仿真系统是一个基于真实轨道数据的7节点混合网络仿真平台，用于测试 PQ-NTOR 协议在复杂动态拓扑中的性能。

### 核心组件

1. **轨道仿真器** (`sagin_orbit_simulator.py`)
   - 基于 Skyfield 库和 SGP4 算法
   - 实时计算卫星、飞机、地面站位置
   - 动态计算链路可见性和延迟

2. **网络拓扑管理器** (`network_topology_manager.py`)
   - 使用 tc netem 控制链路延迟
   - 使用 iptables 控制链路启用/禁用
   - 实时同步网络状态与轨道仿真

3. **集成控制器** (`sagin_integration.py`)
   - Docker 容器管理
   - 组件编排
   - 日志和监控

4. **快速启动脚本** (`quick_start.sh`)
   - 一键启动/停止
   - 状态检查
   - 环境清理

### 网络拓扑

**7个节点**:
- **2颗卫星**: Sat-1 (LEO, 550km), Sat-2 (MEO, 8000km)
- **2架飞机**: Aircraft-1 (Beijing→London), Aircraft-2 (London→NewYork)
- **3个地面站**: GS-Beijing, GS-London, GS-NewYork

**5种链路类型**:
1. ISL (Inter-Satellite Link) - 星间链路
2. SGLink (Satellite-Ground Link) - 星地链路
3. SALink (Satellite-Aircraft Link) - 星机链路
4. AGLink (Aircraft-Ground Link) - 机地链路
5. GLink (Ground Link) - 地面链路（基准）

---

## 🚀 快速开始

### 1. 检查系统要求

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts
sudo ./quick_start.sh check
```

**要求**:
- Docker (容器化)
- Python 3.8+ (脚本运行)
- Skyfield 库 (轨道计算)
- root 权限 (Docker 和网络配置)

### 2. 运行测试

```bash
# 单元测试（测试各组件）
sudo ./quick_start.sh unit-test

# Dry-run 测试（不创建真实容器）
sudo ./quick_start.sh test
```

### 3. 启动仿真

```bash
# 运行10分钟（默认）
sudo ./quick_start.sh start

# 运行5分钟，每10秒更新一次拓扑
sudo ./quick_start.sh start 5 10

# 无限运行（按 Ctrl+C 停止）
sudo ./quick_start.sh infinite

# 无限运行，每5秒更新一次
sudo ./quick_start.sh infinite 5
```

### 4. 查看状态

```bash
# 查看系统状态和日志
sudo ./quick_start.sh status

# 实时查看日志
tail -f /tmp/sagin_integration.log
```

### 5. 清理环境

```bash
# 停止所有容器并清理网络
sudo ./quick_start.sh cleanup
```

---

## 📊 输出和日志

### 日志文件

**位置**: `/tmp/sagin_integration.log`

**内容**:
- 拓扑更新事件
- 链路启用/禁用记录
- 网络延迟变化
- 错误和警告

**示例**:
```
2025-11-12 15:12:36 - INFO - === Iteration 1 at 2025-11-12T07:12:36Z ===
2025-11-12 15:12:36 - INFO - Visible links: 3/21
2025-11-12 15:12:36 - INFO - Applied 3 link enables, 0 link disables, 0 link updates
```

### 控制台输出

实时显示：
- 仿真进度
- 可见链路数量
- 网络更新统计

---

## 🔧 高级用法

### 直接使用 Python 脚本

#### 1. 轨道仿真器

```bash
# 测试轨道仿真
python3 sagin_orbit_simulator.py

# 在代码中使用
from sagin_orbit_simulator import SAGINOrbitSimulator

sim = SAGINOrbitSimulator('configs/sagin_topology_config.json')
topology = sim.get_network_topology()
print(f"可见链路: {topology['visible_link_count']}")
```

#### 2. 网络拓扑管理器

```bash
# 测试网络管理器
python3 network_topology_manager.py

# 在代码中使用
from network_topology_manager import NetworkTopologyManager

mgr = NetworkTopologyManager('configs/sagin_topology_config.json', dry_run=False)
mgr.apply_topology_update(topology)
```

#### 3. 完整集成

```bash
# 运行30分钟，每5秒更新
python3 sagin_integration.py --duration 30 --interval 5

# Dry-run 模式（不修改网络）
python3 sagin_integration.py --dry-run --duration 5

# 只运行仿真，不创建容器
python3 sagin_integration.py --no-docker --duration 5

# 只清理，不运行
python3 sagin_integration.py --cleanup-only
```

---

## 📁 目录结构

```
sagin-experiments/
├── configs/
│   └── sagin_topology_config.json       # 拓扑配置
│
├── scripts/
│   ├── sagin_orbit_simulator.py         # 轨道仿真器
│   ├── network_topology_manager.py      # 网络管理器
│   ├── sagin_integration.py             # 集成控制器
│   └── quick_start.sh                   # 快速启动脚本
│
├── tests/
│   └── test_skyfield_basic.py           # Skyfield 基础测试
│
├── docs/
│   ├── Skyfield-SAGIN实施工作列表.md    # 工作计划
│   └── 代码重构评估与本地验证方案.md    # 代码评估
│
└── results/                             # 实验结果（待生成）
```

---

## 🧪 测试场景

根据配置文件定义了5个测试场景：

### Scenario 1: 星间链路 (ISL)
- **路径**: Sat-1 ↔ Sat-2
- **预期延迟**: 10ms
- **预期距离**: 3000km

### Scenario 2: 星地链路
- **路径**: Sat-1 ↔ GS-Beijing
- **预期延迟**: 5ms
- **预期距离**: 1000km

### Scenario 3: 多跳混合链路
- **路径**: GS-Beijing → Sat-1 → Aircraft-1 → GS-London
- **预期延迟**: 50ms
- **预期距离**: 8000km

### Scenario 4: 全球端到端
- **路径**: GS-Beijing → Sat-1 → Sat-2 → GS-NewYork
- **预期延迟**: 100ms
- **预期距离**: 13000km

### Scenario 5: 动态切换
- **路径**: GS-Beijing → Sat-1 → GS-London
- **特点**: 动态可见性变化
- **持续时间**: 30分钟

---

## 🐛 故障排查

### 问题1: Docker 权限错误

**错误**: `permission denied while trying to connect to the Docker daemon`

**解决**:
```bash
sudo ./quick_start.sh [command]
```

### 问题2: Skyfield 库未安装

**错误**: `ModuleNotFoundError: No module named 'skyfield'`

**解决**:
```bash
pip3 install skyfield
```

### 问题3: 容器无法创建

**错误**: `Error response from daemon: Conflict`

**解决**:
```bash
# 清理旧容器
sudo ./quick_start.sh cleanup

# 重新启动
sudo ./quick_start.sh start
```

### 问题4: 网络配置失败

**错误**: `tc: command not found` 或 `iptables: command not found`

**解决**: 这些命令在容器内运行，确保容器正确创建并安装了 `iproute2` 和 `iptables`。

---

## 📈 性能监控

### 查看链路状态

在仿真运行期间，可以进入容器查看网络配置：

```bash
# 进入容器
docker exec -it sagin_sat-1 bash

# 查看 tc 配置
tc qdisc show dev eth0

# 查看 iptables 规则
iptables -L OUTPUT

# 测试连通性
ping 172.20.1.12  # Ping Sat-2
```

### 提取性能数据

日志中包含每次拓扑更新的详细信息：

```bash
# 提取链路变化事件
grep "Applied.*link" /tmp/sagin_integration.log

# 提取可见链路统计
grep "Visible links" /tmp/sagin_integration.log

# 统计拓扑更新次数
grep "Iteration" /tmp/sagin_integration.log | wc -l
```

---

## 🔄 与 PQ-NTOR 集成

### Phase 2 计划（Week 2）

在 Phase 1 完成后，将在此基础上集成 PQ-NTOR 性能测试：

1. **在容器中部署 PQ-NTOR**
   - 每个容器运行 PQ-NTOR 节点
   - 配置中继和客户端

2. **运行性能测试**
   - 测试各种链路类型的电路建立时间
   - 测量延迟、吞吐量、超时率
   - 对比 PQ-NTOR 和传统 NTOR

3. **数据收集**
   - 收集每个测试场景的性能指标
   - 生成对比图表
   - 分析动态切换场景的表现

### 预期修改

- 容器镜像：从 `ubuntu:22.04` 改为包含 PQ-NTOR 的自定义镜像
- 端口映射：为每个节点暴露 PQ-NTOR 端口
- 测试脚本：添加自动化测试脚本，在容器间运行 PQ-NTOR 测试

---

## 📝 配置修改

### 修改拓扑配置

编辑 `configs/sagin_topology_config.json`:

```json
{
  "satellites": {
    "Sat-1": {
      "altitude_km": 550,      // 修改轨道高度
      "ip": "172.20.1.11",     // 修改 IP 地址
      "max_range_km": 2000     // 修改通信距离
    }
  },
  "network_parameters": {
    "topology_update_interval_sec": 10,  // 修改更新间隔
    "max_hops": 3                        // 修改最大跳数
  }
}
```

### 修改仿真参数

在命令行中指定：

```bash
# 修改更新间隔为5秒
sudo ./quick_start.sh start 10 5

# 修改持续时间为30分钟
sudo ./quick_start.sh start 30 10
```

---

## ✅ Phase 1 完成检查清单

- [x] Task 1.1: Skyfield 环境配置
- [x] Task 1.2: SAGIN 拓扑配置文件
- [x] Task 1.3: 轨道仿真器开发
- [x] Task 1.4: Docker 网络拓扑管理器
- [x] Task 1.5: 端到端集成
- [x] 快速启动脚本
- [x] 使用文档

---

## 📞 下一步工作

**Phase 2 (Week 2)**: PQ-NTOR 性能测试

1. 构建 PQ-NTOR Docker 镜像
2. 适配测试脚本到容器化环境
3. 运行5个测试场景
4. 收集和分析性能数据

**Phase 3 (Week 3)**: 数据分析和论文撰写

1. 生成对比图表
2. 撰写实验部分
3. 完成论文初稿

---

**最后更新**: 2025-11-12
**维护者**: Claude Code
**状态**: ✅ Phase 1 完成，可以进入 Phase 2
