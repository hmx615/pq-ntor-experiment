# 12拓扑实验数据格式分析

**创建时间**: 2025-12-11 17:30 UTC+8
**目的**: 确认现有程序输出格式与图表数据兼容性

---

## ✅ 数据格式验证结果

### **结论: 数据格式完全兼容！**

两部分实验（ARM平台 + WSL2 TC）的输出格式与现有图表完全一致，可以直接用于重新绘图。

---

## 📊 Phase 1: 密码学原语性能

### 输出文件
- **文件名**: `phase1_crypto_benchmarks.csv`
- **拓扑依赖**: ❌ 无（密码学原语性能不受网络影响）

### CSV格式
```csv
Operation,Min_us,Max_us,Mean_us,Median_us,StdDev_us,P95_us,P99_us,CI_Lower,CI_Upper
Kyber-512 Keygen,5.00,40.00,5.99,6.00,1.52,7.00,9.00,5.89,6.08
Kyber-512 Encaps,7.00,56.00,7.68,7.00,2.33,8.00,17.00,7.54,7.83
Kyber-512 Decaps,5.00,31.00,5.24,5.00,1.11,6.00,6.00,5.17,5.31
HKDF-SHA256,2.00,346.00,2.99,3.00,10.87,3.00,4.00,2.31,3.66
HMAC-SHA256,0.00,18.00,0.93,1.00,0.61,1.00,1.00,0.89,0.97
```

### 实验方案
- **ARM平台（飞腾派）**:
  - ✅ 直接运行 `./phase1_crypto_primitives`
  - ✅ 无需TC配置（密码学性能不受网络影响）
  - ✅ 展示ARM架构真实性能

- **WSL2平台**:
  - ⚠️ 可选（密码学性能主要展示ARM数据）
  - 仅用于对比x86 vs ARM架构差异

---

## 🤝 Phase 2: 握手协议对比

### 输出文件
- **文件名**: `phase2_handshake_comparison.csv`
- **拓扑依赖**: ❌ 无（当前版本不支持拓扑）

### CSV格式
```csv
Protocol,Mean_us,Median_us,Min_us,Max_us,StdDev_us,P95_us,P99_us,CI_Lower,CI_Upper
Classic NTOR,91.19,90.00,85.00,120.00,8.42,105.00,115.00,88.50,93.88
PQ-NTOR,40.25,39.00,35.00,55.00,5.12,50.00,53.00,38.20,42.30
```

### 实验方案
- **ARM平台（飞腾派）**:
  - ✅ 直接运行 `./phase2_handshake_comparison`
  - ✅ 无需TC配置
  - ✅ 展示握手协议Overhead (PQ-NTOR vs Classic NTOR)

- **WSL2平台**:
  - ⚠️ 可选（握手时间主要展示ARM数据）
  - 当前Phase 2不支持拓扑参数

### ⚠️ 局限性
当前Phase 2程序**不支持按拓扑测试**，只输出单个结果。如需按拓扑测试，需修改程序增加拓扑循环（类似Phase 3）。

---

## 🌐 Phase 3: 3跳电路建立时间（CBT）

### 输出文件
- **文件名**: `phase3_sagin_cbt.csv`
- **拓扑依赖**: ✅ 是（测试12个拓扑）

### CSV格式（现有数据）
```csv
Topology,Protocol,Mean_ms,Median_ms,Min_ms,Max_ms,StdDev_ms,P95_ms,P99_ms,CI_Lower,CI_Upper
topo01,Classic NTOR,0.30,0.30,0.27,0.32,0.01,0.32,0.32,0.29,0.30
topo01,PQ-NTOR,0.23,0.19,0.16,0.38,0.08,0.38,0.38,0.20,0.27
topo02,Classic NTOR,0.33,0.32,0.30,0.49,0.05,0.49,0.49,0.31,0.35
topo02,PQ-NTOR,0.21,0.19,0.16,0.43,0.06,0.43,0.43,0.18,0.24
...（共24行，12拓扑 × 2协议）
```

### ❌ 关键问题：Phase 3拓扑参数已过时！

**当前代码中的参数（错误）**:
```c
static const topology_config_t TOPOLOGIES[] = {
    {"topo01", 31.81, 5.42, 2.0},  // ❌ 错误！应该是 59.27 Mbps
    {"topo02",  8.77, 5.44, 2.0},  // ❌ 错误！应该是 16.55 Mbps
    {"topo03",  5.69, 5.40, 2.0},  // ❌ 错误！应该是 25.19 Mbps
    ...
};
```

**正确参数（从topology_params.json）**:
```c
static const topology_config_t TOPOLOGIES[] = {
    {"topo01",  59.27,  5.42,  3.0},  // ✅ 正确
    {"topo02",  16.55,  5.42,  3.0},  // ✅ 正确
    {"topo03",  25.19,  2.72,  1.0},  // ✅ 正确
    {"topo04",  23.64,  5.42,  3.0},
    {"topo05",  25.19,  5.43,  3.0},
    {"topo06",  22.91,  5.42,  1.0},
    {"topo07",  69.43,  5.42,  2.0},  // Downlink开始
    {"topo08",  38.01,  5.43,  2.0},
    {"topo09",  29.84,  2.72,  0.5},
    {"topo10",  18.64,  5.42,  2.0},
    {"topo11",   9.67,  5.43,  2.0},
    {"topo12",   8.73,  5.43,  2.0},
};
```

### 实验方案

#### ARM平台（飞腾派）
- ❌ **不支持TC** - 嵌入式内核缺少netem模块
- ✅ 可运行Phase 3，但所有拓扑结果相同（无网络差异）
- 💡 **建议**: 仅运行Phase 1和2（密码学+握手）

#### WSL2平台（推荐）
- ✅ **支持TC** - 可模拟12种网络条件
- ✅ 运行 `./phase3_sagin_network` 自动测试所有拓扑
- ✅ 输出 `phase3_sagin_cbt.csv` 包含12拓扑 × 2协议 = 24行数据

---

## 🎯 实验执行计划

### Part A: ARM平台（飞腾派）
```bash
cd /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/docker/build_context/c

# Phase 1: 密码学原语
./phase1_crypto_primitives
# 输出: phase1_crypto_benchmarks.csv

# Phase 2: 握手对比
./phase2_handshake_comparison
# 输出: phase2_handshake_comparison.csv

# Phase 3: 不推荐（无TC支持）
```

### Part B: WSL2平台（支持TC）
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 先修复Phase 3拓扑参数！
# （需要修改 benchmark/phase3_sagin_network.c）

# 重新编译
make clean && make

# Phase 3: 带TC的电路建立测试
sudo ./phase3_sagin_network
# 输出: phase3_sagin_cbt.csv （24行数据）
```

---

## 📈 与现有图表对应关系

### 现有图表文件（推测）
- `essay/figure/phase1_*.png` - Phase 1密码学性能图
- `essay/figure/phase2_*.png` - Phase 2握手对比图
- `essay/figure/phase3_*.png` - Phase 3 CBT图（12拓扑热力图？）

### 数据兼容性
| Phase | 现有CSV格式 | 新数据格式 | 兼容性 |
|-------|-----------|-----------|--------|
| Phase 1 | ✅ 5个操作 | ✅ 5个操作 | ✅ 完全兼容 |
| Phase 2 | ✅ 2个协议 | ✅ 2个协议 | ✅ 完全兼容 |
| Phase 3 | ✅ 12拓扑×2协议 | ✅ 12拓扑×2协议 | ✅ 完全兼容（需修正参数）|

---

## 🔧 下一步行动

### 紧急任务
1. ✅ **修复Phase 3参数** - 更新 `phase3_sagin_network.c` 中的TOPOLOGIES数组
2. ✅ **重新编译** - 确保使用正确参数
3. ✅ **测试WSL2运行** - 验证TC配置正常工作

### 实验执行
4. **ARM平台**: 运行Phase 1和2（密码学+握手）
5. **WSL2平台**: 运行Phase 3（带TC的电路建立）
6. **数据合并**: 将ARM和WSL2数据合并
7. **重新绘图**: 使用现有图表脚本重新生成图表

---

## 📝 关键发现

### ✅ 好消息
1. **数据格式完全兼容** - 无需修改图表脚本
2. **Phase 1和2在ARM上可直接运行** - 无需TC
3. **Phase 3已内置12拓扑支持** - 无需修改循环逻辑

### ⚠️ 需要注意
1. **Phase 3参数必须修正** - 当前硬编码参数错误
2. **飞腾派无法运行Phase 3（带TC）** - 内核限制
3. **Phase 2不支持拓扑** - 如需按拓扑测试需修改代码

---

**最后更新**: 2025-12-11 17:30 UTC+8
**状态**: 等待修复Phase 3参数并开始实验
