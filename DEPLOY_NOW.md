# 🚀 立即开始：单飞腾派部署步骤

## 第1步：连接到飞腾派

```bash
# 在你的WSL终端执行
ssh user@192.168.5.110
# 输入密码
```

---

## 第2步：克隆代码

```bash
# 在飞腾派上执行
cd ~

# 如果之前已克隆过，先删除
rm -rf pq-ntor-experiment

# 克隆最新代码（使用你的GitHub仓库地址）
git clone https://github.com/your-username/pq-ntor-experiment.git

# 或如果你的仓库是私有的，使用HTTPS + token
# git clone https://your-token@github.com/your-username/pq-ntor-experiment.git

# 进入目录
cd pq-ntor-experiment

# 检查关键文件
ls deployment/
ls last_experiment/phytium_deployment/
```

**预期看到：**
```
deployment/
  deploy_all.sh
  start_all.sh
  stop_all.sh
  README_CN.md

last_experiment/phytium_deployment/
  benchmark_3hop_circuit.c
  configure_tc.sh
  ...
```

---

## 第3步：安装依赖

```bash
# 更新系统
sudo apt update

# 安装编译工具和库
sudo apt install -y \
    gcc \
    make \
    liboqs-dev \
    iproute2 \
    python3 \
    python3-pip \
    bc \
    net-tools

# 验证安装
gcc --version        # 应该显示版本号
pkg-config --modversion liboqs  # 应该显示liboqs版本
```

---

## 第4步：编译代码

```bash
cd ~/pq-ntor-experiment/c

# 清理旧编译
make clean

# 编译所有程序
make all

# 查看生成的二进制文件
ls -lh directory relay benchmark_pq_ntor
```

**预期输出：**
```
-rwxr-xr-x 1 user user 128K directory
-rwxr-xr-x 1 user user 156K relay
-rwxr-xr-x 1 user user  89K benchmark_pq_ntor
```

**如果编译失败：**

查看错误信息，常见问题：

```bash
# 问题1：找不到liboqs
sudo apt install -y liboqs-dev

# 问题2：找不到pthread
# 在Makefile中添加 -lpthread

# 问题3：OpenSSL版本问题
# 使用我们提供的compile_benchmark_only.py
cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
python3 compile_benchmark_only.py
```

---

## 第5步：测试单组件

### 测试A：基准测试程序（握手测试）

```bash
cd ~/pq-ntor-experiment/c

# 运行握手测试（100次）
./benchmark_pq_ntor 100

# 预期输出：
# === PQ-NTOR Benchmark ===
# Iterations: 100
# Average: 180.xx µs
# ...
```

**✅ 如果看到结果，说明PQ-NTOR工作正常！**

---

### 测试B：目录服务器

```bash
# 启动目录服务器
cd ~/pq-ntor-experiment/c
./directory 5000

# 预期输出：
# [Directory] Server started on port 5000
# [Directory] Waiting for connections...
```

**保持运行，开启新终端测试：**

```bash
# 新终端
ssh user@192.168.5.110

# 测试目录服务器
curl http://localhost:5000/nodes

# 预期输出（JSON格式）：
# {"nodes":[]}  # 空列表，因为还没有中继注册
```

**✅ 如果能连接，说明目录服务器工作正常！**

按 Ctrl+C 停止目录服务器

---

### 测试C：中继节点

```bash
# 终端1：启动目录服务器（后台）
cd ~/pq-ntor-experiment/c
nohup ./directory 5000 > ~/directory.log 2>&1 &

# 终端1：启动Guard中继
./relay 6000 guard localhost:5000

# 预期输出：
# [Relay] Guard relay started on port 6000
# [Relay] Registered with directory
# [Relay] Ready
```

**开启新终端测试注册：**

```bash
# 新终端
ssh user@192.168.5.110

# 查看目录中的节点
curl http://localhost:5000/nodes

# 预期输出：
# {"nodes":[{"hostname":"localhost","port":6000,"type":"guard",...}]}
```

**✅ 如果看到guard节点，说明中继注册成功！**

按 Ctrl+C 停止中继

---

### 测试D：完整三跳（所有组件）

```bash
# 清理旧进程
pkill -f directory
pkill -f relay

# 启动目录服务器
cd ~/pq-ntor-experiment/c
nohup ./directory 5000 > ~/directory.log 2>&1 &

# 启动3个中继（后台）
nohup ./relay 6000 guard localhost:5000 > ~/guard.log 2>&1 &
nohup ./relay 6001 middle localhost:5000 > ~/middle.log 2>&1 &
nohup ./relay 6002 exit localhost:5000 > ~/exit.log 2>&1 &

# 等待2秒让服务启动
sleep 2

# 检查所有进程
pgrep -a directory
pgrep -a relay

# 预期看到4个进程
```

---

## 第6步：运行三跳电路测试（关键）

```bash
cd ~/pq-ntor-experiment/last_experiment/phytium_deployment

# 编译三跳测试程序
gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread

# 运行测试（10次迭代）
./benchmark_3hop_circuit 10 localhost 5000
```

**预期输出：**

```
=== PQ-NTOR 3-Hop Circuit Construction Benchmark ===
Directory: localhost:5000
Iterations: 10
Protocol: PQ-NTOR (Kyber-512)

Running benchmark...
  Progress: 10/10

Completed: 10/10 successful

=== RESULTS ===

Total Circuit Construction Time:
  Average:  XXX.XX µs (X.XX ms)
  Median:   XXX.XX µs (X.XX ms)
  Min:      XXX.XX µs (X.XX ms)
  Max:      XXX.XX µs (X.XX ms)
  StdDev:   XX.XX µs

Breakdown by Stage:
  Directory Fetch:  XXX.XX µs (XX.X%)
  Hop 1 (Guard):    XXX.XX µs (XX.X%)
  Hop 2 (Middle):   XXX.XX µs (XX.X%)
  Hop 3 (Exit):     XXX.XX µs (XX.X%)

=== JSON OUTPUT ===
{
  "total_us": XXX.XX,
  "total_ms": X.XX,
  ...
}
```

**✅ 如果看到这个输出，恭喜！所有组件工作正常！**

**注意：** 因为是本地测试（localhost），延迟会很低（可能只有几百微秒），这是正常的。真正的7π分布式测试会有更真实的网络延迟。

---

## 第7步：创建节点配置脚本

```bash
cat > ~/pq-ntor-experiment/setup_node.sh << 'EOF'
#!/bin/bash
# setup_node.sh - 首次启动配置脚本
# 用法：sudo ./setup_node.sh <node_id>

NODE_ID=$1

if [ -z "$NODE_ID" ] || [ "$NODE_ID" -lt 1 ] || [ "$NODE_ID" -gt 7 ]; then
    echo "用法: sudo $0 <node_id>"
    echo "node_id: 1-7"
    exit 1
fi

# IP地址映射
BASE_IP="192.168.5"
IP="${BASE_IP}.$((109 + NODE_ID))"

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

# 保存角色信息
echo "$ROLE" > /home/user/pq-ntor-experiment/.node_role
echo "$NODE_ID" > /home/user/pq-ntor-experiment/.node_id
chown user:user /home/user/pq-ntor-experiment/.node_*

echo "✓ 配置完成"
echo ""
echo "提示：如需设置静态IP和主机名，请手动配置网络"
EOF

chmod +x ~/pq-ntor-experiment/setup_node.sh
```

---

## 第8步：清理进程

```bash
# 停止所有测试进程
pkill -f directory
pkill -f relay
pkill -f benchmark

# 验证
pgrep -f "directory|relay" || echo "✓ 所有进程已停止"

# 清理日志（可选）
rm -f ~/*.log
```

---

## ✅ 检查清单

完成以下所有项，就可以制作镜像了：

- [ ] 代码已克隆到 `~/pq-ntor-experiment`
- [ ] 所有依赖已安装（gcc, liboqs-dev等）
- [ ] 所有组件编译成功（directory, relay, benchmark）
- [ ] 握手测试通过（benchmark_pq_ntor 100）
- [ ] 目录服务器可启动并响应
- [ ] 中继节点可注册到目录
- [ ] 三跳电路测试通过（benchmark_3hop_circuit 10）
- [ ] `setup_node.sh` 脚本已创建
- [ ] 所有测试进程已停止

---

## 📋 测试结果记录

请把测试结果发给我：

```bash
# 运行这个命令，把输出发给我
cat << 'REPORT'
========== 单Pi测试报告 ==========

1. 握手测试结果：
$(cd ~/pq-ntor-experiment/c && ./benchmark_pq_ntor 10 2>&1 | tail -10)

2. 三跳电路测试结果：
$(cd ~/pq-ntor-experiment/last_experiment/phytium_deployment && ./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tail -20)

3. 编译的二进制文件：
$(ls -lh ~/pq-ntor-experiment/c/directory ~/pq-ntor-experiment/c/relay ~/pq-ntor-experiment/c/benchmark_pq_ntor)

4. 系统信息：
$(uname -a)
$(gcc --version | head -1)

===================================
REPORT
```

---

## 🆘 故障排查

### 问题1：编译失败 "cannot find -loqs"

```bash
# 检查liboqs
dpkg -l | grep liboqs

# 如果没有，安装
sudo apt update
sudo apt install -y liboqs-dev

# 验证
pkg-config --modversion liboqs
```

### 问题2：三跳测试连接失败

```bash
# 检查目录服务器是否运行
pgrep -a directory

# 如果没有，启动
cd ~/pq-ntor-experiment/c
./directory 5000 &

# 检查端口
netstat -tuln | grep 5000
```

### 问题3：中继节点无法注册

```bash
# 查看目录服务器日志
cat ~/directory.log

# 查看中继日志
cat ~/guard.log

# 检查localhost解析
ping -c 1 localhost
```

---

## 🎯 完成后

**告诉我测试结果，我会指导你：**

1. ✅ 如果所有测试通过 → 准备制作SD卡镜像
2. ❌ 如果有问题 → 帮你调试解决

**预计时间：** 30-60分钟

**准备好了吗？开始吧！** 🚀
