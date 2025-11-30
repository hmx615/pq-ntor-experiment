# 三跳Tor电路构建时间测试方案

**当前状态**: 已测试PQ-NTOR单次握手性能 (~180 µs)
**目标**: 测试完整三跳Tor电路构建时间 (包含网络传输、多次握手、电路建立)

---

## 🔍 当前测试 vs 完整电路测试对比

### 当前测试: PQ-NTOR握手计算时间

```
测试内容:
  - 单次Kyber-512 KEM握手
  - 纯计算时间 (Client create + Server reply + Client finish)
  - 单机运行，无网络传输

测试结果:
  - 飞腾派: ~180 µs
  - 主要瓶颈: CPU密码运算

局限性:
  ✗ 没有真实网络延迟
  ✗ 没有多跳中继
  ✗ 没有电路建立开销
  ✗ 不反映实际Tor使用场景
```

### 完整三跳电路测试

```
测试内容:
  - Client → Guard Relay (第1跳握手)
  - Guard → Middle Relay (第2跳握手，通过第1跳转发)
  - Middle → Exit Relay (第3跳握手，通过第1、2跳转发)
  - 电路建立确认
  - 包含真实网络传输延迟

预期结果:
  - 总时间 = 3×握手时间 + 网络延迟 + 建立开销
  - 主要瓶颈: 网络延迟 (特别是SAGIN场景)

价值:
  ✓ 真实反映Tor使用体验
  ✓ 展示SAGIN网络影响
  ✓ 端到端性能指标
  ✓ 更高的论文价值
```

---

## 📊 三跳电路构建时间组成

### 时间分解

```
总电路构建时间 = T_hop1 + T_hop2 + T_hop3 + T_overhead

其中:
  T_hop1 = Client → Guard握手
         = RTT(Client-Guard) + Compute(Guard)

  T_hop2 = Guard → Middle握手 (通过Guard转发)
         = RTT(Client-Guard) + RTT(Guard-Middle) + Compute(Middle)

  T_hop3 = Middle → Exit握手 (通过Guard和Middle转发)
         = RTT(Client-Guard) + RTT(Guard-Middle) + RTT(Middle-Exit) + Compute(Exit)

  T_overhead = 电路建立确认、状态同步等
```

### 12拓扑场景分析

以**topo01**(卫星直连NOMA，31.81 Mbps, 5.42 ms)为例:

**单机测试** (当前):
```
握手时间: 180 µs
网络影响: 0 (无真实网络)
```

**三跳电路测试** (预期):
```
假设拓扑:
  Client (Ground) → Guard (UAV1) → Middle (SAT) → Exit (UAV2)

第1跳 (Client→Guard):
  RTT: 2.7 ms (D2D-UAV)
  握手计算: 180 µs
  小计: ~2.9 ms

第2跳 (Guard→Middle，通过Guard转发):
  RTT(Client-Guard): 2.7 ms
  RTT(Guard-Middle): 5.4 ms (UAV-SAT)
  握手计算: 180 µs
  小计: ~8.3 ms

第3跳 (Middle→Exit，通过Guard和Middle转发):
  RTT(Client-Guard): 2.7 ms
  RTT(Guard-Middle): 5.4 ms
  RTT(Middle-Exit): 5.4 ms (SAT-UAV)
  握手计算: 180 µs
  小计: ~13.7 ms

总电路构建时间: ~25-30 ms
```

**关键观察**:
- 网络延迟成为主导 (25 ms >> 0.5 ms握手计算)
- SAGIN高延迟场景影响显著
- 多跳累加效应明显

---

## 🛠️ 实现方案

### 方案1: 单机模拟 + TC网络延迟 (推荐，快速验证)

**设计**:
```
飞腾派单机运行:
  - Directory Server
  - Guard Relay (端口9001)
  - Middle Relay (端口9002)
  - Exit Relay (端口9003)
  - Client

使用TC (Traffic Control)模拟网络延迟:
  - 为每个端口配置不同的延迟/丢包/带宽
  - 模拟12种SAGIN拓扑的网络参数
```

**实现步骤**:

1. **配置TC规则** (每个拓扑不同):
```bash
#!/bin/bash
# 以topo01为例

# Guard Relay (9001) - D2D-UAV链路
tc qdisc add dev lo parent 1:1 handle 10: netem \
   delay 1.35ms \
   rate 20mbit \
   loss 0.5%

# Middle Relay (9002) - UAV-SAT链路
tc qdisc add dev lo parent 1:2 handle 20: netem \
   delay 2.71ms \
   rate 31.81mbit \
   loss 2.0%

# Exit Relay (9003) - SAT-UAV链路
tc qdisc add dev lo parent 1:3 handle 30: netem \
   delay 2.71ms \
   rate 29.21mbit \
   loss 0.1%
```

2. **编写测试程序**:
```c
// test_3hop_circuit_time.c

#include <time.h>
#include "tor_client.h"

typedef struct {
    double hop1_ms;
    double hop2_ms;
    double hop3_ms;
    double total_ms;
} CircuitBuildTime;

CircuitBuildTime measure_circuit_build() {
    struct timespec start, end;
    CircuitBuildTime result = {0};

    // 开始计时
    clock_gettime(CLOCK_MONOTONIC, &start);

    // 第1跳: Client → Guard
    struct timespec hop1_start;
    clock_gettime(CLOCK_MONOTONIC, &hop1_start);

    tor_extend_circuit(guard_addr, guard_port);

    struct timespec hop1_end;
    clock_gettime(CLOCK_MONOTONIC, &hop1_end);
    result.hop1_ms = timespec_diff_ms(&hop1_start, &hop1_end);

    // 第2跳: Guard → Middle (通过Guard转发)
    struct timespec hop2_start;
    clock_gettime(CLOCK_MONOTONIC, &hop2_start);

    tor_extend_circuit(middle_addr, middle_port);

    struct timespec hop2_end;
    clock_gettime(CLOCK_MONOTONIC, &hop2_end);
    result.hop2_ms = timespec_diff_ms(&hop2_start, &hop2_end);

    // 第3跳: Middle → Exit (通过Guard和Middle转发)
    struct timespec hop3_start;
    clock_gettime(CLOCK_MONOTONIC, &hop3_start);

    tor_extend_circuit(exit_addr, exit_port);

    struct timespec hop3_end;
    clock_gettime(CLOCK_MONOTONIC, &hop3_end);
    result.hop3_ms = timespec_diff_ms(&hop3_start, &hop3_end);

    // 总时间
    clock_gettime(CLOCK_MONOTONIC, &end);
    result.total_ms = timespec_diff_ms(&start, &end);

    return result;
}

int main() {
    // 为每个拓扑运行100次测试
    for (int topo = 1; topo <= 12; topo++) {
        load_topology_tc_config(topo);

        printf("Testing topo%02d...\n", topo);

        double total_times[100];
        for (int i = 0; i < 100; i++) {
            CircuitBuildTime cbt = measure_circuit_build();
            total_times[i] = cbt.total_ms;

            if (i == 0) {
                // 打印第一次的详细分解
                printf("  Hop1: %.2f ms\n", cbt.hop1_ms);
                printf("  Hop2: %.2f ms\n", cbt.hop2_ms);
                printf("  Hop3: %.2f ms\n", cbt.hop3_ms);
                printf("  Total: %.2f ms\n", cbt.total_ms);
            }
        }

        // 统计
        double avg = compute_average(total_times, 100);
        double std = compute_stddev(total_times, 100);

        printf("  Average: %.2f ± %.2f ms\n", avg, std);
    }
}
```

**优点**:
- ✅ 快速实现 (1-2天)
- ✅ 可在单个飞腾派上测试
- ✅ 包含网络延迟影响
- ✅ 可测试12拓扑

**缺点**:
- ❌ TC模拟有误差
- ❌ loopback优化可能影响结果
- ❌ 非真实分布式环境

---

### 方案2: 7个飞腾派真实分布式测试 (论文级)

**设计**:
```
飞腾派部署:
  飞腾派1: Directory Server
  飞腾派2: Guard Relay (Ground节点角色)
  飞腾派3: Middle Relay (UAV节点角色)
  飞腾派4: Exit Relay (SAT节点角色)
  飞腾派5: 备用Relay
  飞腾派6: Client
  飞腾派7: 控制台 + 监控

真实TC配置:
  - 每个飞腾派配置真实网络延迟
  - 根据12拓扑动态切换TC参数
```

**实现步骤**:

1. **拓扑映射**:
```python
# 为12拓扑定义节点角色和链路参数

TOPO_CONFIGS = {
    'topo01': {  # 卫星直连NOMA
        'guard': {'role': 'UAV1', 'ip': '192.168.100.12'},
        'middle': {'role': 'SAT', 'ip': '192.168.100.11'},
        'exit': {'role': 'UAV2', 'ip': '192.168.100.13'},
        'links': {
            'client-guard': {'delay': 1.35, 'rate': 20, 'loss': 0.5},
            'guard-middle': {'delay': 2.71, 'rate': 161, 'loss': 0.1},
            'middle-exit': {'delay': 2.71, 'rate': 29.21, 'loss': 0.1},
        }
    },
    # ... topo02-12
}
```

2. **动态TC配置脚本**:
```bash
#!/bin/bash
# apply_topo_tc.sh

TOPO=$1

# 在每个飞腾派上应用TC规则
ssh guard@192.168.100.12 "sudo tc qdisc del dev eth0 root; \
    sudo tc qdisc add dev eth0 root netem delay ${GUARD_DELAY}ms rate ${GUARD_RATE}mbit loss ${GUARD_LOSS}%"

ssh middle@192.168.100.11 "sudo tc qdisc del dev eth0 root; \
    sudo tc qdisc add dev eth0 root netem delay ${MIDDLE_DELAY}ms rate ${MIDDLE_RATE}mbit loss ${MIDDLE_LOSS}%"

# ...
```

3. **自动化测试脚本**:
```python
#!/usr/bin/env python3
# test_3hop_distributed.py

import paramiko
import time

for topo_id in range(1, 13):
    print(f"Testing topo{topo_id:02d}...")

    # 1. 应用TC配置
    apply_topo_tc(topo_id)
    time.sleep(2)

    # 2. 重启所有Relay
    restart_all_relays()
    time.sleep(5)

    # 3. 运行Client测试
    results = run_client_circuit_test(num_circuits=100)

    # 4. 收集结果
    save_results(topo_id, results)
```

**优点**:
- ✅ 真实分布式环境
- ✅ 真实网络传输
- ✅ 高论文价值
- ✅ 可演示展示

**缺点**:
- ❌ 需要7个飞腾派
- ❌ 配置复杂 (5-7天)
- ❌ 调试困难

---

## 📊 预期测试结果

### 三跳电路构建时间估算 (基于5.42ms平均RTT)

**单机模拟** (方案1):

| 拓扑 | 网络参数 | 预期电路构建时间 |
|------|---------|----------------|
| topo01 | 31.81 Mbps, 5.42ms | 25-30 ms |
| topo02 | 8.77 Mbps, 5.44ms | 25-30 ms |
| topo03 | 20.53 Mbps, 2.73ms | 12-15 ms (低延迟) |
| topo11 | 3.60 Mbps, 5.44ms | 25-30 ms |

**公式**:
```
T_circuit ≈ 3 × RTT_avg + 3 × T_handshake + T_overhead
         ≈ 3 × 5.42ms + 3 × 0.18ms + 2ms
         ≈ 16.26 + 0.54 + 2
         ≈ 19 ms
```

**真实分布式** (方案2):
```
预期会更慢，因为:
  - 真实网络抖动
  - 跨设备通信开销
  - 可能的重传

估计: 30-50 ms
```

---

## 🔬 测试指标对比

### 当前握手测试

```
指标:
  - 握手计算时间 (µs)
  - 标准差

价值:
  ✓ 证明PQ-NTOR计算开销
  ✓ 算法性能评估

局限:
  ✗ 不反映实际使用场景
```

### 三跳电路测试

```
新增指标:
  - 电路构建总时间 (ms)
  - 每跳分解时间
  - 网络延迟占比
  - 握手计算占比
  - 吞吐量 (电路数/秒)

价值:
  ✓ 端到端性能
  ✓ 真实用户体验
  ✓ 网络影响量化
  ✓ 更高论文价值
```

---

## 🎯 推荐实施路线

### 阶段1: 快速验证 (1-2天)

**目标**: 证明三跳电路测试可行

1. **修改现有代码**:
   - 在 `c/examples/test_3hop.c` 基础上扩展
   - 添加时间测量
   - 添加TC配置脚本

2. **单机测试**:
   - 在飞腾派上运行
   - 测试3-4个拓扑
   - 验证TC参数生效

3. **初步结果**:
   - 确认电路构建时间 > 握手时间
   - 验证网络延迟影响

### 阶段2: 完整单机测试 (2-3天)

**目标**: 收集12拓扑完整数据

1. **自动化脚本**:
   - 12拓扑自动切换
   - 每拓扑100次测试
   - 自动生成报告

2. **数据分析**:
   - 电路构建时间 vs 网络延迟
   - 握手时间占比分析
   - 上行 vs 下行对比

3. **论文数据**:
   - 可用于论文撰写
   - 单机模拟的合理性说明

### 阶段3: 分布式验证 (可选，5-7天)

**目标**: 真实环境验证

1. **7派部署**
2. **12拓扑真实测试**
3. **对比分析**: 单机 vs 分布式

---

## 📁 需要修改的代码

### 1. 扩展benchmark程序

**新文件**: `c/benchmark/benchmark_3hop_circuit.c`

```c
// 测量三跳电路构建时间
// 输出: hop1, hop2, hop3, total时间
```

### 2. TC配置脚本

**新文件**: `apply_12topo_tc.sh`

```bash
# 根据拓扑ID配置TC参数
# 支持loopback或真实网卡
```

### 3. Python自动化测试

**新文件**: `test_3hop_12topo.py`

```python
# 自动化运行12拓扑
# 收集结果
# 生成报告
```

---

## 💡 论文价值提升

### 增加三跳电路测试后

**新增贡献**:
1. ✅ 端到端性能评估 (不只是握手)
2. ✅ SAGIN网络延迟影响量化
3. ✅ 多跳累加效应分析
4. ✅ 更真实的用户体验指标

**新增图表** (建议):
- 图7: 电路构建时间 vs 握手时间对比
- 图8: 每跳时间分解 (堆叠柱状图)
- 图9: 网络延迟 vs 计算时间占比
- 图10: 三跳累加延迟分析

**论文影响**:
- 从"算法性能"扩展到"系统性能"
- 更适合系统类顶会 (USENIX, NSDI)
- 审稿人接受度更高

---

## ❓ 下一步行动

**您的决定**:

1. **快速路线**:
   - 先完成单机三跳测试
   - 1-2天产出数据
   - 适合快速发论文

2. **完整路线**:
   - 单机 + 分布式
   - 5-7天
   - 论文价值更高

3. **仅握手数据**:
   - 使用当前数据
   - 论文定位为"算法性能"
   - 也可以发表

**我的建议**:
- 如果时间充足 → 做三跳测试 (方案1单机即可)
- 如果时间紧 → 当前握手数据也足够

**需要我帮您**:
1. 编写三跳测试代码?
2. 创建TC配置脚本?
3. 设计自动化测试流程?

请告诉我您的选择!
