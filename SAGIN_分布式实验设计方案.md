# SAGIN 分布式 PQ-NTOR 实验设计方案

**项目**: 后量子密码在SAGIN网络中的性能评估
**日期**: 2025-11-27
**状态**: 📋 设计阶段

---

## 📋 实验需求理解

### 当前状态
- ✅ PQ-NTOR 协议实现完成
- ✅ 本地性能测试通过 (Benchmark)
- ✅ 单机多进程测试成功

### 真实需求
**分布式SAGIN网络仿真实验**:
1. 多个物理设备（飞腾派）部署在不同位置
2. 根据老师提供的链路条件配置网络
3. 模拟真实的卫星-航空-地面网络环境
4. 测试不同信道条件下的PQ-NTOR性能

---

## 🌐 SAGIN 网络拓扑

### 三层网络架构

```
        🛰️ 卫星层 (Satellite)
           ↕️ (高延迟, 低带宽)
        ✈️ 航空层 (Aerial - UAV/Aircraft)
           ↕️ (中延迟, 中带宽)
        🏢 地面层 (Ground Station)
           ↕️ (低延迟, 高带宽)
        👤 用户终端 (User)
```

### 12拓扑配置示例

每个拓扑代表不同的网络场景：
- **Z1-UP1**: Zone 1, 上行链路配置1
- **Z1-UP2**: Zone 1, 上行链路配置2
- **Z2**: Zone 2 配置
- ...

---

## 📊 链路参数配置需求

### 需要从老师获取的数据

#### 1. 信道质量参数 (RSSI-based)

```yaml
高RSSI信道:
  RSSI范围: -50 ~ -30 dBm
  最高传输速率: ??? Mbps
  平均延迟: ??? ms
  丢包率: ??? %

中RSSI信道:
  RSSI范围: -70 ~ -50 dBm
  最高传输速率: ??? Mbps
  平均延迟: ??? ms
  丢包率: ??? %
低RSSI信道:
  RSSI范围: -90 ~ -70 dBm
  最高传输速率: ??? Mbps
  平均延迟: ??? ms
  丢包率: ??? %
```

#### 2. NOMA (非正交多址接入) 参数

```yaml
协作NOMA信道:
  用户数: ???
  功率分配系数: [α1, α2, ..., αn]
  干扰消除能力: ??? dB
  总带宽: ??? MHz
  每用户速率: ??? Mbps

单用户OMA对比:
  带宽分配: ??? MHz
  传输速率: ??? Mbps
```

#### 3. 各层链路特性

```yaml
卫星链路 (Sat-to-Air):
  传播延迟: ??? ms (典型 250-500ms)
  带宽: ??? Mbps
  误码率: ???

航空链路 (Air-to-Ground):
  传播延迟: ??? ms (典型 10-50ms)
  带宽: ??? Mbps
  多普勒效应: ??? Hz

地面链路 (Ground-to-Ground):
  传播延迟: ??? ms (< 10ms)
  带宽: ??? Mbps
  干扰情况: ???
```

---

## 🎯 实验目标

### 核心研究问题

1. **PQ-NTOR 在不同信道质量下的性能**
   - 高/中/低 RSSI 对握手延迟的影响
   - 链路质量对加密性能的影响

2. **NOMA 技术对 PQ-NTOR 的影响**
   - 协作 NOMA vs 传统 OMA
   - 多用户场景下的性能对比

3. **SAGIN 多跳延迟分析**
   - 端到端延迟组成分析
   - 各层链路对总延迟的贡献

4. **可靠性评估**
   - 不同链路条件下的握手成功率
   - 丢包/重传对 PQ-NTOR 的影响

---

## 🏗️ 实验架构设计

### 方案 A: 完全物理部署 (理想方案)

#### 所需设备
```
最少配置:
- 1 × 飞腾派 (卫星节点)
- 2 × 飞腾派 (航空节点)
- 2 × 飞腾派 (地面站)
- 1 × 飞腾派 或 PC (客户端)
- 1 × 中心服务器 (目录服务器)

理想配置:
- 6+ × 飞腾派 (模拟完整SAGIN网络)
- 网络模拟器 (用于控制链路参数)
```

#### 物理连接方式

**选项 1: 真实无线链路**
```
飞腾派 ↔️ WiFi/蓝牙 ↔️ 飞腾派
优点: 真实信道条件
缺点: 难以精确控制参数
```

**选项 2: 有线 + Linux 流量控制 (推荐)**
```
飞腾派 ↔️ 以太网交换机 ↔️ 飞腾派
       ↑ 使用 tc (traffic control) 模拟链路
优点: 参数可控，可重复
缺点: 需要配置 tc 规则
```

#### 网络拓扑示例 (3层5节点)

```
┌─────────────────────────────────────────────┐
│            中心控制 & Directory              │
│         192.168.1.1 (PC/服务器)             │
└────────────────┬────────────────────────────┘
                 │ 交换机
        ┌────────┼────────┐
        │        │        │
    [Sat-1]  [Air-1]  [GS-1]
      :11      :21      :31
        │        │        │
        └────┬───┴───┬────┘
           [Air-2] [GS-2]
             :22     :32
```

---

### 方案 B: 混合仿真 (实用方案)

**核心设备物理部署 + 链路模拟**

#### 架构
```
┌─────────────────────────────────────────────┐
│  网络仿真器 (NetEm / Mininet)               │
│  - 控制延迟、带宽、丢包                      │
│  - 动态调整 RSSI 对应的链路参数             │
└─────────────────────────────────────────────┘
                    ↕️
┌─────────────────────────────────────────────┐
│  2-3 个飞腾派物理节点                        │
│  - 部署真实 PQ-NTOR 程序                    │
│  - 测量实际计算开销                          │
└─────────────────────────────────────────────┘
                    ↕️
┌─────────────────────────────────────────────┐
│  虚拟节点 (Docker/VM)                        │
│  - 补充拓扑节点数量                          │
│  - 降低硬件成本                              │
└─────────────────────────────────────────────┘
```

---

### 方案 C: 纯软件仿真 (快速验证)

**全部在单台PC/服务器上运行**

#### 优点
- ✅ 快速部署和测试
- ✅ 易于调试
- ✅ 参数完全可控

#### 缺点
- ❌ 无法反映真实硬件性能
- ❌ CPU/内存共享影响结果
- ❌ 说服力相对较弱

#### 适用场景
- 算法验证
- 参数调优
- 初步实验

---

## 🛠️ 技术实现方案

### 1. Linux Traffic Control (tc) 配置链路

#### 配置延迟和带宽

```bash
# 卫星链路: 300ms 延迟, 10Mbps 带宽, 1% 丢包
sudo tc qdisc add dev eth0 root netem delay 300ms rate 10mbit loss 1%

# 航空链路: 50ms 延迟, 50Mbps 带宽
sudo tc qdisc add dev eth0 root netem delay 50ms rate 50mbit

# 地面链路: 10ms 延迟, 100Mbps 带宽
sudo tc qdisc add dev eth0 root netem delay 10ms rate 100mbit
```

#### 模拟 RSSI 变化

```bash
# 高RSSI: 5ms延迟, 100Mbps, 0.1%丢包
sudo tc qdisc add dev eth0 root netem delay 5ms rate 100mbit loss 0.1%

# 中RSSI: 20ms延迟, 50Mbps, 1%丢包
sudo tc qdisc change dev eth0 root netem delay 20ms rate 50mbit loss 1%

# 低RSSI: 100ms延迟, 10Mbps, 5%丢包
sudo tc qdisc change dev eth0 root netem delay 100ms rate 10mbit loss 5%
```

#### 动态调整脚本

```python
# simulate_rssi.py
import subprocess
import time

rssi_profiles = {
    'high': {'delay': '5ms', 'rate': '100mbit', 'loss': '0.1%'},
    'medium': {'delay': '20ms', 'rate': '50mbit', 'loss': '1%'},
    'low': {'delay': '100ms', 'rate': '10mbit', 'loss': '5%'}
}

def apply_profile(interface, profile_name):
    profile = rssi_profiles[profile_name]
    cmd = f"sudo tc qdisc change dev {interface} root netem " \
          f"delay {profile['delay']} rate {profile['rate']} loss {profile['loss']}"
    subprocess.run(cmd, shell=True)
    print(f"Applied {profile_name} RSSI profile to {interface}")

# 模拟 RSSI 变化
for _ in range(10):
    apply_profile('eth0', 'high')
    time.sleep(30)
    apply_profile('eth0', 'medium')
    time.sleep(30)
    apply_profile('eth0', 'low')
    time.sleep(30)
```

---

### 2. NOMA 模拟方案

#### 方案 1: 应用层模拟 (推荐)

**在程序中添加 NOMA 仿真模块**:

```c
// noma_simulator.c
typedef struct {
    int user_id;
    double power_coefficient;  // 功率分配系数
    double sinr;               // 信干噪比
    double achievable_rate;    // 可达速率
} noma_user_t;

// 计算 NOMA 用户的可达速率
double calculate_noma_rate(noma_user_t *users, int num_users, double bandwidth) {
    // 根据老师提供的 NOMA 参数计算
    // ...
}

// 模拟 NOMA 传输延迟
int noma_transmit(const uint8_t *data, size_t len, noma_user_t *user) {
    double transmission_time = len * 8.0 / user->achievable_rate;
    usleep(transmission_time * 1000); // 模拟传输延迟
    return 0;
}
```

#### 方案 2: 网络层限速

```bash
# 根据 NOMA 分配的速率限制带宽
# 用户1: 20Mbps
sudo tc qdisc add dev eth0 root tbf rate 20mbit burst 32kbit latency 400ms

# 用户2: 30Mbps (协作NOMA获得更高速率)
sudo tc qdisc add dev eth1 root tbf rate 30mbit burst 32kbit latency 400ms
```

---

### 3. 实验控制系统

#### 中心化控制架构

```python
# experiment_controller.py
class SAGINExperimentController:
    def __init__(self):
        self.nodes = {}  # 节点字典
        self.topology = None  # 当前拓扑
        self.link_params = {}  # 链路参数

    def load_topology(self, topology_file):
        """加载拓扑配置"""
        with open(topology_file) as f:
            self.topology = json.load(f)

    def apply_link_params(self, link_id, params):
        """应用链路参数 (延迟/带宽/丢包)"""
        node = self.nodes[link_id]
        node.set_tc_rules(params['delay'], params['bandwidth'], params['loss'])

    def run_experiment(self, scenario):
        """运行一个实验场景"""
        # 1. 配置网络拓扑
        self.setup_topology(scenario.topology)

        # 2. 应用 RSSI/NOMA 参数
        for link in scenario.links:
            self.apply_link_params(link.id, link.params)

        # 3. 启动节点
        self.start_nodes()

        # 4. 运行测试
        results = self.run_tests(scenario.test_cases)

        # 5. 收集结果
        return self.collect_results(results)
```

---

## 📊 实验场景设计

### 场景 1: RSSI 影响分析

**目的**: 测量不同信道质量对 PQ-NTOR 性能的影响

```yaml
场景配置:
  拓扑: 简单 3-hop (Guard → Middle → Exit)

变量:
  - 信道质量: [高RSSI, 中RSSI, 低RSSI]

固定参数:
  - 节点算力: 飞腾派 (ARM64, 4核)
  - PQ算法: Kyber-512

测量指标:
  - 握手延迟 (ms)
  - 握手成功率 (%)
  - 吞吐量 (Mbps)
  - CPU使用率 (%)
```

---

### 场景 2: NOMA vs OMA 对比

**目的**: 评估协作 NOMA 对加密性能的提升

```yaml
对比组:
  组A (OMA):
    - 传统正交多址
    - 每用户独占带宽
    - 基准测试

  组B (NOMA):
    - 协作非正交多址
    - 功率域复用
    - 提升测试

测试内容:
  - 相同网络负载下的 PQ-NTOR 性能
  - 多用户并发握手
  - 资源利用效率
```

---

### 场景 3: 12拓扑完整测试

**目的**: 验证各种网络配置下的协议可靠性

```yaml
测试拓扑:
  - topology_01_z1up1.json
  - topology_02_z1up2.json
  - ...
  - topology_12.json

每个拓扑测试:
  - 100次 PQ-NTOR 握手
  - 记录成功/失败
  - 分析失败原因

统计分析:
  - 成功率分布
  - 延迟分布
  - 异常模式识别
```

---

## 📋 需要从老师获取的具体数据

### 清单模板 (发给老师)

```markdown
## SAGIN 网络仿真参数需求

尊敬的老师，

为了完成 PQ-NTOR 在 SAGIN 网络中的性能评估实验，我们需要以下网络参数：

### 1. RSSI-速率映射表

| RSSI范围 (dBm) | 最高速率 (Mbps) | 平均延迟 (ms) | 丢包率 (%) |
|----------------|----------------|---------------|------------|
| -50 ~ -30 (高)  | ?              | ?             | ?          |
| -70 ~ -50 (中)  | ?              | ?             | ?          |
| -90 ~ -70 (低)  | ?              | ?             | ?          |

### 2. NOMA 信道参数

- 用户数量: ?
- 功率分配系数: [α₁=?, α₂=?, ...]
- 总带宽: ? MHz
- 干扰消除增益: ? dB
- 每用户可达速率: ? Mbps

### 3. SAGIN 各层链路特性

| 链路类型 | 传播延迟 (ms) | 带宽 (Mbps) | 误码率 | 备注 |
|----------|--------------|-------------|--------|------|
| 卫星-航空 | ?            | ?           | ?      | LEO/GEO? |
| 航空-地面 | ?            | ?           | ?      | 高度? |
| 地面-地面 | ?            | ?           | ?      | 距离? |

### 4. 12拓扑配置

请提供各拓扑（Z1-UP1, Z1-UP2, Z2等）的具体参数配置，或者说明如何根据拓扑名称确定参数。

感谢！
```

---

## 🚀 实施步骤

### Phase 1: 参数收集 (1-2天)
- [ ] 联系老师获取链路参数
- [ ] 整理成配置文件格式
- [ ] 验证参数合理性

### Phase 2: 环境搭建 (3-5天)
- [ ] 确定使用方案 (A/B/C)
- [ ] 采购/准备设备
- [ ] 配置网络环境
- [ ] 安装 tc/NetEm 工具

### Phase 3: 程序适配 (2-3天)
- [ ] 添加链路参数读取模块
- [ ] 实现 NOMA 模拟器
- [ ] 集成 tc 控制接口
- [ ] 自动化测试脚本

### Phase 4: 实验执行 (1周)
- [ ] 场景 1: RSSI 影响分析
- [ ] 场景 2: NOMA vs OMA
- [ ] 场景 3: 12拓扑测试
- [ ] 数据收集和初步分析

### Phase 5: 数据分析 (3-5天)
- [ ] 统计分析
- [ ] 可视化图表
- [ ] 撰写实验报告
- [ ] 论文数据整理

---

## 📊 预期输出

### 实验数据
```
results/
├── scenario_1_rssi/
│   ├── high_rssi_results.csv
│   ├── medium_rssi_results.csv
│   └── low_rssi_results.csv
├── scenario_2_noma/
│   ├── oma_baseline.csv
│   └── noma_comparison.csv
└── scenario_3_12topo/
    ├── topology_01_results.csv
    ├── topology_02_results.csv
    └── ...
```

### 论文图表
- 📊 RSSI vs 握手延迟曲线图
- 📊 NOMA vs OMA 性能对比柱状图
- 📊 12拓扑成功率热力图
- 📊 端到端延迟组成饼图

### 技术报告
- 📄 实验设计文档 (本文档)
- 📄 参数配置说明
- 📄 实验执行记录
- 📄 数据分析报告

---

## 💡 关键问题和建议

### 问题 1: 设备数量有限
**建议**: 采用混合方案B，核心节点用物理设备，其他用虚拟化

### 问题 2: 参数不确定
**建议**: 先使用典型值进行预实验，后续根据老师数据调整

### 问题 3: 实验时间紧张
**建议**: 并行准备，参数获取的同时搭建环境

### 问题 4: 结果可重复性
**建议**: 所有配置脚本化，记录完整实验日志

---

## 📞 下一步行动

### 立即执行
1. ✅ **发送参数需求给老师** (使用上面的模板)
2. ⏳ **确定实验方案** (A/B/C哪个？)
3. ⏳ **盘点现有资源** (几个飞腾派？网络设备？)

### 等待老师回复期间
- 搭建本地测试环境 (方案C)
- 编写参数配置框架
- 准备自动化脚本

---

**文档版本**: v1.0
**创建日期**: 2025-11-27
**状态**: ✅ 就绪，等待参数数据

---

## 附录: 参考资料

### Linux Traffic Control 教程
- `man tc`
- `man tc-netem`
- https://wiki.linuxfoundation.org/networking/netem

### NOMA 技术参考
- 3GPP Release 15/16 NOMA specifications
- Power-domain NOMA vs Code-domain NOMA

### SAGIN 网络模型
- ITU-T SG13 SAGIN framework
- 3GPP TR 38.811 (NTN - Non-Terrestrial Networks)
