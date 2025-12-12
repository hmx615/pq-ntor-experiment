# SAGIN PQ-NTOR 完整实验设计方案

## 一、实验目标

基于师妹提供的速率计算模型，设计真实的 SAGIN 网络环境，测试 PQ-NTOR 握手协议在不同链路条件下的性能表现，对比 OMA 和 NOMA 两种多址接入方式。

**核心研究问题**:
1. PQ-NTOR 握手在不同链路速率下的延迟表现
2. NOMA 相比 OMA 对 PQ-NTOR 性能的影响
3. 卫星、无人机、D2D 三种链路类型的握手成功率对比

---

## 二、实验场景设计

### 场景 1: 卫星→地面用户直连 (Satellite-to-Ground)

**物理参数**:
- 卫星位置: `[-118056.04, 14085.41, 813291.98]` m (时间槽15)
- 频率: 20 GHz
- 带宽: 20 MHz
- 发射功率: 20W (43 dBm)

**用户配置**:

| 用户类型 | 位置 (x, y, z) | 距波束中心距离 | 信道增益预期 |
|---------|---------------|--------------|-------------|
| 中心用户 | `[0, 5000, 0]` | 5 km | 强 |
| 边缘用户 | `[0, 15000, 0]` | 15 km | 弱 |

**测试配置**:
1. **OMA 模式**: 中心用户和边缘用户分别使用 20 MHz 带宽
2. **NOMA 模式**: 两用户共享 20 MHz，功率分配 α=0.7 (边缘用户70%，中心用户30%)

**预期速率** (需运行 `test_satellite_noma.py` 计算):
```python
# OMA
rate_center_oma ≈ ? Mbps
rate_edge_oma ≈ ? Mbps

# NOMA
rate_weak_noma ≈ ? Mbps  (边缘用户)
rate_strong_noma ≈ ? Mbps (中心用户)
```

---

### 场景 2: 无人机→地面用户 (UAV-to-Ground)

**物理参数**:
- 无人机位置: `[0, 0, 1000]` m (高度1000米)
- 频率: 2.4 GHz
- 带宽: 2 MHz
- 发射功率: 3.16W (35 dBm)

**用户配置**:

| 用户类型 | 位置 (x, y, z) | 水平距离 | LOS概率预期 |
|---------|---------------|---------|------------|
| 近端用户 | `[0, 0, 0]` | 0 m | 高 (~90%) |
| 远端用户 | `[2500, 500, 0]` | ~2550 m | 中 (~60%) |

**测试配置**:
1. **OMA 模式**: 每用户 2 MHz
2. **NOMA 模式**: 共享 2 MHz，α=0.7

**预期速率** (需运行 `test_uav_noma.py` 计算):
```python
# OMA
rate_near_oma ≈ ? Mbps
rate_far_oma ≈ ? Mbps

# NOMA
rate_weak_noma ≈ ? Mbps  (远端)
rate_strong_noma ≈ ? Mbps (近端)
```

---

### 场景 3: D2D 用户间直连 (Device-to-Device)

**物理参数**:
- 频率: 2.4 GHz
- 带宽: 2 MHz
- 发射功率: 0.2W (23 dBm)
- 路径损耗指数: 3.0

**用户配置**:

| 用户类型 | 位置 (x, y, z) | 距发射端距离 | 信道质量 |
|---------|---------------|------------|---------|
| 发射端 | `[0, 0, 0]` | - | - |
| 强用户 | `[30, 0, 0]` | 30 m | 强 |
| 弱用户 | `[100, 0, 0]` | 100 m | 弱 |

**测试配置**:
1. **OMA 模式**: 每用户 2 MHz
2. **NOMA 模式**: 共享 2 MHz，α=0.7

**预期速率** (需运行 `test_d2d_noma.py` 计算):
```python
# OMA
rate_strong_oma ≈ ? Mbps
rate_weak_oma ≈ ? Mbps

# NOMA
rate_weak_noma ≈ ? Mbps
rate_strong_noma ≈ ? Mbps
```

---

### 场景 4: 两跳混合链路 (Satellite→UAV→User)

**拓扑**: 卫星 → 无人机 → 地面用户

**第一跳 (卫星→无人机)**:
- 卫星位置: `[-118056.04, 14085.41, 813291.98]` m
- 无人机位置: `[0, 0, 1000]` m
- 频率: 20 GHz, 带宽: 20 MHz, 功率: 20W
- 无人机接收增益: 25 dB (高增益天线)

**第二跳 (无人机→用户)**:
- 无人机位置: `[0, 0, 1000]` m
- 用户位置: `[2500, 500, 0]` m
- 频率: 2.4 GHz, 带宽: 2 MHz, 功率: 3.16W

**关键规则**: **两跳速率取较小值**
```
端到端速率 = min(卫星→无人机速率, 无人机→用户速率)
```

---

## 三、实验指标定义

### 3.1 链路速率计算

使用师妹提供的三个计算程序:

```bash
# 计算所有场景的速率
python3 last_experiment/test_satellite_noma.py > results/satellite_rates.txt
python3 last_experiment/test_uav_noma.py > results/uav_rates.txt
python3 last_experiment/test_d2d_noma.py > results/d2d_rates.txt
```

### 3.2 Linux TC 参数映射

根据计算得到的速率，配置网络参数:

| 计算结果 | TC 配置 |
|---------|---------|
| 速率 (Mbps) | `tc qdisc add dev eth0 root tbf rate XMbit burst 32kbit latency 400ms` |
| SINR (dB) | 用于估算丢包率: `loss $(calculate_loss_from_sinr)%` |
| 距离 (m) | 用于估算延迟: `delay $(calculate_delay_from_distance)ms` |

**延迟计算公式**:
```
传播延迟 (ms) = 距离 (m) / (3 × 10^8 m/s) × 1000
```

示例:
- 卫星链路 (~815 km): ~2.7 ms
- 无人机链路 (~2.6 km): ~0.009 ms
- D2D 链路 (~100 m): ~0.0003 ms

### 3.3 PQ-NTOR 性能指标

对于每个场景，测量:

1. **握手延迟**:
   - 平均握手时间 (ms)
   - 最小/最大握手时间
   - 标准差

2. **成功率**:
   - 握手成功次数 / 总尝试次数
   - 超时失败率

3. **吞吐量**:
   - 握手后数据传输速率
   - 与理论速率的对比

4. **协议开销**:
   - PQ-NTOR 消息大小 (bytes)
   - 相对经典 NTOR 的开销比

---

## 四、实验拓扑映射 (12-Topology)

### 拓扑命名规则

基于论文中的 12 种拓扑，映射到实际场景:

| 拓扑编号 | 名称 | 链路类型 | 多址方式 | 用户位置 |
|---------|------|---------|---------|---------|
| 1 | Z1-UP1-OMA | 卫星→用户 | OMA | 中心用户 |
| 2 | Z1-UP1-NOMA | 卫星→用户 | NOMA | 中心+边缘 |
| 3 | Z1-UP2-OMA | 无人机→用户 | OMA | 近端用户 |
| 4 | Z1-UP2-NOMA | 无人机→用户 | NOMA | 近端+远端 |
| 5 | Z2-D2D-OMA | D2D | OMA | 30m用户 |
| 6 | Z2-D2D-NOMA | D2D | NOMA | 30m+100m |
| 7 | Z3-2Hop-Sat | 卫星→UAV | OMA | UAV中继 |
| 8 | Z3-2Hop-UAV | UAV→用户 | OMA | 远端用户 |
| 9 | Z3-2Hop-Full | 卫星→UAV→用户 | OMA | 端到端 |
| 10 | NOMA-Strong | 卫星NOMA | NOMA | 仅强用户 |
| 11 | NOMA-Weak | 卫星NOMA | NOMA | 仅弱用户 |
| 12 | Mix-All | 混合场景 | OMA+NOMA | 全部 |

### 配置文件生成

为每个拓扑生成 JSON 配置:

```json
{
  "topology_id": 1,
  "name": "Z1-UP1-OMA",
  "link_type": "satellite",
  "access_method": "OMA",
  "nodes": {
    "satellite": {"position": [-118056.04, 14085.41, 813291.98]},
    "user": {"position": [0, 5000, 0]}
  },
  "physical_params": {
    "frequency_hz": 20e9,
    "bandwidth_hz": 20e6,
    "tx_power_w": 20.0
  },
  "calculated_rates": {
    "rate_mbps": null,  // 运行计算后填入
    "sinr_db": null,
    "gain_db": null
  },
  "tc_config": {
    "rate": null,  // 从 calculated_rates 计算
    "delay": null,
    "loss": null
  }
}
```

---

## 五、实验流程

### Phase 1: 速率计算

```bash
cd /home/ccc/pq-ntor-experiment

# 创建结果目录
mkdir -p results/rate_calculations

# 运行三个计算程序
python3 last_experiment/test_satellite_noma.py | tee results/rate_calculations/satellite.txt
python3 last_experiment/test_uav_noma.py | tee results/rate_calculations/uav.txt
python3 last_experiment/test_d2d_noma.py | tee results/rate_calculations/d2d.txt

# 解析结果，填入配置文件
python3 scripts/parse_rates_to_config.py
```

### Phase 2: 网络参数配置

```bash
# 为每个拓扑应用 TC 配置
for topo in {1..12}; do
    python3 scripts/apply_tc_config.py --topology $topo
done
```

### Phase 3: PQ-NTOR 性能测试

```bash
# 在飞腾派上运行测试
./sagin-experiments/scripts/run_12topo_with_params.sh
```

### Phase 4: 数据分析

```bash
# 收集结果
python3 scripts/collect_results.py

# 生成对比图表
python3 scripts/plot_oma_vs_noma.py
python3 scripts/plot_link_comparison.py
```

---

## 六、关键脚本设计

### 6.1 统一速率计算模块 (`scripts/unified_rate_calc.py`)

```python
#!/usr/bin/env python3
"""
统一速率计算模块
整合三个计算程序，提供统一接口
"""

import numpy as np
import sys
sys.path.append('last_experiment')

from test_satellite_noma import (
    oma_rate_single_device as sat_oma,
    noma_rate_two_devices as sat_noma
)
from test_uav_noma import (
    uav_oma_rate,
    uav_noma_rate
)
from test_d2d_noma import (
    d2d_oma_rate,
    d2d_noma_rate
)

def calculate_all_scenarios():
    """计算所有 12 个拓扑的速率"""

    results = {}

    # === 场景 1-2: 卫星链路 ===
    sat_pos = np.array([-118056.04, 14085.41, 813291.98])
    user_center = np.array([0.0, 5000.0, 0.0])
    user_edge = np.array([0.0, 15000.0, 0.0])
    P_sat = 20.0
    B_sat = 20e6

    # OMA
    rate_c, sinr_c, gain_c = sat_oma(sat_pos, user_center, P_sat, B_sat)
    rate_e, sinr_e, gain_e = sat_oma(sat_pos, user_edge, P_sat, B_sat)

    results['Z1-UP1-OMA-center'] = {
        'rate_mbps': rate_c,
        'sinr_db': 10 * np.log10(sinr_c),
        'gain_db': 10 * np.log10(gain_c)
    }
    results['Z1-UP1-OMA-edge'] = {
        'rate_mbps': rate_e,
        'sinr_db': 10 * np.log10(sinr_e),
        'gain_db': 10 * np.log10(gain_e)
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = sat_noma(
        sat_pos, user_edge, user_center, P_sat, B_sat, 0.7,
        weak_is_uav=False, strong_is_uav=False
    )

    results['Z1-UP1-NOMA-weak'] = {
        'rate_mbps': rw,
        'sinr_db': 10 * np.log10(sw),
        'gain_db': 10 * np.log10(gw)
    }
    results['Z1-UP1-NOMA-strong'] = {
        'rate_mbps': rs,
        'sinr_db': 10 * np.log10(ss),
        'gain_db': 10 * np.log10(gs)
    }

    # === 场景 3-4: 无人机链路 ===
    uav_pos = np.array([0.0, 0.0, 1000.0])
    user_near = np.array([0.0, 0.0, 0.0])
    user_far = np.array([2500.0, 500.0, 0.0])
    P_uav = 3.16
    B_uav = 2e6

    # OMA
    rate_n, sinr_n, gain_n = uav_oma_rate(uav_pos, user_near, P_uav, B_uav)
    rate_f, sinr_f, gain_f = uav_oma_rate(uav_pos, user_far, P_uav, B_uav)

    results['Z1-UP2-OMA-near'] = {
        'rate_mbps': rate_n,
        'sinr_db': 10 * np.log10(sinr_n),
        'gain_db': 10 * np.log10(gain_n)
    }
    results['Z1-UP2-OMA-far'] = {
        'rate_mbps': rate_f,
        'sinr_db': 10 * np.log10(sinr_f),
        'gain_db': 10 * np.log10(gain_f)
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = uav_noma_rate(
        uav_pos, user_far, user_near, P_uav, B_uav, 0.7
    )

    results['Z1-UP2-NOMA-weak'] = {
        'rate_mbps': rw,
        'sinr_db': 10 * np.log10(sw),
        'gain_db': 10 * np.log10(gw)
    }
    results['Z1-UP2-NOMA-strong'] = {
        'rate_mbps': rs,
        'sinr_db': 10 * np.log10(ss),
        'gain_db': 10 * np.log10(gs)
    }

    # === 场景 5-6: D2D 链路 ===
    tx_pos = np.array([0.0, 0.0, 0.0])
    strong_rx = np.array([30.0, 0.0, 0.0])
    weak_rx = np.array([100.0, 0.0, 0.0])
    P_d2d = 0.2
    B_d2d = 2e6

    # OMA
    rate_s, sinr_s, gain_s = d2d_oma_rate(tx_pos, strong_rx, P_d2d, B_d2d)
    rate_w, sinr_w, gain_w = d2d_oma_rate(tx_pos, weak_rx, P_d2d, B_d2d)

    results['Z2-D2D-OMA-strong'] = {
        'rate_mbps': rate_s,
        'sinr_db': 10 * np.log10(sinr_s),
        'gain_db': 10 * np.log10(gain_s)
    }
    results['Z2-D2D-OMA-weak'] = {
        'rate_mbps': rate_w,
        'sinr_db': 10 * np.log10(sinr_w),
        'gain_db': 10 * np.log10(gain_w)
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = d2d_noma_rate(
        tx_pos, weak_rx, strong_rx, P_d2d, B_d2d, 0.7
    )

    results['Z2-D2D-NOMA-weak'] = {
        'rate_mbps': rw,
        'sinr_db': 10 * np.log10(sw),
        'gain_db': 10 * np.log10(gw)
    }
    results['Z2-D2D-NOMA-strong'] = {
        'rate_mbps': rs,
        'sinr_db': 10 * np.log10(ss),
        'gain_db': 10 * np.log10(gs)
    }

    # === 场景 7-9: 两跳链路 ===
    # 第一跳: 卫星→无人机
    rate_hop1, sinr_hop1, gain_hop1 = sat_oma(
        sat_pos, uav_pos, P_sat, B_sat, is_uav=True
    )

    # 第二跳: 无人机→远端用户
    rate_hop2, sinr_hop2, gain_hop2 = uav_oma_rate(
        uav_pos, user_far, P_uav, B_uav
    )

    # 端到端速率 = min(hop1, hop2)
    rate_e2e = min(rate_hop1, rate_hop2)

    results['Z3-2Hop-Sat'] = {
        'rate_mbps': rate_hop1,
        'sinr_db': 10 * np.log10(sinr_hop1),
        'gain_db': 10 * np.log10(gain_hop1)
    }
    results['Z3-2Hop-UAV'] = {
        'rate_mbps': rate_hop2,
        'sinr_db': 10 * np.log10(sinr_hop2),
        'gain_db': 10 * np.log10(gain_hop2)
    }
    results['Z3-2Hop-Full'] = {
        'rate_mbps': rate_e2e,
        'sinr_db': min(10*np.log10(sinr_hop1), 10*np.log10(sinr_hop2)),
        'gain_db': 10 * np.log10(gain_hop1 * gain_hop2)
    }

    return results

if __name__ == '__main__':
    import json
    results = calculate_all_scenarios()

    print("=" * 60)
    print("所有场景速率计算结果")
    print("=" * 60)

    for scenario, metrics in sorted(results.items()):
        print(f"\n{scenario}:")
        print(f"  速率: {metrics['rate_mbps']:.2f} Mbps")
        print(f"  SINR: {metrics['sinr_db']:.2f} dB")
        print(f"  增益: {metrics['gain_db']:.2f} dB")

    # 保存为 JSON
    with open('results/all_scenarios_rates.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n结果已保存到: results/all_scenarios_rates.json")
```

### 6.2 TC 配置应用脚本 (`scripts/apply_tc_config.py`)

```python
#!/usr/bin/env python3
"""
根据计算的速率配置 Linux TC
"""

import json
import subprocess
import argparse

def calculate_delay_from_distance(distance_m):
    """根据距离计算传播延迟"""
    speed_of_light = 3e8  # m/s
    delay_s = distance_m / speed_of_light
    return delay_s * 1000  # 转换为 ms

def calculate_loss_from_sinr(sinr_db):
    """根据 SINR 估算丢包率"""
    # 简化模型: SINR < 0 dB 时丢包率显著增加
    if sinr_db >= 20:
        return 0.0
    elif sinr_db >= 10:
        return 0.1
    elif sinr_db >= 0:
        return 1.0
    else:
        return 5.0

def apply_tc(interface, rate_mbps, delay_ms, loss_pct):
    """应用 TC 配置"""

    # 清除现有配置
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', interface, 'root'],
                   stderr=subprocess.DEVNULL)

    # 添加带宽限制
    cmd_rate = [
        'sudo', 'tc', 'qdisc', 'add', 'dev', interface, 'root',
        'tbf', f'rate', f'{rate_mbps}mbit',
        'burst', '32kbit',
        'latency', '400ms'
    ]
    subprocess.run(cmd_rate, check=True)

    # 添加延迟和丢包
    cmd_netem = [
        'sudo', 'tc', 'qdisc', 'add', 'dev', interface, 'parent', '1:1',
        'netem', f'delay', f'{delay_ms}ms',
        'loss', f'{loss_pct}%'
    ]
    subprocess.run(cmd_netem, check=True)

    print(f"✅ Applied TC: rate={rate_mbps}Mbps, delay={delay_ms}ms, loss={loss_pct}%")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', required=True, help='场景名称')
    parser.add_argument('--interface', default='eth0', help='网络接口')
    args = parser.parse_args()

    # 读取计算结果
    with open('results/all_scenarios_rates.json', 'r') as f:
        results = json.load(f)

    if args.scenario not in results:
        print(f"❌ 场景 {args.scenario} 不存在")
        return 1

    metrics = results[args.scenario]

    # 计算 TC 参数
    rate_mbps = metrics['rate_mbps']
    sinr_db = metrics['sinr_db']

    # 根据场景类型估算距离和延迟
    if 'Sat' in args.scenario:
        distance_m = 815000  # 815 km
    elif 'UAV' in args.scenario:
        distance_m = 2600  # 2.6 km
    elif 'D2D' in args.scenario:
        distance_m = 100  # 100 m
    else:
        distance_m = 1000  # 默认

    delay_ms = calculate_delay_from_distance(distance_m)
    loss_pct = calculate_loss_from_sinr(sinr_db)

    # 应用配置
    apply_tc(args.interface, rate_mbps, delay_ms, loss_pct)

    return 0

if __name__ == '__main__':
    exit(main())
```

---

## 七、预期成果

### 7.1 数据输出

每个拓扑生成:
1. 速率计算结果 (JSON)
2. PQ-NTOR 握手日志 (TXT)
3. 性能指标统计 (CSV)

### 7.2 对比分析

生成对比图表:
1. **OMA vs NOMA 握手延迟对比**
2. **三种链路类型的成功率对比**
3. **速率-延迟关系曲线**
4. **PQ-NTOR vs 经典 NTOR 开销对比**

### 7.3 论文结论支撑

通过实验数据验证:
- [ ] PQ-NTOR 在低速率链路下的可行性
- [ ] NOMA 对后量子密钥交换的影响
- [ ] SAGIN 网络环境下的实际部署性能

---

## 八、下一步行动

1. **立即执行**: 运行统一速率计算脚本
   ```bash
   cd /home/ccc/pq-ntor-experiment
   mkdir -p scripts results
   # 创建并运行 unified_rate_calc.py
   ```

2. **验证结果**: 检查计算的速率是否合理

3. **生成配置**: 为 12 个拓扑生成完整的配置文件

4. **部署测试**: 在飞腾派上应用 TC 配置并运行 PQ-NTOR 测试

---

**设计完成时间**: 2025-11-27
**设计者**: Claude (基于师妹提供的速率计算模型)
