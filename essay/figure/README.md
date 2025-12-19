# PQ-NTOR SAGIN 实验图表目录

本目录包含论文实验的所有可视化图表。

---

## 三阶段实验设计

| 阶段 | 名称 | 内容 | 图表数量 |
|------|------|------|----------|
| Phase 1 | 密码学原语基准测试 | ML-KEM/HKDF/HMAC独立性能 | **3张** |
| Phase 2 | 文献对比 | 4平台握手性能对比 | **3张** |
| Phase 3 | SAGIN端到端测试 | 12拓扑CBT分析（三协议） | **10张** |

**总计: 16张PDF图表**

---

## 协议支持

Phase 3 所有图表现已支持**三种协议**对比：

| 协议 | 算法 | 图表颜色 |
|------|------|----------|
| Classic NTOR | X25519 ECDH | 蓝色 |
| PQ-NTOR | ML-KEM-768 (Kyber) | 红色 |
| Hybrid NTOR | X25519 + ML-KEM-768 | 绿色 |

---

## Phase 1: 密码学原语基准测试 (3张图)

在飞腾派平台上测试各密码学操作的独立性能。

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 图1-1 | `phase1_fig1_crypto_performance.pdf` | 性能柱状图（含误差棒） |
| 图1-2 | `phase1_fig2_crypto_breakdown.pdf` | 操作时间分解饼图 |
| 图1-3 | `phase1_fig3_crypto_statistics.pdf` | 统计信息汇总表 |

**数据来源**: `/sagin-experiments/docker/build_context/c/phase1_crypto_benchmarks.csv`

**测试操作**:
| 操作 | 平均时间 (µs) | 说明 |
|------|--------------|------|
| Kyber-512 Keygen | 6.68 | 密钥生成 |
| Kyber-512 Encaps | 8.78 | 封装 |
| Kyber-512 Decaps | 5.92 | 解封装 |
| HKDF-SHA256 | 3.31 | 密钥派生 |
| HMAC-SHA256 | 1.11 | 消息认证 |

---

## Phase 2: 文献对比 (3张图)

与文献中不同平台的握手性能对比。

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 图2-1 | `phase2_fig1_handshake_comparison.pdf` | 4平台握手时间对比柱状图 |
| 图2-2 | `phase2_fig2_overhead_comparison.pdf` | PQ-NTOR相对开销倍数对比 |
| 图2-3 | `phase2_fig3_summary_table.pdf` | 性能汇总表格 |

**对比平台**:
- Intel x86 (Tor官方实现)
- Hardware Research (硬件优化实现)
- Raspberry Pi 4
- 飞腾派 (本文实现)

---

## Phase 3: SAGIN网络端到端测试 (10张图)

12种SAGIN拓扑下的Circuit Build Time (CBT)对比分析，支持**三种协议**。

| 图表 | 文件名 | 说明 |
|------|--------|------|
| 图3-1 | `phase3_fig1_cbt_comparison.pdf` | 三协议CBT柱状对比图 |
| 图3-2 | `phase3_fig2_overhead_ratio.pdf` | **折线+柱状图**：Classic基准柱 + PQ/Hybrid开销折线 |
| 图3-3 | `phase3_fig3_absolute_overhead.pdf` | 绝对开销对比 (ms) |
| 图3-4 | `phase3_fig4_cbt_breakdown.pdf` | CBT组成分解堆叠图 |
| 图3-5 | `phase3_fig5_network_ratio.pdf` | 网络延迟占比对比（三协议） |
| 图3-6 | `phase3_fig6_overhead_vs_bandwidth.pdf` | 开销 vs 带宽散点图 |
| 图3-7 | `phase3_fig7_overhead_vs_delay.pdf` | 开销 vs 延迟散点图 |
| 图3-8 | `phase3_fig8_bandwidth_category.pdf` | 按带宽分类汇总 |
| 图3-9 | `phase3_fig9_best_worst_scenarios.pdf` | 最佳/最差场景对比 |
| 图3-10 | `phase3_fig10_summary_table.pdf` | 三协议性能汇总表 |

**数据来源**: `/sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl/phase3_sagin_cbt_with_network_20251216.csv`

### 关键发现 (三协议对比)

| 指标 | Classic NTOR | PQ-NTOR | Hybrid NTOR |
|------|-------------|---------|-------------|
| 平均CBT | ~19.4 ms | ~19.3 ms | ~19.9 ms |
| 平均开销 | 1.000× | ~0.99× | ~1.03× |
| 网络占比 | ~83.8% | ~84.4% | ~81.5% |

---

## 12种SAGIN拓扑

### 上行链路 (topo01-06)
| 拓扑 | 描述 | 带宽 | 延迟 | 丢包率 |
|------|------|------|------|--------|
| topo01 | Z1 Up - 直连NOMA | 123.89 Mbps | 2.71 ms | 5.0% |
| topo02 | Z2 Up - T协作接入 | 59.73 Mbps | 2.72 ms | 5.0% |
| topo03 | Z3 Up - T用户协作NOMA | 102.76 Mbps | 2.71 ms | 2.0% |
| topo04 | Z4 Up - 混合直连+协作 | 95.02 Mbps | 2.72 ms | 5.0% |
| topo05 | Z5 Up - 多层树形结构 | 102.76 Mbps | 2.71 ms | 5.0% |
| topo06 | Z6 Up - 双UAV中继+T | 91.33 Mbps | 2.72 ms | 2.0% |

### 下行链路 (topo07-12)
| 拓扑 | 描述 | 带宽 | 延迟 | 丢包率 |
|------|------|------|------|--------|
| topo07 | Z1 Down - 直连NOMA+协作 | 192.18 Mbps | 2.71 ms | 3.0% |
| topo08 | Z2 Down - T协作接入+协作 | 177.95 Mbps | 2.71 ms | 3.0% |
| topo09 | Z3 Down - T用户协作下行 | 125.97 Mbps | 2.71 ms | 1.0% |
| topo10 | Z4 Down - 混合直连+协作 | 118.22 Mbps | 2.72 ms | 3.0% |
| topo11 | Z5 Down - NOMA接收+转发 | 27.04 Mbps | 2.71 ms | 3.0% |
| topo12 | Z6 Down - 双中继NOMA+协作 | 22.98 Mbps | 2.72 ms | 3.0% |

---

## 其他文档

| 文件 | 说明 |
|------|------|
| `EXPERIMENT_PARAMETERS.md` | 完整实验参数文档（功率、带宽、12拓扑参数） |
| `SHIMEI_MODEL_PARAMETERS.md` | 师妹NOMA物理层模型参数 |

---

## 图表生成脚本

```bash
python3 /home/ccc/pq-ntor-experiment/essay/visualize_comprehensive_comparison_pdf.py
```

---

*更新时间: 2025-12-16*
