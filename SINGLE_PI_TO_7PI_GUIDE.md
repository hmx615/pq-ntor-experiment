# 单飞腾派测试 → 7π镜像复制指南

## 📋 策略概述

由于当前只有1台飞腾派，我们采用**渐进式部署**：

```
阶段1：在Pi #1上完整测试所有组件 ✅
  ↓
阶段2：制作SD卡镜像 ✅
  ↓
阶段3：批量烧录到其余6张SD卡 ✅
  ↓
阶段4：修改各Pi的IP和角色配置 ✅
  ↓
阶段5：启动7π分布式系统 ✅
```

---

## 🚀 阶段1：单Pi完整测试（今天完成）

### 目标
在一台飞腾派上部署并验证所有组件：
- ✅ 目录服务器（directory）
- ✅ 中继节点（relay - guard/middle/exit）
- ✅ 客户端（benchmark_3hop_circuit）
- ✅ 目标服务器（HTTP server）
- ✅ 监控系统（可选）

**重要**：所有组件都在本机测试，使用 `localhost` 或 `127.0.0.1`

---

### 步骤1：在飞腾派上部署代码

```bash
# 在飞腾派上执行
ssh user@192.168.5.110

# 克隆代码
cd ~
git clone https://github.com/your-username/pq-ntor-experiment.git
cd pq-ntor-experiment

# 检查文件
ls -la deployment/
ls -la last_experiment/phytium_deployment/
```

---

### 步骤2：安装依赖

```bash
# 更新系统
sudo apt update

# 安装必要工具
sudo apt install -y \
    git \
    gcc \
    make \
    liboqs-dev \
    iproute2 \
    python3 \
    python3-pip \
    bc

# 验证安装
gcc --version
python3 --version
tc -V
```

---

### 步骤3：编译所有组件

```bash
cd ~/pq-ntor-experiment/c

# 清理旧编译
make clean

# 编译全部
make all

# 验证二进制文件
ls -lh directory relay benchmark_3hop_circuit
```

**预期输出：**
```
-rwxr-xr-x 1 user user 128K directory
-rwxr-xr-x 1 user user 156K relay
-rwxr-xr-x 1 user user  89K benchmark_3hop_circuit
```

---

### 步骤4：单机测试所有组件

#### 测试1：目录服务器

```bash
# 终端1：启动目录服务器
cd ~/pq-ntor-experiment/c
./directory 5000

# 预期输出：
# [Directory] Server started on port 5000
# [Directory] Waiting for connections...
```

```bash
# 终端2：测试连接
curl http://localhost:5000/nodes

# 预期输出（JSON格式的节点列表）：
# {"nodes":[...]}
```

**✅ 如果成功，Ctrl+C停止目录服务器**

---

#### 测试2：中继节点

```bash
# 终端1：启动目录服务器（后台）
cd ~/pq-ntor-experiment/c
nohup ./directory 5000 > ~/directory.log 2>&1 &

# 终端2：启动Guard中继
./relay 6000 guard localhost:5000

# 预期输出：
# [Relay] Guard relay started on port 6000
# [Relay] Registered with directory at localhost:5000
# [Relay] Ready to accept connections
```

```bash
# 终端3：启动Middle中继
./relay 6001 middle localhost:5000

# 终端4：启动Exit中继
./relay 6002 exit localhost:5000
```

**✅ 验证：查看目录服务器日志**
```bash
tail -f ~/directory.log

# 应该看到3个中继注册信息
```

---

#### 测试3：完整三跳电路

保持目录服务器和3个中继运行，新开终端：

```bash
# 终端5：运行客户端测试
cd ~/pq-ntor-experiment/c
./benchmark_3hop_circuit 10 localhost 5000

# 预期输出：
# === PQ-NTOR 3-Hop Circuit Construction Benchmark ===
# Directory: localhost:5000
# Iterations: 10
#
# === RESULTS ===
# Total Circuit Construction Time:
#   Average:  XXX µs (X.XX ms)
#   ...
```

**✅ 如果看到结果（即使延迟很低因为是本地），说明系统工作正常！**

---

### 步骤5：清理进程

```bash
# 停止所有进程
pkill -f directory
pkill -f relay
pkill -f benchmark

# 验证
pgrep -f "directory|relay" || echo "所有进程已停止"
```

---

## 💾 阶段2：制作SD卡镜像

### 重要准备工作

在制作镜像前，**清理敏感信息**：

```bash
# 清理历史记录
history -c
rm -f ~/.bash_history

# 清理SSH密钥（重要！每台Pi应该有不同的密钥）
# 注意：如果需要保留密钥，跳过此步骤
# rm -f ~/.ssh/id_*

# 清理日志
sudo rm -f /var/log/*.log
rm -f ~/*.log

# 清理临时文件
rm -rf /tmp/*
sudo apt clean
```

### 创建通用启动脚本

在制作镜像前，创建一个脚本，让每台Pi首次启动时自动配置：

```bash
cat > ~/pq-ntor-experiment/setup_node.sh << 'EOF'
#!/bin/bash
# setup_node.sh - 首次启动配置脚本
# 用法：sudo ./setup_node.sh <node_id>
# node_id: 1-7 (对应Pi #1到Pi #7)

NODE_ID=$1

if [ -z "$NODE_ID" ] || [ "$NODE_ID" -lt 1 ] || [ "$NODE_ID" -gt 7 ]; then
    echo "用法: sudo $0 <node_id>"
    echo "node_id: 1 (client), 2 (directory), 3 (guard), 4 (middle), 5 (exit), 6 (target), 7 (monitor)"
    exit 1
fi

# IP地址映射
BASE_IP="192.168.5"
IP="${BASE_IP}.$((109 + NODE_ID))"  # .110, .111, ..., .116

# 角色映射
declare -A ROLES
ROLES[1]="client"
ROLES[2]="directory"
ROLES[3]="guard"
ROLES[4]="middle"
ROLES[5]="exit"
ROLES[6]="target"
ROLES[7]="monitor"

ROLE=${ROLES[$NODE_ID]}
HOSTNAME="phytium-pi${NODE_ID}-${ROLE}"

echo "========================================"
echo "  配置飞腾派 #${NODE_ID}"
echo "========================================"
echo "角色: $ROLE"
echo "IP: $IP"
echo "主机名: $HOSTNAME"
echo ""

# 设置静态IP
echo "设置静态IP..."
cat > /etc/netplan/01-netcfg.yaml << NETPLAN
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - ${IP}/24
      gateway4: ${BASE_IP}.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
NETPLAN

netplan apply
echo "✓ IP设置为 $IP"

# 设置主机名
echo "设置主机名..."
hostnamectl set-hostname $HOSTNAME
echo "✓ 主机名设置为 $HOSTNAME"

# 创建角色标记文件
echo "$ROLE" > /home/user/pq-ntor-experiment/.node_role
echo "$NODE_ID" > /home/user/pq-ntor-experiment/.node_id
chown user:user /home/user/pq-ntor-experiment/.node_*

echo ""
echo "========================================"
echo "  ✓ 配置完成"
echo "========================================"
echo ""
echo "请重启系统："
echo "  sudo reboot"
EOF

chmod +x ~/pq-ntor-experiment/setup_node.sh
```

### 关机准备镜像

```bash
# 同步文件系统
sudo sync

# 关机
sudo poweroff
```

---

## 💿 阶段3：镜像制作与复制

### 方法A：使用读卡器（推荐）

**在你的电脑上（Windows/Linux/Mac）：**

1. **读取SD卡镜像：**

```bash
# Linux/Mac:
sudo dd if=/dev/sdX of=phytium-pi-base.img bs=4M status=progress

# Windows: 使用Win32DiskImager或Rufus
```

2. **压缩镜像（可选，节省空间）：**

```bash
gzip -9 phytium-pi-base.img
# 生成: phytium-pi-base.img.gz
```

3. **烧录到其余6张SD卡：**

```bash
# 对每张SD卡重复
sudo dd if=phytium-pi-base.img of=/dev/sdX bs=4M status=progress

# 或从压缩镜像：
gunzip -c phytium-pi-base.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
```

---

### 方法B：使用树莓派镜像工具

1. **使用Raspberry Pi Imager：**
   - 下载：https://www.raspberrypi.com/software/
   - 选择"Use custom" → 选择你的`.img`文件
   - 烧录到7张SD卡

---

## 🔧 阶段4：首次启动配置

### 为每台Pi配置IP和角色

将7张SD卡分别插入7台飞腾派，逐一配置：

#### Pi #1 (客户端, .110)

```bash
# 首次启动后登录
ssh user@192.168.5.XXX  # 可能是DHCP分配的IP

# 运行配置脚本
sudo ~/pq-ntor-experiment/setup_node.sh 1

# 重启
sudo reboot

# 重启后验证
ssh user@192.168.5.110
hostname  # 应该是 phytium-pi1-client
ip addr show eth0  # 应该是 192.168.5.110
```

#### Pi #2 (目录服务器, .111)

```bash
ssh user@192.168.5.XXX
sudo ~/pq-ntor-experiment/setup_node.sh 2
sudo reboot
```

#### 重复 Pi #3 到 #7

```bash
# Pi #3 (Guard)
sudo ~/pq-ntor-experiment/setup_node.sh 3

# Pi #4 (Middle)
sudo ~/pq-ntor-experiment/setup_node.sh 4

# Pi #5 (Exit)
sudo ~/pq-ntor-experiment/setup_node.sh 5

# Pi #6 (Target)
sudo ~/pq-ntor-experiment/setup_node.sh 6

# Pi #7 (Monitor)
sudo ~/pq-ntor-experiment/setup_node.sh 7
```

---

## ✅ 阶段5：启动7π系统

### 验证所有Pi已配置

```bash
# 在你的控制机（WSL）上
for i in {110..116}; do
    echo -n "192.168.5.$i: "
    ssh user@192.168.5.$i "cat /home/user/pq-ntor-experiment/.node_role"
done

# 预期输出：
# 192.168.5.110: client
# 192.168.5.111: directory
# 192.168.5.112: guard
# 192.168.5.113: middle
# 192.168.5.114: exit
# 192.168.5.115: target
# 192.168.5.116: monitor
```

### 使用部署脚本启动系统

```bash
cd ~/pq-ntor-experiment/deployment
./start_all.sh

# 系统会自动：
#   - 启动目录服务器 (Pi #2)
#   - 启动3个中继 (Pi #3, #4, #5)
#   - 启动目标服务器 (Pi #6)
#   - 启动监控 (Pi #7)
```

### 运行测试

```bash
# 在控制机上
ssh user@192.168.5.110
cd ~/pq-ntor-experiment/c
./benchmark_3hop_circuit 10 192.168.5.111 5000

# 或使用脚本运行12拓扑
cd ~/pq-ntor-experiment/scripts
python3 test_12topo_distributed.py
```

---

## 📊 检查清单

### 单Pi测试阶段
- [ ] 代码已克隆到飞腾派
- [ ] 所有组件编译成功
- [ ] 目录服务器可启动
- [ ] 3个中继可注册到目录
- [ ] 客户端测试通过
- [ ] 创建了`setup_node.sh`脚本

### 镜像准备阶段
- [ ] 清理了敏感信息
- [ ] 清理了日志和临时文件
- [ ] `setup_node.sh`脚本已创建
- [ ] 系统已关机

### 镜像复制阶段
- [ ] SD卡镜像已制作
- [ ] 镜像已烧录到7张SD卡
- [ ] 每张SD卡都可启动

### 首次配置阶段
- [ ] 7台Pi都已运行`setup_node.sh`
- [ ] IP地址正确 (.110-.116)
- [ ] 主机名正确
- [ ] 角色标记文件存在

### 系统启动阶段
- [ ] `start_all.sh`成功启动所有服务
- [ ] 客户端可连接到目录服务器
- [ ] 三跳电路测试通过
- [ ] 准备运行12拓扑测试

---

## 🆘 故障排查

### 问题1：编译失败

```bash
# 检查依赖
dpkg -l | grep liboqs-dev

# 如果缺失，安装
sudo apt install -y liboqs-dev
```

### 问题2：SD卡镜像太大

```bash
# 压缩前清理
sudo apt clean
sudo rm -rf /var/log/*.log
rm -rf ~/.cache/*

# 使用PiShrink减小镜像（可选）
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
chmod +x pishrink.sh
sudo ./pishrink.sh phytium-pi-base.img
```

### 问题3：IP配置不生效

```bash
# 检查netplan配置
sudo cat /etc/netplan/01-netcfg.yaml

# 重新应用
sudo netplan apply

# 或使用nmcli (如果是NetworkManager)
sudo nmcli con mod eth0 ipv4.addresses 192.168.5.110/24
sudo nmcli con mod eth0 ipv4.gateway 192.168.5.1
sudo nmcli con mod eth0 ipv4.method manual
sudo nmcli con up eth0
```

### 问题4：节点无法连接

```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 5000  # 目录服务器
sudo ufw allow 6000:6002/tcp  # 中继节点

# 测试连通性
ping 192.168.5.111  # 从client ping directory
```

---

## ⏱️ 时间估算

| 阶段 | 时间 | 说明 |
|-----|------|------|
| 单Pi测试 | 1-2小时 | 部署、编译、测试 |
| 镜像准备 | 30分钟 | 清理、关机 |
| 镜像制作 | 30分钟 | 读取SD卡 |
| 烧录6张卡 | 2小时 | 每张约20分钟 |
| 首次配置 | 1小时 | 7台Pi逐一配置 |
| 系统启动测试 | 30分钟 | 验证工作 |
| **总计** | **5-6小时** | 一天可完成 |

---

## 📝 下一步

**现在开始单Pi测试：**

1. 推送代码到GitHub（已完成 ✓）
2. 在飞腾派上克隆代码
3. 编译所有组件
4. 测试各个组件
5. 创建`setup_node.sh`脚本

完成后告诉我，我会指导镜像制作！

---

**版本**: v1.0
**日期**: 2025-11-30
**状态**: 准备开始单Pi测试
