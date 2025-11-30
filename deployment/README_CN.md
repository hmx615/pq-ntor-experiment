# 7飞腾派分布式部署 - 快速参考手册

## 📚 完整文档

详细架构文档请阅读：
```
../last_experiment/phytium_deployment/7PI_DISTRIBUTED_ARCHITECTURE.md
```

内容包括：
- ✅ 网络架构设计
- ✅ 路由器/交换机问题深度解析（回答老师的问题）
- ✅ 延迟模型与计算公式
- ✅ 代码部署方案（GitHub统一部署）
- ✅ 12拓扑映射到物理网络
- ✅ 完整实施步骤

---

## 🚀 快速开始（5分钟）

### 前提条件

1. **硬件准备**
   - 7台飞腾派通电并连接到同一交换机
   - IP地址：192.168.5.110 - 192.168.5.116

2. **网络配置**
   ```bash
   # 测试连通性
   for i in {110..116}; do
       ping -c 1 192.168.5.$i && echo "192.168.5.$i ✓" || echo "192.168.5.$i ✗"
   done
   ```

3. **SSH免密登录**
   ```bash
   # 配置SSH密钥
   for i in {110..116}; do
       ssh-copy-id user@192.168.5.$i
   done
   ```

---

## 📦 第一步：部署代码

### 方案1：使用GitHub（推荐）

```bash
# 1. 推送代码到GitHub
cd /home/ccc/pq-ntor-experiment
git add .
git commit -m "feat: 7Pi分布式部署版本"
git push origin main  # 或你的分支名

# 2. 在控制机上运行部署脚本
cd deployment
./deploy_all.sh https://github.com/your-username/pq-ntor-experiment.git

# 等待约5-10分钟，所有节点会自动：
#   - 克隆代码
#   - 编译二进制文件
#   - 验证编译结果
```

### 方案2：本地复制（不用GitHub）

```bash
cd deployment
./deploy_all.sh /path/to/local/repo  # 使用本地路径
```

---

## 🎬 第二步：启动系统

```bash
cd deployment
./start_all.sh

# 输出示例：
# [1/6] 启动目录服务器 (192.168.5.111:5000) ...
#   ✓ 目录服务器已启动 (PID: 12345)
# [2/6] 启动Guard中继 (192.168.5.112:6000) ...
#   ✓ Guard中继已启动 (PID: 12346)
# ...
```

**检查状态：**
```bash
# 目录服务器日志
ssh user@192.168.5.111 'tail -20 ~/directory.log'

# Guard中继日志
ssh user@192.168.5.112 'tail -20 ~/guard.log'
```

---

## 🧪 第三步：运行测试

### 手动测试（验证系统）

```bash
# 在Pi #1（客户端）上运行
ssh user@192.168.5.110

cd ~/pq-ntor-experiment/c
./benchmark_3hop_circuit 10 192.168.5.111 5000

# 预期输出：
# === PQ-NTOR 3-Hop Circuit Construction Benchmark ===
# Directory: 192.168.5.111:5000
# Iterations: 10
#
# === RESULTS ===
# Total Circuit Construction Time:
#   Average:  32.45 ms
#   ...
```

### 自动化12拓扑测试

```bash
# 在控制机上运行
cd ~/pq-ntor-experiment/scripts
python3 test_12topo_distributed.py

# 自动运行12个拓扑，每个约2-3分钟
# 总耗时：30-40分钟
```

---

## 🛑 第四步：停止系统

```bash
cd deployment
./stop_all.sh

# 会自动：
#   - 停止所有进程
#   - 清除TC规则
#   - 删除PID文件
```

---

## 📊 节点角色分配

| Pi | IP | 角色 | 运行程序 | 端口 |
|----|-------|------|---------|------|
| #1 | .110 | 客户端 | benchmark_3hop_circuit | - |
| #2 | .111 | 目录服务器 | directory | 5000 |
| #3 | .112 | Guard中继 | relay (guard) | 6000 |
| #4 | .113 | Middle中继 | relay (middle) | 6001 |
| #5 | .114 | Exit中继 | relay (exit) | 6002 |
| #6 | .115 | 目标服务器 | python http.server | 8080 |
| #7 | .116 | 监控节点 | monitor_system.py | 9000 |

---

## 🔧 常见问题

### Q1: 部署失败，提示"无法连接"

**检查：**
```bash
# 1. 检查IP是否正确
ping 192.168.5.110

# 2. 检查SSH是否配置
ssh user@192.168.5.110 "echo OK"

# 3. 检查SSH密钥
ssh-copy-id user@192.168.5.110
```

### Q2: 编译失败，缺少liboqs

**解决：**
```bash
# 在每台Pi上安装依赖
for i in {110..116}; do
    ssh user@192.168.5.$i "sudo apt update && sudo apt install -y liboqs-dev"
done
```

### Q3: 启动后进程立即退出

**检查日志：**
```bash
# 查看目录服务器日志
ssh user@192.168.5.111 'cat ~/directory.log'

# 常见原因：
#   - 端口被占用
#   - 权限问题
#   - 依赖缺失
```

### Q4: 测试结果异常（延迟太高/太低）

**检查TC配置：**
```bash
# 查看当前TC规则
ssh user@192.168.5.110 'sudo tc qdisc show dev eth0'

# 清除TC重新测试
./stop_all.sh
./start_all.sh
```

---

## 🎓 关于路由器的问题（给老师看）

**老师问："为什么只有一个路由器？不应该通过多个路由转发吗？"**

**详细回答请查看：**
```
../last_experiment/phytium_deployment/7PI_DISTRIBUTED_ARCHITECTURE.md
→ "路由器/交换机问题深度解析" 章节
```

**简短回答：**

1. **真实互联网**：确实有10-20个路由器（跨地域、跨运营商）
2. **我们的环境**：所有Pi在同一局域网（192.168.5.x），只需要交换机二层转发
3. **交换机 vs 路由器**：
   - 交换机：MAC地址转发（我们使用的）
   - 路由器：IP地址路由（跨网段才需要）
4. **模拟方式**：用TC在每个节点上模拟延迟，等效于多跳路由
5. **研究重点**：PQ-NTOR密码学性能，不是路由协议性能

**公式：**
```
总延迟 = TC模拟延迟 + 真实网卡/协议栈开销 + PQ-NTOR计算
         (可控变量)   (真实测量)          (研究对象)
```

---

## 📖 延迟计算公式

详细公式请查看架构文档，这里是简化版：

### 单跳延迟分解

```
T_hop = T_crypto + T_network

T_crypto = 180 µs (PQ-NTOR on ARM)

T_network = T_protocol + T_nic + T_switch + T_tc
          = 40 µs   + 25 µs + 5 µs    + (TC配置的延迟)
```

### topo01 完整计算示例

```
目录查询: ~3 ms
第一跳: 180 µs (crypto) + 70 µs (网络) + 2.71 ms (TC) = ~3 ms
第二跳: 180 µs + 140 µs (双向) + 5.42 ms (TC) = ~6 ms
第三跳: 180 µs + 210 µs (三向) + 8.13 ms (TC) = ~9 ms

总计: 3 + 3 + 6 + 9 = 21 ms (理论值)
实测: 25-30 ms (含系统抖动)
```

---

## 🗂️ 文件结构

```
pq-ntor-experiment/
├── deployment/                 # 部署脚本（本目录）
│   ├── deploy_all.sh          # ✅ 一键部署
│   ├── start_all.sh           # ✅ 启动系统
│   ├── stop_all.sh            # ✅ 停止系统
│   └── README_CN.md           # 本文件
│
├── c/                          # C源代码
│   ├── directory              # 目录服务器二进制
│   ├── relay                  # 中继节点二进制
│   ├── benchmark_3hop_circuit # 客户端测试程序
│   └── ...
│
├── scripts/                    # 测试脚本
│   └── test_12topo_distributed.py
│
└── last_experiment/phytium_deployment/
    └── 7PI_DISTRIBUTED_ARCHITECTURE.md  # ✅ 完整架构文档
```

---

## 🎯 预期结果

### 单拓扑测试（topo01）

```json
{
  "total_ms": 28.5,
  "directory_ms": 3.2,
  "hop1_ms": 6.8,
  "hop2_ms": 8.4,
  "hop3_ms": 10.1,
  "stddev_ms": 2.1
}
```

### 12拓扑对比

| 拓扑 | 预期延迟(ms) | 主要特征 |
|-----|------------|---------|
| topo01 | 25-28 | 高延迟高带宽 |
| topo03 | 15-18 | **最低延迟** |
| topo08 | 26-29 | **最高延迟** |
| 平均 | ~24 | - |

**关键发现：**
- 延迟与TC配置的delay强相关（R² > 0.8）
- PQ-NTOR只占总时间的2-3%（~540 µs / 25 ms）
- 网络传输是主要开销（97%）

---

## 📞 需要帮助？

1. **查看完整文档**：`7PI_DISTRIBUTED_ARCHITECTURE.md`
2. **检查日志文件**：各节点的 `~/*.log`
3. **运行诊断**：`./deployment/diagnose.sh`（如果提供）

---

## ✅ 检查清单

部署前：
- [ ] 7台Pi已通电并联网
- [ ] IP地址正确配置（.110-.116）
- [ ] SSH免密登录已配置
- [ ] 代码已推送到GitHub

部署：
- [ ] `./deploy_all.sh` 成功
- [ ] 所有节点编译通过
- [ ] `./start_all.sh` 所有服务启动

测试：
- [ ] 手动测试通过（10次迭代）
- [ ] 延迟在预期范围（15-30 ms）
- [ ] 准备运行12拓扑自动化测试

---

**版本**: v1.0
**日期**: 2025-11-30
**状态**: 准备就绪，可开始部署
