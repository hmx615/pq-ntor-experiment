# PQ-Tor SAGIN 论文写作工作区

**创建日期**: 2025-11-27
**目标**: 撰写高质量学术论文，投稿 USENIX Security / ACM CCS / IEEE INFOCOM

---

## 📁 文件夹内容

### 核心文档

| 文件 | 用途 | 状态 |
|------|------|------|
| **实验设计写作指南.md** | 实验设计章节写作指导 | ✅ 完成 |
| **性能对比分析报告.md** | 与Berger论文性能对比 | ✅ 完成 |
| **参考文献管理.md** | BibTeX引用与文献分析 | ✅ 完成 |
| **2503.10238v1.pdf** | Berger论文PDF | ✅ 已收录 |
| **README.md** | 本文件，工作区导航 | ✅ 当前 |

### 待创建文档

- [ ] `论文大纲.md` - 完整论文结构规划
- [ ] `实验章节草稿.md` - Section 5 初稿
- [ ] `相关工作草稿.md` - Section 2 初稿
- [ ] `系统设计草稿.md` - Section 3-4 初稿
- [ ] `图表规划.md` - 所有图表的设计方案
- [ ] `结果数据汇总.md` - 实验数据整理

---

## 🎯 论文核心卖点

### 我们的工作 vs Berger et al. [2025]

| 维度 | Berger论文 | 我们的工作 | 创新性 |
|------|-----------|----------|--------|
| **PQ-NTOR实现** | ❌ 理论估算 | ✅ **完整C实现** | ⭐⭐⭐⭐⭐ |
| **握手性能** | 161 μs (估算) | **31 μs** (实测) | ⭐⭐⭐⭐⭐ |
| **网络场景** | 单一拓扑 | **12种拓扑** | ⭐⭐⭐⭐ |
| **SAGIN集成** | ❌ 无 | ✅ **LEO/MEO/GEO** | ⭐⭐⭐⭐⭐ |
| **卫星模拟** | ❌ 无 | ✅ **Skyfield真实轨道** | ⭐⭐⭐⭐⭐ |
| **对比实验** | ❌ 无 | ✅ **Classic vs PQ** | ⭐⭐⭐⭐ |
| **测试规模** | ~50次 | **240次** | ⭐⭐⭐ |

### 核心贡献（Abstract中强调）

1. ✅ **首个完整PQ-NTOR实现** - 真实握手31 μs，非理论拼凑
2. ✅ **SAGIN网络集成** - 首次将PQ-Tor应用于空天地网络
3. ✅ **真实卫星轨道模拟** - Skyfield + TLE数据 + 可见性窗口
4. ✅ **全面性能验证** - 240次测试，12种拓扑，100%成功率
5. ✅ **开源可复现** - 完整代码 + 自动化脚本 + ARM64部署

---

## 📊 论文结构规划

### 推荐结构（USENIX Security风格）

```
1. Introduction (1.5页)
   - Motivation: Quantum threat to Tor
   - Problem: How to migrate Tor to post-quantum era
   - Challenge: SAGIN高延迟网络的特殊挑战
   - Contribution: 4-5个核心贡献

2. Background (1页)
   - Tor NTOR handshake (简述)
   - Post-quantum KEM (Kyber-512)
   - SAGIN network architecture

3. PQ-NTOR Design (2页)
   - Protocol specification
   - Security properties
   - Implementation choices

4. System Implementation (1.5页)
   - Architecture overview
   - Kyber integration (liboqs)
   - SAGIN network simulation

5. Evaluation (4-5页)  ← 核心章节
   - 5.1 Experimental Setup
   - 5.2 Phase 1: Handshake Benchmarks
   - 5.3 Phase 2: SAGIN Integration
   - 5.4 Phase 3: Classic vs PQ Comparison
   - 5.5 Discussion

6. Related Work (1.5页)
   - PQC for Tor [Berger2025, ...]
   - NIST standardization
   - SAGIN networks

7. Conclusion (0.5页)
   - Summary
   - Future work (hybrid mode, ARM optimization)

Total: ~12-14页 (USENIX双栏格式)
```

---

## 📈 关键实验数据总结

### Phase 1: Handshake Performance

**数据来源**: `benchmark_results.csv`

| 指标 | 值 | 对比Berger论文 |
|------|-----|---------------|
| Full Handshake (avg) | 31.00 μs | 161 μs (理论) → **5.2× 更快** |
| Client Create | 5.53 μs | 43 μs → **7.8× 更快** |
| Server Reply | 13.72 μs | 52 μs → **3.8× 更快** |
| Client Finish | 12.28 μs | 66 μs → **5.4× 更快** |
| Throughput | 32,258 hs/s | 6,200 hs/s → **5.2× 更高** |
| Std Dev | 3.90 μs | 未报告 |

**关键图表**:
- Figure 1: Handshake latency box plot (4个操作)
- Figure 2: CDF of full handshake time
- Table 1: Performance statistics summary

---

### Phase 2: SAGIN Network Integration

**数据来源**: `sagin-experiments/results/*.csv`

**12种拓扑**:
1. Pure Terrestrial (baseline)
2. LEO Satellite (1-hop)
3. LEO Multi-hop
4. MEO Satellite
5. GEO Satellite
6. LEO + MEO Hybrid
7. LEO + Ground Hybrid
8. 3-tier SAGIN (LEO+MEO+Ground)
9. ... (其他变体)

**关键发现**:
- PQ-NTOR延迟在LEO场景中占比 < 0.2% (31 μs vs 10 ms RTT)
- GEO场景中完全可忽略 (31 μs vs 250 ms RTT)

**关键图表**:
- Figure 3: Circuit Build Time across 12 topologies
- Figure 4: SAGIN link delay impact (LEO/MEO/GEO)
- Figure 5: Satellite visibility window + handshake timing
- Table 2: 12 topologies detailed configuration

---

### Phase 3: Classic vs PQ-NTOR

**数据来源**: `sagin-experiments/pq-ntor-12topo-experiment/results/comparison/`

**测试规模**:
- 12 topologies × 2 modes (Classic, PQ) × 10 trials = 240 tests
- Success rate: **100%** (240/240)

**关键发现**:
- Bandwidth overhead: 10.9× (预期，Kyber密钥大)
- Latency overhead: < 1% in SAGIN scenarios
- Both modes: 100% success rate

**关键图表**:
- Figure 6: Classic vs PQ CDF comparison
- Figure 7: Overhead breakdown (computation vs communication)
- Table 3: Statistical comparison (t-test, p-value, effect size)

---

## 🎓 目标期刊分析

### USENIX Security

**适合度**: ⭐⭐⭐⭐⭐ (最推荐)

**优势**:
- ✅ 重视系统实现（我们有完整实现）
- ✅ 接受网络安全主题（PQ-Tor）
- ✅ 欣赏实验驱动研究（240次测试）
- ✅ 12-14页篇幅合适

**类似已发表论文**:
- Onion routing security
- Post-quantum TLS (KEMTLS)
- Network anonymity systems

**写作建议**:
- 强调系统实现细节
- 提供完整性能评估
- 讨论真实部署可行性

---

### ACM CCS

**适合度**: ⭐⭐⭐⭐

**优势**:
- ✅ 顶级密码学会议
- ✅ PQC主题契合
- ✅ 接受应用密码学

**挑战**:
- ⚠️ 更偏理论/证明（我们偏工程）
- ⚠️ 竞争更激烈

**写作建议**:
- 补充安全性证明（PQ-NTOR协议安全性）
- 强调密码学正确性

---

### IEEE INFOCOM

**适合度**: ⭐⭐⭐⭐⭐ (次推荐)

**优势**:
- ✅ SAGIN主题非常契合！
- ✅ 网络性能评估是重点
- ✅ 接受系统实现

**写作建议**:
- 强调SAGIN网络创新
- 详细讨论网络拓扑设计
- 突出卫星轨道模拟

---

## 📝 写作进度跟踪

### 已完成的准备工作

- [x] 性能数据收集（benchmark_results.csv）
- [x] SAGIN实验数据（12种拓扑，240次测试）
- [x] Classic vs PQ对比数据
- [x] 参考文献整理（Berger论文分析）
- [x] 实验设计框架规划
- [x] 核心创新点梳理

### 待完成的写作任务

#### 第一阶段：大纲与草稿（预计3-5天）

- [ ] **论文大纲** - 完整的章节结构
- [ ] **Section 1: Introduction** - 草稿
- [ ] **Section 5: Evaluation** - 草稿（最重要）
- [ ] **图表设计方案** - 所有图表的mockup

#### 第二阶段：技术章节（预计5-7天）

- [ ] **Section 3: PQ-NTOR Design** - 协议设计
- [ ] **Section 4: Implementation** - 系统实现
- [ ] **Section 2: Background** - 背景知识
- [ ] **Section 6: Related Work** - 相关工作

#### 第三阶段：图表与数据（预计3-5天）

- [ ] 生成所有性能图表（Python + matplotlib）
- [ ] 创建网络拓扑示意图
- [ ] 绘制系统架构图
- [ ] 制作所有表格

#### 第四阶段：打磨与投稿（预计5-7天）

- [ ] Abstract 打磨（最后写）
- [ ] Introduction 优化
- [ ] 全文润色（语法、逻辑）
- [ ] 格式化（USENIX LaTeX模板）
- [ ] 内部审阅
- [ ] 提交投稿

**总预计时间**: 3-4周

---

## 🔧 工具与资源

### LaTeX 模板

```bash
# USENIX Security模板
wget https://www.usenix.org/sites/default/files/usenix2025_v3.2.tar.gz
tar xzf usenix2025_v3.2.tar.gz
```

### 图表生成工具

**Python脚本**（已存在）:
- `sagin-experiments/pq-ntor-12topo-experiment/scripts/visualize_results.py`
- `c/benchmark/visualize.py`

**需要创建的新图表**:
- CDF plot (Classic vs PQ)
- Multi-topology comparison bar chart
- SAGIN delay impact heatmap
- Satellite visibility window timeline

### 数据分析

**已有数据**:
- `c/benchmark_results.csv` - Phase 1数据
- `sagin-experiments/results/*.csv` - Phase 2数据
- `sagin-experiments/pq-ntor-12topo-experiment/results/comparison/*.json` - Phase 3数据

**分析工具**:
- Pandas (数据处理)
- NumPy (统计分析)
- SciPy (t-test, 置信区间)
- Matplotlib/Seaborn (可视化)

---

## 📞 下一步建议

### 立即开始

1. **创建论文大纲** (`论文大纲.md`)
   - 完整的章节结构
   - 每节的关键点列表
   - 字数分配规划

2. **撰写Section 5.1 Experimental Setup**
   - 硬件配置表格
   - 软件栈描述
   - 12种拓扑详细说明

3. **设计关键图表**
   - Phase 1: Handshake performance (2-3个图)
   - Phase 2: SAGIN integration (3-4个图)
   - Phase 3: Comparison (2-3个图)

### 本周目标

- [ ] 完成论文大纲
- [ ] 完成实验设计章节初稿（Section 5.1-5.2）
- [ ] 生成Phase 1的所有图表

---

## 📚 参考资源

### 已读论文

- ✅ **Berger et al. 2025** - Post Quantum Migration of Tor
  - PDF: `essay/2503.10238v1.pdf`
  - 笔记: `essay/性能对比分析报告.md`

### 待读论文（补充相关工作）

- [ ] KEMTLS (USENIX Security 2020)
- [ ] Google CECPQ2 (实际部署经验)
- [ ] Tor协议相关（Goldberg 2013）
- [ ] SAGIN架构综述（Liu 2018）

### 写作指南

- [USENIX Security写作风格](https://www.usenix.org/conferences/author-resources/paper-templates)
- [How to write a systems paper (SOSP)](https://people.inf.ethz.ch/troscoe/pubs/hotos09-paper.pdf)

---

## 🎯 成功标准

### 论文质量目标

1. **技术贡献明确**
   - ✅ 首个完整PQ-NTOR实现
   - ✅ 首个SAGIN-PQ-Tor集成
   - ✅ 240次实验，100%成功率

2. **实验评估充分**
   - ✅ 三阶段实验设计
   - ✅ 12种网络拓扑
   - ✅ Classic vs PQ对比

3. **写作清晰专业**
   - 逻辑严密，结构清晰
   - 图表丰富，数据可信
   - 语言精炼，无语法错误

4. **可重复性**
   - ✅ 开源代码
   - ✅ 详细实验步骤
   - ✅ 自动化脚本

### 投稿目标

- **首选**: USENIX Security 2026
- **备选**: IEEE INFOCOM 2026
- **保底**: ACM CCS 2026 或其他网络安全会议

---

**创建日期**: 2025-11-27
**最后更新**: 2025-11-27
**维护者**: PQ-Tor SAGIN 项目组

**下一步**: 开始撰写论文大纲！🚀
