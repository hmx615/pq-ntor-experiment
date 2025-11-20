# SAGIN Phase 2 使用指南 - PQ-NTOR 性能测试

**版本**: 1.0
**日期**: 2025-11-12
**阶段**: Phase 2 (Week 2)
**状态**: 准备就绪

---

## 📋 Phase 2 概述

Phase 2 的目标是在 SAGIN 仿真环境中测试 PQ-NTOR 协议的性能，并与传统 NTOR 进行对比。

### 核心任务

1. ✅ 构建 PQ-NTOR Docker 镜像
2. ✅ 适配测试脚本到容器环境
3. ⏳ 运行 5 种链路类型性能测试
4. ⏳ 运行动态切换场景测试
5. ⏳ PQ-NTOR vs 传统 NTOR 对比测试
6. ⏳ 数据分析和结果可视化

---

## 🚀 快速开始

### 前置条件检查

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts
sudo ./phase2_quick_start.sh check
```

应该显示：
```
✓ Docker 已安装
✓ Python3 已安装
✓ 权限检查通过
ℹ PQ-NTOR 镜像未找到，需要先构建
```

### 步骤1: 构建 PQ-NTOR 镜像

```bash
sudo ./phase2_quick_start.sh build
```

**预计时间**: 5-10 分钟（首次构建）

这会：
- 拉取 Ubuntu 22.04 基础镜像
- 编译安装 liboqs (Open Quantum Safe library)
- 编译 PQ-NTOR 源代码
- 安装网络工具（tc, iptables等）
- 创建可执行文件：relay, client, directory, benchmark_pq_ntor

### 步骤2: 运行测试

#### 选项A: 运行单个协议测试

```bash
# 运行 PQ-NTOR 测试（所有场景）
sudo ./phase2_quick_start.sh test-pq

# 运行传统 NTOR 测试（所有场景）
sudo ./phase2_quick_start.sh test-trad
```

#### 选项B: 运行特定场景

```bash
# 仅测试场景1（星间链路）
sudo ./phase2_quick_start.sh test-pq scenario_1

# 仅测试场景3（多跳混合）
sudo ./phase2_quick_start.sh test-trad scenario_3
```

#### 选项C: 运行对比测试（推荐）

```bash
# 自动运行 PQ-NTOR 和传统 NTOR 的对比测试
sudo ./phase2_quick_start.sh comparison
```

这会依次运行：
1. PQ-NTOR 测试（所有场景）
2. 等待 5 秒
3. 传统 NTOR 测试（所有场景）

### 步骤3: 查看结果

```bash
# 查看系统状态和最新结果
sudo ./phase2_quick_start.sh status

# 查看结果文件
ls -lh ../results/sagin_test_*.csv

# 查看日志
tail -f /tmp/sagin_pq_ntor_test.log
```

### 步骤4: 清理环境

```bash
sudo ./phase2_quick_start.sh cleanup
```

---

## 📊 测试场景详解

### Scenario 1: 星间链路 (ISL)

**配置**:
- 路径: Sat-1 ↔ Sat-2
- 跳数: 1
- 距离: ~3000 km
- 预期延迟: ~10 ms

**测试目标**:
- 卫星间直接通信
- 长距离、中等延迟场景
- 测试 PQ-NTOR 在简单拓扑中的性能

### Scenario 2: 星地链路

**配置**:
- 路径: Sat-1 ↔ GS-Beijing
- 跳数: 1
- 距离: ~1000 km
- 预期延迟: ~5 ms

**测试目标**:
- 卫星到地面站通信
- 中等距离、低延迟场景
- 测试地面接入性能

### Scenario 3: 多跳混合链路

**配置**:
- 路径: GS-Beijing → Sat-1 → Aircraft-1 → GS-London
- 跳数: 4
- 距离: ~8000 km
- 预期延迟: ~50 ms

**测试目标**:
- 复杂多跳场景
- 混合节点类型（地面站、卫星、飞机）
- 测试多层加密开销

### Scenario 4: 全球端到端

**配置**:
- 路径: GS-Beijing → Sat-1 → Sat-2 → GS-NewYork
- 跳数: 4
- 距离: ~13000 km
- 预期延迟: ~100 ms

**测试目标**:
- 跨大陆通信
- 长距离、高延迟场景
- 测试极限情况下的性能

### Scenario 5: 动态切换

**配置**:
- 路径: GS-Beijing → Sat-1 → GS-London
- 持续时间: 30 分钟
- 特点: 卫星可见性动态变化

**测试目标**:
- 测试链路动态切换场景
- 验证拓扑变化对性能的影响
- （注：当前版本暂时跳过此场景）

---

## 📈 性能指标

每个测试场景会收集以下指标：

### 核心指标

| 指标 | 说明 | 单位 |
|------|------|------|
| circuit_time_ms | 电路建立时间（平均值） | 毫秒 |
| min_time_ms | 最小电路建立时间 | 毫秒 |
| max_time_ms | 最大电路建立时间 | 毫秒 |
| success_rate | 成功率 | 百分比 |
| timeout_rate | 超时率 | 百分比 |
| iterations | 测试迭代次数 | 次 |

### 测试参数

- **迭代次数**: 每个场景 10 次（可调整）
- **超时设置**: 90 秒
- **协议**: PQ-NTOR (Kyber512) vs 传统 NTOR

---

## 📂 输出文件

### 测试结果 CSV

**位置**: `results/sagin_test_<protocol>_<timestamp>.csv`

**格式**:
```csv
scenario_id,scenario_name,path,status,circuit_time_ms,min_time_ms,max_time_ms,success_rate,timeout_rate,iterations,timestamp,use_pq
scenario_1,Inter-Satellite Link (ISL),Sat-1 -> Sat-2,success,12.5,10.2,15.8,100.0,0.0,10,2025-11-12T08:00:00Z,true
...
```

### 日志文件

**位置**: `/tmp/sagin_pq_ntor_test.log`

**内容**:
- 测试进度
- 容器创建和配置
- 网络拓扑更新
- 错误和警告

---

## 🔧 高级用法

### 直接使用 Python 脚本

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts

# 运行 PQ-NTOR 测试
python3 sagin_pq_ntor_test.py --config ../configs/sagin_topology_config.json

# 运行传统 NTOR 测试
python3 sagin_pq_ntor_test.py --config ../configs/sagin_topology_config.json --traditional

# 运行特定场景
python3 sagin_pq_ntor_test.py --scenario scenario_1

# Dry-run 模式（不实际运行测试）
python3 sagin_pq_ntor_test.py --dry-run

# 仅清理
python3 sagin_pq_ntor_test.py --cleanup-only
```

### 查看帮助

```bash
python3 sagin_pq_ntor_test.py --help
```

### 调整测试参数

编辑 `sagin_pq_ntor_test.py` 中的参数：

```python
# 修改迭代次数（第 XXX 行）
'--iterations', '10'  # 改为 50 或 100

# 修改超时时间
timeout=60  # 在 _run_command 中修改
```

---

## 🐛 故障排查

### 问题1: 镜像构建失败

**错误**: `liboqs 编译失败`

**解决**:
```bash
# 检查磁盘空间
df -h

# 检查网络连接
ping -c 3 github.com

# 手动重试
cd docker
sudo ./build_pq_ntor_image.sh
```

### 问题2: 容器无法创建

**错误**: `Error response from daemon: Conflict`

**解决**:
```bash
# 清理旧容器
sudo ./phase2_quick_start.sh cleanup

# 或手动清理
docker ps -a --filter "name=sagin_" -q | xargs docker rm -f
docker network rm sagin_net
```

### 问题3: 测试一直失败

**错误**: `benchmark failed`

**解决**:
```bash
# 进入容器检查
docker exec -it sagin_gs-beijing bash

# 检查 PQ-NTOR 可执行文件
ls -lh /root/pq-ntor/relay
ldd /root/pq-ntor/relay

# 手动运行 relay
/root/pq-ntor/relay --port 9005 --log /tmp/test.log
```

### 问题4: 网络配置问题

**错误**: `tc: command not found`

**解决**: 这些命令应该在容器内预装。检查镜像是否正确构建：

```bash
docker run --rm pq-ntor-sagin:latest which tc
docker run --rm pq-ntor-sagin:latest which iptables
```

---

## 📊 预期结果

### PQ-NTOR vs 传统 NTOR

基于之前的测试数据，预期结果：

| 场景 | PQ-NTOR 时间 | 传统 NTOR 时间 | 开销 |
|------|--------------|----------------|------|
| Scenario 1 (ISL) | ~15 ms | ~12 ms | +25% |
| Scenario 2 (SGLink) | ~8 ms | ~6 ms | +33% |
| Scenario 3 (多跳) | ~55 ms | ~45 ms | +22% |
| Scenario 4 (全球) | ~110 ms | ~95 ms | +16% |

**注意**: 实际结果会因网络状况、系统负载等因素而变化。

### 成功率

- 预期成功率: >95%
- 预期超时率: <5%

如果结果显著偏离预期，需要检查：
- 网络拓扑配置
- 容器网络连通性
- 系统资源使用情况

---

## 📝 下一步（Phase 3）

Phase 2 完成后，将进入 Phase 3（数据分析和论文撰写）：

1. **数据分析脚本**
   - 对比 PQ-NTOR 和传统 NTOR 性能
   - 生成统计摘要
   - 计算性能开销百分比

2. **可视化**
   - 电路建立时间对比图
   - 时间分布箱型图
   - 超时率分析图
   - 性能开销对比图

3. **论文撰写**
   - 实验方法部分
   - 结果分析部分
   - 讨论和结论

---

## ✅ Phase 2 检查清单

开始 Phase 2 前：
- [ ] Phase 1 已完成
- [ ] Docker 环境正常
- [ ] PQ-NTOR 源代码可用
- [ ] 有足够磁盘空间（>5GB）
- [ ] 有 root 权限

Phase 2 步骤：
- [ ] 构建 PQ-NTOR 镜像
- [ ] 运行 PQ-NTOR 测试（所有场景）
- [ ] 运行传统 NTOR 测试（所有场景）
- [ ] 验证测试结果
- [ ] 保存结果文件

完成 Phase 2 后：
- [ ] 结果文件已保存
- [ ] 日志文件已备份
- [ ] 环境已清理
- [ ] 准备进入 Phase 3

---

## 📞 获取帮助

```bash
# 查看 Phase 2 脚本帮助
./phase2_quick_start.sh help

# 查看 Python 脚本帮助
python3 sagin_pq_ntor_test.py --help

# 查看系统状态
./phase2_quick_start.sh status

# 查看日志
tail -f /tmp/sagin_pq_ntor_test.log
```

---

## 🔗 相关文档

- `Phase1完成总结.md` - Phase 1 成果
- `SAGIN系统使用指南.md` - 系统使用手册
- `快速参考.md` - 快速参考卡片
- `docs/Skyfield-SAGIN实施工作列表.md` - 完整工作计划

---

**创建日期**: 2025-11-12
**维护者**: Claude Code
**状态**: ✅ Phase 2 准备完成，可以开始测试
