# 7π实际部署方案

## 🎯 实际网络配置

### 节点分配（实际IP）

| 节点ID | IP地址 | 角色 | 功能 | 端口 |
|--------|--------|------|------|------|
| Pi #1 | **192.168.5.110** | Client | 测试客户端 | - |
| Pi #2 | **192.168.5.185** | Directory | 目录服务器 | 5000 |
| Pi #3 | **192.168.5.186** | Guard | 入口中继 | 6000 |
| Pi #4 | **192.168.5.187** | Middle | 中间中继 | 6001 |
| Pi #5 | **192.168.5.188** | Exit | 出口中继 | 6002 |
| Pi #6 | **192.168.5.189** | Target | HTTP目标 | 8000 |
| Pi #7 | **192.168.5.190** | Monitor | 监控节点 | - |

### 网络拓扑

```
客户端 (110) → 获取节点列表 → Directory (185)
                                      ↓
        Guard (186) → Middle (187) → Exit (188) → Target (189)
            ↑            ↑              ↑
            └────────────┴──────────────┘
              三跳PQ-NTOR电路

Monitor (190) ← 收集所有节点性能数据
```

---

## 🚀 快速部署步骤

### 步骤0：验证连通性 ✅

所有节点已确认在线：
```
✅ 192.168.5.110 - Client
✅ 192.168.5.185 - Directory
✅ 192.168.5.186 - Guard
✅ 192.168.5.187 - Middle
✅ 192.168.5.188 - Exit
✅ 192.168.5.189 - Target
✅ 192.168.5.190 - Monitor
```

### 步骤1：检查Pi #1 (110) 状态

Pi #1 已经完成单机测试，包含：
- ✅ 编译好的所有二进制文件
- ✅ 依赖库 (liboqs, OpenSSL)
- ✅ 测试代码

我们需要：
1. 确认Pi #1的代码是最新的
2. 将代码分发到其他6台Pi
3. 在每台Pi上编译

### 步骤2：自动化部署到6台新Pi

创建自动部署脚本，将Pi #1的代码复制到185-190。

---

## 📋 部署任务清单

- [ ] 检查Pi #1 (110) 代码状态
- [ ] 将代码分发到Pi 185-190
- [ ] 在每台Pi上编译
- [ ] 配置每个节点的角色
- [ ] 启动Directory服务器 (185)
- [ ] 启动3个Relay节点 (186-188)
- [ ] 启动Target服务器 (189)
- [ ] 配置Monitor节点 (190)
- [ ] 运行完整三跳电路测试
- [ ] 验证成功率
- [ ] 开始12拓扑SAGIN测试

---

## 🔧 部署命令

### 方案A：使用已有的部署脚本

```bash
cd /home/ccc/pq-ntor-experiment
python3 deploy_7pi_cluster.py
```

### 方案B：手动部署（如果脚本不存在）

1. **分发代码**
```bash
for ip in 185 186 187 188 189 190; do
    echo "部署到 192.168.5.$ip..."
    scp -r ~/pq-ntor-experiment user@192.168.5.$ip:~/
done
```

2. **在每台Pi上编译**
```bash
for ip in 185 186 187 188 189 190; do
    echo "编译 192.168.5.$ip..."
    ssh user@192.168.5.$ip "cd ~/pq-ntor-experiment/c && make clean && make"
done
```

3. **启动各节点**
```bash
# Directory (185)
ssh user@192.168.5.185 "cd ~/pq-ntor-experiment/c && nohup ./directory 5000 > ~/directory.log 2>&1 &"

# Guard (186)
ssh user@192.168.5.186 "cd ~/pq-ntor-experiment/c && nohup ./relay 6000 192.168.5.185 5000 > ~/guard.log 2>&1 &"

# Middle (187)
ssh user@192.168.5.187 "cd ~/pq-ntor-experiment/c && nohup ./relay 6001 192.168.5.185 5000 > ~/middle.log 2>&1 &"

# Exit (188)
ssh user@192.168.5.188 "cd ~/pq-ntor-experiment/c && nohup ./relay 6002 192.168.5.185 5000 > ~/exit.log 2>&1 &"

# Target (189)
ssh user@192.168.5.189 "cd ~/pq-ntor-experiment/c && nohup python3 -m http.server 8000 > ~/target.log 2>&1 &"
```

4. **在Client (110)运行测试**
```bash
ssh user@192.168.5.110 "cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 100 192.168.5.185 5000"
```

---

## ⚠️ 注意事项

### SSH访问
- 用户名: `user`
- 密码: `user` (如之前配置)
- 或使用SSH密钥（如果已配置）

### 防火墙
确保以下端口开放：
- 5000 (Directory)
- 6000-6002 (Relay)
- 8000 (Target HTTP)

### 同步问题
如果Pi #1代码已更新，确保：
1. 先在Pi #1上git pull最新代码
2. 或直接从本地WSL推送到所有Pi

---

## 📊 测试验证

### 基础连通性测试
```bash
# 测试Directory
curl http://192.168.5.185:5000/nodes

# 测试Target
curl http://192.168.5.189:8000
```

### 完整电路测试
```bash
ssh user@192.168.5.110 "cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 10 192.168.5.185 5000"
```

**预期结果**:
- 10次测试全部成功
- 平均时间 ~2-5 ms (含真实网络延迟)

---

## 🎯 下一步

部署完成后：
1. **基准测试** - LAN环境性能
2. **12拓扑测试** - 应用TC配置模拟SAGIN
3. **数据收集** - 完整性能数据
4. **论文写作** - 使用真实7π数据

---

**创建时间**: 2025-12-01
**状态**: 准备开始部署
**预计时间**: 1-2小时完成部署和基础测试
