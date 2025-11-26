# PQ-NTOR 12拓扑实验设计方案

**创建时间**: 2025-11-24
**实验目标**: 在12种SAGIN NOMA拓扑下测试PQ-NTOR后量子加密协议性能

---

## 📋 实验需求理解

### 老师的要求（原文）
> "把现有的加密的程序放到12个拓扑里跑，首先在本地仿真，每个节点的区别就是链路质量，位置的不一样。然后再放到飞腾派测试实际数据。卫星的数据或者说是轨道可以参考师妹发的satellite_orbit.py文件"

### 需求拆解

1. **加密程序**: PQ-NTOR（后量子Tor协议）
   - 位置: `/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/`
   - 核心: Kyber-512 KEM + 3-hop onion routing
   - 组件: Directory Server, Guard Relay, Middle Relay, Exit Relay, Client

2. **12个拓扑**: SAGIN NOMA拓扑（已定义）
   - 位置: `/home/ccc/pq-ntor-experiment/sagin-experiments/noma-topologies/configs/`
   - 拓扑1-6: 上行链路（Uplink）
   - 拓扑7-12: 下行链路（Downlink）

3. **节点区别**:
   - **链路质量**: 延迟（delay_ms）、带宽（bandwidth_mbps）、丢包率（loss_percent）
   - **节点位置**: 卫星（SAT）、无人机（UAV1/2）、地面终端（Ground1/2/3）
   - **节点角色**: Guard, Middle, Exit（映射到NOMA拓扑节点）

4. **测试环境**:
   - **阶段1**: 本地WSL仿真（Linux tc/netem模拟网络）
   - **阶段2**: 飞腾派物理设备（6+1分布式架构，真实网络）

5. **卫星轨道数据**: `satellite_orbit.py`（Skyfield库）
   - 卫星高度: ~800km LEO
   - 轨道参数: TLE数据
   - 通信窗口: 仰角>10°的可见时段

---

## 🏗️ 系统架构

### 现有架构

```
┌─────────────────────────────────────────────────────────────┐
│                   SAGIN NOMA 拓扑可视化系统                    │
├─────────────────────────────────────────────────────────────┤
│  Frontend (瘦客户端模式 - 飞腾派浏览器)                          │
│  ├─ control-panel/index.html (控制台 - 12拓扑切换)            │
│  └─ node-view/index.html (节点视图 - 6个Pi设备)                │
├─────────────────────────────────────────────────────────────┤
│  Backend (WSL服务端)                                          │
│  ├─ hub.py (WebSocket中心)                                   │
│  ├─ node_agent.py (虚拟节点代理 x6)                           │
│  └─ satellite_orbit.py (卫星轨道计算)                         │
├─────────────────────────────────────────────────────────────┤
│  PQ-NTOR加密层 (Docker容器 / 本地编译)                         │
│  ├─ directory (目录服务器 - 5000端口)                         │
│  ├─ relay_guard (守卫中继 - 6001端口)                         │
│  ├─ relay_middle (中间中继 - 6002端口)                        │
│  ├─ relay_exit (出口中继 - 6003端口)                          │
│  └─ client (Tor客户端)                                        │
├─────────────────────────────────────────────────────────────┤
│  网络仿真层 (Linux tc/netem)                                  │
│  └─ 模拟12种拓扑的链路参数                                     │
└─────────────────────────────────────────────────────────────┘
```

### 需要新增的实验框架

```
┌─────────────────────────────────────────────────────────────┐
│          PQ-NTOR 12拓扑自动化测试框架 (新增)                    │
├─────────────────────────────────────────────────────────────┤
│  实验编排器 (run_pq_ntor_12topologies.py)                     │
│  ├─ 读取12个拓扑配置                                           │
│  ├─ 启动PQ-NTOR节点（根据拓扑角色映射）                        │
│  ├─ 配置网络参数（tc/netem）                                  │
│  ├─ 执行性能测试（N次运行）                                    │
│  ├─ 集成卫星轨道数据                                           │
│  └─ 收集性能指标                                               │
├─────────────────────────────────────────────────────────────┤
│  拓扑-Tor映射器 (topology_tor_mapper.py)                      │
│  ├─ SAT → Middle/Exit Relay                                 │
│  ├─ UAV1/2 → Guard/Middle Relay                             │
│  └─ Ground1/2/3 → Client/Guard Relay                        │
├─────────────────────────────────────────────────────────────┤
│  卫星轨道集成 (satellite_integration.py)                       │
│  ├─ 实时卫星位置计算                                           │
│  ├─ 链路延迟动态调整（基于距离）                                │
│  └─ 通信窗口检测（仰角>10°）                                   │
├─────────────────────────────────────────────────────────────┤
│  结果分析器 (analyze_pq_ntor_results.py)                      │
│  ├─ PQ握手时间统计                                            │
│  ├─ 端到端延迟分析                                             │
│  ├─ 吞吐量测量                                                 │
│  ├─ 成功率计算                                                 │
│  └─ 12拓扑对比可视化                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 拓扑到Tor电路的映射规则

### 关键问题：6个虚拟节点 vs 3-hop Tor电路

**SAGIN节点**（虚拟拓扑）:
- SAT (卫星)
- UAV1, UAV2 (无人机)
- Ground1, Ground2, Ground3 (地面终端)

**Tor节点**（加密电路）:
- Directory Server (1个)
- Guard Relay (1个)
- Middle Relay (1个)
- Exit Relay (1个)
- Client (1个)

### 映射策略（基于拓扑定义）

#### 上行拓扑（Uplink 1-6）

**拓扑1: Z1 Up - 直连NOMA**
```
物理路径: UAV2 → SAT, Ground2 → SAT
Tor映射:
  Client → Ground2
  Guard → UAV2
  Middle → SAT
  Exit → SAT (复用)
  Target → 外部服务器
```

**拓扑2: Z1 Up - 双路径**
```
物理路径: Ground3 → Ground2 → SAT, Ground3 → UAV2 → SAT
Tor映射:
  Client → Ground3
  Guard → Ground2 (主路径) / UAV2 (备份)
  Middle → SAT
  Exit → SAT
```

**拓扑3: Z3 Up - 双终端中继**
```
物理路径: Ground1 → UAV1, Ground2 → UAV1, UAV1 → SAT
Tor映射:
  Client → Ground1
  Guard → UAV1
  Middle → SAT
  Exit → SAT
```

**拓扑6: Z6 Up - 无人机+终端双中继** ⭐
```
物理路径:
  路径1: Ground1 → UAV1 → SAT
  路径2: Ground3 → Ground2 → SAT
Tor映射:
  Client → Ground1
  Guard → UAV1 (路径1) / Ground2 (路径2)
  Middle → SAT
  Exit → SAT
```

#### 下行拓扑（Downlink 7-12）

**拓扑7: Z1 Down - 直连NOMA+协作**
```
物理路径: SAT → UAV2, SAT → Ground2, UAV2 ⇄ Ground2
Tor映射:
  Client → 外部
  Guard → SAT
  Middle → SAT
  Exit → UAV2 / Ground2
  Target → Ground2
```

### 统一映射规则

| SAGIN节点类型 | Tor角色候选 | 优先级 |
|--------------|-----------|-------|
| SAT (卫星) | Middle/Exit | 高（核心节点） |
| UAV (无人机) | Guard/Middle | 中（中继节点） |
| Ground (终端) | Client/Guard | 低（边缘节点） |

---

## 📊 实验指标

### 性能指标

1. **PQ-NTOR握手性能**
   - PQ握手时间（微秒）
   - Kyber-512 KEM封装/解封装时间
   - 密钥协商成功率

2. **端到端通信性能**
   - 总延迟（RTT）
   - 吞吐量（Mbps）
   - 丢包率（%）

3. **拓扑特定指标**
   - 不同NOMA配置的影响
   - 协作通信vs非协作
   - 上行vs下行性能差异

4. **卫星轨道影响**
   - 动态延迟变化
   - 多普勒效应
   - 通信窗口利用率

### 数据收集

```python
# 每次测试收集的数据结构
{
  "topology_id": 1,
  "topology_name": "Z1 Up - 直连NOMA",
  "run_id": 1,
  "timestamp": "2025-11-24T10:30:00",

  "network_config": {
    "delay_ms": 20,
    "bandwidth_mbps": 50,
    "loss_percent": 0.5
  },

  "satellite_state": {
    "position_enu": [12000.5, 8000.3, 800000.0],
    "elevation_deg": 45.2,
    "distance_km": 850.5,
    "in_comm_window": true
  },

  "pq_ntor_metrics": {
    "handshake_time_us": 152,
    "circuit_build_time_ms": 350,
    "total_rtt_ms": 420,
    "throughput_mbps": 45.2,
    "success": true
  },

  "tor_circuit": {
    "guard": "UAV2",
    "middle": "SAT",
    "exit": "SAT",
    "hops": 3
  }
}
```

---

## 🚀 实施步骤

### 阶段1: 本地WSL仿真（优先）

#### Step 1: 准备PQ-NTOR程序
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make clean && make
```

#### Step 2: 创建拓扑-Tor映射配置
生成12个拓扑的Tor电路配置文件

#### Step 3: 编写测试脚本
- `run_pq_ntor_12topologies.py` - 主测试脚本
- `topology_tor_mapper.py` - 拓扑映射器
- `satellite_integration.py` - 卫星轨道集成

#### Step 4: 本地测试运行
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments
python3 run_pq_ntor_12topologies.py --mode local --runs 10
```

#### Step 5: 数据分析
```bash
python3 analyze_pq_ntor_results.py --input results/pq_ntor_12topo_*.json
```

### 阶段2: 飞腾派物理设备测试

#### Step 1: 适配部署脚本
修改 `deploy_all.sh` 支持PQ-NTOR容器

#### Step 2: 6+1架构映射
```
Pi-1 (SAT)    → Middle/Exit Relay
Pi-2 (UAV1)   → Guard Relay
Pi-3 (UAV2)   → Guard Relay
Pi-4 (Ground1) → Client
Pi-5 (Ground2) → Client/Guard
Pi-6 (Ground3) → Client
WSL (Hub)     → Directory Server
```

#### Step 3: 真实网络测试
使用物理Pi设备间的真实网络延迟

---

## 📂 文件结构规划

```
/home/ccc/pq-ntor-experiment/sagin-experiments/
├── pq-ntor-12topo-experiment/          # 新建实验目录
│   ├── configs/                         # 拓扑-Tor映射配置
│   │   ├── topo01_tor_mapping.json
│   │   ├── topo02_tor_mapping.json
│   │   └── ... (12个)
│   ├── scripts/                         # 测试脚本
│   │   ├── run_pq_ntor_12topologies.py  # 主测试脚本
│   │   ├── topology_tor_mapper.py       # 拓扑映射器
│   │   ├── satellite_integration.py     # 卫星轨道集成
│   │   └── analyze_pq_ntor_results.py   # 结果分析
│   ├── results/                         # 实验结果
│   │   ├── local_wsl/                   # WSL本地测试
│   │   └── phytium_pi/                  # 飞腾派实测
│   └── logs/                            # 日志文件
├── satellite_orbit.py                   # 卫星轨道计算（已有）
└── noma-topologies/                     # NOMA拓扑配置（已有）
```

---

## ⚠️ 技术挑战和解决方案

### 挑战1: 6虚拟节点 vs 3-hop Tor电路

**问题**: SAGIN有6个节点，但Tor只需要3-hop（Guard-Middle-Exit）

**解决方案**:
- 每个拓扑定义明确的Tor电路映射
- 未使用的节点作为"旁观者"（监控、备份）
- 支持多路径场景（如拓扑2）

### 挑战2: 动态卫星位置

**问题**: 卫星在移动，延迟/距离实时变化

**解决方案**:
- **静态测试**: 选择固定时刻的卫星位置
- **动态测试**: 在通信窗口内多次测试，记录轨道状态
- 使用`satellite_orbit.py`的`get_satellite_position_for_env(time)`

### 挑战3: 网络仿真精度

**问题**: Linux tc/netem无法完美模拟卫星信道

**解决方案**:
- **本地**: tc/netem提供基础延迟/丢包/带宽限制
- **飞腾派**: 真实物理网络（WiFi/以太网）+ tc增强
- 记录差异，对比分析

### 挑战4: PQ-NTOR性能开销

**问题**: Kyber-512增加了额外的计算和通信开销

**测量方法**:
- 对比传统NTOR vs PQ-NTOR
- 分离测量:
  - KEM封装时间
  - KEM解封装时间
  - 网络传输时间
  - 总握手时间

---

## 📈 预期成果

### 实验输出

1. **性能报告**
   - 12种拓扑下的PQ-NTOR性能对比
   - 上行vs下行性能差异分析
   - 卫星轨道影响量化

2. **可视化图表**
   - PQ握手时间柱状图（12拓扑）
   - 端到端延迟箱线图
   - 成功率饼图
   - 卫星轨道vs性能散点图

3. **科研数据**
   - 原始实验数据（JSON格式）
   - 统计分析结果
   - 论文素材

### 验证目标

✅ PQ-NTOR在SAGIN场景下的可行性
✅ 后量子加密对不同拓扑的性能影响
✅ 卫星通信中PQ密钥协商的实际表现
✅ NOMA协作通信与PQ加密的兼容性

---

## 🎯 下一步行动

### 立即开始（本次会话）

1. ✅ **完成此设计文档**
2. 🔄 **创建拓扑-Tor映射配置** (进行中)
3. 🔄 **编写主测试脚本框架**
4. 📝 **验证PQ-NTOR编译环境**

### 后续任务

5. 集成卫星轨道数据
6. 本地WSL测试运行
7. 结果分析脚本
8. 飞腾派适配

---

**文档版本**: v1.0
**状态**: ✅ 设计完成，待评审
**下一步**: 创建拓扑-Tor映射配置
