# PQ-NTOR 12拓扑实验框架 - 详细分析报告

**生成时间**: 2025-11-24  
**分析对象**: `/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment`  
**项目状态**: 🚧 开发中 | 框架完成度: 80%

---

## 1. 整体目录结构

### 1.1 核心目录树

```
pq-ntor-12topo-experiment/
├── README.md                          # 项目文档（详细指南）
├── configs/                           # 12个拓扑Tor映射配置
│   ├── topo01_tor_mapping.json        # 拓扑1：Z1 Up - 直连NOMA
│   ├── topo02_tor_mapping.json        # 拓扑2：Z1 Up - 双路径
│   ├── ...
│   └── topo12_tor_mapping.json        # 拓扑12：Z6 Down - 双中继协作下行
│
├── scripts/                           # 核心测试和分析脚本 (5个)
│   ├── run_pq_ntor_12topologies.py    # ⭐ 主测试脚本 (600+行)
│   ├── satellite_integration.py       # 卫星轨道集成 (336行)
│   ├── analyze_results.py             # 结果分析工具 (199行)
│   ├── generate_all_tor_mappings.py   # 配置生成器
│   ├── quick_test.sh                  # 快速验证脚本
│   └── monitor_test.sh                # 监控脚本
│
├── results/                           # 实验结果输出
│   ├── local_wsl/                     # WSL本地仿真结果
│   │   ├── topo01_results.json        # 已有结果
│   │   ├── topo02_results.json
│   │   ├── topo03_results.json
│   │   └── overall_report_*.json
│   │
│   ├── phytium_pi/                    # 飞腾派物理设备结果（预留）
│   │   └── (待填充)
│   │
│   └── analysis/                      # 分析报告和图表
│       └── comparison_report_*.md     # 拓扑对比报告
│
└── logs/                              # 详细测试日志 (70+个文件)
    ├── directory_topo01_run01.log
    ├── guard_topo01_run01.log
    ├── middle_topo01_run01.log
    ├── exit_topo01_run01.log
    ├── client_topo01_run01.log
    └── ... (每个拓扑 x 多次运行 x 4个角色 = 70+日志文件)
```

### 1.2 统计数据

| 指标 | 数值 |
|------|------|
| **总文件数** | 71个 |
| **目录总大小** | 316 KB |
| **配置文件** | 12个 (JSON) |
| **脚本文件** | 5个 (Python/Shell) |
| **日志文件** | 70+个 |
| **已有结果** | 3个拓扑 (JSON) |

---

## 2. 包含的文件和子目录详解

### 2.1 配置目录 (configs/)

**文件数**: 12个配置文件，每个对应一个NOMA拓扑

**配置文件格式** (`topo{XX}_tor_mapping.json`):

```json
{
  "topology_id": 1,
  "topology_name": "Z1 Up - 直连NOMA",
  "description": "上行直连NOMA拓扑",
  
  "physical_topology": {
    "links": [...],
    "direction": "uplink"
  },
  
  "tor_circuit_mapping": {
    "roles": {
      "client": {"sagin_node": "Ground2", "port": null},
      "guard": {"sagin_node": "UAV2", "port": 6001},
      "middle": {"sagin_node": "SAT", "port": 6002},
      "exit": {"sagin_node": "SAT", "port": 6003},
      "directory": {"sagin_node": "HUB", "port": 5000}
    }
  },
  
  "network_simulation": {
    "method": "linux_tc_netem",
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
  
  "expected_performance": {
    "pq_handshake_us": 147,
    "circuit_build_ms": 138,
    "total_rtt_ms": 120,
    "throughput_mbps": 28,
    "success_rate_percent": 90
  },
  
  "test_configuration": {
    "num_runs": 10,
    "timeout_seconds": 120,
    "target_url": "http://127.0.0.1:8000/"
  }
}
```

**12个拓扑的网络参数对比**:

| 拓扑 | 名称 | 方向 | 延迟(ms) | 带宽(Mbps) | 丢包率(%) |
|-----|------|------|----------|-----------|---------|
| 1 | Z1 Up | 上行 | 20 | 35 | 1.25 |
| 2 | Z1 Up | 上行 | 25 | 40 | 0.8 |
| 3 | Z3 Up | 上行 | 18 | 60 | 0.5 |
| 4 | Z4 Up | 上行 | 22 | 50 | 0.7 |
| 5 | Z5 Up | 上行 | 20 | 55 | 0.6 |
| 6 | Z6 Up | 上行 | 15 | 50 | 0.6 |
| 7 | Z1 Down | 下行 | 25 | 30 | 1.5 |
| 8 | Z2 Down | 下行 | 35 | 25 | 2.0 |
| 9 | Z3 Down | 下行 | 28 | 35 | 1.2 |
| 10 | Z4 Down | 下行 | 30 | 28 | 1.8 |
| 11 | Z5 Down | 下行 | 40 | 22 | 2.5 |
| 12 | Z6 Down | 下行 | 32 | 30 | 1.6 |

### 2.2 脚本目录 (scripts/)

#### 2.2.1 run_pq_ntor_12topologies.py (600+行) ⭐ 核心脚本

**功能**:
- 自动化运行12个拓扑的PQ-NTOR测试
- 管理PQ-NTOR进程生命周期（Directory, Guard, Middle, Exit, Client）
- 配置Linux tc/netem网络参数
- 收集和保存测试结果

**关键函数**:

| 函数 | 作用 |
|------|------|
| `configure_network()` | 使用tc/netem配置网络参数 |
| `start_directory_server()` | 启动Directory服务器(5000端口) |
| `start_relay_nodes()` | 启动Guard/Middle/Exit中继(6001-6003端口) |
| `run_client_test()` | 运行客户端测试，收集性能指标 |
| `parse_client_log()` | 从日志提取性能数据 |
| `test_single_topology()` | 测试单个拓扑N次 |
| `test_all_topologies()` | 遍历所有拓扑 |
| `generate_overall_report()` | 生成总体测试报告 |

**使用方式**:

```bash
# 快速测试（3次运行）
python3 run_pq_ntor_12topologies.py --quick

# 完整测试（每个拓扑10次）
python3 run_pq_ntor_12topologies.py

# 测试单个拓扑
python3 run_pq_ntor_12topologies.py --topo 1 --runs 5

# 测试拓扑范围
python3 run_pq_ntor_12topologies.py --start 1 --end 6 --runs 10
```

**输出**:
- 日志: `logs/` 目录（每个节点、每次运行）
- 结果: `results/local_wsl/topoXX_results.json`
- 报告: `results/local_wsl/overall_report_TIMESTAMP.json`

#### 2.2.2 satellite_integration.py (336行) 卫星轨道集成

**功能**:
- 封装卫星轨道计算（基于satellite_orbit.py）
- 计算传播延迟（基于卫星距离）
- 根据仰角动态调整网络参数

**关键类**: `SatelliteLinkCalculator`

| 方法 | 功能 |
|------|------|
| `__init__()` | 初始化，支持静态/动态模式 |
| `get_satellite_state()` | 获取卫星位置、仰角、距离 |
| `calculate_propagation_delay()` | 计算传播延迟（毫秒） |
| `adjust_network_params_for_satellite()` | 根据卫星状态调整网络参数 |
| `is_in_communication_window()` | 检查通信窗口 |
| `generate_test_time_slots()` | 生成测试时间槽 |

**使用示例**:

```python
from satellite_integration import SatelliteLinkCalculator

# 静态模式（可重复测试）
calc = SatelliteLinkCalculator(use_static_snapshot=True)
state = calc.get_satellite_state()
delay = calc.calculate_propagation_delay()  # 返回毫秒

# 动态模式（实时计算）
calc_dyn = SatelliteLinkCalculator(use_static_snapshot=False)
adjusted = calc_dyn.adjust_network_params_for_satellite(
    base_params={'delay_ms': 20, 'bandwidth_mbps': 50}
)
```

#### 2.2.3 analyze_results.py (199行) 结果分析

**功能**:
- 统计每个拓扑的测试成功率
- 计算性能指标（延迟、吞吐量等）
- 生成拓扑对比报告

**关键函数**:

| 函数 | 功能 |
|------|------|
| `analyze_single_topology()` | 分析单个拓扑的结果 |
| `analyze_all_topologies()` | 分析所有12个拓扑 |
| `generate_comparison_report()` | 生成Markdown对比报告 |

**使用方式**:

```bash
# 分析所有拓扑
python3 analyze_results.py

# 分析单个拓扑
python3 analyze_results.py --topo 1
```

**输出**: `results/analysis/comparison_report_TIMESTAMP.md`

#### 2.2.4 其他脚本

| 脚本 | 功能 |
|------|------|
| `quick_test.sh` | Shell脚本：快速验证框架（测试拓扑1，3次运行） |
| `monitor_test.sh` | 监控脚本：实时显示测试进度 |
| `generate_all_tor_mappings.py` | 初始化脚本：生成12个拓扑配置文件 |

### 2.3 结果目录 (results/)

#### 2.3.1 local_wsl/ - 本地仿真结果

**文件**:
- `topo01_results.json` - 拓扑1测试结果（已有，3次运行）
- `topo02_results.json` - 拓扑2测试结果（已有，3次运行）
- `topo03_results.json` - 拓扑3测试结果（已有，3次运行）
- `overall_report_*.json` - 总体报告

**结果JSON格式**:

```json
{
  "topology_id": 1,
  "topology_name": "Z1 Up - 直连NOMA",
  "config": { /* 完整配置 */ },
  "test_runs": [
    {
      "topology_id": 1,
      "run_id": 1,
      "success": true,
      "duration": 62.34,
      "exit_code": 0,
      "timestamp": "2025-11-24T11:28:30.123456",
      "circuit_build_time_ms": 138,
      "total_rtt_ms": 120,
      "pq_handshake_time_us": 50,
      "throughput_mbps": 28.5,
      "network_config": { /* 网络参数 */ }
    },
    /* ... 更多运行 ... */
  ],
  "summary": {
    "total_runs": 3,
    "success_count": 3,
    "success_rate": 100.0,
    "avg_duration": 62.15
  }
}
```

#### 2.3.2 analysis/ - 分析报告

**格式**: Markdown文件

**内容**: 
- 各拓扑的成功率统计
- 平均耗时/延迟/吞吐量
- 上/下行拓扑对比
- 12拓扑汇总表格

### 2.4 日志目录 (logs/) - 70+个文件

**命名规则**: `{role}_topo{XX}_run{YY}.log`

**日志文件类型**:
- `directory_topo*_run*.log` - Directory服务器日志
- `guard_topo*_run*.log` - Guard中继日志
- `middle_topo*_run*.log` - Middle中继日志
- `exit_topo*_run*.log` - Exit中继日志
- `client_topo*_run*.log` - Client客户端日志
- `full_test_run.log` - 完整测试运行日志

**日志大小统计**:
- 总大小: 148 KB
- 典型单日志: 40-50 行

---

## 3. 与主项目的关系

### 3.1 项目层级关系

```
/home/ccc/pq-ntor-experiment/
│
├── sagin-experiments/                   (主项目目录)
│   │
│   ├── docker/build_context/c/          ← PQ-NTOR源码 (directory, relay, client)
│   │
│   ├── noma-topologies/                 ← 12种NOMA拓扑定义
│   │   ├── configs/topology_XX_*.json
│   │   └── README.md
│   │
│   ├── satellite_orbit.py               ← 卫星轨道模块（依赖）
│   │
│   ├── distributed-demo/                ← WebSocket分布式系统
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── docker/
│   │
│   └── pq-ntor-12topo-experiment/       ← 本目录（新增实验框架）
│       ├── configs/                     (引用noma-topologies配置)
│       ├── scripts/                     (新增测试脚本)
│       ├── results/                     (实验结果)
│       └── logs/                        (测试日志)
│
└── (其他旧项目目录)
```

### 3.2 关键依赖关系

| 依赖项 | 位置 | 用途 |
|--------|------|------|
| **PQ-NTOR程序** | `../docker/build_context/c/` | 调用 directory/relay/client 可执行文件 |
| **NOMA拓扑配置** | `../noma-topologies/configs/` | 参考拓扑定义，基础生成tor_mapping配置 |
| **卫星轨道模块** | `../satellite_orbit.py` | satellite_integration.py导入使用 |
| **Python库** | psutil, skyfield, numpy | 进程管理、轨道计算、数学运算 |

### 3.3 数据流向

```
┌──────────────────────────┐
│   NOMA拓扑定义            │
│ (noma-topologies/configs) │
└────────────┬─────────────┘
             │ (参考)
             ▼
┌──────────────────────────────────┐
│  配置生成器                       │
│ (generate_all_tor_mappings.py)    │
└────────────┬─────────────────────┘
             │ (生成)
             ▼
┌──────────────────────────┐
│   Tor映射配置             │
│ (configs/topoXX_*.json)   │
└────────────┬─────────────┘
             │ (读取)
             ▼
┌──────────────────────────────────────┐
│   主测试脚本                          │
│ (run_pq_ntor_12topologies.py)         │
├───────────────────────────────────────┤
│  ├─ 配置网络(tc/netem)                │
│  ├─ 启动PQ-NTOR(directory/relay...)   │
│  ├─ 运行客户端测试                     │
│  └─ 收集结果                          │
└────────────┬────────────────────────┘
             │ (生成)
             ▼
┌──────────────────────────┐
│   测试结果                │
│ (results/local_wsl/*.json)│
└────────────┬─────────────┘
             │ (分析)
             ▼
┌──────────────────────────────────┐
│   对比报告                        │
│ (results/analysis/*.md)           │
└──────────────────────────────────┘
```

---

## 4. 现有代码和配置的状态

### 4.1 完成度评估

| 组件 | 状态 | 完成度 | 备注 |
|------|------|--------|------|
| **框架设计** | ✅ | 100% | README + 详细说明 |
| **拓扑配置** | ✅ | 100% | 12个JSON配置生成完成 |
| **主测试脚本** | ✅ | 95% | 功能完整，待性能优化 |
| **卫星轨道集成** | ✅ | 85% | 基础实现完成，待深度集成 |
| **结果分析** | ✅ | 80% | 基础分析完成，待图表/可视化 |
| **快速测试脚本** | ✅ | 100% | 验证脚本完成 |
| **本地WSL测试** | ⚠️ | 30% | 已测试3个拓扑，共9次运行 |
| **飞腾派集成** | ⏳ | 0% | 待开发 |

### 4.2 已有实验数据

**已完成的测试**: 3个拓扑 × 3次运行 = 9次

**结果统计**:
- `topo01_results.json`: 3次运行，100%成功率，平均耗时 ~62秒
- `topo02_results.json`: 3次运行，100%成功率
- `topo03_results.json`: 3次运行，100%成功率

**日志数据**: 70+个日志文件（包含详细执行过程）

### 4.3 现有问题和改进空间

#### 已发现的问题

| 问题 | 严重性 | 状态 | 描述 |
|------|--------|------|------|
| psutil deprecation | 低 | ⚠️ | `proc.connections()` 已弃用，应改用 `net_connections()` |
| 性能指标估算 | 中 | ⚠️ | 部分性能指标（PQ握手时间）使用固定值（50μs）而非日志解析 |
| 卫星动态参数 | 中 | ⚠️ | 卫星轨道数据未实际集成到测试流程中 |
| 飞腾派适配 | 高 | ⏳ | 还需适配6+1分布式部署模式 |

#### 改进建议

1. **性能指标完善**:
   - 从日志精确解析PQ握手时间
   - 实现端到端延迟测量
   - 添加吞吐量实际计算

2. **卫星轨道深度集成**:
   - 根据实时卫星仰角调整网络参数
   - 实现通信窗口检测和测试调度
   - 添加轨道参数到结果JSON

3. **可视化和报告**:
   - 生成性能对比图表（Matplotlib/Plotly）
   - 创建交互式HTML报告
   - 添加上/下行拓扑的统计对比

4. **飞腾派适配**:
   - 实现6个节点分布式部署脚本
   - 添加跨设备网络配置
   - 实现真实Tor网络（不使用localhost）

---

## 5. 实验框架的设计思路

### 5.1 核心设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                    三层递进测试架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  第1层: 本地仿真 (Linux tc/netem)                             │
│  ├─ 优点: 快速、可重复、易调试                               │
│  ├─ 工具: Linux tc命令行工具                                 │
│  └─ 耗时: ~2小时 (12拓扑 × 10次)                             │
│                                                               │
│  第2层: 飞腾派分布式测试 (6+1架构)                            │
│  ├─ 优点: 接近真实场景                                       │
│  ├─ 工具: Docker容器化部署                                  │
│  └─ 耗时: ~8小时 (包括部署和清理)                            │
│                                                               │
│  第3层: 真实卫星链路测试 (未来扩展)                           │
│  ├─ 优点: 完全真实                                           │
│  ├─ 工具: 卫星地面站、专网                                   │
│  └─ 耗时: 待定                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 配置驱动设计

**核心思想**: 所有拓扑参数通过JSON配置文件驱动，脚本通用无需修改

**优势**:
- 易于添加新拓扑（只需新增JSON）
- 易于修改网络参数（编辑JSON即可）
- 配置可重用、可版本控制
- 便于参数扫描和对比研究

**配置内容**:
1. **拓扑定义**: 节点角色、NOMA拓扑参考
2. **Tor电路映射**: 节点→端口→角色映射
3. **网络参数**: 延迟、带宽、丢包率及tc命令
4. **卫星集成**: 轨道数据使用配置
5. **测试配置**: 运行次数、超时时间、目标URL

### 5.3 自动化设计

**三个自动化层次**:

```python
# 层次1: 单个拓扑自动化
test_single_topology(topo_id=1, num_runs=10)

# 层次2: 批量拓扑自动化  
test_all_topologies(start_topo=1, end_topo=12, num_runs=10)

# 层次3: 参数扫描自动化
for num_runs in [3, 5, 10, 20]:
    test_all_topologies(..., num_runs=num_runs)
```

**进程管理**:
- 自动清理残留进程
- 信号处理（Ctrl+C优雅退出）
- 端口冲突检测和自动清理

### 5.4 模块化设计

**关键模块**:

| 模块 | 职责 |
|------|------|
| **主编排器** | 流程控制、进程管理 |
| **网络配置** | Linux tc/netem配置 |
| **卫星轨道** | 位置计算、参数调整 |
| **节点管理** | PQ-NTOR进程启停 |
| **结果收集** | 日志解析、指标提取 |
| **报告生成** | 统计分析、可视化 |

**解耦优势**:
- 各模块相对独立
- 易于单元测试
- 支持后续扩展

---

## 6. 需要推进的工作内容

### 6.1 短期任务 (本周完成) ⚡

#### 🎯 Task 1: 完成本地仿真全测试
- [ ] 运行所有12个拓扑的完整测试 (每个10次)
  - 预计耗时: 1.5-2小时
  - 命令: `python3 run_pq_ntor_12topologies.py`
- [ ] 验证所有拓扑的成功率和性能指标
- [ ] 检查日志中的错误和异常

#### 🎯 Task 2: 改进性能指标计算
- [ ] 修复psutil deprecation警告
  - 改用 `psutil.net_connections()`
- [ ] 从日志精确解析PQ握手时间
  - 而不是使用固定的50μs
- [ ] 实现端到端延迟测量
- [ ] 计算实际吞吐量（不仅仅是估算）

#### 🎯 Task 3: 卫星轨道深度集成
- [ ] 将动态卫星参数实际应用到网络配置
- [ ] 实现通信窗口检测
- [ ] 添加仰角约束（仅在仰角>10°时测试）
- [ ] 将卫星状态保存到结果JSON

#### 🎯 Task 4: 生成完整的分析报告
- [ ] 执行 `analyze_results.py` 生成对比报告
- [ ] 创建性能对比表格和图表
- [ ] 分析上/下行拓扑的性能差异

### 6.2 中期任务 (1-2周) 📅

#### 🎯 Task 5: 优化和完善框架
- [ ] 添加结果验证（异常检测）
- [ ] 实现结果缓存和增量测试
- [ ] 添加详细的进度报告和ETA估算
- [ ] 实现结果的版本控制

#### 🎯 Task 6: 飞腾派适配 (第1阶段)
- [ ] 设计6+1分布式部署方案
- [ ] 编写部署脚本 (`deploy_to_phytium.sh`)
- [ ] 配置跨设备网络通信
- [ ] 实现节点间PQ-NTOR通信

#### 🎯 Task 7: 创建可视化仪表板
- [ ] 生成HTML报告（交互式表格）
- [ ] 创建性能对比图表（matplotlib）
- [ ] 实现拓扑拓扑性能预测模型
- [ ] 集成到distributed-demo系统

### 6.3 长期任务 (2-4周) 🚀

#### 🎯 Task 8: 完整的飞腾派测试 (第2阶段)
- [ ] 在6个飞腾派上部署PQ-NTOR
- [ ] 配置实际网络（不仅仅是localhost）
- [ ] 执行全量拓扑测试
- [ ] 对比本地仿真和物理设备的结果

#### 🎯 Task 9: 性能优化
- [ ] 分析PQ-NTOR的性能瓶颈
- [ ] 尝试不同的Kyber参数变体
- [ ] 对比传统Tor vs PQ-NTOR的开销
- [ ] 优化网络参数

#### 🎯 Task 10: 论文和报告
- [ ] 撰写实验方案文档
- [ ] 创建详细的技术报告
- [ ] 准备数据可视化和对比分析
- [ ] 生成最终的实验总结

### 6.4 工作计划时间表

```
2025-11-24 (本周)
├─ 完成12拓扑全测试
├─ 改进性能指标计算
├─ 卫星轨道集成
└─ 生成分析报告

2025-11-25-11-30 (下周)
├─ 框架优化完善
├─ 飞腾派适配(第1阶段)
└─ 可视化仪表板

2025-12-01-12-15 (第3-4周)
├─ 飞腾派物理测试
├─ 性能优化迭代
└─ 论文和报告撰写
```

---

## 7. 快速命令参考

### 快速开始

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment

# 快速验证（拓扑1，3次）
bash scripts/quick_test.sh

# 完整测试（所有12拓扑，每个10次）
python3 scripts/run_pq_ntor_12topologies.py

# 快速模式（所有12拓扑，每个3次）
python3 scripts/run_pq_ntor_12topologies.py --quick

# 测试单个拓扑
python3 scripts/run_pq_ntor_12topologies.py --topo 1 --runs 5

# 测试拓扑范围
python3 scripts/run_pq_ntor_12topologies.py --start 1 --end 6 --runs 10
```

### 结果分析

```bash
# 分析所有拓扑
python3 scripts/analyze_results.py

# 分析单个拓扑
python3 scripts/analyze_results.py --topo 1

# 查看原始结果
cat results/local_wsl/topo01_results.json | jq .

# 查看对比报告
cat results/analysis/comparison_report_*.md
```

### 故障排查

```bash
# 检查占用的端口
lsof -i :5000,6001,6002,6003

# 清理残留进程
pkill -9 directory relay client

# 清理tc规则
sudo tc qdisc del dev lo root

# 查看实时日志
tail -f logs/directory_topo01_run01.log
tail -f logs/client_topo01_run01.log
```

---

## 8. 文件路径快速导航

| 内容 | 路径 |
|------|------|
| **项目根目录** | `/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/` |
| **PQ-NTOR源码** | `/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/` |
| **拓扑定义** | `/home/ccc/pq-ntor-experiment/sagin-experiments/noma-topologies/configs/` |
| **卫星轨道模块** | `/home/ccc/pq-ntor-experiment/sagin-experiments/satellite_orbit.py` |
| **配置文件** | `./configs/topoXX_tor_mapping.json` |
| **测试脚本** | `./scripts/run_pq_ntor_12topologies.py` |
| **测试结果** | `./results/local_wsl/topoXX_results.json` |
| **分析报告** | `./results/analysis/comparison_report_*.md` |
| **测试日志** | `./logs/*.log` |

---

## 总结

这是一个**完整的后量子加密协议（PQ-NTOR）在空天地一体化网络（SAGIN NOMA）中的性能评估框架**。

**框架特点**:
- ✅ 配置驱动，易于扩展
- ✅ 自动化程度高
- ✅ 三层递进测试（仿真→分布式→实际）
- ✅ 模块化设计，便于维护

**当前状态**: 本地仿真框架已搭建，待完成全量测试和飞腾派集成

**下一步**: 运行完整的12拓扑测试，分析性能指标，为飞腾派物理测试奠定基础

