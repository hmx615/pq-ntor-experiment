# 7飞腾派物理SAGIN展示系统 - 代码需求分析

## 1. 系统架构概述

### 硬件配置
- **7个飞腾派**: 每个代表一个SAGIN节点（物理设备，非Docker容器）
- **7个显示器**: 每个显示器连接一个飞腾派，显示该节点状态
- **1个架子**: 物理承载，可能象征网络拓扑布局
- **网络设备**: 交换机/路由器连接7个飞腾派

### 节点角色分配

| 飞腾派编号 | 节点角色 | 网络类型 | IP地址（建议） | 功能 |
|-----------|---------|---------|---------------|------|
| **Pi-1** | Sat-1 (卫星1) | 卫星层 | 192.168.100.11 | Guard节点，PQ-NTOR入口 |
| **Pi-2** | Sat-2 (卫星2) | 卫星层 | 192.168.100.12 | ISL通信，中继 |
| **Pi-3** | Aircraft-1 (飞行器1) | 空中层 | 192.168.100.21 | Middle节点，链路中转 |
| **Pi-4** | Aircraft-2 (飞行器2) | 空中层 | 192.168.100.22 | 备用中继 |
| **Pi-5** | GS-Beijing (北京地面站) | 地面层 | 192.168.100.31 | 客户端，发起连接 |
| **Pi-6** | GS-London (伦敦地面站) | 地面层 | 192.168.100.32 | Exit节点，出口 |
| **Pi-7** | GS-NewYork (纽约地面站) | 地面层 | 192.168.100.33 | 目录服务器 |

### 网络拓扑逻辑

```
        [Sat-1 (Pi-1)]  ←→  [Sat-2 (Pi-2)]       (ISL: 星间链路)
             ↕                    ↕
             ↕                    ↕
    [Aircraft-1 (Pi-3)]  ←→  [Aircraft-2 (Pi-4)]  (空中层)
             ↕                    ↕
             ↕                    ↕
      [GS-Beijing]        [GS-London]        [GS-NewYork]
         (Pi-5)              (Pi-6)             (Pi-7)
```

---

## 2. 核心代码需求分析

### 2.1 网络层代码需求

#### ✅ 已有代码（可复用）

**位置**: `scripts/network_topology_manager_simple.py`

**功能**:
- iptables链路控制（启用/禁用链路）
- 节点IP映射

**需要修改**:
```python
# 原版：容器映射
self.node_containers = {
    'Sat-1': 'sagin_sat-1',  # Docker容器名
    'Sat-2': 'sagin_sat-2'
}

# 新版：物理设备SSH映射
self.node_connections = {
    'Sat-1': {'ip': '192.168.100.11', 'ssh_port': 22},
    'Sat-2': {'ip': '192.168.100.12', 'ssh_port': 22}
}
```

**需要新增**:
```python
class PhysicalNetworkManager:
    """物理飞腾派网络管理器"""

    def __init__(self, config_file, ssh_credentials):
        self.nodes = {}  # 节点SSH连接池
        self.credentials = ssh_credentials  # SSH认证信息

    def connect_to_node(self, node_name):
        """建立到物理节点的SSH连接"""
        # 使用paramiko连接到远程飞腾派
        pass

    def enable_link(self, source, destination):
        """启用物理链路"""
        # SSH到source节点，执行iptables命令
        ssh_client = self.nodes[source]
        ssh_client.exec_command(
            f'sudo iptables -D OUTPUT -d {dest_ip} -j DROP'
        )

    def disable_link(self, source, destination):
        """禁用物理链路"""
        # SSH到source节点，阻断到destination的流量
        pass

    def set_link_delay(self, source, destination, delay_ms):
        """设置链路延迟（软件层模拟）"""
        # 由于物理网络延迟很小，需要在应用层模拟
        # 方法1: 在relay程序中sleep
        # 方法2: 使用tc netem（如果内核支持）
        pass
```

#### ❌ 缺少的代码

1. **SSH多节点管理器**
   - 需求：同时管理7个飞腾派的SSH连接
   - 文件：`scripts/physical_node_manager.py`（需新建）
   - 功能：
     - 批量SSH连接
     - 命令分发执行
     - 状态收集汇总

2. **物理网络拓扑控制器**
   - 需求：控制7个飞腾派之间的路由/防火墙
   - 文件：`scripts/physical_topology_controller.py`（需新建）
   - 功能：
     - 动态修改路由表
     - iptables规则管理
     - 链路启用/禁用

3. **延迟模拟模块**（如果TC不可用）
   - 需求：在应用层模拟卫星链路延迟
   - 位置：修改 `c/src/relay_node.c`
   - 实现：在转发cell前sleep指定时间

---

### 2.2 PQ-NTOR应用层代码需求

#### ✅ 已有代码（可复用）

**位置**: `/home/ccc/pq-ntor-experiment/c/src/`

| 文件 | 功能 | 是否需要修改 |
|------|------|-------------|
| `relay_node.c` | 中继节点（Sat、Aircraft） | ✅ 需要修改 |
| `client.c` | 客户端（GS-Beijing） | ⚠️ 可能需要修改 |
| `directory_server.c` | 目录服务（GS-NewYork） | ✅ 需要修改 |
| `benchmark.c` | 性能测试 | ⚠️ 可选 |
| `pq_ntor.c` | 核心加密协议 | ✅ 不需要修改 |

#### 需要修改的代码

**1. `directory_server.c` - 节点列表**

```c
// 当前版本（硬编码容器IP）
static node_info_t nodes[] = {
    {
        .hostname = "172.20.1.11",  // Docker容器IP
        .port = 9001,
        .type = NODE_TYPE_GUARD,
        // ...
    }
};

// 需要改为物理IP
static node_info_t nodes[] = {
    {
        .hostname = "192.168.100.11",  // 飞腾派Pi-1 (Sat-1)
        .port = 9001,
        .type = NODE_TYPE_GUARD,
        .identity = "Sat-1",
        // ...
    },
    {
        .hostname = "192.168.100.21",  // 飞腾派Pi-3 (Aircraft-1)
        .port = 9003,
        .type = NODE_TYPE_MIDDLE,
        .identity = "Aircraft-1",
        // ...
    },
    {
        .hostname = "192.168.100.32",  // 飞腾派Pi-6 (GS-London)
        .port = 9005,
        .type = NODE_TYPE_EXIT,
        .identity = "GS-London",
        // ...
    }
};
```

**2. `relay_node.c` - 延迟模拟（可选）**

```c
// 在转发cell时添加延迟模拟
int relay_process_cell(relay_context_t *ctx, cell_t *cell) {
    // 根据源节点和目标节点，查询应该的延迟
    int delay_ms = get_link_delay(ctx->source_node, ctx->dest_node);

    if (delay_ms > 0) {
        usleep(delay_ms * 1000);  // 模拟链路延迟
    }

    // 原有转发逻辑
    // ...
}

// 延迟配置表（根据节点类型）
typedef struct {
    const char *from_type;  // "satellite", "aircraft", "ground"
    const char *to_type;
    int delay_ms;
} link_delay_config_t;

static link_delay_config_t delay_table[] = {
    {"satellite", "satellite", 10},   // ISL: 10ms
    {"satellite", "ground", 5},       // SG: 5ms
    {"satellite", "aircraft", 7},     // SA: 7ms
    {"aircraft", "ground", 3},        // AG: 3ms
};
```

**3. 节点启动配置文件**

每个飞腾派需要知道自己的角色：

```bash
# 文件: /home/user/node_config.sh （在每个飞腾派上）
export NODE_NAME="Sat-1"
export NODE_TYPE="satellite"
export NODE_IP="192.168.100.11"
export RELAY_PORT=9001
export DIRECTORY_IP="192.168.100.33"  # GS-NewYork
```

#### ❌ 缺少的代码

1. **节点自动配置脚本**
   - 需求：每个飞腾派启动时自动配置角色
   - 文件：`scripts/node_init.sh`（需新建）
   - 功能：
     - 读取节点配置
     - 启动对应的服务（relay/client/directory）
     - 配置网络路由

2. **分布式日志收集**
   - 需求：将7个节点的日志汇总到一处
   - 文件：`scripts/log_collector.py`（需新建）
   - 功能：
     - SSH收集各节点日志
     - 时间戳同步
     - 统一格式输出

---

### 2.3 可视化展示代码需求

#### 目标效果

每个显示器显示该节点的实时状态：

```
┌──────────────────────────────────────┐
│    SAGIN节点: Sat-1 (卫星1)          │
├──────────────────────────────────────┤
│ 状态: 运行中                         │
│ IP: 192.168.100.11                   │
│ 角色: Guard (入口节点)               │
├──────────────────────────────────────┤
│ 活动链路:                            │
│  ✓ Sat-1 → Sat-2       (ISL, 10ms)  │
│  ✓ Sat-1 → Aircraft-1  (SA, 7ms)    │
│  ✗ Sat-1 → GS-Beijing  (已断开)     │
├──────────────────────────────────────┤
│ PQ-NTOR统计:                         │
│  CREATE2接收: 15                     │
│  CREATED2发送: 15                    │
│  EXTEND2转发: 8                      │
│  平均握手时间: 49μs                  │
├──────────────────────────────────────┤
│ 系统资源:                            │
│  CPU: 15%  内存: 512MB  网络: 2MB/s  │
└──────────────────────────────────────┘
```

#### ✅ 可复用的技术栈

1. **Python + curses/blessed** (终端UI)
   - 优点：轻量，SSH直接显示
   - 适合：黑客风格的终端界面

2. **Python + PyQt5/Tkinter** (图形界面)
   - 优点：美观，支持图表
   - 适合：正式展示

3. **Web界面 (Flask/FastAPI + HTML/JS)**
   - 优点：跨平台，支持远程访问
   - 适合：可能需要在其他设备上监控

#### ❌ 缺少的代码

**1. 节点状态监控程序**

```python
# 文件: scripts/node_monitor.py （需新建）
class NodeMonitor:
    """单节点状态监控"""

    def __init__(self, node_name, node_config):
        self.node_name = node_name
        self.config = node_config

    def get_link_status(self):
        """获取链路状态"""
        # 检查iptables规则，判断哪些链路启用
        # 检查路由表，判断路由是否可达
        return {
            'Sat-1 -> Sat-2': {'enabled': True, 'latency_ms': 10},
            'Sat-1 -> Aircraft-1': {'enabled': True, 'latency_ms': 7},
            'Sat-1 -> GS-Beijing': {'enabled': False}
        }

    def get_pq_stats(self):
        """获取PQ-NTOR统计"""
        # 解析relay日志，统计握手次数
        # 或者修改relay_node.c，输出统计信息到共享内存
        return {
            'create2_received': 15,
            'created2_sent': 15,
            'extend2_forwarded': 8,
            'avg_handshake_us': 49
        }

    def get_system_stats(self):
        """获取系统资源"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'network_mbps': psutil.net_io_counters().bytes_sent / 1024 / 1024
        }
```

**2. 可视化界面程序**

```python
# 文件: scripts/node_display.py （需新建）
import curses
from node_monitor import NodeMonitor

class NodeDisplay:
    """节点状态可视化显示"""

    def __init__(self, node_name):
        self.monitor = NodeMonitor(node_name, load_config())

    def render_terminal_ui(self, stdscr):
        """终端UI渲染（使用curses）"""
        while True:
            stdscr.clear()

            # 标题
            stdscr.addstr(0, 0, f"SAGIN节点: {self.monitor.node_name}", curses.A_BOLD)

            # 链路状态
            links = self.monitor.get_link_status()
            y = 3
            for link, status in links.items():
                symbol = "✓" if status['enabled'] else "✗"
                stdscr.addstr(y, 2, f"{symbol} {link} ({status['latency_ms']}ms)")
                y += 1

            # PQ统计
            stats = self.monitor.get_pq_stats()
            y += 1
            stdscr.addstr(y, 0, "PQ-NTOR统计:", curses.A_UNDERLINE)
            stdscr.addstr(y+1, 2, f"CREATE2接收: {stats['create2_received']}")
            stdscr.addstr(y+2, 2, f"平均握手: {stats['avg_handshake_us']}μs")

            # 系统资源
            sys_stats = self.monitor.get_system_stats()
            y += 4
            stdscr.addstr(y, 0, "系统资源:", curses.A_UNDERLINE)
            stdscr.addstr(y+1, 2, f"CPU: {sys_stats['cpu_percent']:.1f}%")

            stdscr.refresh()
            time.sleep(1)

if __name__ == '__main__':
    import sys
    node_name = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    display = NodeDisplay(node_name)
    curses.wrapper(display.render_terminal_ui)
```

**3. 中央控制台（可选）**

```python
# 文件: scripts/central_dashboard.py （需新建）
class CentralDashboard:
    """7节点统一监控界面"""

    def __init__(self):
        self.nodes = {
            'Sat-1': NodeMonitor('Sat-1', ...),
            'Sat-2': NodeMonitor('Sat-2', ...),
            # ... 7个节点
        }

    def render_network_topology(self):
        """渲染整个网络拓扑图"""
        # 使用ASCII art或图形库绘制网络拓扑
        # 显示所有7个节点的连接关系
        # 高亮显示活跃链路
        pass

    def show_overall_stats(self):
        """显示整体统计"""
        total_handshakes = sum(
            node.get_pq_stats()['create2_received']
            for node in self.nodes.values()
        )
        print(f"网络总握手次数: {total_handshakes}")
```

---

### 2.4 轨道仿真与动态拓扑代码需求

#### ✅ 已有代码（可复用）

**位置**: `scripts/orbit_simulator.py`

**功能**:
- 使用Skyfield计算卫星轨道
- TLE数据解析
- 计算卫星-地面站可见性
- 计算星间距离

**可复用部分**:
```python
# 计算Sat-1和GS-Beijing之间的距离
simulator = OrbitSimulator()
distance_km = simulator.calculate_distance('Sat-1', 'GS-Beijing', time_now)

# 判断链路是否可用（仰角 > 5°）
is_visible = simulator.is_link_available('Sat-1', 'GS-Beijing', time_now)
```

#### ❌ 缺少的代码

**动态拓扑更新器**

```python
# 文件: scripts/dynamic_topology_updater.py （需新建）
class DynamicTopologyUpdater:
    """根据轨道仿真动态更新物理网络拓扑"""

    def __init__(self, orbit_sim, network_mgr):
        self.orbit_sim = orbit_sim
        self.network_mgr = network_mgr

    def update_topology_realtime(self):
        """实时更新拓扑（每秒运行）"""
        while True:
            current_time = datetime.utcnow()

            # 计算所有链路可用性
            links = [
                ('Sat-1', 'Sat-2'),      # ISL
                ('Sat-1', 'GS-Beijing'), # SG
                ('Sat-2', 'Aircraft-1'),
                # ... 所有可能的链路
            ]

            for source, dest in links:
                is_available = self.orbit_sim.is_link_available(
                    source, dest, current_time
                )

                if is_available:
                    self.network_mgr.enable_link(source, dest)
                else:
                    self.network_mgr.disable_link(source, dest)

            time.sleep(1)  # 每秒更新一次

    def calculate_link_delay(self, source, dest, current_time):
        """计算链路延迟（基于距离）"""
        distance_km = self.orbit_sim.calculate_distance(
            source, dest, current_time
        )

        # 光速延迟
        delay_ms = distance_km / 300.0  # 光速 300,000 km/s

        return delay_ms
```

---

## 3. 系统整体架构

### 3.1 软件架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    中央控制台（可选）                        │
│              central_dashboard.py (Pi-7或PC)                │
│          - 全网拓扑可视化                                    │
│          - 统计数据汇总                                      │
│          - 手动控制界面                                      │
└──────────────────┬──────────────────────────────────────────┘
                   │ SSH通信
         ┌─────────┼─────────┬─────────┬─────────┐
         │         │         │         │         │
    ┌────▼────┐┌──▼────┐┌──▼────┐┌──▼────┐┌──▼────┐...
    │ Pi-1    ││ Pi-2  ││ Pi-3  ││ Pi-4  ││ Pi-5  │
    │ Sat-1   ││ Sat-2 ││Air-1  ││Air-2  ││GS-Bei │
    └────┬────┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘
         │         │         │         │         │
    ┌────▼─────────▼─────────▼─────────▼─────────▼────┐
    │          物理局域网（交换机/路由器）              │
    │            192.168.100.0/24                      │
    └──────────────────────────────────────────────────┘
```

**每个飞腾派上运行的进程**:

```
Pi-1 (Sat-1):
├── relay_node (端口9001) - PQ-NTOR中继
├── node_monitor.py       - 状态监控
├── node_display.py       - 显示器UI
└── network_controller.py - 本地网络控制

Pi-5 (GS-Beijing):
├── client (端口随机)     - PQ-NTOR客户端
├── node_monitor.py
├── node_display.py
└── test_runner.py        - 自动化测试

Pi-7 (GS-NewYork):
├── directory_server (端口5000) - 目录服务
├── node_monitor.py
├── node_display.py
└── central_dashboard.py  - 中央控制台
```

### 3.2 数据流

**1. PQ-NTOR握手流程**

```
GS-Beijing (Pi-5)  →  Directory (Pi-7): 请求节点列表
                    ←  返回: [Sat-1, Aircraft-1, GS-London]

GS-Beijing         →  Sat-1 (Pi-1): CREATE2 (Kyber公钥)
                    ←  CREATED2 (加密响应)

GS-Beijing         →  Sat-1 → Aircraft-1 (Pi-3): EXTEND2
                    ←  Aircraft-1 → Sat-1: EXTENDED2

GS-Beijing         →  Sat-1 → Aircraft-1 → GS-London (Pi-6): EXTEND2
                    ←  GS-London → Aircraft-1 → Sat-1: EXTENDED2

✓ 电路建立完成
```

**2. 链路动态控制流程**

```
orbit_simulator.py (Pi-7):
  计算当前时刻卫星位置
  ↓
  判断 Sat-1 ↔ GS-Beijing 链路是否可见
  ↓
  发送控制命令到 PhysicalNetworkManager
  ↓
PhysicalNetworkManager:
  SSH到 Pi-1 (Sat-1)
  ↓
  执行: sudo iptables -A OUTPUT -d 192.168.100.31 -j DROP
  ↓
  链路断开，模拟卫星不可见
```

**3. 可视化数据收集**

```
node_monitor.py (在Pi-1上):
  读取 /var/log/relay.log
  ↓
  解析: "CREATE2 received from 192.168.100.31"
  ↓
  更新统计: create2_count += 1
  ↓
node_display.py:
  每秒刷新显示器UI
  ↓
显示器显示: "CREATE2接收: 23"
```

---

## 4. 代码清单与开发优先级

### 4.1 必须新建的代码

| 优先级 | 文件名 | 功能 | 预计代码量 |
|-------|--------|------|-----------|
| **P0** | `scripts/physical_node_manager.py` | SSH多节点管理 | 300行 |
| **P0** | `scripts/node_init.sh` | 节点启动脚本 | 100行 |
| **P0** | `c/src/directory_server.c` 修改 | 物理IP配置 | 50行修改 |
| **P1** | `scripts/node_monitor.py` | 节点状态监控 | 400行 |
| **P1** | `scripts/node_display.py` | 终端UI显示 | 500行 |
| **P2** | `scripts/dynamic_topology_updater.py` | 动态拓扑更新 | 250行 |
| **P2** | `scripts/central_dashboard.py` | 中央控制台 | 600行 |
| **P3** | `c/src/relay_node.c` 修改 | 延迟模拟（可选） | 150行修改 |

**总计**: 约2,350行新代码 + 200行修改

### 4.2 可复用的现有代码

| 文件 | 复用程度 | 需要修改 |
|------|---------|---------|
| `scripts/orbit_simulator.py` | 90% | 轻微调整参数 |
| `scripts/network_topology_manager_simple.py` | 60% | 改为SSH远程执行 |
| `c/src/pq_ntor.c` | 100% | 无需修改 |
| `c/src/relay_node.c` | 80% | 可能添加延迟模拟 |
| `c/src/client.c` | 100% | 仅需重新编译 |
| `sagin_topology_config.json` | 70% | 修改IP地址 |

---

## 5. 关键技术挑战

### 5.1 物理网络延迟模拟

**问题**: 7个飞腾派在同一局域网，实际延迟 < 1ms，但卫星链路延迟应为5-10ms

**解决方案**:

| 方案 | 优点 | 缺点 | 可行性 |
|------|------|------|--------|
| **tc netem** | 精确、内核级 | 飞腾派内核不支持 | ❌ 不可行 |
| **应用层sleep** | 简单、可控 | CPU浪费 | ✅ 可行 |
| **专用延迟设备** | 真实硬件延迟 | 成本高、需要额外设备 | ⚠️ 预算允许可考虑 |
| **不模拟延迟** | 无额外工作 | 不符合真实场景 | ⚠️ 备选 |

**推荐**: 应用层sleep（修改relay_node.c）

```c
// 在relay_node.c的转发函数中添加
int forward_cell_with_delay(cell_t *cell, const char *next_hop) {
    // 查询链路类型
    link_type_t type = get_link_type(current_node, next_hop);

    // 根据链路类型延迟
    switch (type) {
        case LINK_ISL:
            usleep(10000);  // 10ms
            break;
        case LINK_SG:
            usleep(5000);   // 5ms
            break;
        // ...
    }

    return forward_cell(cell, next_hop);
}
```

### 5.2 时间同步

**问题**: 7个飞腾派的系统时间必须同步（用于轨道仿真）

**解决方案**:

```bash
# 每个飞腾派上配置NTP
sudo apt install ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# 或使用Pi-7作为本地NTP服务器
# Pi-7上:
sudo apt install ntp
# 配置为NTP server

# Pi-1到Pi-6:
# /etc/ntp.conf
server 192.168.100.33  # Pi-7的IP
```

### 5.3 SSH连接管理

**问题**: 需要从一个节点（如Pi-7）SSH到其他6个节点

**解决方案**: 使用SSH密钥认证

```bash
# 在Pi-7上生成密钥
ssh-keygen -t rsa -b 4096

# 复制公钥到其他6个飞腾派
for i in {11..16}; do
    ssh-copy-id user@192.168.100.$i
done

# 测试免密登录
ssh user@192.168.100.11 'hostname'
```

### 5.4 进程守护与自动重启

**问题**: 如果relay崩溃，需要自动重启

**解决方案**: 使用systemd服务

```bash
# /etc/systemd/system/sagin-relay.service
[Unit]
Description=SAGIN PQ-NTOR Relay Node
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/pq-ntor
ExecStart=/home/user/pq-ntor/relay -p 9001 -i Sat-1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sagin-relay
sudo systemctl start sagin-relay
```

---

## 6. 部署流程建议

### 阶段1: 单节点功能验证（1-2天）

1. 在1个飞腾派上编译PQ-NTOR程序
2. 验证relay/client/directory可运行
3. 测试本地loopback握手

### 阶段2: 双节点通信测试（2-3天）

1. 配置Pi-1和Pi-5的网络互通
2. Pi-5(client)向Pi-1(relay)发起握手
3. 验证CREATE2/CREATED2消息传递

### 阶段3: 3节点电路建立（3-4天）

1. 添加Pi-3(Aircraft-1)作为middle
2. 测试GS-Beijing → Sat-1 → Aircraft-1电路
3. 验证EXTEND2消息转发

### 阶段4: 完整7节点部署（5-7天）

1. 部署所有7个节点
2. 配置网络拓扑管理
3. 测试完整电路：GS-Beijing → Sat-1 → Aircraft-1 → GS-London

### 阶段5: 可视化界面开发（7-10天）

1. 开发node_monitor.py
2. 开发node_display.py（终端UI）
3. 集成到每个节点

### 阶段6: 动态拓扑集成（5-7天）

1. 集成orbit_simulator.py
2. 开发dynamic_topology_updater.py
3. 测试链路动态启用/禁用

### 阶段7: 联调与展示准备（7-10天）

1. 全系统压力测试
2. 美化可视化界面
3. 准备演示脚本

**总计**: 30-45天（约1-1.5个月）

---

## 7. 成本估算

### 开发工作量

| 任务 | 人天 | 说明 |
|------|------|------|
| 网络层代码开发 | 5 | SSH管理、iptables控制 |
| 应用层代码修改 | 3 | directory/relay修改 |
| 可视化界面开发 | 10 | 监控+UI |
| 动态拓扑开发 | 5 | 轨道仿真集成 |
| 部署脚本编写 | 3 | 自动化部署 |
| 测试与调试 | 14 | 7节点联调 |
| **总计** | **40人天** | **约2个月（1人）** |

### 硬件需求确认

- ✅ 7个飞腾派（已有）
- ✅ 7个显示器（已有）
- ✅ 1个架子（已有）
- ⚠️ 1个交换机（8口千兆，约200元）
- ⚠️ 网线若干（约50元）

---

## 8. 快速启动检查清单

在开始编码前，请确认：

### 硬件准备

- [ ] 7个飞腾派已到货
- [ ] 7个显示器已连接
- [ ] 交换机/路由器已配置
- [ ] 所有设备可互相ping通

### 软件环境

- [ ] 每个飞腾派已安装Ubuntu 20.04
- [ ] 已安装gcc、make等编译工具
- [ ] 已安装Python 3.8+
- [ ] 已安装SSH服务器
- [ ] 已配置静态IP (192.168.100.11-33)

### 网络配置

- [ ] 所有飞腾派在同一子网
- [ ] 防火墙允许SSH (22)、Relay (9001-9007)、Directory (5000)
- [ ] 时间已同步（NTP）

### 代码准备

- [ ] PQ-NTOR C代码已在1个飞腾派上编译通过
- [ ] 简化版网络管理器已测试
- [ ] SSH免密登录已配置

---

## 9. 总结

### 核心代码需求

| 类别 | 已有 | 需新建 | 需修改 |
|------|------|--------|--------|
| **网络控制** | 简化版iptables管理 | SSH多节点管理器 | 改为远程执行 |
| **PQ-NTOR** | 完整协议实现 | - | directory IP列表 |
| **可视化** | - | 监控+UI全套 | - |
| **动态拓扑** | 轨道仿真器 | 实时拓扑更新器 | 集成到网络控制 |
| **部署工具** | - | 启动脚本、服务配置 | - |

### 下一步行动

1. **立即执行**: 在1个飞腾派上验证PQ-NTOR程序可运行
2. **本周完成**: 配置7个飞腾派的网络互通
3. **两周内**: 开发SSH多节点管理器和基础监控
4. **一个月内**: 完成可视化界面和动态拓扑

### 可行性结论

✅ **完全可行**，基于以下理由：

1. PQ-NTOR核心代码已完整，仅需配置调整
2. 网络控制有简化版基础，改造工作量可控
3. 可视化可采用成熟技术栈（curses/PyQt）
4. 动态拓扑有orbit_simulator基础

⚠️ **关键风险**：

1. 物理延迟模拟（建议应用层实现）
2. 7节点联调复杂度（建议分阶段测试）
3. 时间同步精度（建议本地NTP）

---

**文档版本**: v1.0
**日期**: 2025-11-14
**预计开发周期**: 1-2个月（1名开发者）
