# Phase 3 WSL2真实网络模拟运行指南

## 问题解决方案

**问题**: Phytium Pi内核不支持netem模块
**解决**: 在WSL2主机上运行Phase 3测试，WSL2内核完整支持tc/netem

## WSL2内核支持验证 ✅

```bash
# 已验证WSL2内核配置
CONFIG_NET_SCH_NETEM=m  ✅ 支持网络延迟/丢包模拟
CONFIG_NET_SCH_TBF=m    ✅ 支持带宽限制
```

## 运行步骤

### 方法1: 使用包装脚本（推荐）

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
sudo ./run_phase3_with_sudo.sh
```

**脚本自动处理**:
- ✅ 检查tc/netem支持
- ✅ 加载netem内核模块
- ✅ 清理旧的tc配置
- ✅ 运行Phase 3测试（480次电路构建）
- ✅ 自动应用/清理每个拓扑的网络参数
- ✅ 保存结果到essay目录
- ✅ 生成快速统计报告

### 方法2: 手动运行

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 1. 清理现有tc配置
sudo tc qdisc del dev lo root 2>/dev/null || true

# 2. 运行测试
sudo ./phase3_sagin_network

# 3. 查看结果
cat phase3_sagin_cbt.csv
```

## 测试配置

### 12个SAGIN拓扑参数

| 拓扑 | 带宽(Mbps) | 延迟(ms) | 丢包率(%) | 说明 |
|------|-----------|----------|-----------|------|
| topo01 | 31.81 | 2.72 | 0.1 | LEO-GW (高带宽/低延迟) |
| topo02 | 31.81 | 5.46 | 0.1 | LEO-GW (高带宽/高延迟) |
| topo03 | 31.81 | 5.46 | 2.0 | LEO-GW (高带宽/高延迟/高丢包) |
| topo04 | 25.86 | 2.72 | 0.1 | UAV-LEO (中带宽/低延迟) |
| topo05 | 25.86 | 5.46 | 0.1 | UAV-LEO (中带宽/高延迟) |
| topo06 | 25.86 | 5.46 | 2.0 | UAV-LEO (中带宽/高延迟/高丢包) |
| topo07 | 6.02 | 5.46 | 2.0 | 恶劣条件 |
| topo08 | 14.26 | 2.72 | 0.1 | 中等条件 |
| topo09 | 14.26 | 2.72 | 2.0 | 中等延迟高丢包 |
| topo10 | 3.60 | 2.72 | 0.1 | 低带宽 |
| topo11 | 3.60 | 2.72 | 2.0 | 低带宽高丢包 |
| topo12 | 3.60 | 5.46 | 2.0 | 最恶劣条件 |

### 测试协议

- **Classic NTOR**: 传统Tor握手协议（Curve25519 + SHA256）
- **PQ-NTOR**: 后量子Tor握手协议（Kyber-512 + Curve25519 + SHA256）

### 测试规模

- **每个拓扑**: 3次预热 + 20次测量
- **每个协议**: 12个拓扑
- **总测试数**: 12拓扑 × 2协议 × 20迭代 = **480次电路构建**
- **预计耗时**: 10-15分钟

## 预期结果

测试将生成 `phase3_sagin_cbt.csv`，包含每个拓扑的统计数据：

- **Mean_ms**: 平均CBT（电路构建时间）
- **Median_ms**: 中位数CBT
- **Min_ms / Max_ms**: 最小/最大CBT
- **StdDev_ms**: 标准差
- **P95_ms / P99_ms**: 95分位数/99分位数
- **CI_Lower / CI_Upper**: 95%置信区间

### 关键指标

1. **网络参数影响**: 不同拓扑应该显示不同的CBT（验证网络模拟生效）
2. **PQ开销**: PQ-NTOR相对Classic NTOR的性能开销
3. **稳定性**: 标准差和置信区间大小

## 结果验证

### 验证网络模拟是否生效

```bash
# 测试时观察tc配置
sudo tc qdisc show dev lo

# 应该看到类似输出:
# qdisc netem 8001: root refcnt 2 limit 1000 delay 2.7ms loss 0.1%
```

### 快速检查结果

```bash
# 方法1: 使用脚本自动统计
sudo ./run_phase3_with_sudo.sh
# 脚本结束时会显示快速统计

# 方法2: 手动统计
awk -F',' 'NR>1 && $2~/Classic/ {sum+=$3; count++} END {print "Classic平均:", sum/count, "ms"}' phase3_sagin_cbt.csv
awk -F',' 'NR>1 && $2~/PQ/ {sum+=$3; count++} END {print "PQ平均:", sum/count, "ms"}' phase3_sagin_cbt.csv
```

## 与Phytium Pi结果对比

### Phytium Pi测试结果（无网络模拟）

```
平均Classic NTOR CBT:    1.96 ms
平均PQ-NTOR CBT:         0.79 ms
PQ开销倍数:              0.40×  ⚠️ 异常（PQ反而更快）
```

**问题**: 所有拓扑结果一致，证明网络模拟未生效

### WSL2预期结果（真实网络模拟）

**预期**:
- 不同拓扑应该显示明显差异
- 高延迟拓扑（5.46ms）> 低延迟拓扑（2.72ms）
- 高丢包拓扑会有更大的标准差和最大值
- PQ-NTOR开销应在1.2-2.5×之间（合理范围）

## 故障排除

### 问题1: "RTNETLINK answers: Operation not permitted"

**原因**: 没有root权限
**解决**: 使用 `sudo ./run_phase3_with_sudo.sh`

### 问题2: "Specified qdisc kind is unknown"

**原因**: netem模块未加载
**解决**: `sudo modprobe sch_netem`

### 问题3: 结果显示所有拓扑性能相同

**原因**: tc配置未生效或权限不足
**验证**: 测试期间运行 `sudo tc qdisc show dev lo`

### 问题4: "Cannot find device lo"

**原因**: WSL2网络配置问题
**解决**: 使用其他网络接口（如eth0）或重启WSL2

## 下一步

运行完成后：

1. **查看完整结果**:
   ```bash
   cat /home/ccc/pq-ntor-experiment/essay/phase3_results_wsl2_*/phase3_sagin_cbt.csv
   ```

2. **生成可视化图表**:
   ```bash
   cd /home/ccc/pq-ntor-experiment/essay
   python3 visualize_phase3.py
   ```

3. **综合分析Phase 1+2+3**:
   ```bash
   python3 comprehensive_analysis.py
   ```

4. **撰写论文实验章节**

## 技术说明

### 为什么使用lo（loopback）接口

- **优势**: 无外部网络依赖，完全可控
- **性能**: 无实际网络传输，纯本地通信
- **稳定性**: 不受外部网络波动影响
- **准确性**: tc/netem可以精确控制lo接口参数

### netem模拟原理

```bash
# netem在内核层面模拟网络特性
tc qdisc add dev lo root netem \
  delay 5.46ms \     # 固定延迟
  loss 2.0%          # 随机丢包率
```

- **延迟**: 数据包在发送前延迟指定时间
- **丢包**: 按概率随机丢弃数据包
- **实时性**: 内核级别处理，延迟<1μs

### 与Phytium Pi方案对比

| 特性 | Phytium Pi | WSL2 |
|------|-----------|------|
| 内核支持 | ❌ netem不可用 | ✅ 完整支持 |
| 编译时间 | 快（ARM @ 2.3GHz） | 快（x86 @ 更高频率） |
| 网络模拟 | ❌ 无法生效 | ✅ 完全生效 |
| 论文价值 | ⚠️ 被质疑 | ✅ 真实网络测试 |

## 文件清单

- `/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase3_sagin_network` - 测试程序
- `/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/run_phase3_with_sudo.sh` - 自动化运行脚本
- `/home/ccc/pq-ntor-experiment/essay/phase3_results_wsl2_*/` - 结果目录
- `/home/ccc/pq-ntor-experiment/essay/Phase3_WSL2运行指南.md` - 本文档

## 总结

✅ **WSL2是完美的解决方案**:
- 内核完整支持tc/netem
- 无需购买新硬件
- 测试结果可信度高
- 满足论文对真实网络模拟的要求

**立即运行**:
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
sudo ./run_phase3_with_sudo.sh
```
