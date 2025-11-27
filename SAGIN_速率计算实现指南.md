# SAGIN 速率计算实现指南

**基于师妹提供的速率计算模型**
**日期**: 2025-11-27

---

## 📋 文档概述

师妹提供了完整的 SAGIN 网络速率计算模型，包括：
1. ✅ **卫星轨迹数据** (30个时间槽)
2. ✅ **三种链路类型的速率计算**
3. ✅ **OMA 和 NOMA 对比**
4. ✅ **完整的 Python 实现代码**

---

## 🛰️ 网络拓扑模型

### 三层架构

```
    🛰️ 卫星 (Satellite)
        ↓↑ 20 GHz, 20 MHz
    ✈️ 无人机 (UAV)
        ↓↑ 2.4 GHz, 2 MHz
    👤 地面用户 (User)
        ↔️ 2.4 GHz, 2 MHz (D2D)
    👤 其他用户
```

### 关键参数设置

#### 发射功率
- **卫星**: 20 W
- **无人机**: 3-5 W
- **用户终端**: 0.2 W

#### 频率和带宽
- **卫星链路**: 20 GHz, 20 MHz/信道
- **UAV链路**: 2.4 GHz, 2 MHz/信道
- **D2D链路**: 2.4 GHz, 2 MHz/信道

#### 天线增益
- **卫星**: 32 dBi
- **无人机**: 25 dBi
- **用户**: 5 dBi

---

## 🌍 场景设置

### 卫星轨迹

师妹提供了**30个时间槽**的卫星位置数据，建议使用：
- **时间槽 15**: 卫星在目标区域正上方
  - 位置: `[-118056.04, 14085.41, 813291.98]` (单位: 米)

### 用户分布区域

以 `(0, 0, 0)` 为中心，半径 **15 km** 的圆形区域：
- 可选位置:
  - `(0, 15000, 0)` - 正北
  - `(0, -15000, 0)` - 正南
  - `(-15000, 0, 0)` - 正西
  - `(15000, 0, 0)` - 正东
  - 或任意圆内点

### 无人机高度

默认: **1000 米**

---

## 💻 速率计算模型

### 1️⃣ 卫星到地面/无人机 (Sat-to-Ground/UAV)

#### 模型特点
- ✅ 考虑**自由空间路径损耗** (FSPL)
- ✅ 考虑**波束赋形增益** (Beam Pattern)
- ✅ 使用 Bessel 函数计算方向性

#### 核心函数

```python
def oma_rate_single_device(sat_pos, dev_pos, P_tx_W, B_Hz, is_uav=False):
    """
    计算卫星到单个设备的 OMA 速率

    参数:
        sat_pos: 卫星位置 [x, y, z] (米)
        dev_pos: 设备位置 [x, y, z] (米)
        P_tx_W: 发射功率 (瓦特)
        B_Hz: 带宽 (Hz)
        is_uav: 是否为无人机 (影响天线增益)

    返回:
        rate_mbps: 速率 (Mbps)
        sinr: 信干噪比 (线性值)
        gain: 信道增益 (线性值)
    """
```

#### NOMA 双用户速率

```python
def noma_rate_two_devices(sat_pos, weak_pos, strong_pos,
                         P_tx_W, B_Hz, alpha_power,
                         weak_is_uav=False, strong_is_uav=False):
    """
    计算 NOMA 模式下两个用户的速率

    参数:
        alpha_power: 分配给弱用户的功率比例 (0.7-0.8推荐)
                    弱用户 = 距离远/信道差
                    强用户 = 距离近/信道好

    NOMA 原理:
        - 弱用户分配更高功率 (70-80%)
        - 强用户使用 SIC (串行干扰消除) 解码
    """
```

---

### 2️⃣ 无人机到地面用户 (UAV-to-User)

#### 模型特点
- ✅ 考虑**视距/非视距概率** (LOS/NLOS)
- ✅ 基于**仰角**计算 LOS 概率
- ✅ 不同路径损耗

#### 参数设置
```python
A_SUB, B_SUB = 4.88, 0.43  # 环境参数
ETA_LOS_DB = 1.0           # LOS 额外损耗
ETA_NLOS_DB = 21.0         # NLOS 额外损耗
FREQ_UAV = 2.4e9           # 2.4 GHz
```

#### 核心函数

```python
def uav_oma_rate(uav_pos, user_pos, P_uav_W, B_Hz):
    """计算 UAV 到用户的 OMA 速率"""

def uav_noma_rate(uav_pos, weak_user_pos, strong_user_pos,
                 P_uav_W, B_Hz, alpha_power):
    """计算 UAV 的 NOMA 双用户速率"""
```

---

### 3️⃣ 用户到用户 (D2D - Device-to-Device)

#### 模型特点
- ✅ 简化的**路径损耗模型**
- ✅ 路径损耗指数: **3.0**
- ✅ 参考距离: **1.0 米**

#### 核心函数

```python
def d2d_oma_rate(user_a_pos, user_b_pos, P_tx_W, B_Hz):
    """计算 D2D OMA 速率"""

def d2d_noma_rate(tx_pos, weak_rx_pos, strong_rx_pos,
                 P_tx_W, B_Hz, alpha_power):
    """计算 D2D NOMA 速率"""
```

---

## 🎯 关键计算逻辑

### 两跳链路速率规则

**重要**: 两跳链路的最终速率 = `min(第一跳速率, 第二跳速率)`

```python
# 示例: 卫星 → UAV → 用户
rate_sat_to_uav = oma_rate_single_device(sat_pos, uav_pos, P_sat, B_sat, is_uav=True)
rate_uav_to_user = uav_oma_rate(uav_pos, user_pos, P_uav, B_uav)

# 端到端速率
end_to_end_rate = min(rate_sat_to_uav[0], rate_uav_to_user[0])
```

### NOMA 功率分配策略

- **弱用户** (距离远/信道差): α = 0.7 ~ 0.8 (分配70-80%功率)
- **强用户** (距离近/信道好): 1-α = 0.2 ~ 0.3

**原理**:
- 弱用户接收高功率信号，直接解码
- 强用户先解码弱用户信号，然后 SIC 消除，再解码自己的信号

---

## 🚀 实际应用示例

### 场景 1: 卫星直连地面用户 (单跳)

```python
import numpy as np

# 卫星位置 (时间槽 15)
sat = np.array([-118056.04, 14085.41, 813291.98])

# 地面用户
user = np.array([10000.0, 5000.0, 0.0])  # 15km 圆内任意点

# 卫星参数
P_sat = 20.0      # 20 W
B_sat = 20e6      # 20 MHz

# 计算速率
rate, sinr, gain = oma_rate_single_device(sat, user, P_sat, B_sat, is_uav=False)

print(f"速率: {rate:.3f} Mbps")
print(f"SINR: {10*np.log10(sinr):.2f} dB")
```

### 场景 2: 两跳中继 (Sat → UAV → User)

```python
# 卫星位置
sat = np.array([-118056.04, 14085.41, 813291.98])

# UAV 位置 (1km 高空)
uav = np.array([3000.0, 2000.0, 1000.0])

# 地面用户
user = np.array([4000.0, 2500.0, 0.0])

# 第一跳: 卫星 → UAV
rate1, _, _ = oma_rate_single_device(sat, uav, P_sat=20.0, B_Hz=20e6, is_uav=True)

# 第二跳: UAV → 用户
rate2, _, _ = uav_oma_rate(uav, user, P_uav_W=3.16, B_Hz=2e6)

# 端到端速率
end_to_end = min(rate1, rate2)

print(f"第一跳 (Sat→UAV): {rate1:.3f} Mbps")
print(f"第二跳 (UAV→User): {rate2:.3f} Mbps")
print(f"端到端速率: {end_to_end:.3f} Mbps")
```

### 场景 3: NOMA 多用户对比

```python
# 卫星 → 两个用户 (NOMA)
weak_user = np.array([12000.0, 8000.0, 0.0])   # 距离远
strong_user = np.array([5000.0, 3000.0, 0.0])  # 距离近

# NOMA (功率分配 α=0.7)
(rate_w, rate_s), _, _ = noma_rate_two_devices(
    sat, weak_user, strong_user,
    P_tx_W=20.0, B_Hz=20e6, alpha_power=0.7,
    weak_is_uav=False, strong_is_uav=False
)

# OMA 对比 (每用户 10 MHz)
rate_w_oma, _, _ = oma_rate_single_device(sat, weak_user, 20.0, 10e6, False)
rate_s_oma, _, _ = oma_rate_single_device(sat, strong_user, 20.0, 10e6, False)

print("NOMA vs OMA 对比:")
print(f"弱用户: NOMA {rate_w:.3f} Mbps vs OMA {rate_w_oma:.3f} Mbps")
print(f"强用户: NOMA {rate_s:.3f} Mbps vs OMA {rate_s_oma:.3f} Mbps")
print(f"总和: NOMA {rate_w+rate_s:.3f} vs OMA {rate_w_oma+rate_s_oma:.3f}")
```

---

## 🛠️ 集成到 PQ-NTOR 实验

### 方案: 链路速率映射到网络参数

#### 1. 计算每条链路的理论速率

```python
# link_calculator.py
class SAGINLinkCalculator:
    def __init__(self):
        self.sat_pos = np.array([-118056.04, 14085.41, 813291.98])

    def calculate_link_params(self, node_a, node_b):
        """
        根据节点类型和位置计算链路参数

        返回:
            rate_mbps: 速率 (Mbps)
            delay_ms: 传播延迟 (ms)
            loss_rate: 丢包率 (%)
        """
        # 计算速率
        if node_a['type'] == 'satellite':
            rate, sinr, _ = oma_rate_single_device(
                self.sat_pos, node_b['pos'],
                P_tx_W=20.0, B_Hz=20e6,
                is_uav=(node_b['type'] == 'uav')
            )
        elif node_a['type'] == 'uav':
            rate, sinr, _ = uav_oma_rate(
                node_a['pos'], node_b['pos'],
                P_uav_W=3.16, B_Hz=2e6
            )
        else:  # D2D
            rate, sinr, _ = d2d_oma_rate(
                node_a['pos'], node_b['pos'],
                P_tx_W=0.2, B_Hz=2e6
            )

        # 计算传播延迟
        distance = np.linalg.norm(node_a['pos'] - node_b['pos'])
        delay_ms = distance / 3e8 * 1000  # 光速传播

        # 根据 SINR 估算丢包率
        sinr_db = 10 * np.log10(sinr)
        if sinr_db > 20:
            loss_rate = 0.1
        elif sinr_db > 10:
            loss_rate = 1.0
        else:
            loss_rate = 5.0

        return rate, delay_ms, loss_rate
```

#### 2. 应用到 Linux TC

```python
def apply_link_to_tc(interface, rate_mbps, delay_ms, loss_rate):
    """将计算的链路参数应用到 TC"""
    cmd = f"sudo tc qdisc add dev {interface} root netem " \
          f"delay {delay_ms}ms rate {rate_mbps}mbit loss {loss_rate}%"
    subprocess.run(cmd, shell=True)
```

#### 3. 拓扑配置生成

```python
def generate_topology_config(topology_name):
    """
    为每个拓扑生成配置

    示例: topology_01_z1up1.json
    """
    if topology_name == "topology_01_z1up1":
        nodes = {
            'sat': {'type': 'satellite', 'pos': sat_pos_slot15},
            'uav1': {'type': 'uav', 'pos': np.array([3e3, 2e3, 1e3])},
            'user1': {'type': 'user', 'pos': np.array([5e3, 0, 0])},
        }

        links = [
            ('sat', 'uav1'),
            ('uav1', 'user1'),
        ]

        # 计算每条链路参数
        config = []
        for src, dst in links:
            rate, delay, loss = calculate_link_params(nodes[src], nodes[dst])
            config.append({
                'link': f"{src}->{dst}",
                'rate': rate,
                'delay': delay,
                'loss': loss
            })

        return config
```

---

## 📊 典型速率值参考

### 基于师妹模型的估算

#### 卫星链路 (20 W, 20 GHz, 20 MHz)
- 到地面用户 (15km内): **10-50 Mbps**
- 到无人机 (1km高): **50-100 Mbps**

#### UAV 链路 (3-5 W, 2.4 GHz, 2 MHz)
- 到地面用户 (1-5km): **1-10 Mbps**

#### D2D 链路 (0.2 W, 2.4 GHz, 2 MHz)
- 用户间 (100m-1km): **0.5-5 Mbps**

### NOMA vs OMA 提升

- **弱用户**: NOMA 比 OMA **高 20-40%**
- **强用户**: NOMA 比 OMA **高 10-20%**
- **系统总和**: NOMA 比 OMA **高 15-30%**

---

## 🎯 实验设计建议

### Phase 1: 验证速率模型

```python
# test_rate_calculator.py
# 使用师妹提供的示例验证计算正确性

sat = np.array([0.0, 0.0, 35786e3])  # GEO 卫星
user_A = np.array([5e3, 2e3, 0.0])

rate, sinr, gain = oma_rate_single_device(sat, user_A, 5.0, 20e6, False)
print(f"速率: {rate:.3f} Mbps")  # 应与师妹示例结果一致
```

### Phase 2: 批量生成拓扑配置

```python
# 为 12 个拓扑生成链路参数配置文件
topologies = [
    'topology_01_z1up1',
    'topology_02_z1up2',
    # ... 其他拓扑
]

for topo in topologies:
    config = generate_topology_config(topo)
    save_to_json(f"configs/{topo}_link_params.json", config)
```

### Phase 3: 集成到实验控制器

```python
# experiment_runner.py
class SAGINExperiment:
    def __init__(self):
        self.link_calc = SAGINLinkCalculator()

    def run_topology_test(self, topology_name):
        # 1. 加载拓扑
        config = load_topology_config(topology_name)

        # 2. 计算链路参数
        link_params = self.link_calc.calculate_link_params(config)

        # 3. 应用 TC 规则
        apply_tc_rules(link_params)

        # 4. 运行 PQ-NTOR 测试
        results = run_pq_ntor_test()

        # 5. 记录结果
        save_results(topology_name, results, link_params)
```

---

## ✅ 总结

### 师妹提供的模型优势

1. ✅ **物理层级准确** - 基于真实的无线通信模型
2. ✅ **参数可配置** - 发射功率、带宽、天线增益等
3. ✅ **支持 OMA/NOMA** - 可对比两种多址方式
4. ✅ **完整 Python 实现** - 直接可用的代码
5. ✅ **考虑实际因素** - LOS/NLOS、波束赋形、SIC 等

### 与 PQ-NTOR 实验的完美结合

```
速率计算模型 → 链路参数 → TC 配置 → PQ-NTOR 测试 → 性能分析
```

### 下一步行动

1. ✅ **提取代码** - 将师妹的代码整理成模块
2. ⏳ **验证模型** - 运行示例确认结果
3. ⏳ **生成配置** - 为 12 拓扑计算链路参数
4. ⏳ **集成实验** - 连接到 PQ-NTOR 测试框架
5. ⏳ **收集数据** - 运行完整实验

---

**文档版本**: v1.0
**基于**: 师妹提供的速率计算模型
**状态**: ✅ 模型理解完成，可开始实现

---

## 附录: 完整代码框架

```python
# sagin_rate_calculator.py - 完整速率计算器模块
# 将师妹提供的所有函数整合到一个类中

import numpy as np
import math
from scipy.special import jv

class SAGINRateCalculator:
    """SAGIN 网络速率计算器"""

    def __init__(self):
        # 物理常数
        self.C = 3e8

        # 频率设置
        self.FREQ_SAT = 20e9
        self.FREQ_UAV = 2.4e9
        self.FREQ_D2D = 2.4e9

        # 天线增益
        self.G_SAT_TX = 10 ** (32.0 / 10)
        self.G_UAV_RX = 10 ** (25.0 / 10)
        self.G_USER_RX = 10 ** (5.0 / 10)

        # 噪声功率谱密度
        self.N0 = 10 ** ((-174 - 30) / 10)

        # 卫星位置 (时间槽 15)
        self.sat_pos_slot15 = np.array([-118056.04, 14085.41, 813291.98])

    # ... 实现所有速率计算函数 ...

    def calculate_end_to_end_rate(self, path):
        """
        计算多跳路径的端到端速率

        参数:
            path: 路径节点列表，如 [sat, uav, user]

        返回:
            end_to_end_rate: 瓶颈速率 (Mbps)
            hop_rates: 每一跳的速率列表
        """
        hop_rates = []
        for i in range(len(path) - 1):
            rate = self.calculate_single_hop(path[i], path[i+1])
            hop_rates.append(rate)

        return min(hop_rates), hop_rates

# 使用示例
if __name__ == "__main__":
    calc = SAGINRateCalculator()

    # 定义网络拓扑
    sat = {'type': 'satellite', 'pos': calc.sat_pos_slot15}
    uav = {'type': 'uav', 'pos': np.array([3e3, 2e3, 1e3])}
    user = {'type': 'user', 'pos': np.array([5e3, 0, 0])}

    # 计算端到端速率
    path = [sat, uav, user]
    end_rate, hop_rates = calc.calculate_end_to_end_rate(path)

    print(f"端到端速率: {end_rate:.3f} Mbps")
    print(f"各跳速率: {hop_rates}")
```
