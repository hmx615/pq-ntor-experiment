# 飞腾派 TC 问题解决指南

## 问题描述

在飞腾派上配置SAGIN网络时出现错误：
```
Specified qdisc kind is unknown
```

这是因为飞腾派（ARM架构）的内核缺少Linux流量控制（TC）所需的内核模块。

## 根本原因

SAGIN网络拓扑管理器使用以下Linux TC功能来模拟网络特性：

| TC组件 | 用途 | 内核模块 |
|--------|------|----------|
| **HTB** (Hierarchical Token Bucket) | 带宽限制 | `sch_htb` |
| **netem** (Network Emulator) | 延迟/抖动/丢包模拟 | `sch_netem` |
| **u32** | IP流量分类 | `cls_u32` |
| **TBF** (Token Bucket Filter) | 流量整形 | `sch_tbf` |

飞腾派的默认内核可能没有编译或加载这些模块。

## 快速诊断

运行诊断脚本：

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments
./fix_phytium_tc.sh
```

脚本会自动检测：
- ✅ 内核模块是否可用
- ✅ tc工具是否安装
- ✅ Docker容器内tc是否可用
- ✅ 生成详细的修复建议

## 解决方案

### 方案1: 加载内核模块（推荐）

如果内核已编译模块但未加载：

```bash
# 加载必要的模块
sudo modprobe sch_htb
sudo modprobe sch_netem
sudo modprobe cls_u32
sudo modprobe sch_tbf

# 验证加载成功
lsmod | grep -E 'sch_htb|sch_netem|cls_u32'

# 设置开机自动加载
echo 'sch_htb' | sudo tee -a /etc/modules
echo 'sch_netem' | sudo tee -a /etc/modules
echo 'cls_u32' | sudo tee -a /etc/modules
echo 'sch_tbf' | sudo tee -a /etc/modules
```

### 方案2: 安装完整的iproute2工具

```bash
sudo apt update
sudo apt install -y iproute2 kmod linux-modules-extra-$(uname -r)
```

### 方案3: 检查内核配置

验证内核是否编译了TC支持：

```bash
# 查看当前内核配置
zcat /proc/config.gz | grep -E 'CONFIG_NET_SCH|CONFIG_NET_CLS'

# 或者查看模块目录
find /lib/modules/$(uname -r) -name '*sch_*' -o -name '*cls_*'
```

**需要的配置项：**
```
CONFIG_NET_SCH_HTB=m     # 或 =y
CONFIG_NET_SCH_NETEM=m   # 或 =y
CONFIG_NET_CLS_U32=m     # 或 =y
CONFIG_NET_SCH_TBF=m     # 或 =y
```

如果这些配置不存在，则需要重新编译内核或使用不同的发行版。

### 方案4: 使用简化版网络控制（备选方案）

如果无法加载TC模块，使用仅基于iptables的简化版本：

```bash
# 诊断脚本会自动生成简化版脚本
ls -lh scripts/network_topology_manager_simple.py

# 修改测试脚本使用简化版
# 将 from network_topology_manager import NetworkTopologyManager
# 改为 from network_topology_manager_simple import SimpleNetworkTopologyManager
```

**简化版的限制：**
- ✅ 可以控制链路启用/禁用（iptables）
- ❌ 无法模拟延迟和抖动（无tc netem）
- ❌ 无法限制带宽（无tc htb）

**影响：**
- 对于学术论文：如果使用混合测量-仿真方法，简化版**不影响**结果有效性（延迟已在仿真脚本中计算）
- 对于真实网络测试：需要完整TC支持

## 验证修复

### 1. 宿主机测试

```bash
# 获取网卡名称
ip addr

# 测试 netem
sudo tc qdisc add dev eth0 root netem delay 10ms
sudo tc qdisc show dev eth0
sudo tc qdisc del dev eth0 root

# 测试 HTB
sudo tc qdisc add dev eth0 root handle 1: htb default 10
sudo tc qdisc show dev eth0
sudo tc qdisc del dev eth0 root
```

### 2. Docker容器内测试

```bash
# 创建测试容器（需要 NET_ADMIN 权限）
docker run -d --name tc_test --cap-add NET_ADMIN alpine:latest sleep 300

# 在容器内测试
docker exec tc_test tc qdisc add dev eth0 root netem delay 10ms
docker exec tc_test tc qdisc show dev eth0

# 清理
docker stop tc_test
docker rm tc_test
```

### 3. SAGIN完整测试

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts

# 启动测试（dry-run模式）
python3 network_topology_manager.py ../sagin_topology_config.json --dry-run

# 如果通过，运行真实测试
python3 simulate_pq_ntor_test.py
```

## 常见问题

### Q1: modprobe 提示 "Module not found"

**原因：** 内核未编译该模块

**解决：**
1. 使用完整内核的发行版（如Ubuntu Server）
2. 重新编译内核并启用TC模块
3. 使用简化版网络控制（方案4）

### Q2: Docker容器内tc命令不工作

**原因：** 容器缺少 `NET_ADMIN` 权限

**解决：**
```bash
# 启动容器时添加权限
docker run --cap-add NET_ADMIN --privileged ...

# 检查现有容器权限
docker inspect <container_name> | grep CapAdd
```

### Q3: 在WSL2环境下开发，在飞腾派部署

**建议：**
1. WSL2开发时使用完整版网络控制（测试功能）
2. 飞腾派部署前运行 `fix_phytium_tc.sh` 诊断
3. 根据飞腾派硬件能力选择完整版或简化版
4. 学术论文使用混合仿真方法（不依赖真实TC）

### Q4: 如何判断使用完整版还是简化版？

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| **学术论文（混合仿真）** | 简化版 | 延迟已在Python中计算，无需TC |
| **真实网络测试** | 完整版 | 需要测量真实的延迟/带宽影响 |
| **开发调试** | 完整版 | 测试所有功能 |
| **飞腾派资源受限** | 简化版 | 减少内核负担 |

## 针对您当前情况的建议

### 场景分析
您目前是：
- ✅ 在飞腾派上部署SAGIN网络
- ✅ 已有完整的仿真测试结果（Phase2）
- ✅ 使用混合测量-仿真方法写论文

### 推荐方案

**立即执行：**

```bash
# 1. 运行诊断脚本
cd /home/ccc/pq-ntor-experiment/sagin-experiments
./fix_phytium_tc.sh

# 2. 根据诊断结果选择：

# 2a. 如果TC模块可用（方案1成功）
#     继续使用完整版 network_topology_manager.py

# 2b. 如果TC模块不可用
#     使用简化版 network_topology_manager_simple.py

# 3. 修改测试脚本（如果使用简化版）
# 编辑 scripts/simulate_pq_ntor_test.py
# 找到: from network_topology_manager import NetworkTopologyManager
# 改为: from network_topology_manager_simple import SimpleNetworkTopologyManager
```

### 对论文的影响

**无影响！** 原因：
1. 您使用的是混合测量-仿真方法
2. 延迟/抖动已在Python仿真脚本中计算（基于物理模型）
3. TC netem仅用于真实网络测试，而您的论文数据来自仿真
4. 简化版仍然验证了SAGIN拓扑的可行性（容器互通、链路控制）

### 下一步

```bash
# 运行诊断
./fix_phytium_tc.sh

# 根据输出决定：
# - 通过: 继续使用完整版
# - 失败: 切换到简化版（论文数据不受影响）

# 然后继续波束仿真或其他实验
```

## 技术细节

### TC在SAGIN中的作用

**代码位置：** `scripts/network_topology_manager.py:173-209`

```python
def update_link_delay(self, source, destination, delay_ms, jitter_ms, bandwidth_mbps):
    commands = [
        # 1. 创建HTB队列调度器
        ['tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'handle', '1:', 'htb', 'default', '12'],

        # 2. 创建流量类别（带宽限制）
        ['tc', 'class', 'add', 'dev', 'eth0', 'parent', '1:', 'classid', '1:1',
         'htb', 'rate', f'{bandwidth_mbps}mbit'],

        # 3. 添加流量分类器（目标IP匹配）
        ['tc', 'filter', 'add', 'dev', 'eth0', 'protocol', 'ip', 'parent', '1:0',
         'prio', '1', 'u32', 'match', 'ip', 'dst', dest_ip, 'flowid', '1:1'],

        # 4. 添加netem延迟和抖动
        ['tc', 'qdisc', 'add', 'dev', 'eth0', 'parent', '1:1', 'handle', '10:',
         'netem', 'delay', f'{delay_ms}ms', f'{jitter_ms}ms']
    ]
```

**依赖的内核模块：**
- Line 181: `htb` → 需要 `sch_htb.ko`
- Line 189: `u32` → 需要 `cls_u32.ko`
- Line 193: `netem` → 需要 `sch_netem.ko`

### 简化版的实现

**代码位置：** 自动生成于 `scripts/network_topology_manager_simple.py`

```python
def enable_link(self, source, destination):
    """仅使用 iptables 控制链路"""
    command = ['iptables', '-D', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
    # 移除DROP规则 = 启用链路

def disable_link(self, source, destination):
    """仅使用 iptables 控制链路"""
    command = ['iptables', '-A', 'OUTPUT', '-d', dest_ip, '-j', 'DROP']
    # 添加DROP规则 = 禁用链路
```

**不需要TC模块，只需要：**
- `iptables` (通常默认安装)
- Docker容器的 `NET_ADMIN` 权限

## 参考资料

- Linux TC文档: https://man7.org/linux/man-pages/man8/tc.8.html
- TC netem: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- Docker网络: https://docs.docker.com/network/
- 飞腾派官方文档: https://www.phytium.com.cn/

## 联系与支持

如果遇到其他问题：
1. 查看 `/tmp/phytium_tc_diagnostic_*.txt` 详细报告
2. 运行 `dmesg | grep -i tc` 查看内核日志
3. 检查 `/var/log/syslog` 系统日志
