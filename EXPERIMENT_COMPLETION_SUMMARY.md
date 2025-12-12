# 12拓扑实验完成总结

**日期**: 2025-12-11
**状态**: ⚠️ 实验已完成但所有测试超时

---

## 实验执行情况

### ✅ 成功部分
1. **修复了关键bug** - directory_server.c的IP地址硬编码问题
2. **所有服务正常启动** - Directory, HTTP服务器, Guard/Middle/Exit Relays
3. **TC网络参数正确配置** - 12个拓扑的delay/bandwidth/loss都已正确设置
4. **完成了12个拓扑测试** - 每个拓扑运行10次

### ⚠️ 问题部分
**所有测试超时** - 120/120 测试 (12拓扑 × 10次) 全部超时

```
总结:
- Topo01-12: 0/10 成功
- 总成功率: 0%
- 总运行时间: ~60分钟 (每个测试30秒超时 × 120次测试)
```

---

## 问题分析

### 客户端超时原因

从手动测试中我们知道，**没有TC网络损伤时**，客户端可以成功建立电路并获取数据:

```
[Client] 3-hop circuit established!
[Client] Received 1205 bytes of data
```

但是当启用TC网络损伤后（例如5.42ms延迟 + 59.27Mbps限速 + 3%丢包），客户端超过30秒未完成。

### 可能的原因

1. **TCP重传** - 3%丢包率导致大量TCP重传
2. **带宽限制** - PQ-NTOR使用较大的密钥材料（Kyber公钥~800字节），在低带宽下传输慢
3. **延迟累积** - 3跳电路，每跳5.42ms延迟会累积
4. **客户端等待逻辑** - 客户端可能在等待更多数据而不是在收到响应后立即结束

---

## 数据收集状态

### 已保存的数据
虽然测试超时，但仍然收集到了以下数据：

```bash
ls -1 sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl/
```

输出：
- `topo01_results.json` through `topo12_results.json` (12个文件)
- 每个文件包含：
  - 拓扑配置（TC参数）
  - 10次测试结果（均为timeout）
  - 汇总统计

### 缺失的数据
- ❌ 实际的CBT (Circuit Build Time)
- ❌ 端到端延迟测量
- ❌ 吞吐量数据
- ❌ 成功率数据

---

## 建议的解决方案

### 方案1: 增加超时时间 (推荐)
修改 `run_simple_test.py:126`:
```python
# 当前
timeout=30

# 修改为
timeout=120  # 2分钟，考虑到网络损伤
```

### 方案2: 优化客户端逻辑
客户端可能在等待EOF或更多数据。修改客户端在收到HTTP响应后立即结束。

### 方案3: 禁用TC测试（仅功能测试）
先不启用TC，验证基本功能：
```python
# 在 configure_tc() 中注释掉TC命令
# 仅测试功能，不测试性能
```

### 方案4: 降低TC损伤参数
使用更温和的网络条件进行初步测试：
```bash
# 降低丢包率和延迟
sudo tc qdisc add dev lo root netem delay 1ms rate 100mbit loss 0.1%
```

---

## 下一步行动

### 立即可做
1. **修改超时时间**到120秒并重新运行单个拓扑测试
2. **检查客户端代码**，了解为什么在收到数据后不立即结束
3. **禁用TC重新测试**，验证基本功能无问题

### 实验建议
由于本地WSL2测试的限制，建议：
1. **降低测试规模** - 先测试1-2个拓扑，确保能成功
2. **逐步增加TC损伤** - 从无损伤 → 轻微损伤 → 实际SAGIN参数
3. **使用7π物理集群** - 真实网络环境可能比TC模拟更可靠

---

## 技术细节

### 网络参数总览

| 拓扑 | 方向 | 延迟(ms) | 带宽(Mbps) | 丢包(%) |
|------|------|---------|-----------|---------|
| Topo01 | Uplink | 5.42 | 59.27 | 3.00 |
| Topo02 | Uplink | 5.42 | 16.55 | 3.00 |
| Topo03 | Uplink | 2.72 | 25.19 | 1.00 |
| Topo04 | Uplink | 5.42 | 23.64 | 3.00 |
| Topo05 | Uplink | 5.43 | 25.19 | 3.00 |
| Topo06 | Uplink | 5.42 | 22.91 | 1.00 |
| Topo07 | Downlink | 5.42 | **69.43** | 2.00 |
| Topo08 | Downlink | 5.43 | 38.01 | 2.00 |
| Topo09 | Downlink | 2.72 | 29.84 | 0.50 |
| Topo10 | Downlink | 5.42 | 18.64 | 2.00 |
| Topo11 | Downlink | 5.43 | 9.67 | 2.00 |
| Topo12 | Downlink | 5.43 | 8.73 | 2.00 |

**预期**: Topo07（Downlink，69.43Mbps）应该比Topo01（Uplink，59.27Mbps）更快。

---

## 结论

### 已完成
✅ 识别并修复IP地址硬编码bug
✅ 正确配置12个拓扑的TC网络参数
✅ 验证所有服务可以正常启动
✅ 收集到拓扑配置数据（虽然测试超时）

### 未完成
❌ 获取实际的性能测量数据（CBT, 延迟, 吞吐量）
❌ 验证Downlink vs Uplink的性能差异

### 核心问题
**客户端在TC网络损伤环境下超时** - 需要增加超时时间或优化客户端代码。

---

## 文件位置

- 实验日志: `/tmp/12topo_full_experiment.log`
- 结果数据: `sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl/topo*.json`
- 测试脚本: `sagin-experiments/pq-ntor-12topo-experiment/scripts/run_simple_test.py`
- 调试报告: `/home/ccc/pq-ntor-experiment/FINAL_DEBUGGING_REPORT.md`

---

**生成时间**: 2025-12-11 12:45 UTC+8
