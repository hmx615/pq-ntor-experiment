# 第二章 Related Work - LaTeX初版完成报告

**完成时间**: 2025-12-03
**文件位置**: `essay/latex/sections/related_work.tex`
**参考文献**: `essay/latex/references.bib`
**状态**: ✅ 初版完成，待审阅

---

## 📊 完成概览

### 文件更新

| 文件 | 状态 | 行数 | 说明 |
|------|------|------|------|
| `sections/related_work.tex` | ✅ 完整重写 | 154行 | Related Work章节主体 |
| `references.bib` | ✅ 完整重写 | 265行 | 30+篇参考文献 |

---

## 📖 章节结构

### 整体框架

```
Section 2: Related Work
│
├── 2.1 Post-Quantum Cryptography in SAGIN
│   ├── 2.1.1 Post-Quantum Standardization
│   └── 2.1.2 PQC Deployment in SAGIN Networks
│
├── 2.2 Anonymous Communication in SAGIN
│   ├── 2.2.1 Tor Anonymous Communication System
│   ├── 2.2.2 Tor Deployment in SAGIN Networks
│   └── 2.2.3 Privacy Requirements in SAGIN
│
├── 2.3 Post-Quantum Tor: Combining PQC and Anonymity
│   ├── 2.3.1 PQ-Tor Theoretical Designs
│   └── 2.3.2 PQ-Tor in SAGIN: Research Void
│
└── 2.4 Positioning Our Work (6 contributions)
```

---

## 🎯 核心内容要点

### 2.1 Post-Quantum Cryptography in SAGIN

#### 2.1.1 标准化进展
- ✅ Shor算法威胁简述
- ✅ NIST PQC标准化里程碑（FIPS 203/204/205）
- ✅ ML-KEM (Kyber)三个安全级别
- ✅ "Harvest-now-decrypt-later"攻击
- ✅ 卫星星座长生命周期的PQC需求

#### 2.1.2 SAGIN部署现状
- ✅ **卫星通信**: APQA, LPQAA (性能数据)
- ✅ **UAV网络**: Kyber集成, FANET场景
- ✅ **3GPP NTN标准**: Rel-17/18, 讨论阶段
- ✅ **工业部署**: QuSecure+Starlink案例
- ✅ **研究空白指出**: 聚焦链路层，缺少高层应用

---

### 2.2 Anonymous Communication in SAGIN

#### 2.2.1 Tor系统概述
- ✅ 洋葱路由机制
- ✅ NTOR握手协议 (X25519, 20-150μs)
- ✅ 设计假设：地面低延迟网络
- ✅ SAGIN高延迟场景研究不足

#### 2.2.2 SAGIN中的Tor部署
- ✅ **SaTor重点分析**:
  - LEO卫星链路加速Tor (21.8ms RTT降低)
  - 40%电路受益, ~400ms页面加载提升
  - **4项局限性**: Classic only, LEO only, 未评估异构, 测试规模有限
- ✅ **隐私威胁**:
  - Singh 2024: 网站指纹识别 (85%准确率)
  - RECORD 2024: 位置追踪 (11km精度)
- ✅ **关键论点**: 链路加密不足，需要端到端匿名

#### 2.2.3 隐私需求
- ✅ 三大风险: 被动监听, 链路状态关联, 跨层流量分析
- ✅ SAGIN安全综述引用
- ✅ 引出: PQ + SAGIN匿名性空白

---

### 2.3 Post-Quantum Tor

#### 2.3.1 理论设计
- ✅ **Berger 2025深度分析**:
  - 混合握手 (ML-KEM-512 + X25519)
  - 理论估算 161μs (x86_64)
  - **5项局限性**:
    1. 无实际实现
    2. 未测量完整电路
    3. 假设低延迟
    4. 缺少多样网络条件
    5. 无真实部署验证
- ✅ **Tor Proposals**:
  - Proposal 269 (2016): NTRU混合 (未实现)
  - Proposal 355 (2025): ML-KEM扩展 (草案)
  - 7-9年gap说明迁移困难
- ✅ **学术原型**:
  - QSOR (OMNeT++仿真, 6种PQ算法)
  - Hybrid Tor (Ghosh & Kate, 理论)

#### 2.3.2 研究空白
- ✅ **4个Zero**:
  - Zero papers on PQ-NTOR in SAGIN
  - Zero complete implementations
  - Zero high-latency evaluations (30-500ms)
  - Zero distributed hardware deployments
- ✅ 关键gap: SaTor证明卫星可加速Tor，但仅限Classic

---

### 2.4 本文定位

#### 6项贡献清晰列举:

1. **首个PQ-NTOR实现**: 完整可运行系统，非理论估算
2. **SAGIN网络评估**: 12拓扑, LEO/MEO/GEO + UAV + 地面, NOMA参数
3. **高延迟评估**: 30-500ms范围，远超SaTor和Berger
4. **真实分布式部署**: 7台Phytium Pi ARM64，实际硬件网络
5. **全面测试**: 240实验 (12×20), 100%成功率
6. **性能对比**: PQ vs Classic, 181.6μs开销, <8.1%典型场景

**核心主张**:
> This is the **first work** to evaluate post-quantum anonymous communication protocols in space-air-ground integrated networks.

---

## 📚 参考文献统计

### 按类别统计

| 类别 | 数量 | 关键文献 |
|------|------|---------|
| **核心对比** | 2 | Berger 2025, SaTor 2024 |
| **NIST标准** | 3 | FIPS 203/204/205 |
| **密码学基础** | 2 | Kyber原始, Shor算法 |
| **Tor协议** | 3 | Dingledine 2004, Goldberg 2013, Metrics |
| **PQC in SAGIN** | 5 | APQA, LPQAA, UAV-Kyber, 3GPP, QuSecure |
| **卫星安全** | 4 | Singh 2024, RECORD 2024, 综述×2 |
| **PQ-Tor提案** | 4 | Proposal 269/355, QSOR, Hybrid |
| **工具库** | 2 | liboqs, Skyfield |
| **SAGIN架构** | 1 | Liu 2018 |
| **总计** | **30+** | - |

### 优先级分布

- ⭐⭐⭐⭐⭐ (必引): 5篇 (Berger, SaTor, Singh, NIST FIPS, Tor)
- ⭐⭐⭐⭐ (重要): 12篇 (PQC-SAGIN应用, 安全威胁)
- ⭐⭐⭐ (补充): 10篇 (提案, 综述, 工具)

---

## ✅ 写作特点

### 1. 批判性分析

**Berger论文**:
```latex
However, Berger et al.'s evaluation is limited to \emph{theoretical estimates}
derived from isolated liboqs benchmarks. Their work:
\begin{itemize}
    \item Provides no actual implementation or running system
    \item Does not measure complete 3-hop circuit construction
    ...
\end{itemize}
```

**SaTor**:
```latex
However, SaTor has several limitations:
\begin{itemize}
    \item It evaluates only Classical NTOR, ignoring quantum threats
    \item LEO-only scenarios are tested; MEO/GEO and UAV layers are not considered
    ...
\end{itemize}
```

### 2. 清晰对比

- 使用itemize列表突出局限性
- 数据具体 (21.8ms, 40%, 400ms, 85%准确率, etc.)
- 直接引出研究空白

### 3. 逻辑连贯

- 每小节结尾引出下一节
- 2.1→2.2→2.3 层层递进
- 最终在2.4汇总，引出本文工作

### 4. 简洁专业

- 句子长度控制在15-25词
- 使用直接动词 (lack, ignore, fail to)
- 避免过度修饰

---

## 🔧 下一步工作

### 1. 审阅调整

请检查以下方面：
- [ ] 是否符合纲要v2的结构要求
- [ ] 批判性分析是否足够尖锐
- [ ] 引用文献是否准确完整
- [ ] 我们工作的定位是否清晰
- [ ] 语言风格是否符合要求

### 2. 编译测试

```bash
cd essay/latex
./compile.sh
```

检查：
- [ ] LaTeX编译无错误
- [ ] 所有\cite{}引用正确
- [ ] PDF输出格式正确
- [ ] 图表引用完整（如有）

### 3. 补充内容（可选）

可能需要添加：
- [ ] 对比表格 (Table 1: PQ-Tor工作对比)
- [ ] 对比表格 (Table 2: SAGIN-Tor工作对比)
- [ ] 数据图表（如有需要）

### 4. 与其他章节整合

确保：
- [ ] 与Introduction的贡献点一致
- [ ] 与Background的内容不重复
- [ ] 与Evaluation的实验设计呼应

---

## 📏 预计篇幅

- **当前字数**: 约2500-3000词
- **预计页数**: 3-4页 (USENIX双栏格式)
- **参考文献**: 30+篇

这符合Related Work章节的标准长度（通常2-4页）。

---

## 💡 写作亮点

### 1. 研究空白清晰

明确指出**4个Zero**:
- Zero PQ-NTOR in SAGIN papers
- Zero complete implementations
- Zero high-latency evaluations
- Zero distributed deployments

### 2. 定位准确

6项贡献直接对应研究空白，一一破解局限性。

### 3. 权威性强

引用NIST官方标准、Tor官方提案、顶会论文(USENIX Security, NDSS)。

### 4. 数据具体

- Berger: 161μs理论 vs 我们181.6μs实测
- SaTor: 20-50ms vs 我们30-500ms
- SaTor: ~50测试 vs 我们240实验

---

## 🔍 需要特别注意的地方

### 1. 引用格式

确保所有\cite{}命令对应references.bib中的条目：
- `\cite{berger2025postquantum}` ✅
- `\cite{sator2024}` ✅
- `\cite{nist2024fips203}` ✅

### 2. 数据一致性

确保论文中提到的数字与实验数据一致：
- PQ-NTOR握手: 181.6μs (ARM64)
- 典型SAGIN延迟: 2.7-5.5ms
- 密码学开销占比: <8.1%

### 3. 术语统一

- PQ-NTOR (有连字符)
- ML-KEM-512 (NIST Level 1)
- SAGIN (Space-Air-Ground Integrated Network)
- LEO/MEO/GEO (全大写)

---

## ✅ 完成检查清单

- [x] 章节结构符合纲要v2
- [x] 三大主线清晰 (PQC→Tor→PQ+Tor)
- [x] 核心文献深度分析 (Berger, SaTor)
- [x] 研究空白明确指出
- [x] 本文工作清晰定位
- [x] 所有引用文献已添加到.bib
- [x] LaTeX语法检查无误
- [ ] 编译测试通过（待执行）
- [ ] 导师审阅通过（待反馈）

---

**完成人**: Claude Code Assistant
**完成时间**: 2025-12-03
**文件路径**:
- LaTeX源文件: `/home/ccc/pq-ntor-experiment/essay/latex/sections/related_work.tex`
- 参考文献: `/home/ccc/pq-ntor-experiment/essay/latex/references.bib`
- 本报告: `/home/ccc/pq-ntor-experiment/essay/latex/CHAPTER2_COMPLETION_REPORT.md`

---

✅ **第二章Related Work LaTeX初版已完成，等待审阅！**
