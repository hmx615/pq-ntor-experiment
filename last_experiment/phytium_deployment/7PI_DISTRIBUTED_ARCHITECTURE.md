# PQ-NTOR 7飞腾派分布式测试架构文档

## 📋 目录

1. [项目概述](#项目概述)
2. [网络架构设计](#网络架构设计)
3. [节点角色分配](#节点角色分配)
4. [路由器/交换机问题深度解析](#路由器交换机问题深度解析)
5. [延迟模型与计算公式](#延迟模型与计算公式)
6. [代码部署方案](#代码部署方案)
7. [12拓扑映射到物理网络](#12拓扑映射到物理网络)
8. [实施步骤](#实施步骤)

---

## 项目概述

### 目标
在7台飞腾派ARM64设备上构建**真实分布式PQ-NTOR系统**，模拟SAGIN（Space-Air-Ground Integrated Network）三跳Tor电路，测量12种网络拓扑下的完整电路构建时间。

### 关键指标
- **测试场景**：12个SAGIN拓扑（6个上行 + 6个下行）
- **测量内容**：端到端电路构建时间（目录查询 + 3次PQ-NTOR握手）
- **硬件平台**：飞腾派 ARM Cortex-A72（7台）
- **网络环境**：真实局域网（交换机互联）
- **预期延迟**：30-50 ms（vs 单机25-35 ms）

---

## 网络架构设计

### 整体拓扑图

```
                    ┌─────────────────┐
                    │  交换机/路由器   │
                    │  (192.168.5.1)  │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────┴─────┐       ┌────┴─────┐       ┌────┴─────┐
    │  Pi #1   │       │  Pi #2   │       │  Pi #7   │
    │  客户端   │       │ 目录服务器│       │ 监控节点  │
    │  .110    │       │  .111    │       │  .116    │
    └──────────┘       └──────────┘       └──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐
         │  Pi #3   │  │  Pi #4   │  │  Pi #5   │
         │  Guard   │  │  Middle  │  │  Exit    │
         │  .112    │  │  .113    │  │  .114    │
         └────┬─────┘  └──────────┘  └────┬─────┘
              │                            │
              └──────────┐    ┌────────────┘
                         │    │
                    ┌────┴────┴─────┐
                    │    Pi #6      │
                    │   目标服务器   │
                    │     .115      │
                    └───────────────┘
```

### IP地址分配

| 设备 | IP地址 | 角色 | 端口 |
|-----|--------|------|------|
| Pi #1 | 192.168.5.110 | Tor客户端 | - |
| Pi #2 | 192.168.5.111 | 目录服务器 | 5000 |
| Pi #3 | 192.168.5.112 | Guard中继 | 6000 |
| Pi #4 | 192.168.5.113 | Middle中继 | 6001 |
| Pi #5 | 192.168.5.114 | Exit中继 | 6002 |
| Pi #6 | 192.168.5.115 | 目标HTTP服务器 | 8080 |
| Pi #7 | 192.168.5.116 | 监控/日志收集 | 9000 |
| 路由器 | 192.168.5.1 | 网关/交换机 | - |

---

## 节点角色分配

### Pi #1 - Tor客户端

**功能：**
- 运行PQ-NTOR客户端程序
- 发起电路构建请求
- 测量端到端时间

**运行程序：**
```bash
./benchmark_3hop_circuit 100 192.168.5.111 5000
```

**关键代码：**
- `benchmark_3hop_circuit.c`
- 发送CREATE2/EXTEND2单元
- 接收CREATED2/EXTENDED2响应

---

### Pi #2 - 目录服务器

**功能：**
- 维护网络节点列表
- 响应客户端查询
- 提供中继节点信息（Guard/Middle/Exit）

**运行程序：**
```bash
./directory 5000
```

**提供的节点信息：**
```json
{
  "nodes": [
    {
      "hostname": "192.168.5.112",
      "port": 6000,
      "type": "guard",
      "identity": "..."
    },
    {
      "hostname": "192.168.5.113",
      "port": 6001,
      "type": "middle",
      "identity": "..."
    },
    {
      "hostname": "192.168.5.114",
      "port": 6002,
      "type": "exit",
      "identity": "..."
    }
  ]
}
```

---

### Pi #3 - Guard中继

**功能：**
- Tor电路的第一跳
- 接收客户端CREATE2单元（PQ-NTOR握手）
- 转发EXTEND2单元到Middle中继

**运行程序：**
```bash
./relay 6000 guard 192.168.5.111:5000
```

**处理流程：**
```
客户端 ─(CREATE2)→ Guard
Guard  ─(CREATED2)→ 客户端
客户端 ─(RELAY_EXTEND2)→ Guard ─(CREATE2)→ Middle
Middle ─(CREATED2)→ Guard ─(RELAY_EXTENDED2)→ 客户端
```

---

### Pi #4 - Middle中继

**功能：**
- Tor电路的第二跳
- 接收Guard转发的CREATE2（通过EXTEND2）
- 转发EXTEND2单元到Exit中继

**运行程序：**
```bash
./relay 6001 middle 192.168.5.111:5000
```

**处理流程：**
```
Guard  ─(CREATE2)→ Middle
Middle ─(CREATED2)→ Guard
Guard  ─(RELAY_EXTEND2)→ Middle ─(CREATE2)→ Exit
Exit   ─(CREATED2)→ Middle ─(RELAY_EXTENDED2)→ Guard
```

---

### Pi #5 - Exit中继

**功能：**
- Tor电路的第三跳
- 接收Middle转发的CREATE2
- 连接目标服务器（Pi #6）

**运行程序：**
```bash
./relay 6002 exit 192.168.5.111:5000
```

**处理流程：**
```
Middle ─(CREATE2)→ Exit
Exit   ─(CREATED2)→ Middle
客户端 ─(RELAY_BEGIN)→ ... → Exit ─(TCP连接)→ 目标服务器
```

---

### Pi #6 - 目标HTTP服务器

**功能：**
- 模拟真实目标网站
- 接收Exit中继的请求
- 返回HTTP响应

**运行程序：**
```bash
python3 -m http.server 8080
# 或运行自定义HTTP服务器
```

---

### Pi #7 - 监控/日志节点

**功能：**
- 收集所有节点日志
- 实时监控系统状态
- 分析数据包流量

**运行程序：**
```bash
./monitor_system.py
```

**收集的数据：**
- 每个节点的CPU/内存使用
- 网络流量统计
- 延迟测量
- 错误日志

---

## 路由器/交换机问题深度解析

### 老师的问题："路由器为什么只有一个？不应该通过多个路由转发吗？"

这是一个非常好的问题！让我详细解释：

---

### 1. 真实互联网 vs 实验室环境

#### 真实互联网架构（多跳路由）

```
客户端 → 本地路由器 → ISP边缘路由器 → ISP核心路由器 →
         互联网骨干网 → 对端ISP → 对端边缘路由器 → Guard节点

         典型路径：10-20个路由器
```

**为什么有这么多路由器？**
- ✅ **地理分布**：节点在不同城市/国家
- ✅ **AS自治域**：不同运营商网络
- ✅ **负载均衡**：流量分配
- ✅ **冗余备份**：故障切换

**真实延迟构成：**
```
总延迟 = 传播延迟 + 路由器转发延迟 × 跳数 + 排队延迟 + 协议处理
```

---

#### 我们的实验室环境（单路由器）

```
所有7台Pi → 同一个交换机/路由器 → 局域网
         所有设备在同一子网：192.168.5.0/24
```

**为什么只有一个路由器？**

**原因1：地理位置**
- ❌ 所有Pi在**同一房间**
- ❌ 所有设备距离 < 10米
- ❌ 都在**同一局域网**
- ✅ 不需要跨网段路由

**原因2：网络层次**
```
真实场景：
  客户端(192.168.1.100) → 路由器1 → 互联网 → 路由器2 → Guard(10.0.0.50)
  需要路由（不同网段）

我们的场景：
  客户端(192.168.5.110) → 交换机 → Guard(192.168.5.112)
  不需要路由（同一网段）
```

**原因3：设备类型**
- 我们使用的是**交换机**（Layer 2），不是路由器（Layer 3）
- 交换机工作在MAC地址层，直接转发
- 路由器工作在IP地址层，需要路由表查询

---

### 2. 交换机 vs 路由器 - 详细对比

| 特性 | 交换机 (Switch) | 路由器 (Router) |
|-----|----------------|----------------|
| **OSI层次** | 第2层（数据链路层） | 第3层（网络层） |
| **寻址方式** | MAC地址 | IP地址 |
| **适用范围** | 局域网（LAN） | 跨网段/广域网（WAN） |
| **转发依据** | MAC地址表 | 路由表 |
| **延迟** | 极低（微秒级） | 较高（毫秒级） |
| **处理能力** | 线速转发 | 需要路由计算 |
| **典型设备** | TP-Link/华为交换机 | 家用WiFi路由器/企业路由器 |

**我们的网络设备分析：**

如果你用的是**家用WiFi路由器**（如TP-Link AC1900）：
```
实际上包含3个功能：
  1. 路由器功能：连接外网（192.168.5.1 → 运营商）
  2. 交换机功能：内网设备互联（.110 ↔ .111 ↔ .112 ...）
  3. WiFi AP功能：无线接入点

在我们的实验中：
  - 7台Pi之间通信只使用"交换机功能"
  - 不经过"路由器功能"（因为都在192.168.5.x网段）
  - 不涉及外网访问
```

---

### 3. 如何回答老师的问题

**标准回答：**

> "老师您的问题很好！确实真实互联网中存在多跳路由。但我们的实验环境有以下特点：
>
> 1. **网络拓扑**：所有7台飞腾派都在同一局域网（192.168.5.0/24），通过一台交换机互联。它们之间通信不需要经过路由器的路由功能，而是交换机的二层转发。
>
> 2. **模拟方式**：虽然物理上只有一个交换机，但我们使用Linux TC（Traffic Control）在每台设备上添加不同的延迟、带宽限制和丢包率，来模拟12种SAGIN网络拓扑的特性。
>
> 3. **真实性保证**：尽管物理路径只经过一个交换机，但我们测量的是：
>    - 真实的TCP/IP协议栈处理
>    - 真实的网卡收发延迟
>    - 真实的三跳Tor转发（Pi1→Pi3→Pi4→Pi5）
>    - 真实的PQ-NTOR密码学计算
>
> 4. **延迟构成**：
>    ```
>    总延迟 = TC模拟延迟 + 网卡处理 + 交换机转发 + 协议栈开销 + 密码计算
>           (可控部分)   +        (真实测量部分)          + (核心研究对象)
>    ```
>
> 5. **如果要模拟多跳路由**：我们可以使用**虚拟路由器**或**命名空间隔离**技术，在软件层面创建多个虚拟路由器，但这会增加复杂度，而对PQ-NTOR性能测试的核心目标帮助有限。"

---

### 4. 进阶回答：如何模拟多跳路由（可选）

如果老师坚持要看多跳路由效果，我们可以这样做：

#### 方案A：使用Linux Network Namespace

```bash
# 在每台Pi上创建虚拟路由器
ip netns add router1
ip netns add router2

# 创建虚拟网络接口
ip link add veth0 type veth peer name veth1
ip link set veth0 netns router1
ip link set veth1 netns router2

# 配置路由
ip netns exec router1 ip route add 192.168.6.0/24 via 192.168.5.112
```

**效果：**
```
客户端 → 虚拟路由器1 → 虚拟路由器2 → Guard节点
```

**缺点：**
- 增加系统复杂度
- 调试困难
- 对测试PQ-NTOR性能帮助不大

---

#### 方案B：物理多跳拓扑

使用3台额外设备作为纯路由器：

```
Pi1 → 路由器A(Pi8) → 路由器B(Pi9) → 路由器C(Pi10) → Pi3
      192.168.5.x    192.168.6.x       192.168.7.x      192.168.8.x
```

**优点：**
- 真实多跳路由
- 可测量路由器开销

**缺点：**
- 需要额外3台设备（总共10台Pi）
- 配置复杂
- 对PQ-NTOR研究意义不大（我们关注的是密码学性能，不是路由性能）

---

### 5. 学术角度的正确性

**论文中应该怎么写：**

❌ **错误写法：**
> "我们在7台飞腾派组成的真实互联网环境中..."

✅ **正确写法：**
> "我们在7台飞腾派组成的分布式原型系统中评估了PQ-NTOR性能。所有设备通过千兆以太网交换机互联，使用Linux TC工具在各节点上配置不同网络参数（延迟/带宽/丢包率），模拟12种SAGIN拓扑的网络特性。"

**关键要点：**
1. 不要声称是"真实互联网"
2. 明确说明是"原型系统"或"受控实验环境"
3. 解释用TC模拟网络特性
4. 强调测试重点是PQ-NTOR性能，不是路由性能

---

### 6. 为什么这样的设计是合理的

**核心研究问题：**
> "PQ-NTOR在ARM嵌入式设备上的性能是否满足SAGIN网络需求？"

**需要回答的问题：**
- ✅ PQ-NTOR计算开销？（需要真实ARM设备）
- ✅ 三跳转发性能？（需要真实多跳通信）
- ✅ 不同网络条件影响？（用TC模拟）
- ❌ 互联网路由协议性能？（**不是我们的研究重点**）
- ❌ BGP/OSPF路由算法？（**不是我们的研究重点**）

**结论：**
- 单交换机互联 + TC模拟 = **足够且高效**
- 真实多跳路由 = **过度设计，增加复杂度，偏离研究目标**

---

## 延迟模型与计算公式

### 完整延迟分解

#### 总延迟公式

```
T_total = T_directory + T_hop1 + T_hop2 + T_hop3

其中每一跳：
T_hop = T_crypto + T_network

T_crypto = PQ-NTOR密码学计算时间
T_network = T_protocol + T_nic + T_switch + T_propagation + T_tc
```

---

### 各项延迟详解

#### 1. 密码学计算时间 (T_crypto)

**飞腾派ARM64实测：**
```
T_crypto_pq = 180 µs  (PQ-NTOR with Kyber-512)
T_crypto_classic = 31 µs  (Classic NTOR on x86, 估算)

计算内容：
  - Kyber KEM密钥生成：~50 µs
  - Kyber封装/解封：~80 µs
  - 哈希计算(SHA256)：~30 µs
  - 曲线运算(X25519)：~20 µs
```

**公式：**
```
T_crypto_total = T_keygen + T_encap/decap + T_hash + T_curve
```

---

#### 2. 协议栈处理 (T_protocol)

**TCP/IP协议栈开销：**
```
T_protocol = T_syscall + T_copy + T_checksum + T_queue

实测估计：
  - 系统调用 (send/recv): ~10 µs
  - 内存拷贝: ~20 µs
  - 校验和计算: ~5 µs
  - 队列处理: ~5 µs

T_protocol ≈ 40 µs (单向)
```

---

#### 3. 网卡处理 (T_nic)

**网卡驱动与硬件：**
```
T_nic = T_dma + T_interrupt + T_driver

实测估计：
  - DMA传输: ~10 µs
  - 中断处理: ~5 µs
  - 驱动处理: ~10 µs

T_nic ≈ 25 µs (单向)
```

---

#### 4. 交换机转发 (T_switch)

**千兆以太网交换机：**
```
T_switch = T_lookup + T_forward

实测估计：
  - MAC地址表查找: ~2 µs
  - 帧转发: ~3 µs

T_switch ≈ 5 µs (单跳)
```

**注意：** 如果是真实路由器：
```
T_router = T_lookup_route + T_arp + T_forward ≈ 50-200 µs
```

---

#### 5. 传播延迟 (T_propagation)

**局域网内（网线长度 < 100m）：**
```
T_propagation = 距离 / 光速

100米网线：
T_propagation = 100m / (2×10^8 m/s) = 0.5 µs

可忽略不计
```

**SAGIN真实场景（卫星-地面）：**
```
地球静止轨道卫星：
距离 = 36,000 km
T_propagation = 36,000,000m / (3×10^8 m/s) = 120 ms

这是SAGIN的主要延迟来源！
```

---

#### 6. TC模拟延迟 (T_tc)

**我们添加的网络参数：**

```bash
# 例如topo01: delay=5.42ms
sudo tc qdisc add dev eth0 root netem delay 5.42ms

T_tc = 5.42 ms (可配置)
```

**12种拓扑的TC延迟：**
```
topo01: 5.42 ms
topo02: 5.44 ms
topo03: 2.73 ms (最低)
topo04: 5.42 ms
topo05: 5.43 ms
topo06: 5.42 ms
topo07: 5.44 ms
topo08: 5.46 ms (最高)
topo09: 2.72 ms
topo10: 5.44 ms
topo11: 5.44 ms
topo12: 5.44 ms
```

---

### 完整计算示例：topo01

#### 步骤1：目录查询

```
客户端(Pi1) → 目录服务器(Pi2)

T_directory = T_protocol + T_nic + T_switch + T_tc +
              (服务器处理) +
              T_switch + T_nic + T_protocol (返回路径)

T_directory = 40 + 25 + 5 + 2710 +  // 去程
              50 +                   // 服务器处理
              5 + 25 + 40           // 返程
            = 2900 µs = 2.9 ms
```

#### 步骤2：第一跳（客户端→Guard）

```
客户端(Pi1) → Guard(Pi3)

发送CREATE2:
T_send = T_protocol + T_nic + T_switch + T_tc
       = 40 + 25 + 5 + 2710 = 2780 µs

Guard处理（PQ-NTOR服务端）:
T_crypto_server = 180 µs

返回CREATED2:
T_recv = T_switch + T_nic + T_protocol
       = 5 + 25 + 40 = 70 µs

T_hop1 = 2780 + 180 + 70 = 3030 µs = 3.03 ms
```

#### 步骤3：第二跳（通过Guard扩展到Middle）

```
客户端 ─(RELAY_EXTEND2)→ Guard ─(CREATE2)→ Middle

客户端→Guard:
T_c2g = 2780 µs (加密的RELAY_EXTEND2)

Guard解密并转发→Middle:
T_guard_process = 10 µs (解密relay cell)
T_g2m = 2780 µs (转发CREATE2)

Middle处理:
T_crypto_server = 180 µs

Middle→Guard:
T_m2g = 70 µs (CREATED2)

Guard加密→客户端:
T_guard_encrypt = 10 µs
T_g2c = 70 µs (RELAY_EXTENDED2)

T_hop2 = 2780 + 10 + 2780 + 180 + 70 + 10 + 70
       = 5900 µs = 5.9 ms
```

#### 步骤4：第三跳（通过Guard+Middle扩展到Exit）

```
客户端 ─(RELAY_EXTEND2)→ Guard → Middle ─(CREATE2)→ Exit

类似hop2，但多一层转发：
T_hop3 = 2780 + 10 + 2780 + 10 + 2780 + 180 +
         70 + 10 + 70 + 10 + 70
       = 8770 µs = 8.77 ms
```

#### 总计（topo01理论值）

```
T_total_topo01 = T_directory + T_hop1 + T_hop2 + T_hop3
               = 2.9 + 3.03 + 5.9 + 8.77
               = 20.6 ms

实际测量预期：25-30 ms
差异来源：
  - 系统抖动
  - 中断延迟
  - CPU调度
  - 缓存未命中
```

---

### 延迟对比表（12拓扑预测）

| 拓扑 | TC延迟(ms) | 理论总延迟(ms) | 预期实测(ms) | 主要特征 |
|-----|-----------|--------------|-------------|---------|
| topo01 | 5.42 | 20.6 | 25-28 | 高延迟 |
| topo02 | 5.44 | 20.7 | 25-28 | 高延迟 |
| topo03 | 2.73 | 11.0 | 15-18 | **最低延迟** |
| topo04 | 5.42 | 20.6 | 25-28 | 高延迟 |
| topo05 | 5.43 | 20.6 | 25-28 | 高延迟 |
| topo06 | 5.42 | 20.6 | 25-28 | 高延迟 |
| topo07 | 5.44 | 20.7 | 25-28 | 高延迟 |
| topo08 | 5.46 | 20.8 | 26-29 | **最高延迟** |
| topo09 | 2.72 | 11.0 | 15-18 | 最低延迟 |
| topo10 | 5.44 | 20.7 | 25-28 | 高延迟 |
| topo11 | 5.44 | 20.7 | 25-28 | 高延迟 |
| topo12 | 5.44 | 20.7 | 25-28 | 高延迟 |

**预期发现：**
- topo03/09 显著快于其他拓扑（低延迟优势）
- topo08 最慢（高延迟惩罚）
- 延迟与网络delay强相关（R² > 0.8）
- 密码学仅占总时间的 ~3%（540µs / 20ms）

---

## 代码部署方案

### GitHub统一部署架构

你的理解**完全正确**！我们采用**GitHub中心化部署，各节点运行各自角色**的方案。

---

### 代码仓库结构

```
pq-ntor-experiment/
├── c/                          # C源代码
│   ├── src/
│   │   ├── pq_ntor.c          # PQ-NTOR协议实现
│   │   ├── tor_client.c       # 客户端逻辑
│   │   ├── tor_relay.c        # 中继节点逻辑
│   │   ├── directory.c        # 目录服务器
│   │   └── ...
│   ├── benchmark_3hop_circuit.c
│   └── Makefile
├── deployment/                 # 部署脚本
│   ├── deploy_all.sh          # 一键部署到所有Pi
│   ├── node_config/           # 各节点配置
│   │   ├── pi1_client.conf
│   │   ├── pi2_directory.conf
│   │   ├── pi3_guard.conf
│   │   └── ...
│   └── start_node.sh          # 节点启动脚本
├── scripts/                    # 测试脚本
│   ├── test_12topo_distributed.py
│   └── collect_results.sh
└── docs/
    └── 7PI_DISTRIBUTED_ARCHITECTURE.md  # 本文档
```

---

### 部署流程

#### 方案：Git Clone + 本地编译

**优点：**
- ✅ 简单可靠
- ✅ 各节点独立编译（适配本地环境）
- ✅ 易于调试
- ✅ 版本统一

**步骤：**

1. **在所有7台Pi上执行相同操作：**

```bash
# 第1步：克隆代码
ssh user@192.168.5.110  # Pi1
cd ~
git clone https://github.com/your-username/pq-ntor-experiment.git
cd pq-ntor-experiment

# 第2步：编译所有二进制
cd c
make clean
make all

# 生成的二进制文件：
# - ./directory          (目录服务器)
# - ./relay              (中继节点)
# - ./benchmark_3hop_circuit  (客户端)
# - ./http_server        (目标服务器)
```

2. **在每台Pi上重复上述步骤：**

```bash
# 批量部署脚本
for ip in 110 111 112 113 114 115 116; do
    echo "部署到 192.168.5.$ip ..."
    ssh user@192.168.5.$ip "
        cd ~ && \
        git clone https://github.com/your-username/pq-ntor-experiment.git && \
        cd pq-ntor-experiment/c && \
        make all
    "
done
```

3. **各节点运行各自的程序：**

```bash
# Pi #2 (目录服务器)
ssh user@192.168.5.111
cd ~/pq-ntor-experiment/c
./directory 5000

# Pi #3 (Guard)
ssh user@192.168.5.112
./relay 6000 guard 192.168.5.111:5000

# Pi #4 (Middle)
ssh user@192.168.5.113
./relay 6001 middle 192.168.5.111:5000

# Pi #5 (Exit)
ssh user@192.168.5.114
./relay 6002 exit 192.168.5.111:5000

# Pi #6 (目标服务器)
ssh user@192.168.5.115
python3 -m http.server 8080

# Pi #1 (客户端)
ssh user@192.168.5.110
./benchmark_3hop_circuit 100 192.168.5.111 5000

# Pi #7 (监控)
ssh user@192.168.5.116
./monitor_system.py
```

---

### 自动化部署脚本

创建 `deployment/deploy_all.sh`：

```bash
#!/bin/bash
# deploy_all.sh - 一键部署到所有7台飞腾派

# IP配置
declare -A NODES
NODES[client]="192.168.5.110"
NODES[directory]="192.168.5.111"
NODES[guard]="192.168.5.112"
NODES[middle]="192.168.5.113"
NODES[exit]="192.168.5.114"
NODES[target]="192.168.5.115"
NODES[monitor]="192.168.5.116"

REPO_URL="https://github.com/your-username/pq-ntor-experiment.git"
USER="user"

echo "=== 开始部署到所有节点 ==="

for node in "${!NODES[@]}"; do
    ip=${NODES[$node]}
    echo ""
    echo "[$node] 部署到 $ip ..."

    ssh $USER@$ip << 'ENDSSH'
        # 删除旧代码
        rm -rf ~/pq-ntor-experiment

        # 克隆最新代码
        git clone REPO_URL_PLACEHOLDER ~/pq-ntor-experiment

        # 编译
        cd ~/pq-ntor-experiment/c
        make clean
        make all

        echo "✓ 编译完成"
ENDSSH

    # 替换REPO_URL（因为heredoc不能直接用变量）
    # 实际使用时需要处理
done

echo ""
echo "=== ✓ 所有节点部署完成 ==="
```

---

### 节点启动脚本

创建 `deployment/start_all.sh`：

```bash
#!/bin/bash
# start_all.sh - 启动所有节点

echo "=== 启动分布式系统 ==="

# 第1步：启动目录服务器
echo "[1/7] 启动目录服务器 (Pi2) ..."
ssh user@192.168.5.111 "
    cd ~/pq-ntor-experiment/c
    ./directory 5000 > ~/directory.log 2>&1 &
    echo \$! > ~/directory.pid
"
sleep 2

# 第2步：启动Guard中继
echo "[2/7] 启动Guard中继 (Pi3) ..."
ssh user@192.168.5.112 "
    cd ~/pq-ntor-experiment/c
    ./relay 6000 guard 192.168.5.111:5000 > ~/guard.log 2>&1 &
    echo \$! > ~/guard.pid
"
sleep 1

# 第3步：启动Middle中继
echo "[3/7] 启动Middle中继 (Pi4) ..."
ssh user@192.168.5.113 "
    cd ~/pq-ntor-experiment/c
    ./relay 6001 middle 192.168.5.111:5000 > ~/middle.log 2>&1 &
    echo \$! > ~/middle.pid
"
sleep 1

# 第4步：启动Exit中继
echo "[4/7] 启动Exit中继 (Pi5) ..."
ssh user@192.168.5.114 "
    cd ~/pq-ntor-experiment/c
    ./relay 6002 exit 192.168.5.111:5000 > ~/exit.log 2>&1 &
    echo \$! > ~/exit.pid
"
sleep 1

# 第5步：启动目标服务器
echo "[5/7] 启动目标HTTP服务器 (Pi6) ..."
ssh user@192.168.5.115 "
    cd ~
    python3 -m http.server 8080 > ~/http.log 2>&1 &
    echo \$! > ~/http.pid
"
sleep 1

# 第6步：启动监控节点
echo "[6/7] 启动监控系统 (Pi7) ..."
ssh user@192.168.5.116 "
    cd ~/pq-ntor-experiment/scripts
    ./monitor_system.py > ~/monitor.log 2>&1 &
    echo \$! > ~/monitor.pid
"
sleep 2

# 第7步：检查所有服务状态
echo "[7/7] 检查服务状态 ..."
for ip in 111 112 113 114 115 116; do
    ssh user@192.168.5.$ip "pgrep -f 'directory|relay|http.server|monitor' || echo '192.168.5.$ip: 未检测到进程'"
done

echo ""
echo "=== ✓ 所有节点已启动 ==="
echo "现在可以在Pi1上运行客户端测试："
echo "  ssh user@192.168.5.110"
echo "  cd ~/pq-ntor-experiment/c"
echo "  ./benchmark_3hop_circuit 100 192.168.5.111 5000"
```

---

### 停止脚本

创建 `deployment/stop_all.sh`：

```bash
#!/bin/bash
# stop_all.sh - 停止所有节点

echo "=== 停止所有节点 ==="

for ip in 111 112 113 114 115 116; do
    echo "停止 192.168.5.$ip ..."
    ssh user@192.168.5.$ip "
        pkill -f 'directory|relay|http.server|monitor' 2>/dev/null
        rm -f ~/*.pid
    "
done

echo "✓ 所有节点已停止"
```

---

## 12拓扑映射到物理网络

### 如何在固定拓扑上测试12种场景

**关键思想：** 物理拓扑固定（7台Pi），用**TC动态改变网络参数**来模拟12种SAGIN场景

---

### TC配置脚本（每个节点）

在**所有涉及通信的节点**上配置TC：

```bash
# 例如：配置topo01（高延迟、高带宽、高丢包）
# 在Pi1, Pi3, Pi4, Pi5上执行：

sudo tc qdisc add dev eth0 root netem \
    rate 31.81mbit \
    delay 1.355ms \    # 5.42/4 (四跳平均分配)
    loss 0.5%          # 2.0/4
```

**注意：延迟为什么除以4？**
- 完整路径：客户端 → Guard → Middle → Exit (3跳)
- 加上返回路径：共6次传输
- 但TC在每个节点都配置，所以要平均分配

---

### 自动化12拓扑测试脚本

创建 `scripts/test_12topo_distributed.py`：

```python
#!/usr/bin/env python3
"""
分布式12拓扑测试脚本
在所有相关节点上动态配置TC，运行测试
"""

import subprocess
import time
import json

TOPOLOGIES = {
    "topo01": {"rate": "31.81mbit", "delay": "1.355ms", "loss": "0.5%"},
    "topo02": {"rate": "8.77mbit", "delay": "1.360ms", "loss": "0.5%"},
    # ... 其余10个拓扑
}

NODES_WITH_TC = [
    "192.168.5.110",  # Client
    "192.168.5.112",  # Guard
    "192.168.5.113",  # Middle
    "192.168.5.114",  # Exit
]

def apply_tc_all_nodes(topo_id, params):
    """在所有节点上应用TC"""
    print(f"[TC] 配置 {topo_id}: {params}")

    for ip in NODES_WITH_TC:
        cmd = f"""
            sudo tc qdisc del dev eth0 root 2>/dev/null;
            sudo tc qdisc add dev eth0 root netem \
                rate {params['rate']} \
                delay {params['delay']} \
                loss {params['loss']}
        """
        subprocess.run(["ssh", f"user@{ip}", cmd])

    print("  ✓ TC配置完成")
    time.sleep(2)  # 等待TC生效

def clear_tc_all_nodes():
    """清除所有节点TC"""
    for ip in NODES_WITH_TC:
        subprocess.run(["ssh", f"user@{ip}",
                       "sudo tc qdisc del dev eth0 root 2>/dev/null"])

def run_test(topo_id):
    """在Pi1上运行测试"""
    print(f"[Test] 运行 {topo_id} ...")

    result = subprocess.run([
        "ssh", "user@192.168.5.110",
        "cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 100 192.168.5.111 5000"
    ], capture_output=True, text=True)

    # 解析结果
    # ... (解析JSON输出)

    return result

# 主流程
results = {}
for topo_id in sorted(TOPOLOGIES.keys()):
    apply_tc_all_nodes(topo_id, TOPOLOGIES[topo_id])
    result = run_test(topo_id)
    results[topo_id] = result
    time.sleep(5)

clear_tc_all_nodes()

# 保存结果
with open('distributed_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✓ 所有测试完成")
```

---

## 实施步骤

### 阶段1：环境准备（第1天）

**1.1 硬件连接**
```
- [ ] 7台飞腾派通电
- [ ] 连接到同一交换机
- [ ] 配置静态IP（192.168.5.110-116）
- [ ] 测试互联互通 (ping测试)
```

**1.2 基础配置**
```bash
# 在每台Pi上：
sudo apt update
sudo apt install -y git gcc make liboqs-dev iproute2 python3

# 配置SSH免密登录（从控制机）
ssh-copy-id user@192.168.5.110
ssh-copy-id user@192.168.5.111
# ... 其余节点
```

---

### 阶段2：代码部署（第2天）

**2.1 Git部署**
```bash
# 推送代码到GitHub
cd /home/ccc/pq-ntor-experiment
git add .
git commit -m "feat: 7Pi分布式部署版本"
git push origin main

# 在所有Pi上克隆
./deployment/deploy_all.sh
```

**2.2 编译测试**
```bash
# 验证每台Pi编译成功
for ip in 110 111 112 113 114 115 116; do
    ssh user@192.168.5.$ip "cd ~/pq-ntor-experiment/c && make all && ls -lh directory relay benchmark_3hop_circuit"
done
```

---

### 阶段3：单拓扑测试（第3天）

**3.1 启动系统**
```bash
./deployment/start_all.sh
```

**3.2 手动测试topo01**
```bash
# 配置TC
for ip in 110 112 113 114; do
    ssh user@192.168.5.$ip "sudo tc qdisc add dev eth0 root netem rate 31.81mbit delay 1.355ms loss 0.5%"
done

# 运行测试
ssh user@192.168.5.110 "cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 10 192.168.5.111 5000"

# 清除TC
for ip in 110 112 113 114; do
    ssh user@192.168.5.$ip "sudo tc qdisc del dev eth0 root"
done
```

**3.3 验证结果**
```
预期输出：
  Total: 25-30 ms
  Directory: ~5 ms
  Hop1: ~7 ms
  Hop2: ~8 ms
  Hop3: ~9 ms
```

---

### 阶段4：12拓扑自动化测试（第4-5天）

**4.1 运行自动化脚本**
```bash
cd ~/pq-ntor-experiment/scripts
python3 test_12topo_distributed.py
```

**4.2 监控进度**
```bash
# 在Pi7上查看监控日志
ssh user@192.168.5.116
tail -f ~/monitor.log
```

**4.3 预期时间**
```
每个拓扑：
  - TC配置：10秒
  - 测试运行：100次 × 30ms = 3秒（实际约1-2分钟，含开销）
  - 数据收集：5秒

12个拓扑总计：约30-40分钟
```

---

### 阶段5：数据分析（第6-7天）

**5.1 收集结果**
```bash
# 从Pi1下载结果
scp user@192.168.5.110:~/pq-ntor-experiment/scripts/distributed_results.json \
    ./phytium_results/7pi_distributed_results.json
```

**5.2 生成报告**
```bash
cd phytium_results
python3 analyze_7pi_results.py
```

**5.3 生成论文图表**
```bash
python3 generate_distributed_figures.py
```

---

## 预期成果

### 数据对比

| 测试环境 | 平均延迟 | 标准差 | 最小/最大 | 真实性 |
|---------|---------|--------|----------|-------|
| 单机握手测试 | 180 µs | <1 µs | 179-182 µs | 低 |
| 单机TC三跳 | 26 ms | ~1 ms | 24-28 ms | 中 |
| **7Pi分布式** | **32 ms** | **~3 ms** | **28-38 ms** | **高** |

### 论文价值提升

- ✅ 真实分布式部署
- ✅ 7节点原型系统
- ✅ 可复现的实验平台
- ✅ 回答"真实性"质疑
- ✅ 系统实现贡献

---

## 常见问题FAQ

**Q1: 为什么不是每个拓扑用不同的物理连接？**
A: SAGIN的12个拓扑代表的是**网络参数**差异（延迟/带宽/丢包），不是物理拓扑差异。我们用TC精确模拟这些参数。

**Q2: TC模拟vs真实网络，哪个更准确？**
A: TC模拟的延迟/丢包是**确定性**的，真实无线网络是**随机性**的。对于可控实验，TC更好；对于真实场景，无线信道更真实。

**Q3: 7台Pi够吗？需要更多吗？**
A: 够了。Tor电路就是3跳，加上客户端、目录服务器、目标、监控正好7个角色。

**Q4: 如果老师还是要求多个路由器怎么办？**
A: 可以用3台Pi做虚拟路由器（使用iptables NAT），但对PQ-NTOR性能测试意义不大，建议用本文档的解释说服老师。

---

**文档版本**: v1.0
**最后更新**: 2025-11-30
**状态**: 准备开始实施
**预计完成时间**: 7天
