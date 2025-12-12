# 12拓扑实验说明文档

**创建时间**: 2025-12-11
**目的**: 避免后续Claude误解实验目标

---

## 🎯 实验目标

### 核心目的
测试**PQ-NTOR协议**和**Classic NTOR协议**在**12种不同SAGIN网络拓扑**下的性能表现。

### 测试内容
对每个拓扑（共12个），需要测试：

1. **Phase 1: 密码学原语性能**
   - Kyber KEM (密钥生成、封装、解封装)
   - X25519 ECDH (密钥生成、共享密钥计算)
   - SHA256/SHA3 哈希
   - AES-CTR 加密
   - 程序: `phase1_crypto_primitives`

2. **Phase 2: 握手协议对比**
   - PQ-NTOR 握手时间
   - Classic NTOR 握手时间
   - 开销对比 (Overhead)
   - 程序: `phase2_handshake_comparison`

3. **Phase 3: 电路建立时间**
   - 3跳电路建立总时间 (Circuit Build Time, CBT)
   - 包含网络延迟影响
   - 程序: `phase3_sagin_network`

### 网络拓扑参数
12个拓扑分为两类：
- **Topo 01-06**: Uplink (上行) - 较低带宽、较高丢包
- **Topo 07-12**: Downlink (下行) - 较高带宽、较低丢包

每个拓扑有3个关键参数：
- `delay_ms`: 网络延迟（毫秒）
- `bandwidth_mbps`: 带宽（Mbps）
- `loss_percent`: 丢包率（%）

---

## 📁 文件结构

```
/home/ccc/pq-ntor-experiment/
├── sagin-experiments/
│   ├── docker/build_context/c/
│   │   ├── benchmark/
│   │   │   ├── phase1_crypto_primitives.c    # Phase 1 源码
│   │   │   ├── phase2_handshake_comparison.c # Phase 2 源码
│   │   │   ├── phase3_sagin_network.c        # Phase 3 源码
│   │   ├── phase1_crypto_primitives          # 编译后的可执行文件
│   │   ├── phase2_handshake_comparison       # 编译后的可执行文件
│   │   ├── phase3_sagin_network              # 编译后的可执行文件
│   │
│   └── pq-ntor-12topo-experiment/
│       ├── configs/
│       │   ├── topo01_tor_mapping.json       # 拓扑1配置（含TC参数）
│       │   ├── topo02_tor_mapping.json       # 拓扑2配置
│       │   └── ... (共12个)
│       ├── scripts/
│       │   └── run_12topo_benchmark.sh       # 应该创建的脚本
│       └── results/
│           └── (实验结果JSON文件)
```

---

## ⚠️ 常见误区

### ❌ 错误理解1: 运行Tor完整电路测试
**错误做法**:
```bash
# 这个会超时，不是主要实验！
python3 run_simple_test.py --all --runs 10
```

这个脚本启动完整的Tor服务（Directory, Guard, Middle, Exit, Client），然后建立3跳电路并发送HTTP请求。这**不是**12拓扑实验的主要目标。

### ✅ 正确理解: 运行Phase 1-3 Benchmark
**正确做法**:
```bash
# 对每个拓扑配置TC，然后运行benchmark
for topo in {01..12}; do
    # 1. 读取拓扑配置
    delay=$(jq -r ".network_simulation.aggregate_params.delay_ms" topo${topo}_tor_mapping.json)
    bandwidth=$(jq -r ".network_simulation.aggregate_params.bandwidth_mbps" topo${topo}_tor_mapping.json)
    loss=$(jq -r ".network_simulation.aggregate_params.loss_percent" topo${topo}_tor_mapping.json)

    # 2. 配置TC
    sudo tc qdisc add dev lo root netem delay ${delay}ms rate ${bandwidth}mbit loss ${loss}%

    # 3. 运行Phase 1-3
    ./phase1_crypto_primitives > results/topo${topo}_phase1.json
    ./phase2_handshake_comparison > results/topo${topo}_phase2.json
    ./phase3_sagin_network > results/topo${topo}_phase3.json

    # 4. 清理TC
    sudo tc qdisc del dev lo root
done
```

---

## 🔧 技术限制

### 飞腾派限制
- **内核**: `5.10.209-phytium-embedded-v2.2`
- **TC支持**: ❌ **不支持** netem模块
- **原因**: 嵌入式内核未编译TC qdisc模块
- **影响**: 无法在飞腾派上模拟网络延迟/带宽/丢包

### WSL2支持
- **内核**: 标准Linux内核
- **TC支持**: ✅ 支持 netem, tbf 等模块
- **平台**: x86_64（不是ARM）

---

## 📊 实验数据来源

### 当前已有数据（可能需要重新生成）
- `essay/phase1_results_phytium_*` - 飞腾派Phase 1结果（无TC）
- `essay/phase2_results_phytium_*` - 飞腾派Phase 2结果（无TC）
- `essay/phase3_results_phytium_*` - 飞腾派Phase 3结果（无TC）

### 需要的数据（12拓扑 × 3阶段）
- 每个拓扑的Phase 1-3结果（含TC网络损伤）
- 对比Uplink vs Downlink性能差异
- 验证：Downlink overhead < Uplink overhead

---

## 🚀 下一步行动

### 选项A: WSL2环境运行（推荐）
**优点**:
- ✅ 支持TC网络模拟
- ✅ 可以测试网络条件影响
- ✅ 快速迭代

**缺点**:
- ❌ 不是ARM平台
- ❌ 性能数据可能与飞腾派略有差异

### 选项B: 飞腾派无TC运行
**优点**:
- ✅ ARM平台真实性能
- ✅ 论文可以声明"在ARM设备上测试"

**缺点**:
- ❌ 无法测试网络条件影响
- ❌ 所有拓扑结果相同（无网络差异）

### 选项C: 混合方案
1. **Phase 1-2**: 在飞腾派运行（无TC）- 展示ARM平台密码学性能
2. **Phase 3**: 在WSL2运行（有TC）- 展示网络条件影响

---

## 📝 关键发现记录

### 2025-12-11 调试总结

1. **配置文件已修复**
   - 旧配置: 硬编码参数（20ms/35Mbps/1.25%）
   - 新配置: 真实NOMA数据（5.42ms/59.27Mbps/3%等）
   - 备份位置: `backup/old_experiment_data_20251211/`

2. **飞腾派TC问题**
   - 所有7个飞腾派都不支持TC netem
   - 已配置sudo无密码（for tc命令）
   - 但内核缺少sch_netem.ko模块

3. **Tor完整电路测试问题**
   - `run_simple_test.py`一直超时（60秒不够）
   - 即使增加到120秒也可能超时
   - 这**不是**主要实验目标

---

## 🔗 相关文档

- 拓扑参数来源: `last_experiment/topology_params.json`
- NOMA数据来源: 师妹真实测量数据
- Phase 1-3代码: `sagin-experiments/docker/build_context/c/benchmark/`
- 配置生成脚本: `sagin-experiments/pq-ntor-12topo-experiment/scripts/regenerate_configs_with_correct_params.py`

---

**最后更新**: 2025-12-11 17:10 UTC+8
**状态**: 等待用户确认实验方案
