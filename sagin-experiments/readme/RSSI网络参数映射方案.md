# RSSI到网络参数映射方案

**创建时间**: 2025-11-14
**项目**: PQ-Tor SAGIN NOMA演示系统
**目的**: 定义RSSI等级到实际网络参数的映射规则

---

## 📊 映射表

### 主映射方案

| RSSI等级 | 延迟(RTT) | 带宽 | 丢包率 | 抖动 | 适用链路 |
|----------|-----------|------|--------|------|---------|
| **高RSSI(空/地)** | 5ms | 100Mbps | 0.1% | 1ms | 无人机↔地面 |
| **低RSSI(空/地)** | 15ms | 50Mbps | 1% | 3ms | 无人机↔地面(远) |
| **高RSSI(天基上行)** | 10ms | 50Mbps | 0.5% | 2ms | 地面/空中→卫星 |
| **低RSSI(天基上行)** | 30ms | 20Mbps | 2% | 5ms | 地面/空中→卫星(远) |
| **高RSSI(天基下行)** | 10ms | 100Mbps | 0.5% | 2ms | 卫星→地面/空中 |
| **低RSSI(天基下行)** | 30ms | 50Mbps | 2% | 5ms | 卫星→地面/空中(远) |
| **卫星链路(无标注)** | 8ms | 200Mbps | 0.1% | 1ms | 卫星↔卫星/无人机 |
| **协作链路(无标注)** | 5ms | 100Mbps | 0.1% | 1ms | NOMA组内协作 |

---

## 🔧 Linux TC命令映射

### 延迟配置 (netem)

```bash
# 高RSSI空/地 (5ms延迟 + 1ms抖动)
tc qdisc add dev eth0 root netem delay 5ms 1ms

# 低RSSI空/地 (15ms延迟 + 3ms抖动)
tc qdisc add dev eth0 root netem delay 15ms 3ms

# 高RSSI天基上行 (10ms延迟 + 2ms抖动)
tc qdisc add dev eth0 root netem delay 10ms 2ms

# 低RSSI天基上行 (30ms延迟 + 5ms抖动)
tc qdisc add dev eth0 root netem delay 30ms 5ms
```

### 带宽限制 (tbf)

```bash
# 100Mbps
tc qdisc add dev eth0 root tbf rate 100mbit burst 32kbit latency 400ms

# 50Mbps
tc qdisc add dev eth0 root tbf rate 50mbit burst 16kbit latency 400ms

# 20Mbps
tc qdisc add dev eth0 root tbf rate 20mbit burst 8kbit latency 400ms
```

### 丢包配置 (netem)

```bash
# 0.1%丢包
tc qdisc add dev eth0 root netem loss 0.1%

# 0.5%丢包
tc qdisc add dev eth0 root netem loss 0.5%

# 1%丢包
tc qdisc add dev eth0 root netem loss 1%

# 2%丢包
tc qdisc add dev eth0 root netem loss 2%
```

### 综合配置示例

```bash
# 低RSSI空/地链路完整配置
tc qdisc add dev eth0 root handle 1: htb default 10
tc class add dev eth0 parent 1: classid 1:10 htb rate 50mbit
tc qdisc add dev eth0 parent 1:10 handle 10: netem delay 15ms 3ms loss 1%
```

---

## 📝 飞腾派简化方案 (无TC支持)

### 方案说明

由于飞腾派内核不支持TC模块，我们使用**应用层延迟模拟**：

1. **延迟**: 在Python脚本中使用 `time.sleep()` 模拟
2. **带宽**: 记录但不限制（演示用途）
3. **丢包**: 在应用层随机丢弃数据包
4. **抖动**: 延迟时间加随机抖动

### Python实现示例

```python
import time
import random

class LinkSimulator:
    def __init__(self, rssi_type):
        self.params = RSSI_PARAMS[rssi_type]

    def simulate_delay(self):
        """模拟延迟+抖动"""
        base_delay = self.params['delay_ms'] / 1000.0
        jitter = random.gauss(0, self.params['jitter_ms'] / 1000.0)
        total_delay = max(0, base_delay + jitter)
        time.sleep(total_delay)

    def should_drop_packet(self):
        """模拟丢包"""
        return random.random() < (self.params['loss_rate'] / 100.0)

# 使用示例
link = LinkSimulator('low_rssi_air_ground')
link.simulate_delay()  # 模拟15ms±3ms延迟
if link.should_drop_packet():
    print("数据包丢失")
```

---

## 🎯 配置文件格式

### JSON配置示例

```json
{
  "link_types": {
    "high_rssi_air_ground": {
      "delay_ms": 5,
      "jitter_ms": 1,
      "bandwidth_mbps": 100,
      "loss_rate": 0.1,
      "description": "高RSSI空/地链路"
    },
    "low_rssi_air_ground": {
      "delay_ms": 15,
      "jitter_ms": 3,
      "bandwidth_mbps": 50,
      "loss_rate": 1.0,
      "description": "低RSSI空/地链路"
    },
    "high_rssi_sat_uplink": {
      "delay_ms": 10,
      "jitter_ms": 2,
      "bandwidth_mbps": 50,
      "loss_rate": 0.5,
      "description": "高RSSI天基上行"
    },
    "low_rssi_sat_uplink": {
      "delay_ms": 30,
      "jitter_ms": 5,
      "bandwidth_mbps": 20,
      "loss_rate": 2.0,
      "description": "低RSSI天基上行"
    },
    "high_rssi_sat_downlink": {
      "delay_ms": 10,
      "jitter_ms": 2,
      "bandwidth_mbps": 100,
      "loss_rate": 0.5,
      "description": "高RSSI天基下行"
    },
    "low_rssi_sat_downlink": {
      "delay_ms": 30,
      "jitter_ms": 5,
      "bandwidth_mbps": 50,
      "loss_rate": 2.0,
      "description": "低RSSI天基下行"
    },
    "satellite_link": {
      "delay_ms": 8,
      "jitter_ms": 1,
      "bandwidth_mbps": 200,
      "loss_rate": 0.1,
      "description": "卫星链路(无标注)"
    },
    "cooperation_link": {
      "delay_ms": 5,
      "jitter_ms": 1,
      "bandwidth_mbps": 100,
      "loss_rate": 0.1,
      "description": "协作链路(无标注)"
    }
  }
}
```

---

## 📋 链路类型代码映射

### 代码常量定义

```python
# RSSI链路类型常量
LINK_HIGH_RSSI_AG = "high_rssi_air_ground"
LINK_LOW_RSSI_AG = "low_rssi_air_ground"
LINK_HIGH_RSSI_SAT_UP = "high_rssi_sat_uplink"
LINK_LOW_RSSI_SAT_UP = "low_rssi_sat_uplink"
LINK_HIGH_RSSI_SAT_DOWN = "high_rssi_sat_downlink"
LINK_LOW_RSSI_SAT_DOWN = "low_rssi_sat_downlink"
LINK_SATELLITE = "satellite_link"
LINK_COOPERATION = "cooperation_link"

# RSSI参数字典
RSSI_PARAMS = {
    LINK_HIGH_RSSI_AG: {
        "delay_ms": 5,
        "jitter_ms": 1,
        "bandwidth_mbps": 100,
        "loss_rate": 0.1
    },
    LINK_LOW_RSSI_AG: {
        "delay_ms": 15,
        "jitter_ms": 3,
        "bandwidth_mbps": 50,
        "loss_rate": 1.0
    },
    # ... 其他链路类型
}
```

---

## 🔍 性能影响分析

### 对PQ-Tor握手的影响

| 链路类型 | 单跳延迟 | 3跳总延迟 | PQ-Ntor握手时间 | 总计 |
|----------|----------|-----------|----------------|------|
| **最优** (高RSSI空/地) | 5ms | 15ms | 0.049ms | ~15ms |
| **较好** (高RSSI天基) | 10ms | 30ms | 0.049ms | ~30ms |
| **一般** (低RSSI空/地) | 15ms | 45ms | 0.049ms | ~45ms |
| **较差** (低RSSI天基) | 30ms | 90ms | 0.049ms | ~90ms |

**结论**: 网络延迟远大于握手计算时间(49μs)，延迟是主要瓶颈

### 带宽影响

| 链路类型 | 带宽 | CREATE2大小 | 传输时间 |
|----------|------|-------------|---------|
| **卫星链路** | 200Mbps | 820B | 0.033ms |
| **高RSSI天基** | 100Mbps | 820B | 0.066ms |
| **低RSSI天基** | 50Mbps | 820B | 0.131ms |
| **最低带宽** | 20Mbps | 820B | 0.328ms |

**结论**: 即使最低带宽，传输时间也远小于延迟

---

## 🎨 可视化展示映射

### 链路颜色编码

```python
LINK_COLORS = {
    "high_rssi_air_ground": "#00ff00",      # 绿色 - 优秀
    "low_rssi_air_ground": "#ffff00",       # 黄色 - 良好
    "high_rssi_sat_uplink": "#00ccff",      # 青色 - 较好
    "low_rssi_sat_uplink": "#ff9900",       # 橙色 - 一般
    "high_rssi_sat_downlink": "#00ccff",    # 青色 - 较好
    "low_rssi_sat_downlink": "#ff9900",     # 橙色 - 一般
    "satellite_link": "#0099ff",            # 蓝色 - 优秀
    "cooperation_link": "#ff00ff"           # 紫色 - 协作
}
```

### 链路粗细映射

```python
LINK_WIDTH = {
    "high_rssi": 3,      # 粗线
    "low_rssi": 1,       # 细线
    "satellite": 4,      # 最粗
    "cooperation": 2     # 中等(虚线)
}
```

---

## 📖 使用示例

### 场景1: 拓扑1 (Z1 Up)

```python
# S2地面终端 → 卫星 (低RSSI天基上行)
s2_to_sat = {
    "source": "S2_ground",
    "destination": "SAT",
    "link_type": LINK_LOW_RSSI_SAT_UP,
    "delay_ms": 30,
    "bandwidth_mbps": 20,
    "loss_rate": 2.0
}

# S1无人机 → 卫星 (高RSSI天基上行)
s1_to_sat = {
    "source": "S1_aircraft",
    "destination": "SAT",
    "link_type": LINK_HIGH_RSSI_SAT_UP,
    "delay_ms": 10,
    "bandwidth_mbps": 50,
    "loss_rate": 0.5
}
```

### 场景2: 拓扑7 (Z1 Down)

```python
# 卫星 → S1无人机 (高RSSI天基下行)
sat_to_s1 = {
    "source": "SAT",
    "destination": "S1_aircraft",
    "link_type": LINK_HIGH_RSSI_SAT_DOWN,
    "delay_ms": 10,
    "bandwidth_mbps": 100,
    "loss_rate": 0.5
}

# 卫星 → S2地面 (低RSSI天基下行)
sat_to_s2 = {
    "source": "SAT",
    "destination": "S2_ground",
    "link_type": LINK_LOW_RSSI_SAT_DOWN,
    "delay_ms": 30,
    "bandwidth_mbps": 50,
    "loss_rate": 2.0
}

# S1无人机 → S2地面 (协作链路，单向)
s1_to_s2_coop = {
    "source": "S1_aircraft",
    "destination": "S2_ground",
    "link_type": LINK_COOPERATION,
    "delay_ms": 5,
    "bandwidth_mbps": 100,
    "loss_rate": 0.1
}
```

---

## ✅ 验证清单

- [ ] 所有8种链路类型都有明确参数定义
- [ ] 参数取值符合真实卫星网络特征
- [ ] 高/低RSSI差异明显(至少3倍)
- [ ] 延迟、带宽、丢包率相互匹配
- [ ] 可在飞腾派上实现(应用层模拟)
- [ ] 配置文件格式统一
- [ ] 可视化映射清晰

---

## 📚 参考依据

### 真实卫星网络参数
- **LEO卫星**: RTT 20-40ms, 带宽50-200Mbps
- **MEO卫星**: RTT 100-150ms, 带宽10-50Mbps
- **GEO卫星**: RTT 500-600ms, 带宽1-10Mbps
- **无人机链路**: RTT 5-20ms, 带宽50-150Mbps

### NOMA典型场景
- **近端用户**: 信道条件好，高RSSI，低功率
- **远端用户**: 信道条件差，低RSSI，高功率
- **RSSI差值**: 通常10-20dB (对应3-10倍延迟/带宽差)

---

**文档状态**: ✅ 完成
**下一步**: 生成12个拓扑的配置文件
**相关文档**: `12种NOMA网络拓扑定义.md`
