# PQ-NTOR 12拓扑实验框架 - 快速摘要

**分析时间**: 2025-11-24  
**项目位置**: `/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/`

---

## 快速概览

| 项目 | 内容 |
|------|------|
| **项目名称** | PQ-NTOR 12拓扑自动化测试框架 |
| **目标** | 评估后量子加密协议(PQ-NTOR)在SAGIN NOMA拓扑中的性能 |
| **框架完成度** | 80% (框架搭建完成，待全量测试) |
| **已完成测试** | 3个拓扑 × 3次 = 9次运行 |
| **成功率** | 100% |
| **项目总大小** | 316 KB (71个文件) |

---

## 目录结构速览

```
├── configs/              12个拓扑Tor映射配置 (JSON)
├── scripts/              5个测试和分析脚本
│   ├── run_pq_ntor_12topologies.py    ⭐ 主测试脚本
│   ├── satellite_integration.py        卫星轨道集成
│   ├── analyze_results.py              结果分析
│   ├── quick_test.sh                   快速验证
│   └── ...
├── results/              实验结果
│   ├── local_wsl/        本地仿真结果 (3个拓扑已有)
│   ├── phytium_pi/       飞腾派结果 (待填充)
│   └── analysis/         分析报告
├── logs/                 详细测试日志 (70+个)
└── README.md             项目文档
```

---

## 核心组件

### 1. 配置文件 (12个)

**命名**: `topoXX_tor_mapping.json`

**内容**:
- Tor电路映射（Client→Guard→Middle→Exit）
- 网络参数（延迟、带宽、丢包率）
- Linux tc/netem配置命令
- 卫星轨道集成参数
- 期望的性能指标

**示例参数范围**:
- 延迟: 15-40 ms
- 带宽: 22-60 Mbps
- 丢包率: 0.5-2.5 %

### 2. 主测试脚本 (600+行)

**功能**:
- 自动启动/关闭PQ-NTOR节点
- 配置网络参数
- 运行客户端测试
- 收集性能指标
- 生成测试报告

**支持的运行模式**:

```bash
# 快速测试 (拓扑1, 3次)
python3 run_pq_ntor_12topologies.py --quick

# 完整测试 (所有12拓扑, 每个10次)
python3 run_pq_ntor_12topologies.py

# 单个拓扑 (拓扑1, 5次)
python3 run_pq_ntor_12topologies.py --topo 1 --runs 5

# 拓扑范围 (拓扑1-6, 10次)
python3 run_pq_ntor_12topologies.py --start 1 --end 6 --runs 10
```

### 3. 卫星轨道集成

**功能**:
- 计算卫星位置、仰角、距离
- 计算电磁波传播延迟
- 根据仰角调整网络参数
- 检测通信窗口

**支持两种模式**:
- **静态模式**: 使用固定卫星快照（可重复）
- **动态模式**: 实时计算卫星位置

### 4. 结果分析工具

**功能**:
- 统计成功率
- 计算平均性能指标
- 生成拓扑对比报告
- 上/下行分析

---

## 12种拓扑概览

| 类别 | 拓扑 | 延迟(ms) | 带宽(Mbps) | 丢包率(%) | 状态 |
|------|------|----------|-----------|---------|------|
| **上行** | 1-6 | 15-25 | 35-60 | 0.6-1.25 | ⚠️ 部分测试 |
| **下行** | 7-12 | 25-40 | 22-35 | 1.2-2.5 | ⏳ 未测试 |

---

## 与主项目的依赖关系

```
本目录 (pq-ntor-12topo-experiment)
  ↓ 依赖
  ├─ PQ-NTOR可执行文件 (../docker/build_context/c/)
  ├─ NOMA拓扑定义 (../noma-topologies/configs/)
  └─ 卫星轨道模块 (../satellite_orbit.py)
```

---

## 现有状态评估

### 完成部分 ✅

- [x] 框架架构设计 (100%)
- [x] 12个拓扑配置生成 (100%)
- [x] 主测试脚本编写 (95%)
- [x] 卫星轨道集成 (85%)
- [x] 结果分析工具 (80%)
- [x] 快速验证脚本 (100%)
- [x] 基础性能测试 (30%) - 3个拓扑已测

### 待完成部分 ⏳

- [ ] 12个拓扑的全量测试 (0%)
- [ ] 性能指标精准计算 (50%)
- [ ] 卫星动态参数深度集成 (30%)
- [ ] 可视化图表和仪表板 (0%)
- [ ] 飞腾派分布式部署 (0%)
- [ ] 物理设备验证 (0%)

---

## 已有实验数据

### 测试成果

**运行统计**:
- 总运行次数: 9次
- 成功次数: 9次
- 成功率: 100%
- 平均耗时: ~62秒/次

**拓扑覆盖**:
- 拓扑1 (Z1 Up): ✅ 3次运行
- 拓扑2 (Z1 Up): ✅ 3次运行
- 拓扑3 (Z3 Up): ✅ 3次运行
- 拓扑4-12: ⏳ 待测试

**日志总量**: 70+个日志文件, 148 KB

---

## 关键问题和改进点

### 已发现的问题

1. **psutil 弃用警告**
   - 当前: `proc.connections()` (已弃用)
   - 改进: 更新为 `net_connections()`
   - 优先级: 低

2. **性能指标不准确**
   - 问题: PQ握手时间使用固定值(50μs)
   - 改进: 从日志精确解析
   - 优先级: 中

3. **卫星轨道未深度集成**
   - 问题: 卫星参数未应用到实际测试
   - 改进: 动态调整网络参数
   - 优先级: 中

4. **缺少飞腾派支持**
   - 问题: 仅支持localhost测试
   - 改进: 6+1分布式部署
   - 优先级: 高

---

## 推进工作计划

### 本周 (第1优先级) ⚡

- [ ] **Task 1**: 运行全部12拓扑测试 (~2小时)
  ```bash
  python3 scripts/run_pq_ntor_12topologies.py
  ```

- [ ] **Task 2**: 改进性能指标计算
  - 修复psutil警告
  - 精确解析PQ握手时间
  - 实现端到端延迟测量

- [ ] **Task 3**: 卫星轨道深度集成
  - 应用动态参数到测试流程
  - 实现通信窗口检测
  - 保存轨道状态到结果

- [ ] **Task 4**: 生成完整分析报告
  ```bash
  python3 scripts/analyze_results.py
  ```

### 下周 (第2优先级) 📅

- [ ] **Task 5**: 框架优化和完善
- [ ] **Task 6**: 飞腾派适配(第1阶段)
- [ ] **Task 7**: 创建可视化仪表板

### 后续 (第3优先级) 🚀

- [ ] **Task 8**: 飞腾派完整测试
- [ ] **Task 9**: 性能优化
- [ ] **Task 10**: 论文和报告

---

## 快速命令速查

```bash
# 进入项目目录
cd /home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment

# 快速验证 (1-2分钟)
bash scripts/quick_test.sh

# 完整测试 (1.5-2小时)
python3 scripts/run_pq_ntor_12topologies.py

# 分析结果
python3 scripts/analyze_results.py

# 查看日志
tail -f logs/*.log

# 查看结果
cat results/local_wsl/topo01_results.json | jq .

# 清理进程
pkill -9 directory relay client
sudo tc qdisc del dev lo root
```

---

## 补充资源

| 资源 | 位置 |
|------|------|
| **详细分析报告** | `./DETAILED_ANALYSIS_REPORT.md` |
| **项目文档** | `./README.md` |
| **实验设计方案** | `../实验设计_PQ-NTOR_12拓扑测试.md` |
| **拓扑定义** | `../noma-topologies/README.md` |
| **PQ-NTOR源码** | `../docker/build_context/c/` |

---

**项目状态**: 🚧 开发中 | **下一步**: 运行全量测试

