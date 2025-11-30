# 🚀 快速部署指南（交互式）

## 方案：手动SSH + 复制粘贴命令

由于自动化需要额外权限，我们使用**交互式方案**更简单快速。

---

## 第1步：安装sshpass（一次性）

在你的WSL终端执行：

```bash
# 安装sshpass（需要输入WSL的sudo密码）
sudo apt-get update && sudo apt-get install -y sshpass

# 验证
sshpass -V
```

---

## 第2步：连接到飞腾派

```bash
ssh user@192.168.5.110
# 密码: user
```

---

## 第3步：复制代码到飞腾派（在飞腾派上执行）

**整块复制，一次性粘贴执行：**

```bash
# 清理旧代码
cd ~
rm -rf pq-ntor-experiment

# 创建目录
mkdir -p pq-ntor-experiment

# 退出（准备从WSL复制文件）
exit
```

---

## 第4步：从WSL复制代码（在WSL上执行）

```bash
cd /home/ccc/pq-ntor-experiment

# 使用scp复制（需要输入密码：user）
scp -r * user@192.168.5.110:~/pq-ntor-experiment/

# 等待复制完成（可能需要1-2分钟）
```

---

## 第5步：重新连接并编译（在飞腾派上执行）

```bash
ssh user@192.168.5.110
# 密码: user
```

**整块复制，一次性粘贴执行：**

```bash
# 进入目录
cd ~/pq-ntor-experiment/c

# 清理
make clean 2>/dev/null || true

# 编译
make all

# 查看结果
ls -lh directory relay benchmark_pq_ntor
```

**预期看到三个二进制文件。如果编译失败，执行：**

```bash
# 检查依赖
dpkg -l | grep -E "gcc|make|liboqs"

# 如果缺失liboqs，安装：
sudo apt update
sudo apt install -y liboqs-dev

# 重新编译
cd ~/pq-ntor-experiment/c
make all
```

---

## 第6步：编译三跳测试程序

```bash
cd ~/pq-ntor-experiment/last_experiment/phytium_deployment

gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread

# 验证
ls -lh benchmark_3hop_circuit
```

---

## 第7步：运行握手测试

```bash
cd ~/pq-ntor-experiment/c

# 运行10次测试
./benchmark_pq_ntor 10
```

**预期输出：**
```
=== PQ-NTOR Benchmark ===
Iterations: 10
...
Average: ~180 µs
```

**✅ 如果看到结果，继续下一步**

---

## 第8步：运行完整系统测试

**整块复制，一次性粘贴执行：**

```bash
# 清理旧进程
pkill -f directory 2>/dev/null || true
pkill -f relay 2>/dev/null || true
sleep 1

cd ~/pq-ntor-experiment/c

# 启动目录服务器（后台）
nohup ./directory 5000 > ~/directory.log 2>&1 &
echo "目录服务器已启动"
sleep 2

# 启动3个中继（后台）
nohup ./relay 6000 guard localhost:5000 > ~/guard.log 2>&1 &
nohup ./relay 6001 middle localhost:5000 > ~/middle.log 2>&1 &
nohup ./relay 6002 exit localhost:5000 > ~/exit.log 2>&1 &
echo "3个中继已启动"
sleep 2

# 检查进程
echo "当前运行的进程："
pgrep -a directory
pgrep -a relay

# 等待服务完全启动
sleep 3

# 运行三跳测试
cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
echo ""
echo "开始三跳电路测试（5次迭代）..."
./benchmark_3hop_circuit 5 localhost 5000
```

**预期输出：**
```
=== PQ-NTOR 3-Hop Circuit Construction Benchmark ===
Directory: localhost:5000
Iterations: 5

=== RESULTS ===
Total Circuit Construction Time:
  Average: XXX.XX µs (X.XX ms)
  ...
```

**✅ 如果看到结果，说明所有组件工作正常！**

---

## 第9步：清理测试进程

```bash
# 停止所有测试进程
pkill -f directory
pkill -f relay

# 验证
pgrep -f "directory|relay" || echo "✓ 所有进程已停止"
```

---

## 第10步：创建配置脚本（为镜像准备）

**整块复制，一次性粘贴执行：**

```bash
cat > ~/pq-ntor-experiment/setup_node.sh << 'EOF'
#!/bin/bash
NODE_ID=$1

if [ -z "$NODE_ID" ] || [ "$NODE_ID" -lt 1 ] || [ "$NODE_ID" -gt 7 ]; then
    echo "用法: sudo $0 <node_id>"
    echo "node_id: 1-7"
    exit 1
fi

BASE_IP="192.168.5"
IP="${BASE_IP}.$((109 + NODE_ID))"

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

echo "配置飞腾派 #${NODE_ID}"
echo "角色: $ROLE"
echo "IP: $IP"
echo "主机名: $HOSTNAME"

echo "$ROLE" > /home/user/pq-ntor-experiment/.node_role
echo "$NODE_ID" > /home/user/pq-ntor-experiment/.node_id
chown user:user /home/user/pq-ntor-experiment/.node_*

echo "✓ 配置完成"
EOF

chmod +x ~/pq-ntor-experiment/setup_node.sh
echo "✓ setup_node.sh 已创建"
```

---

## ✅ 检查清单

完成后检查：

```bash
# 在飞腾派上执行
cd ~

# 1. 代码目录
ls -la pq-ntor-experiment/

# 2. 编译的二进制
ls -lh pq-ntor-experiment/c/directory
ls -lh pq-ntor-experiment/c/relay
ls -lh pq-ntor-experiment/c/benchmark_pq_ntor
ls -lh pq-ntor-experiment/last_experiment/phytium_deployment/benchmark_3hop_circuit

# 3. 配置脚本
ls -lh pq-ntor-experiment/setup_node.sh

# 4. 测试日志（可选）
ls -lh ~/*.log 2>/dev/null || echo "无日志文件"
```

**全部存在？** ✅ **可以准备制作镜像了！**

---

## 📋 测试结果报告（发给我）

```bash
# 在飞腾派上执行，把输出发给我
cat << 'REPORT'
========== 飞腾派测试报告 ==========

1. 系统信息:
$(uname -a)
$(gcc --version | head -1)

2. 编译的文件:
$(ls -lh ~/pq-ntor-experiment/c/{directory,relay,benchmark_pq_ntor} 2>&1)

3. 三跳测试程序:
$(ls -lh ~/pq-ntor-experiment/last_experiment/phytium_deployment/benchmark_3hop_circuit 2>&1)

4. 配置脚本:
$(ls -lh ~/pq-ntor-experiment/setup_node.sh 2>&1)

5. 握手测试结果（最后几行）:
$(cd ~/pq-ntor-experiment/c && ./benchmark_pq_ntor 5 2>&1 | tail -8)

===================================
REPORT
```

把输出复制给我，我会验证部署是否成功！

---

## 预计时间

- 安装sshpass: 1分钟
- 复制代码: 2分钟
- 编译: 5分钟
- 测试: 5分钟
- **总计: 15分钟**

**准备好了吗？开始吧！** 🚀
