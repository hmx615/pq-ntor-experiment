# Last Experiment - SAGIN PQ-NTOR性能测试

**项目阶段**: 实验准备完成 ✅
**当前状态**: 可开始单机测试
**创建时间**: 2025-11-27 ~ 2025-11-28

---

## 🎯 项目目标

在12种SAGIN网络拓扑下，测试PQ-NTOR（后量子密码握手协议）的性能，为学术论文提供数据支撑。

---

## ✅ 已完成工作

### 阶段一: 参数计算 (2025-11-27)
- ✅ 整合师妹的3个物理模型（卫星/UAV/D2D）
- ✅ 设计12拓扑的3D节点坐标
- ✅ 计算真实网络参数（速率、延迟、丢包率）
- ✅ 生成TC配置文件

### 阶段二: 参数优化 (2025-11-28上午)
- ✅ 识别D2D瓶颈拓扑（topo02/09/11）
- ✅ 优化D2D距离到500m（合理范围）
- ✅ 重新计算优化后参数
- ✅ 速率提升：1.59-31.81 Mbps → 3.60-31.81 Mbps

### 阶段三: 测试准备 (2025-11-28下午)
- ✅ 编写单机自动化测试脚本
- ✅ 编写兼容性检查脚本
- ✅ 准备部署方案对比文档
- ✅ 编写使用指南

---

## 📂 文件结构

```
last_experiment/
│
├── 【师妹的物理模型】
│   ├── test_satellite_noma.py      # 卫星链路计算（20 GHz）
│   ├── test_uav_noma.py           # UAV链路计算（2.4 GHz）
│   └── test_d2d_noma.py           # D2D链路计算（2.4 GHz）
│
├── 【节点坐标与参数计算】
│   ├── topology_node_positions.py  # 12拓扑节点3D坐标 [已优化]
│   ├── calculate_topology_params.py # 参数计算脚本
│   ├── topology_params.json        # 完整参数（含链路详情）
│   ├── topology_tc_params.json     # TC配置参数
│   └── topology_params_distribution.png # 参数分布图
│
├── 【测试脚本】
│   ├── test_pq_ntor_single_machine.py   # 单机自动化测试 ⭐
│   └── quick_compatibility_test.sh      # 环境兼容性检查
│
├── 【分析文档】
│   ├── 项目需求理解文档.md
│   ├── 参数计算结果总结.md
│   ├── 阶段一完成总结.md
│   ├── 12拓扑参数计算详细过程.md
│   ├── 12拓扑链路质量详细分析表.md
│   ├── 分组链路质量对比表.md
│   ├── 低速拓扑优化方案.md
│   ├── 拓扑优化记录.md              # 优化修改记录 ⭐
│   ├── 实验部署方案对比.md          # 1派 vs 7派对比 ⭐
│   └── 单机测试使用指南.md          # 测试指南 ⭐
│
├── 【实验结果】（运行测试后生成）
│   └── results/
│       ├── handshake_times.json
│       ├── performance_summary.csv
│       └── comparison_plots.png
│
└── README.md                       # 本文档
```

---

## 📊 12拓扑参数总览

优化后的网络参数（速率范围: 3.60 - 31.81 Mbps）:

### 上行场景 (topo01-06)
```
topo01: 31.81 Mbps, 5.42ms, 2.0% - 卫星直连NOMA
topo02:  8.77 Mbps, 5.44ms, 2.0% - T协作接入 [已优化 ✓]
topo03: 20.53 Mbps, 2.73ms, 0.1% - T用户协作NOMA
topo04: 29.21 Mbps, 5.42ms, 2.0% - 混合直连+协作
topo05: 23.03 Mbps, 5.43ms, 2.0% - 多层树形
topo06: 29.21 Mbps, 5.42ms, 0.1% - 双UAV中继
```

### 下行场景 (topo07-12)
```
topo07: 14.08 Mbps, 5.44ms, 2.0% - 直连NOMA+协作
topo08:  8.77 Mbps, 5.46ms, 2.0% - 多跳协作
topo09:  8.77 Mbps, 2.72ms, 0.5% - T用户协作 [已优化 ✓]
topo10:  8.77 Mbps, 5.44ms, 2.0% - 混合单跳协作
topo11:  3.60 Mbps, 5.44ms, 2.0% - 混合多跳协作 [已优化 ✓]
topo12:  8.77 Mbps, 5.44ms, 2.0% - 双中继协作
```

**关键特性**:
- ✅ 速率覆盖约9倍范围（3.60 - 31.81 Mbps）
- ✅ 延迟两组：2.7ms（无卫星直连）vs 5.4ms（有卫星直连）
- ✅ 丢包率：0.1% - 2.0%（合理范围）
- ✅ 所有D2D距离 ≤ 1000m（已优化）

---

## 🚀 快速开始

### 1. 环境检查

```bash
# 进入实验目录
cd /home/ccc/pq-ntor-experiment/last_experiment

# 快速检查
python3 -c "
from pathlib import Path
print('Python: ✓')
print('PQ-NTOR程序:', '✓' if Path('../c/benchmark_pq_ntor').exists() else '✗ 需编译')
print('拓扑参数:', '✓' if Path('topology_tc_params.json').exists() else '✗ 需生成')
"
```

### 2. 运行单机测试

```bash
# 运行测试（每个拓扑100次握手，预计2-5分钟）
python3 test_pq_ntor_single_machine.py
```

### 3. 查看结果

```bash
# 查看CSV报告
cat results/performance_summary.csv

# 查看图表（如果有GUI）
xdg-open results/comparison_plots.png
```

**详细使用方法**: 参见 `单机测试使用指南.md`

---

## 📖 关键文档导航

### 快速上手
1. **单机测试使用指南.md** ⭐ - 如何运行测试
2. **实验部署方案对比.md** - 1派 vs 7派方案选择

### 理解参数
3. **分组链路质量对比表.md** - 12拓扑参数对比
4. **12拓扑参数计算详细过程.md** - 计算原理
5. **拓扑优化记录.md** - 优化修改记录

### 需求与设计
6. **项目需求理解文档.md** - 需求澄清
7. **SAGIN_PQ-NTOR实验设计方案.md** - 实验设计（原始15场景版本）

---

## 🎯 实验路线图

### ✅ 已完成
- [x] 阶段一: 参数计算（基于师妹模型）
- [x] 阶段二: 参数优化（D2D瓶颈解决）
- [x] 阶段三: 测试准备（脚本+文档）

### 🔄 当前阶段: 单机测试
- [ ] 在WSL/飞腾派上运行测试
- [ ] 验证兼容性
- [ ] 收集初步数据
- [ ] 分析结果

### 🔮 下一阶段（可选）
- [ ] 准备7个飞腾派
- [ ] 部署分布式环境
- [ ] 运行真实网络实验
- [ ] 论文数据收集

---

## 💡 实验部署方案

### 方案A: 单机测试（当前推荐）
- **时间**: 1-2天
- **设备**: 1个飞腾派或WSL
- **数据**: PQ-NTOR基础性能
- **适用**: 算法类会议、快速验证

### 方案B: 分布式测试（论文级）
- **时间**: 5-7天
- **设备**: 7个飞腾派（6节点+1控制台）
- **数据**: 真实SAGIN网络性能
- **适用**: 系统类顶会（USENIX, NSDI, INFOCOM）

**详细对比**: 参见 `实验部署方案对比.md`

---

## 🔧 故障排除

### benchmark_pq_ntor 未编译

```bash
cd ../c
make benchmark_pq_ntor
```

### 缺少Python依赖

```bash
# matplotlib（生成图表，可选）
pip3 install matplotlib
```

### 拓扑参数文件不存在

```bash
python3 calculate_topology_params.py
```

---

## 📊 预期实验结果

基于PQ-NTOR的理论性能（Kyber-512 KEM）:

**单机测试**（纯计算性能）:
- 平均握手时间: 40-60 µs
- 网络参数影响: 微小（主要是计算）
- 稳定性: 高（标准差 < 5 µs）

**分布式测试**（真实网络）:
- 平均握手时间: 取决于网络延迟
- 网络参数影响: 显著
- topo01 (31 Mbps): 约 5.5 ms
- topo11 (3.6 Mbps): 约 6-8 ms

---

## 🎓 论文支撑

### 可验证的研究问题

1. **PQ-NTOR基础性能** (单机测试) ✅
   - 握手延迟约 50 µs
   - 计算开销可接受

2. **不同网络条件的影响** (单机+分布式) ✅
   - 速率: 3.6 - 31.8 Mbps
   - 延迟: 2.7 - 5.5 ms
   - 丢包: 0.1 - 2.0%

3. **SAGIN网络适用性** (分布式测试) ✅
   - 12种拓扑全覆盖
   - 上行 vs 下行对比
   - 协作链路影响

---

## 📞 下一步行动

**现在可以做**:
1. 运行单机测试验证环境
2. 收集初步数据
3. 调试测试脚本

**测试完成后**:
1. 分析单机数据
2. 决定是否需要分布式
3. 开始论文撰写或继续实验

**命令**:
```bash
cd /home/ccc/pq-ntor-experiment/last_experiment
python3 test_pq_ntor_single_machine.py
```

---

**项目状态**: ✅ 准备就绪，可开始测试
**文档版本**: v2.0
**最后更新**: 2025-11-28
**维护者**: Claude + 用户
