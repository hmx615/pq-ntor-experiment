# PQ-NTOR 12拓扑实验框架

**创建日期**: 2025-11-24
**实验目标**: 在12种SAGIN NOMA拓扑下测试PQ-NTOR后量子加密协议性能

---

## 📋 项目概述

本实验框架将PQ-NTOR（后量子Tor协议）应用到12种SAGIN NOMA拓扑场景，测试后量子加密在空天地一体化网络中的性能表现。

### 核心特性

- ✅ **12种拓扑全覆盖**: 包含上行(1-6)和下行(7-12)所有NOMA拓扑
- ✅ **后量子加密**: 基于Kyber-512 KEM的PQ-NTOR协议
- ✅ **网络仿真**: Linux tc/netem模拟不同链路质量
- ✅ **卫星轨道集成**: 利用Skyfield计算真实卫星位置和链路延迟
- ✅ **自动化测试**: Python脚本自动化运行所有测试
- ✅ **性能分析**: 收集PQ握手时间、延迟、吞吐量等指标

---

## 🏗️ 目录结构

```
pq-ntor-12topo-experiment/
├── configs/                  # 拓扑Tor映射配置 (12个JSON)
│   ├── topo01_tor_mapping.json
│   ├── topo02_tor_mapping.json
│   └── ...
├── scripts/                  # 测试和分析脚本
│   ├── generate_all_tor_mappings.py    # 生成配置文件
│   ├── run_pq_ntor_12topologies.py     # 主测试脚本 ⭐
│   ├── satellite_integration.py        # 卫星轨道集成
│   ├── analyze_results.py              # 结果分析
│   └── quick_test.sh                   # 快速测试脚本
├── results/                  # 实验结果
│   ├── local_wsl/            # WSL本地测试结果
│   │   ├── topo01_results.json
│   │   └── overall_report_*.json
│   ├── phytium_pi/           # 飞腾派实测结果
│   └── analysis/             # 分析报告
│       └── comparison_report_*.md
├── logs/                     # 测试日志
│   ├── directory_topo01_run01.log
│   ├── guard_topo01_run01.log
│   └── ...
└── README.md                 # 本文档
```

---

## 🚀 快速开始

### 前置要求

1. **PQ-NTOR程序已编译**
   ```bash
   cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
   make
   ```

2. **Sudo权限配置（用于tc）**
   ```bash
   sudo visudo
   # 添加: your_username ALL=(ALL) NOPASSWD: /sbin/tc
   ```

3. **Python依赖**
   ```bash
   pip3 install psutil skyfield numpy
   ```

### 快速测试（推荐首次使用）

```bash
cd scripts
./quick_test.sh
```

这将测试拓扑1，运行3次，验证整个流程是否正常。

### 完整测试

```bash
# 测试所有12个拓扑，每个运行10次（约需1-2小时）
python3 scripts/run_pq_ntor_12topologies.py

# 快速模式：每个拓扑仅运行3次
python3 scripts/run_pq_ntor_12topologies.py --quick

# 测试指定拓扑
python3 scripts/run_pq_ntor_12topologies.py --topo 6 --runs 10

# 测试拓扑范围
python3 scripts/run_pq_ntor_12topologies.py --start 1 --end 6 --runs 5
```

### 查看结果

```bash
# 分析所有拓扑结果
python3 scripts/analyze_results.py

# 分析单个拓扑
python3 scripts/analyze_results.py --topo 1

# 查看原始JSON结果
cat results/local_wsl/topo01_results.json | jq .

# 查看对比报告
cat results/analysis/comparison_report_*.md
```

---

## 📊 12种拓扑说明

| 拓扑ID | 名称 | 方向 | Tor电路示例 | 网络参数 |
|--------|------|------|------------|----------|
| 1 | Z1 Up - 直连NOMA | 上行 | Ground2 → UAV2 → SAT → SAT | 20ms, 35Mbps, 1.25% |
| 2 | Z1 Up - 双路径 | 上行 | Ground3 → UAV2 → SAT → SAT | 25ms, 40Mbps, 0.8% |
| 3 | Z3 Up - 双终端中继 | 上行 | Ground1 → UAV1 → SAT → SAT | 18ms, 60Mbps, 0.5% |
| 4 | Z4 Up - 混合直连+协作 | 上行 | Ground3 → UAV2 → SAT → SAT | 22ms, 50Mbps, 0.7% |
| 5 | Z5 Up - 多层树形 | 上行 | Ground1 → UAV2 → SAT → SAT | 20ms, 55Mbps, 0.6% |
| 6 | Z6 Up - 无人机+终端双中继 | 上行 | Ground1 → UAV1 → SAT → SAT | 15ms, 50Mbps, 0.6% |
| 7 | Z1 Down - 直连NOMA+协作 | 下行 | Ground2 → SAT → SAT → UAV2 | 25ms, 30Mbps, 1.5% |
| 8 | Z2 Down - 多跳协作下行 | 下行 | Ground3 → SAT → SAT → UAV2 | 35ms, 25Mbps, 2.0% |
| 9 | Z3 Down - T用户协作下行 | 下行 | Ground2 → SAT → SAT → UAV1 | 28ms, 35Mbps, 1.2% |
| 10 | Z4 Down - 混合直连+单跳协作 | 下行 | Ground3 → SAT → SAT → UAV2 | 30ms, 28Mbps, 1.8% |
| 11 | Z5 Down - 混合多跳协作 | 下行 | Ground3 → SAT → SAT → UAV2 | 40ms, 22Mbps, 2.5% |
| 12 | Z6 Down - 双中继协作下行 | 下行 | Ground1 → SAT → SAT → UAV1 | 32ms, 30Mbps, 1.6% |

---

## 🔧 配置文件说明

每个拓扑的配置文件（`configs/topoXX_tor_mapping.json`）包含:

```json
{
  "topology_id": 1,
  "topology_name": "Z1 Up - 直连NOMA",

  "tor_circuit_mapping": {
    "roles": {
      "client": {"sagin_node": "Ground2", ...},
      "guard": {"sagin_node": "UAV2", "port": 6001, ...},
      "middle": {"sagin_node": "SAT", "port": 6002, ...},
      "exit": {"sagin_node": "SAT", "port": 6003, ...}
    }
  },

  "network_simulation": {
    "tc_commands": [...],
    "aggregate_params": {
      "delay_ms": 20,
      "bandwidth_mbps": 35,
      "loss_percent": 1.25
    }
  },

  "satellite_orbit_integration": {
    "enabled": true,
    "dynamic_parameters": {...}
  },

  "test_configuration": {
    "num_runs": 10,
    "timeout_seconds": 120
  }
}
```

---

## 🛰️ 卫星轨道集成

卫星轨道模块（`satellite_integration.py`）提供:

- **静态模式**: 使用固定时刻的卫星位置（可重复测试）
- **动态模式**: 实时计算卫星位置和链路延迟
- **传播延迟计算**: 基于卫星距离自动计算电磁波传播时间
- **通信窗口检测**: 验证仰角>10°的可见时段

使用示例:

```python
from satellite_integration import SatelliteLinkCalculator

# 静态模式
calc = SatelliteLinkCalculator(use_static_snapshot=True)
state = calc.get_satellite_state()
delay_ms = calc.calculate_propagation_delay()

# 动态模式
calc_dynamic = SatelliteLinkCalculator(use_static_snapshot=False)
adjusted_params = calc_dynamic.adjust_network_params_for_satellite(
    base_params={'delay_ms': 20, 'bandwidth_mbps': 50}
)
```

---

## 📈 性能指标

测试收集的指标:

### 1. PQ-NTOR特有指标
- **PQ握手时间** (μs): Kyber-512 密钥封装/解封装时间
- **电路建立时间** (ms): 3-hop Tor电路完整建立时间
- **PQ开销**: 与传统NTOR相比的额外开销

### 2. 网络性能
- **总RTT** (ms): 端到端往返时延
- **吞吐量** (Mbps): 数据传输速率
- **丢包率** (%): 实际测量的丢包率

### 3. 可靠性
- **成功率** (%): 测试成功的比例
- **失败原因**: 超时/连接失败/加密错误等

---

## 🔍 故障排查

### 1. 端口占用

```bash
# 检查端口占用
lsof -i :5000,6001,6002,6003

# 强制清理
pkill -9 directory; pkill -9 relay; pkill -9 client
```

### 2. tc配置失败

```bash
# 检查tc权限
sudo tc qdisc show dev lo

# 手动清理tc规则
sudo tc qdisc del dev lo root
```

### 3. PQ-NTOR启动失败

```bash
# 查看详细日志
tail -f logs/directory_topo01_run01.log
tail -f logs/guard_topo01_run01.log
tail -f logs/client_topo01_run01.log

# 重新编译
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make clean && make
```

---

## 🎯 下一步计划

### 阶段1: 本地仿真 ✅（当前）
- [x] 设计实验框架
- [x] 创建拓扑配置
- [x] 编写测试脚本
- [x] 集成卫星轨道
- [ ] 本地WSL完整测试
- [ ] 结果分析和优化

### 阶段2: 飞腾派物理设备测试
- [ ] 适配6+1分布式架构
- [ ] Docker容器部署
- [ ] 真实网络测试
- [ ] 性能对比分析

---

## 📚 相关文档

- [实验设计方案](../实验设计_PQ-NTOR_12拓扑测试.md)
- [NOMA拓扑定义](../noma-topologies/README.md)
- [PQ-NTOR源码](../docker/build_context/c/)
- [卫星轨道模块](../satellite_orbit.py)

---

## 👥 贡献者

- **Claude Code** - 实验框架设计和实现
- **指导教师** - 实验需求和方向
- **师妹** - 卫星轨道数据提供

---

## 📝 更新日志

### 2025-11-24
- ✅ 创建实验框架目录结构
- ✅ 生成12个拓扑Tor映射配置
- ✅ 编写主测试脚本 `run_pq_ntor_12topologies.py`
- ✅ 集成卫星轨道模块 `satellite_integration.py`
- ✅ 创建结果分析脚本 `analyze_results.py`
- ✅ 添加快速测试脚本 `quick_test.sh`
- ✅ 验证PQ-NTOR编译环境

---

**项目状态**: 🚧 开发中 | 📅 更新: 2025-11-24
