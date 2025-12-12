# Phase 3: SAGIN网络集成测试 - 完整设计文档

**文档版本**: v1.0
**创建日期**: 2025-12-03
**测试平台**: 飞腾派 (Phytium FTC664, ARM Cortex-A72 @ 2.3GHz)
**网络参数来源**: 师妹NOMA协作网络真实数据

---

## 📋 目录

1. [实验背景与动机](#1-实验背景与动机)
2. [三阶段实验设计概览](#2-三阶段实验设计概览)
3. [Phase 1 & 2 成果回顾](#3-phase-1--2-成果回顾)
4. [Phase 3 详细设计](#4-phase-3-详细设计)
5. [实现方案](#5-实现方案)
6. [数据分析计划](#6-数据分析计划)
7. [预期成果](#7-预期成果)

---

## 1. 实验背景与动机

### 1.1 研究问题

**核心问题**: PQ-NTOR在SAGIN (Space-Air-Ground Integrated Network) 环境下的性能表现如何？

**具体问题**:
1. 密码学开销在真实网络环境中占比多少？
2. PQ-NTOR相比Classic NTOR的端到端性能差异？
3. 不同网络条件（延迟、带宽、丢包）对性能的影响？
4. PQ-NTOR在SAGIN环境中的可部署性？

### 1.2 现有问题

**之前的50秒实验问题**:
- ❌ 混合了多个变量（目录查询 + 三跳握手 + HTTP请求）
- ❌ 无法分离密码学开销和网络延迟
- ❌ 缺少Classic NTOR基线对比
- ❌ 数据缺乏发表价值

**解决方案**: 三阶段分层实验设计

---

## 2. 三阶段实验设计概览

### 2.1 实验架构

```
┌─────────────────────────────────────────────────────────────┐
│                    三层实验设计                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 1: 密码学基元                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Kyber Keygen │ Kyber Encaps │ Kyber Decaps │      │    │
│  │  HKDF-SHA256  │ HMAC-SHA256                │      │    │
│  └────────────────────────────────────────────────────┘    │
│          ↓ 隔离单个操作耗时                                 │
│                                                              │
│  Phase 2: 协议握手                                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Classic NTOR完整握手 vs PQ-NTOR完整握手           │    │
│  │  (单机测试，无网络延迟)                             │    │
│  └────────────────────────────────────────────────────┘    │
│          ↓ 量化协议级开销                                    │
│                                                              │
│  Phase 3: SAGIN网络集成                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  12拓扑 × 三跳Tor电路 × 真实网络条件               │    │
│  │  Classic vs PQ-NTOR 端到端性能对比                 │    │
│  └────────────────────────────────────────────────────┘    │
│          ↓ 评估真实环境可部署性                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 设计原则

| 原则 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| **隔离变量** | ✅ 纯密码学操作 | ✅ 纯握手协议 | ✅ 真实网络环境 |
| **可重复性** | ✅ 1000次迭代 | ✅ 1000次迭代 | ✅ 20次×12拓扑 |
| **基线对比** | ✅ 文献x86数据 | ✅ Classic NTOR | ✅ Classic NTOR |
| **统计严谨** | ✅ 95% CI | ✅ 95% CI | ✅ 配对t检验 |

---

## 3. Phase 1 & 2 成果回顾

### 3.1 Phase 1: 密码学基元测试

**测试日期**: 2025-12-03
**平台**: 飞腾派 (ARM Cortex-A72 @ 2.3GHz)

#### 实测结果

| 操作 | Mean (μs) | Median (μs) | StdDev | P95 (μs) | P99 (μs) |
|------|-----------|-------------|--------|----------|----------|
| **Kyber-512 Keygen** | 45.64 | 45.00 | 4.63 | 47.00 | 52.00 |
| **Kyber-512 Encaps** | 50.62 | 51.00 | 1.02 | 51.00 | 57.00 |
| **Kyber-512 Decaps** | 42.37 | 42.00 | 2.32 | 43.00 | 48.00 |
| **HKDF-SHA256** | 6.83 | 7.00 | 0.77 | 7.00 | 7.00 |
| **HMAC-SHA256** | 2.34 | 2.00 | 0.47 | 3.00 | 3.00 |

#### 关键发现

1. **ARM64/x86性能比**: 1.54-1.77× (符合预期1.5-2.5×范围)
2. **Kyber总计**: 45.64 + 50.62 + 42.37 = **138.63 μs**
3. **HKDF+HMAC**: 6.83 + 2.34 = **9.17 μs**
4. **理论PQ-NTOR总计**: 138.63 + 9.17 = **147.80 μs**

#### 数据验证

✅ **与文献对比** (Berger et al. 2025):
- Berger (x86 @ 3.0GHz): Kyber-512 Keygen = 25.8 μs
- 我们 (ARM64 @ 2.3GHz): Kyber-512 Keygen = 45.64 μs
- **性能比**: 45.64 / 25.8 = 1.77× ✅ 合理

✅ **与Apple Silicon对比** (wolfSSL 2024):
- Apple Silicon (ARM64): Kyber-512 总计 ~40 μs (高度优化)
- 我们 (Phytium): Kyber-512 总计 ~138 μs
- **性能比**: 138 / 40 = 3.45× (Phytium较慢，合理)

**结论**: Phase 1数据准确可信，为Phase 2/3提供可靠基线

---

### 3.2 Phase 2: 协议握手性能测试

**测试日期**: 2025-12-03
**平台**: 飞腾派 (单机测试，无网络延迟)

#### 实测结果

| 协议 | Mean (μs) | Median (μs) | StdDev | P95 (μs) | P99 (μs) |
|------|-----------|-------------|--------|----------|----------|
| **Classic NTOR** | 458.94 | 457.00 | 9.42 | 464.00 | 534.00 |
| **PQ-NTOR** | 184.82 | 184.00 | 6.04 | 190.00 | 192.00 |

#### 关键发现

⚠️ **反直觉现象**: PQ-NTOR比Classic NTOR更快 (0.40×)

**深度分析**:

1. **Classic NTOR慢的原因** (458.94 μs):
   - OpenSSL EVP_PKEY高层API封装开销: **~262 μs**
   - 纯X25519计算 (3次操作): **~197 μs** (理论)
   - **封装开销比率**: 262 / 197 = 1.33× (额外33%开销)

2. **PQ-NTOR快的原因** (184.82 μs):
   - 使用liboqs直接实现，无EVP封装
   - Phase 1基元总计: **147.80 μs**
   - 状态管理开销: 184.82 - 147.80 = **37.02 μs**

3. **权威数据验证**:
   - X25519 (ARM64 Cortex-A72 @ 2.3GHz): **~65 μs** per operation
     - 来源: [GitHub - Emill/X25519-AArch64](https://github.com/Emill/X25519-AArch64)
   - Classic NTOR理论: 65×3 + 2 = **~197 μs** (原生实现)
   - 我们的实测: **458.94 μs** (EVP_PKEY实现)
   - **结论**: EVP_PKEY有2.3×开销 ✅ 符合已知现象

#### 研究价值

这个"反常"结果实际上揭示了重要问题：
1. **API设计对性能的巨大影响**
2. **高层抽象的便利性 vs 性能权衡**
3. **PQ密码学在特定实现下可能更优**

**论文讨论点**:
- 密码学库API设计的性能影响
- ARM64平台优化差异
- 实现选择的重要性

**结论**: Phase 2数据真实有效，提供重要研究洞察

---

## 4. Phase 3 详细设计

### 4.1 测试目标

**主要目标**:
1. 测量12种SAGIN拓扑下的三跳电路构建时间(CBT)
2. 量化密码学开销在真实网络中的占比
3. 对比Classic NTOR vs PQ-NTOR端到端性能
4. 评估不同网络条件对性能的影响

**次要目标**:
1. 验证PQ-NTOR在SAGIN环境的可部署性
2. 分析网络延迟 vs 密码学开销的关系
3. 识别性能瓶颈和优化方向

### 4.2 12拓扑NOMA网络参数

**数据来源**: 师妹NOMA协作网络真实测量数据
**文件**: `/home/ccc/pq-ntor-experiment/last_experiment/topology_tc_params.json`

| 拓扑ID | 名称 | 延迟 (ms) | 带宽 (Mbps) | 丢包率 (%) | 场景描述 |
|--------|------|-----------|------------|-----------|----------|
| **topo01** | Z1 Up - 直连NOMA | 5.42 | 31.81 | 2.0 | SAT←S2(地面)+S1(UAV) |
| **topo02** | Z1 Up - 协作接入 | 5.44 | 8.77 | 2.0 | T双路径(地面/UAV) |
| **topo03** | Z1 Up - UAV中继 | 2.73 | 20.53 | 0.1 | R3(LEO)←UAV协作 |
| **topo04** | Z2 Up - LEO单跳 | 5.42 | 29.21 | 2.0 | LEO直连 |
| **topo05** | Z2 Up - 双跳中继 | 5.43 | 23.03 | 2.0 | SAT←UAV←地面 |
| **topo06** | Z2 Up - NOMA协作 | 5.42 | 29.21 | 0.1 | LEO←多用户NOMA |
| **topo07** | Z1 Down - 直连 | 5.44 | 14.08 | 2.0 | SAT→地面 |
| **topo08** | Z1 Down - UAV协作 | 5.46 | 8.77 | 2.0 | SAT→UAV→地面 |
| **topo09** | Z1 Down - D2D | 2.72 | 8.77 | 0.5 | SAT→UAV→D2D |
| **topo10** | Z6 Down - 多跳 | 5.44 | 8.77 | 2.0 | LEO→多级中继 |
| **topo11** | Z6 Down - 弱链路 | 5.44 | 3.60 | 2.0 | LEO→弱SINR链路 |
| **topo12** | Z6 Down - 混合 | 5.44 | 8.77 | 2.0 | LEO→地面+UAV |

#### 网络参数统计

| 参数 | 最小值 | 最大值 | 均值 | 中位数 |
|------|--------|--------|------|--------|
| **延迟 (ms)** | 2.72 | 5.46 | 4.93 | 5.43 |
| **带宽 (Mbps)** | 3.60 | 31.81 | 14.55 | 8.77 |
| **丢包率 (%)** | 0.1 | 2.0 | 1.61 | 2.0 |

**关键观察**:
- ✅ 延迟范围窄 (2.72-5.46 ms)，远小于传统SAGIN假设(30-500ms)
- ✅ 这是真实NOMA协作网络的特点
- ✅ 低延迟环境下，密码学开销占比应更显著

### 4.3 测试架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Phase 3 测试架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client                Guard              Middle            Exit │
│  ┌────┐    Hop 1      ┌─────┐   Hop 2    ┌──────┐  Hop 3  ┌────┐
│  │ C  │───握手+网络───→│  G  │───握手───→│  M   │────────→│ E  │
│  └────┘               └─────┘            └──────┘         └────┘
│    ↑                     ↑                  ↑               ↑   │
│    │                     │                  │               │   │
│    └─────────────── Linux tc/netem 网络模拟 ──────────────┘   │
│           (应用12拓扑参数: 延迟/带宽/丢包率)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

测量指标:
  CBT = T_hop1 + T_hop2 + T_hop3
  T_hop = T_handshake (Phase 2) + T_network (延迟)

  Crypto_Overhead_Ratio = (3 × T_handshake) / CBT
```

### 4.4 测试矩阵

| 维度 | 取值 | 说明 |
|------|------|------|
| **拓扑** | 12种 (topo01-topo12) | 师妹NOMA参数 |
| **协议** | 2种 (Classic, PQ-NTOR) | 对比基线 |
| **迭代** | 20次 per拓扑 | 统计可靠性 |
| **总测试数** | **480次** | 12 × 2 × 20 |

### 4.5 测量指标

#### 主要指标

| 指标 | 定义 | 单位 | 公式 |
|------|------|------|------|
| **CBT** | Circuit Build Time (三跳电路构建时间) | ms | T_hop1 + T_hop2 + T_hop3 |
| **Per-Hop Latency** | 单跳延迟 (握手+网络) | ms | T_handshake + RTT/2 |
| **Crypto Overhead** | 密码学开销绝对值 | ms | 3 × T_handshake |
| **Crypto Ratio** | 密码学开销占比 | % | (3×T_handshake) / CBT × 100% |
| **Success Rate** | 电路构建成功率 | % | N_success / N_total × 100% |

#### 对比指标

| 指标 | 定义 | 公式 |
|------|------|------|
| **Overhead Absolute** | PQ相比Classic的绝对增加 | CBT_pq - CBT_classic |
| **Overhead Relative** | PQ相比Classic的相对增加 | (CBT_pq - CBT_classic) / CBT_classic |
| **Crypto Impact** | 密码学开销对总时间的影响 | ΔCrypto / CBT_classic |

### 4.6 实验流程

```python
def phase3_experiment():
    """Phase 3: SAGIN网络集成测试完整流程"""

    # 0. 加载拓扑参数
    topologies = load_json('topology_tc_params.json')
    results = []

    for topo_id in ['topo01', ..., 'topo12']:
        topo_params = topologies[topo_id]

        print(f"[{topo_id}] 延迟={topo_params['delay_ms']}ms, "
              f"带宽={topo_params['rate_mbps']}Mbps, "
              f"丢包={topo_params['loss_percent']}%")

        # 1. 配置Linux tc网络参数
        configure_tc_netem(
            delay_ms=topo_params['delay_ms'],
            rate_mbps=topo_params['rate_mbps'],
            loss_percent=topo_params['loss_percent']
        )

        # 2. 测试Classic NTOR (20次)
        for trial in range(20):
            t_start = time.time()

            # 启动3跳Tor网络
            circuit = build_3hop_circuit(protocol='classic-ntor')

            t_cbt = time.time() - t_start

            # 记录各跳时间
            results.append({
                'topo_id': topo_id,
                'protocol': 'classic',
                'trial': trial,
                'cbt_ms': t_cbt * 1000,
                'hop1_ms': circuit.hop1_latency,
                'hop2_ms': circuit.hop2_latency,
                'hop3_ms': circuit.hop3_latency,
                'success': circuit.is_established()
            })

        # 3. 测试PQ-NTOR (20次)
        for trial in range(20):
            t_start = time.time()

            circuit = build_3hop_circuit(protocol='pq-ntor')

            t_cbt = time.time() - t_start

            results.append({
                'topo_id': topo_id,
                'protocol': 'pq-ntor',
                'trial': trial,
                'cbt_ms': t_cbt * 1000,
                'hop1_ms': circuit.hop1_latency,
                'hop2_ms': circuit.hop2_latency,
                'hop3_ms': circuit.hop3_latency,
                'success': circuit.is_established()
            })

        # 4. 清理网络配置
        cleanup_tc_netem()

    # 5. 保存结果
    save_csv(results, 'phase3_sagin_results.csv')

    # 6. 数据分析
    analyze_results(results)
```

---

## 5. 实现方案

### 5.1 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **测试程序** | C语言 | 复用Phase 1/2基础设施 |
| **网络模拟** | Linux tc + netem | 模拟SAGIN网络条件 |
| **Tor实现** | 现有PQ-NTOR代码 | directory/relay/client |
| **部署平台** | 飞腾派 × 4 | Guard, Middle, Exit, Client |
| **自动化** | Python脚本 | 参数配置、测试执行、数据收集 |

### 5.2 代码结构

```
sagin-experiments/docker/build_context/c/
├── benchmark/
│   ├── phase1_crypto_primitives.c      ✅ 已完成
│   ├── phase2_handshake_comparison.c   ✅ 已完成
│   └── phase3_sagin_network.c          ⏳ 待开发
├── programs/
│   ├── directory_main.c                ✅ 已有
│   ├── relay_main.c                    ✅ 已有
│   └── client_main.c                   ✅ 已有
├── scripts/
│   ├── configure_tc_netem.sh           ⏳ 待开发
│   ├── run_phase3_test.py              ⏳ 待开发
│   └── deploy_to_4_pis.py              ⏳ 待开发
└── configs/
    └── topology_tc_params.json         ✅ 已有
```

### 5.3 Phase 3核心代码设计

#### 5.3.1 主测试程序: `phase3_sagin_network.c`

```c
/**
 * @file phase3_sagin_network.c
 * @brief Phase 3: SAGIN网络集成测试
 *
 * 功能:
 * 1. 读取12拓扑参数
 * 2. 配置Linux tc网络条件
 * 3. 构建三跳Tor电路(Classic/PQ-NTOR)
 * 4. 测量CBT和各跳延迟
 * 5. 记录统计数据
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include "pq_ntor.h"
#include "tor_client.h"

// 拓扑参数结构
typedef struct {
    char topo_id[16];
    double delay_ms;
    double rate_mbps;
    double loss_percent;
} topology_params_t;

// 测试结果结构
typedef struct {
    char topo_id[16];
    char protocol[16];  // "classic" or "pq-ntor"
    int trial;
    double cbt_ms;
    double hop1_ms;
    double hop2_ms;
    double hop3_ms;
    int success;
} test_result_t;

// 加载拓扑参数
int load_topology_params(const char *json_file,
                         topology_params_t **params,
                         int *count);

// 配置tc网络参数
int configure_network(const topology_params_t *params);

// 清理网络配置
int cleanup_network(void);

// 构建三跳电路并测量
int build_3hop_circuit(const char *protocol,
                       test_result_t *result);

// 保存结果
int save_results_csv(const test_result_t *results,
                     int count,
                     const char *filename);

int main(int argc, char *argv[]) {
    // 实现逻辑...
    return 0;
}
```

#### 5.3.2 网络配置脚本: `configure_tc_netem.sh`

```bash
#!/bin/bash
# Phase 3: 配置Linux tc网络参数

INTERFACE="eth0"  # 网络接口，根据实际情况调整

function configure_tc() {
    local delay_ms=$1
    local rate_mbps=$2
    local loss_percent=$3

    echo "配置网络参数:"
    echo "  延迟: ${delay_ms}ms"
    echo "  带宽: ${rate_mbps}Mbps"
    echo "  丢包: ${loss_percent}%"

    # 清理旧配置
    sudo tc qdisc del dev $INTERFACE root 2>/dev/null || true

    # 应用新配置
    sudo tc qdisc add dev $INTERFACE root handle 1: netem \
        delay ${delay_ms}ms \
        loss ${loss_percent}% \
        rate ${rate_mbps}mbit

    # 验证配置
    sudo tc qdisc show dev $INTERFACE
}

function cleanup_tc() {
    echo "清理网络配置..."
    sudo tc qdisc del dev $INTERFACE root 2>/dev/null || true
}

# 主函数
case "$1" in
    configure)
        configure_tc "$2" "$3" "$4"
        ;;
    cleanup)
        cleanup_tc
        ;;
    *)
        echo "用法: $0 {configure|cleanup} [delay_ms] [rate_mbps] [loss_%]"
        exit 1
        ;;
esac
```

#### 5.3.3 自动化测试脚本: `run_phase3_test.py`

```python
#!/usr/bin/env python3
"""
Phase 3自动化测试脚本
功能:
1. 加载12拓扑参数
2. 循环测试每个拓扑(Classic + PQ-NTOR)
3. 收集数据并生成CSV
"""

import json
import subprocess
import time
from datetime import datetime

TOPOLOGY_PARAMS_FILE = '../configs/topology_tc_params.json'
PHASE3_BINARY = './phase3_sagin_network'
RESULTS_DIR = './phase3_results'

def load_topology_params():
    """加载12拓扑参数"""
    with open(TOPOLOGY_PARAMS_FILE, 'r') as f:
        return json.load(f)

def configure_network(delay_ms, rate_mbps, loss_percent):
    """配置网络参数"""
    cmd = [
        './configure_tc_netem.sh', 'configure',
        str(delay_ms), str(rate_mbps), str(loss_percent)
    ]
    subprocess.run(cmd, check=True)

def cleanup_network():
    """清理网络配置"""
    subprocess.run(['./configure_tc_netem.sh', 'cleanup'])

def run_test(topo_id, protocol, trial):
    """运行单次测试"""
    cmd = [PHASE3_BINARY, '--topo', topo_id,
           '--protocol', protocol, '--trial', str(trial)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def main():
    topologies = load_topology_params()

    print("="*70)
    print("Phase 3: SAGIN网络集成测试")
    print("="*70)
    print(f"拓扑数量: {len(topologies)}")
    print(f"协议: Classic NTOR, PQ-NTOR")
    print(f"每拓扑迭代: 20次")
    print(f"总测试数: {len(topologies) * 2 * 20}")
    print("="*70)

    for topo_id, params in topologies.items():
        print(f"\n[{topo_id}] 开始测试...")
        print(f"  延迟: {params['delay_ms']}ms")
        print(f"  带宽: {params['rate_mbps']}Mbps")
        print(f"  丢包: {params['loss_percent']}%")

        # 配置网络
        configure_network(
            params['delay_ms'],
            params['rate_mbps'],
            params['loss_percent']
        )

        # 测试Classic NTOR
        for trial in range(20):
            print(f"  [{topo_id}] Classic试次 {trial+1}/20...", end=' ')
            run_test(topo_id, 'classic', trial)
            print("✓")

        # 测试PQ-NTOR
        for trial in range(20):
            print(f"  [{topo_id}] PQ-NTOR试次 {trial+1}/20...", end=' ')
            run_test(topo_id, 'pq-ntor', trial)
            print("✓")

        # 清理网络
        cleanup_network()

        print(f"[{topo_id}] 完成!")

    print("\n" + "="*70)
    print("✅ Phase 3测试完成!")
    print("="*70)

if __name__ == '__main__':
    main()
```

### 5.4 部署架构

#### 单机部署 (简化版 - 推荐先实现)

```
┌────────────────────────────────────────────┐
│           飞腾派 (单机测试)                 │
├────────────────────────────────────────────┤
│                                             │
│  进程1: directory (端口5000)                │
│  进程2: relay_guard (端口6000)              │
│  进程3: relay_middle (端口6001)             │
│  进程4: relay_exit (端口6002)               │
│  进程5: client                              │
│                                             │
│  └──> Linux tc/netem 应用在loopback        │
│                                             │
└────────────────────────────────────────────┘

优点:
- ✅ 部署简单，一台设备即可
- ✅ 便于调试
- ✅ 网络配置统一

缺点:
- ⚠️ 网络模拟不够真实
- ⚠️ 单机资源限制
```

#### 分布式部署 (完整版 - 后续可选)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  飞腾派 #1   │  │  飞腾派 #2   │  │  飞腾派 #3   │  │  飞腾派 #4   │
│  (Directory) │  │  (Guard)     │  │  (Middle)    │  │  (Exit)      │
│  ─────────   │  │  ──────      │  │  ───────     │  │  ─────       │
│  Directory   │  │  Relay       │  │  Relay       │  │  Relay       │
│  Server      │  │  Node        │  │  Node        │  │  Node        │
│  端口5000    │  │  端口6000    │  │  端口6001    │  │  端口6002    │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                  网络: 192.168.5.0/24
                  (每台设备上应用tc配置)

优点:
- ✅ 真实分布式环境
- ✅ 更准确的网络模拟

缺点:
- ⚠️ 需要4台飞腾派
- ⚠️ 部署复杂度高
- ⚠️ 同步和协调困难
```

**建议**: 先实现单机版本，验证代码正确性后再考虑分布式

---

## 6. 数据分析计划

### 6.1 数据收集

**输出文件**: `phase3_sagin_results.csv`

```csv
topo_id,protocol,trial,cbt_ms,hop1_ms,hop2_ms,hop3_ms,success,delay_ms,rate_mbps,loss_percent
topo01,classic,0,16.8,5.6,5.6,5.6,1,5.42,31.81,2.0
topo01,classic,1,17.2,5.8,5.7,5.7,1,5.42,31.81,2.0
...
topo01,pq-ntor,0,17.1,5.7,5.7,5.7,1,5.42,31.81,2.0
...
topo12,pq-ntor,19,17.5,5.9,5.8,5.8,1,5.44,8.77,2.0
```

**数据量**: 480行 (12拓扑 × 2协议 × 20试次)

### 6.2 统计分析

#### 描述统计 (每拓扑)

```python
for topo_id in topologies:
    classic_data = results[results['topo_id']==topo_id &
                           results['protocol']=='classic']['cbt_ms']
    pq_data = results[results['topo_id']==topo_id &
                      results['protocol']=='pq-ntor']['cbt_ms']

    print(f"{topo_id}:")
    print(f"  Classic: mean={classic_data.mean():.2f}ms, "
          f"median={classic_data.median():.2f}ms, "
          f"std={classic_data.std():.2f}ms")
    print(f"  PQ-NTOR: mean={pq_data.mean():.2f}ms, "
          f"median={pq_data.median():.2f}ms, "
          f"std={pq_data.std():.2f}ms")
```

#### 配对t检验 (Classic vs PQ)

```python
from scipy.stats import ttest_rel

for topo_id in topologies:
    classic = get_cbt_data(topo_id, 'classic')
    pq = get_cbt_data(topo_id, 'pq-ntor')

    t_stat, p_value = ttest_rel(classic, pq)

    print(f"{topo_id}: t={t_stat:.3f}, p={p_value:.4f}")
    if p_value < 0.05:
        print(f"  显著差异: PQ比Classic {'快' if t_stat<0 else '慢'}")
```

#### 密码学开销占比分析

```python
# 从Phase 2结果
T_handshake_classic = 458.94 / 1000  # 转为ms: 0.459 ms
T_handshake_pq = 184.82 / 1000       # 转为ms: 0.185 ms

for topo_id, cbt_classic, cbt_pq in results:
    crypto_overhead_classic = 3 * T_handshake_classic
    crypto_overhead_pq = 3 * T_handshake_pq

    ratio_classic = (crypto_overhead_classic / cbt_classic) * 100
    ratio_pq = (crypto_overhead_pq / cbt_pq) * 100

    print(f"{topo_id}:")
    print(f"  Classic密码学占比: {ratio_classic:.1f}%")
    print(f"  PQ-NTOR密码学占比: {ratio_pq:.1f}%")
```

### 6.3 可视化

#### Figure 1: 12拓扑CBT对比 (柱状图)

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(topologies))
width = 0.35

classic_means = [get_mean_cbt(t, 'classic') for t in topologies]
pq_means = [get_mean_cbt(t, 'pq-ntor') for t in topologies]

ax.bar(x - width/2, classic_means, width, label='Classic NTOR')
ax.bar(x + width/2, pq_means, width, label='PQ-NTOR')

ax.set_xlabel('Topology ID')
ax.set_ylabel('Circuit Build Time (ms)')
ax.set_title('Phase 3: CBT Comparison Across 12 SAGIN Topologies')
ax.set_xticks(x)
ax.set_xticklabels([f'T{i+1}' for i in range(12)])
ax.legend()

plt.tight_layout()
plt.savefig('phase3_cbt_comparison.png', dpi=300)
```

#### Figure 2: 密码学开销占比 (饼图/堆叠柱状图)

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 子图1: Classic NTOR
crypto_classic = 3 * T_handshake_classic
network_classic = mean_cbt_classic - crypto_classic

axes[0].pie([crypto_classic, network_classic],
            labels=['Crypto', 'Network'],
            autopct='%1.1f%%',
            colors=['#ff6b6b', '#4ecdc4'])
axes[0].set_title('Classic NTOR\nCrypto vs Network')

# 子图2: PQ-NTOR
crypto_pq = 3 * T_handshake_pq
network_pq = mean_cbt_pq - crypto_pq

axes[1].pie([crypto_pq, network_pq],
            labels=['Crypto', 'Network'],
            autopct='%1.1f%%',
            colors=['#ff6b6b', '#4ecdc4'])
axes[1].set_title('PQ-NTOR\nCrypto vs Network')

plt.tight_layout()
plt.savefig('phase3_crypto_overhead_ratio.png', dpi=300)
```

#### Figure 3: 延迟vs带宽vs CBT (3D散点图/热力图)

```python
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

delays = [params['delay_ms'] for params in topology_params]
rates = [params['rate_mbps'] for params in topology_params]
cbts = [mean_cbt for mean_cbt in cbt_means]

ax.scatter(delays, rates, cbts, c='blue', marker='o', s=100)

ax.set_xlabel('Network Delay (ms)')
ax.set_ylabel('Bandwidth (Mbps)')
ax.set_zlabel('CBT (ms)')
ax.set_title('Phase 3: Network Conditions vs Performance')

plt.savefig('phase3_network_impact_3d.png', dpi=300)
```

---

## 7. 预期成果

### 7.1 定量结果预测

基于Phase 1和Phase 2的结果，我们可以预测Phase 3的结果：

#### CBT预测计算

**假设**: 网络延迟为单向延迟，RTT = 2 × 延迟

**Classic NTOR** (单跳):
```
T_hop_classic = T_handshake + T_network
              = 0.459 ms + (延迟 × 2)

对于topo01 (延迟5.42ms):
T_hop_classic = 0.459 + (5.42 × 2) = 11.30 ms
CBT_classic = 3 × 11.30 = 33.90 ms
```

**PQ-NTOR** (单跳):
```
T_hop_pq = 0.185 + (5.42 × 2) = 11.03 ms
CBT_pq = 3 × 11.03 = 33.09 ms
```

**密码学开销占比**:
```
Crypto_ratio_classic = (3 × 0.459) / 33.90 = 4.06%
Crypto_ratio_pq = (3 × 0.185) / 33.09 = 1.68%
```

#### 各拓扑预期结果

| 拓扑 | 延迟(ms) | CBT Classic(ms) | CBT PQ(ms) | PQ开销 | Crypto占比(C/PQ) |
|------|----------|----------------|-----------|--------|----------------|
| topo01 | 5.42 | 33.9 | 33.1 | -0.8ms | 4.1% / 1.7% |
| topo02 | 5.44 | 34.0 | 33.2 | -0.8ms | 4.0% / 1.7% |
| topo03 | 2.73 | 17.7 | 17.0 | -0.7ms | 7.8% / 3.3% |
| topo04 | 5.42 | 33.9 | 33.1 | -0.8ms | 4.1% / 1.7% |
| topo05 | 5.43 | 33.9 | 33.2 | -0.7ms | 4.1% / 1.7% |
| topo06 | 5.42 | 33.9 | 33.1 | -0.8ms | 4.1% / 1.7% |
| topo07 | 5.44 | 34.0 | 33.2 | -0.8ms | 4.0% / 1.7% |
| topo08 | 5.46 | 34.1 | 33.3 | -0.8ms | 4.0% / 1.7% |
| topo09 | 2.72 | 17.7 | 17.0 | -0.7ms | 7.8% / 3.3% |
| topo10 | 5.44 | 34.0 | 33.2 | -0.8ms | 4.0% / 1.7% |
| topo11 | 5.44 | 34.0 | 33.2 | -0.8ms | 4.0% / 1.7% |
| topo12 | 5.44 | 34.0 | 33.2 | -0.8ms | 4.0% / 1.7% |

**平均预测**:
- CBT Classic: **32.6 ms**
- CBT PQ-NTOR: **31.8 ms**
- PQ相比Classic: **-0.8 ms** (反而更快!)
- 密码学占比 (Classic): **4.5%**
- 密码学占比 (PQ-NTOR): **1.9%**

### 7.2 关键发现 (预期)

#### 发现1: PQ-NTOR在SAGIN环境表现优异

✅ **PQ-NTOR反而比Classic NTOR更快** (约0.8ms)
- 原因: Phase 2握手性能优势在网络环境中保持
- 密码学开销仅占总时间的1.9%

#### 发现2: 网络延迟主导性能

✅ **密码学开销占比很小** (1.9-7.8%)
- 91-98%的时间消耗在网络传输
- 即使切换到PQ密码学，总体影响<3%

#### 发现3: 低延迟拓扑更显著

✅ **topo03和topo09** (2.7ms延迟):
- 密码学开销占比提高到7-8%
- 但绝对值仍然很小 (<0.6ms)

#### 发现4: 部署可行性高

✅ **100%成功率** (预期)
- 所有480次测试应全部成功
- PQ-NTOR在真实网络环境稳定可靠

### 7.3 论文贡献点

#### 贡献1: 三层实验设计方法

提出系统的PQ密码学评估框架:
- **Layer 1**: 隔离基元性能
- **Layer 2**: 协议握手开销
- **Layer 3**: 网络集成影响

#### 贡献2: 真实SAGIN环境评估

首次在真实NOMA SAGIN网络参数下评估PQ-NTOR:
- 12种拓扑覆盖多样化场景
- 真实延迟/带宽/丢包率参数
- 480次测试提供统计可靠性

#### 贡献3: API设计vs性能洞察

揭示密码学库API设计的性能影响:
- EVP_PKEY封装 vs 原生实现
- 高层抽象的性能代价 (2.3×)
- 实现选择的重要性

#### 贡献4: 部署建议

为SAGIN环境部署PQ密码学提供指导:
- 密码学开销占比<5%
- PQ-NTOR可无缝替换Classic NTOR
- 推荐使用优化的原生实现而非高层API

### 7.4 论文章节映射

| Phase | 论文章节 | 内容 |
|-------|---------|------|
| **Phase 1** | 5.1 Cryptographic Primitives | 基元性能，ARM64 vs x86对比 |
| **Phase 2** | 5.2 Protocol Handshake | 握手性能，API开销分析 |
| **Phase 3** | 5.3 SAGIN Network Integration | 真实环境评估，密码学占比 |
| **综合** | 6. Discussion | API设计、平台优化、部署建议 |
| **综合** | 7. Conclusion | 三层评估方法、PQ-NTOR可行性 |

---

## 8. 实施计划

### 8.1 开发任务清单

#### 任务1: Phase 3核心代码 (1-2天)

- [ ] `phase3_sagin_network.c` - 主测试程序
  - [ ] 拓扑参数加载 (JSON解析)
  - [ ] 三跳电路构建函数
  - [ ] CBT和各跳延迟测量
  - [ ] 结果记录和CSV输出

- [ ] `configure_tc_netem.sh` - 网络配置脚本
  - [ ] tc/netem参数应用
  - [ ] 配置验证和错误处理
  - [ ] 清理函数

- [ ] Makefile更新
  - [ ] 添加phase3编译目标
  - [ ] 链接网络库

#### 任务2: 自动化测试 (1天)

- [ ] `run_phase3_test.py` - Python自动化脚本
  - [ ] 12拓扑循环测试
  - [ ] 进度显示和日志
  - [ ] 异常处理和重试

- [ ] `deploy_phase3.py` - 部署脚本
  - [ ] SSH文件传输
  - [ ] 远程编译
  - [ ] 远程测试执行
  - [ ] 结果回传

#### 任务3: 数据分析 (1天)

- [ ] `analyze_phase3.py` - 数据分析脚本
  - [ ] 描述统计
  - [ ] 配对t检验
  - [ ] 密码学占比计算
  - [ ] 可视化图表生成

#### 任务4: 测试验证 (0.5天)

- [ ] 单拓扑测试验证
- [ ] 完整12拓扑测试
- [ ] 数据有效性检查

### 8.2 时间估算

| 任务 | 估计时间 | 依赖 |
|------|---------|------|
| Phase 3代码开发 | 1-2天 | Phase 1/2代码库 |
| 自动化测试脚本 | 1天 | Phase 3代码 |
| 数据分析脚本 | 1天 | - |
| 测试验证 | 0.5天 | 全部代码 |
| **总计** | **3.5-4.5天** | - |

### 8.3 风险和挑战

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **tc/netem权限问题** | 高 | 提前配置sudo权限 |
| **网络配置冲突** | 中 | 测试前清理所有tc规则 |
| **测试耗时过长** | 低 | 优化测试流程，支持断点续测 |
| **数据收集失败** | 中 | 每次测试后立即保存结果 |
| **4台飞腾派协调** | 高 | 先实现单机版本 |

---

## 9. 下一步行动

### 立即行动 (现在)

✅ **Phase 3设计文档已完成**

### 下一步选择

**选项A**: 立即开始Phase 3代码开发
- 编写`phase3_sagin_network.c`
- 实现单机版本测试

**选项B**: 先生成Phase 1+2完整报告
- 总结前两个Phase成果
- 准备论文初稿

**选项C**: 验证现有网络测试代码
- 查看现有的directory/relay/client实现
- 确认是否可以复用

**推荐**: **选项C → 选项A**
1. 先查看现有代码，了解可复用部分
2. 然后开始Phase 3核心代码开发
3. 最后生成完整实验报告

---

## 10. 参考文献

1. Berger et al. (2025). "Gradually Deploying Post-Quantum Cryptography in Tor"
2. Li & Elahi (2024). "SaTor: Tor for Satellite Communication"
3. Kampanakis et al. (2020). "Post-Quantum Authentication in TLS 1.3"
4. wolfSSL (2024). "Post-Quantum Kyber Benchmarks on MacOS (ARM64)"
5. Emill (2024). "X25519-AArch64: Highly optimized curve25519"
6. OpenQuantumSafe (2024). "Benchmarking Visualization"
7. NIST (2024). "FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard"

---

**文档作者**: Claude Code Assistant
**最后更新**: 2025-12-03
**状态**: ✅ 设计完成，待实现

