# 2.3节 PQ-Tor结合研究 - 详细文献调研报告

**调研日期**: 2025-12-03
**调研范围**: PQ-Tor结合研究及相关PQ网络协议
**调研目的**: 为论文第2.3节提供文献支撑,重点突出现有工作的不足

---

## 📊 调研总结

### 核心发现

**方向1: PQ-Tor + SAGIN结合工作**
- **结论**: ❌ **完全空白** - 未找到任何将PQ-Tor应用于SAGIN环境的研究
- **验证**: 多关键词搜索均无相关结果
- **意义**: 这是明确的研究空白,正是本文的核心创新点

**方向2: 非SAGIN的PQ-Tor研究**
- **核心文献数**: 6篇
- **主要形式**: 理论提案(3篇) + 学术论文(3篇)
- **共同局限**: 无真实网络评估,无SAGIN场景考虑

**方向3: 其他匿名网络的PQ迁移**
- **I2P**: 仅处于早期规划阶段
- **Katzenpost**: 已实现PQ,但属于混合网络(非Tor)

**方向4: 相关PQ网络协议**
- **PQ-TLS**: 性能评估充分,但聚焦Web场景
- **PQ-VPN**: 商业部署已开始,但未涉及匿名性
- **PQ-QUIC**: 研究进展较快,但不适用于Tor
- **PQ-WireGuard**: 已有实现,但VPN场景与Tor差异大

---

## 📚 核心文献详细分析

---

### 【文献1】Post Quantum Migration of Tor (Berger et al., 2025) ⭐⭐⭐

**基本信息**:
- **作者**: Denis Berger, Mouad Lemoudden, William J. Buchanan
- **发表**: MDPI Journal of Cybersecurity and Privacy, Vol 5, Issue 2, April 2025
- **状态**: 已发表论文
- **链接**: https://www.mdpi.com/2624-800X/5/2/13 | arXiv:2503.10238 | ePrint:2025/479

**核心内容**:

1. **研究目标**:
   - 分析Tor中的量子脆弱性密码方案
   - 提出PQ迁移路线图
   - 基于孤立基准进行理论性能估算

2. **技术方案**:
   - **电路层**: 推荐ML-KEM-512/768或sntrup761 (KEM) + Falcon-512或ML-DSA-44 (签名)
   - **链路层**: 推荐混合TLS 1.3
   - **迁移策略**: 增量式、逐层迁移

3. **性能数据**:
   - **ML-KEM-512基准** (孤立测试):
     - x86_64: 38,732 keygen/s, 33,241 encaps/s, 36,170 decaps/s
     - 速度差异: 比X25519慢66%
   - **Raspberry Pi 5**:
     - ML-KEM-512: 0.161 ms/exchange
     - X25519: 0.167 ms/exchange
     - 结论: 在某些ARM平台PQ反而更快
   - **ntor v3握手** (理论):
     - 客户端: 0.67 ms
     - 服务器端: 0.63 ms

4. **测试环境**:
   - 本地Tor网络模拟
   - 受限设备测试
   - 未进行真实网络环境评估

**局限性分析** (对应2.4节6大创新):

| 局限性 | 详细说明 | 对应本文创新 |
|--------|---------|-------------|
| ❌ **局限1**: 仅理论估算 | 基于liboqs基准推算,无完整PQ-NTOR实现 | ✅ 完整实现(181.64 µs实测) |
| ❌ **局限2**: 孤立密码学基准 | 性能数据来自孤立的KEM操作,未测试完整电路构建 | ✅ 三跳电路完整测试(1.25 ms) |
| ❌ **局限3**: 未考虑网络影响 | 未评估延迟、带宽、抖动对PQ-NTOR的影响 | ✅ 12拓扑网络场景(30-500ms) |
| ❌ **局限4**: 假设地面网场景 | 仅考虑传统互联网,未涉及SAGIN | ✅ SAGIN多层异构网络 |
| ❌ **局限5**: 模拟测试 | 本地Tor网络,非真实分布式部署 | ✅ 7飞腾派真实部署 |
| ❌ **局限6**: 无高延迟评估 | 未涵盖卫星网络的高延迟、高抖动场景 | ✅ 延迟全覆盖+NOMA真实参数 |

**对本文的价值**:
- ✅ 提供PQ迁移理论框架
- ✅ 验证ML-KEM在Tor中的可行性
- ⚠️ 但缺少实现与网络评估,正是本文填补的空白

---

### 【文献2】Tor Proposal 269: Transitionally Secure Hybrid Handshakes (2016)

**基本信息**:
- **作者**: John Schanck, William Whyte, Zhenfei Zhang, Nick Mathewson, Isis Lovecruft, Peter Schwabe
- **创建**: 2016年6月7日
- **状态**: Needs-Revision (需要修订)
- **类型**: Tor官方提案
- **链接**: https://spec.torproject.org/proposals/269-hybrid-handshake.html

**核心内容**:

1. **目标**:
   - 将PQ KEM集成到ntor握手中
   - 提供过渡期量子安全

2. **技术方案**:
   - 客户端发送KEM公钥
   - 中继返回封装密钥
   - 混合密钥派生: ECC + KEM → 会话密钥

3. **参数集**:
   - `hybrid-ees443ep2`: 使用NTRUEncrypt ntrueess443ep2
   - `hybrid-newhope`: 使用NewHope R-LWE方案

**局限性**:
- ❌ 仍处于提案阶段,未被采纳实施
- ❌ CREATE单元大小限制(505字节 vs NTRU需要693字节)
- ❌ 需要协议层面修改才能实现
- ❌ 无性能评估数据

**对本文的价值**:
- ✅ 说明Tor社区早已意识到PQ需求
- ⚠️ 但7年后仍无实现,凸显本文实现价值

---

### 【文献3】Tor Proposal 355: Options for Postquantum Circuit Extension (2025)

**基本信息**:
- **作者**: Nick Mathewson
- **创建**: 2025年3月6日
- **状态**: Informational (信息性)
- **类型**: Tor官方提案
- **链接**: https://spec.torproject.org/proposals/355-revisiting-pq.html

**核心内容**:

1. **背景更新**:
   - NIST已发布ML-KEM、ML-DSA、SLH-DSA标准
   - TLS开始支持混合ML-KEM
   - Tor已迁移到ntor v3

2. **方案对比**:
   - **PQ-TR方法**: 过渡期可行,但未来量子攻击可解密
   - **PQ-KEM-2方法**: 下一代推荐,但成本较高

3. **结论**:
   - 近期: PQ-TR可接受
   - 长期: PQ-KEM-2更优

**局限性**:
- ❌ 仅为探索性分析,非实施方案
- ❌ 未提供具体实现指导
- ❌ 无性能评估

**对本文的价值**:
- ✅ 证明PQ迁移仍在讨论阶段
- ✅ 本文实现填补了理论到实践的空白

---

### 【文献4】QSOR: Quantum-Safe Onion Routing (Tujner et al., 2020)

**基本信息**:
- **作者**: Zsolt Tujner, Thomas Rooijakkers, Maran van Heesch, Melek Önen
- **发表**: ICETE 2020 (17th International Joint Conference on e-Business and Telecommunications)
- **类型**: 会议论文
- **链接**: arXiv:2001.03418 | SCITEPRESS

**核心内容**:

1. **研究方法**:
   - 评估6种PQ算法 (NIST L1安全级别)
   - 基于SweetOnions仿真器
   - 聚焦电路创建操作

2. **方案**:
   - 纯PQ版本
   - 混合版本 (Classic + PQ)

3. **主要发现**:
   - PQ-Tor电路创建可行
   - 性能开销可接受

**局限性**:
- ❌ 仅仿真测试,非真实Tor网络
- ❌ 未评估网络环境影响
- ❌ 未考虑SAGIN等特殊网络
- ❌ 基于2020年算法,已过时 (现应使用ML-KEM)

**对本文的价值**:
- ✅ 早期PQ-Tor可行性验证
- ⚠️ 但仿真测试与真实部署差距大

---

### 【文献5】Post-Quantum Forward-Secure Onion Routing (Ghosh & Kate, 2015)

**基本信息**:
- **作者**: Satrajit Ghosh, Aniket Kate
- **发表**: ePrint Archive 2015/008
- **呈现**: NIST PQC Workshop 2015
- **类型**: 学术论文
- **链接**: https://eprint.iacr.org/2015/008

**核心内容**:

1. **HybridOR协议**:
   - 混合1W-AKE协议
   - 结合: ring-LWE + 经典DH
   - 双重安全保证

2. **安全性**:
   - 量子安全: ring-LWE假设
   - 经典安全: gap-DH假设
   - 前向安全

3. **性能声明**:
   - 比ntor计算更高效
   - 通信开销可管理
   - 无需修改PKI

**局限性**:
- ❌ 理论设计,无实现
- ❌ 无实际性能数据
- ❌ ring-LWE非NIST标准算法
- ❌ 未考虑网络环境
- ❌ 发表于2015年,算法选择已过时

**对本文的价值**:
- ✅ PQ-Tor早期理论探索
- ⚠️ 但与当前NIST标准脱节

---

### 【文献6】Tor Proposal 263: NTRU for PQ Handshake (2015-2016)

**基本信息**:
- **作者**: John Schanck, William Whyte, Zhenfei Zhang
- **创建**: 2015年8月29日, 更新2016年2月4日
- **状态**: Obsolete (被Proposal 269取代)
- **类型**: Tor官方提案
- **链接**: https://spec.torproject.org/proposals/263-ntru-for-pq-handshake.html

**核心内容**:

1. **技术方案**:
   - 量子安全前向保密
   - 双密钥交换: ECC + NTRUEncrypt
   - KDF派生会话密钥

2. **握手类型**:
   - 0x0102: ntor+ntru (ntrueess443ep2)
   - 0x0103: ntor+rlwe

3. **防护目标**:
   - "收集现在,未来解密"攻击

**局限性**:
- ❌ 已被Proposal 269取代
- ❌ NTRU单元大小问题 (693 vs 505字节)
- ❌ 未实施
- ❌ NTRU未入选NIST标准

**对本文的价值**:
- ✅ 展示Tor社区PQ探索历史
- ⚠️ 但技术路线已过时

---

## 🌐 相关PQ网络协议 (对比参考)

---

### 【对比1】PQ-TLS

**核心文献**:
- "Benchmarking Post-Quantum Cryptography in TLS" (Paquin et al., 2019)
- "Performance Evaluation of Post-Quantum TLS" (2021)
- "The Performance of Post-Quantum TLS 1.3" (2023)
- "Faster Post-Quantum TLS 1.3 Based on ML-KEM" (2024)

**主要发现**:
- Kyber/ML-KEM与经典算法性能相当
- Dilithium、Falcon甚至更快
- 混合模式部署可行

**与Tor的差异**:
- ✅ TLS: 单次握手,短连接
- ⚠️ Tor: 多跳电路,长期连接
- ❌ TLS场景不适用于匿名网络

---

### 【对比2】PQ-QUIC

**核心文献**:
- "QUIC Protocol with Post-quantum Authentication" (2022)
- "Post-Quantum QUIC Protocol in Cloud Networking" (2023)
- "EPQUIC: Efficient Post-Quantum Cryptography for QUIC" (2025)

**主要发现**:
- QUIC在PQ场景下优于TCP/TLS
- Kyber与X25519混合性能损失仅8%
- PQ-KEM增加握手大小,加剧资源消耗攻击风险

**与Tor的差异**:
- ⚠️ QUIC允许多个初始包,缓解PQ大小问题
- ❌ Tor有严格单元大小限制
- ❌ 场景差异大

---

### 【对比3】PQ-WireGuard

**核心文献**:
- "Post-quantum WireGuard" (Hülsing et al., 2020)
- Kudelski Security实现 (2021)
- Rosenpass项目 (形式化验证)

**主要发现**:
- KEM-only设计 (不依赖DH)
- 已有生产级实现
- ExpressVPN全球部署: 连接增加15-20ms,无吞吐量影响

**与Tor的差异**:
- ✅ VPN: 点对点隧道
- ⚠️ Tor: 多跳链式加密
- ❌ WireGuard经验有限适用性

---

### 【对比4】I2P PQ迁移

**基本信息**:
- **状态**: 早期规划阶段
- **当前加密**: X25519 + EdDSA + ChaCha20/Poly1305
- **协议**: ECIES-X25519-AEAD-Ratchet

**PQ计划**:
- 研究混合PQ加密和签名
- 无具体时间表
- 未发表实现

**与Tor的差异**:
- I2P: Garlic路由,不同威胁模型
- 进展比Tor更滞后

---

### 【对比5】Katzenpost (PQ Mix Network)

**基本信息**:
- **定位**: 世界首个PQ混合网络
- **技术**: hpqc库 (hybrid post-quantum cryptography)
- **协议**: Noise-based链路层

**PQ实现**:
- **KEM**: Xwing (ML-KEM-768 + X25519混合)
- **签名**: Ed25519 + Sphincs+ (sphincs-shake-256f)
- **安全**: 抵御主动量子攻击

**与Tor的差异**:
- ✅ 已实现PQ (领先Tor)
- ⚠️ 但Mix网络 ≠ Onion路由
- ❌ 延迟模型完全不同 (连续时间混合 vs 实时电路)

**对本文的价值**:
- ✅ PQ匿名网络实现先例
- ⚠️ 但架构差异使经验难直接迁移

---

## 🚫 方向1调研结果: PQ-Tor + SAGIN = 完全空白

### 搜索策略

**关键词组合**:
1. "post-quantum" + "Tor" + "satellite"
2. "PQ-Tor" + "SAGIN" OR "space-air-ground"
3. "quantum-resistant" + "onion routing" + "satellite"
4. "PQ-Tor SAGIN space-air-ground network"
5. "quantum-safe Tor" + "non-terrestrial network"

**搜索结果**:
- ❌ 无任何PQ-Tor+SAGIN结合研究
- ✅ 找到大量SAGIN综述 (但不涉及PQ-Tor)
- ✅ 找到卫星量子密钥分发 (QKD) 研究 (但与PQC无关)
- ✅ 找到"Quantum Secure Anonymous Communication Networks" (2025, arXiv:2405.06126) - 但基于QKD,非PQC

**明确结论**:
```
PQ-Tor在SAGIN环境的应用是完全的研究空白
├─ 已有: PQ-Tor理论设计 (不考虑SAGIN)
├─ 已有: Tor在SAGIN部署 (不考虑量子威胁)
└─ 缺失: ❌ PQ + SAGIN + Tor 三者结合
```

---

## 📊 2.3节文献总结

### 文献分类统计

| 类别 | 数量 | 状态 | 适用性 |
|------|------|------|--------|
| **PQ-Tor理论/提案** | 4篇 | 讨论/设计阶段 | 高 |
| **PQ-Tor实现研究** | 2篇 | 论文已发表 | 高 |
| **PQ+SAGIN结合** | 0篇 | ❌ 空白 | - |
| **PQ网络协议对比** | 5个方向 | 已部署/研究中 | 中 |

### 推荐引用文献 (2.3节)

#### 核心文献 (必引)
1. **[Berger2025]** Berger, D., Lemoudden, M., & Buchanan, W. J. (2025). Post Quantum Migration of Tor. *Journal of Cybersecurity and Privacy*, 5(2), 13. ⭐⭐⭐
2. **[TorProp269]** Schanck, J., et al. (2016). Tor Proposal 269: Transitionally Secure Hybrid Handshakes. Tor Project. ⭐⭐
3. **[TorProp355]** Mathewson, N. (2025). Tor Proposal 355: Options for Postquantum Circuit Extension. Tor Project. ⭐⭐

#### 重要文献 (建议引用)
4. **[Tujner2020]** Tujner, Z., et al. (2020). QSOR: Quantum-Safe Onion Routing. *ICETE 2020*. arXiv:2001.03418. ⭐
5. **[Ghosh2015]** Ghosh, S., & Kate, A. (2015). Post-Quantum Forward-Secure Onion Routing. ePrint 2015/008. ⭐
6. **[TorProp263]** Schanck, J., Whyte, W., & Zhang, Z. (2016). Tor Proposal 263: NTRU for PQ Handshake. Tor Project.

#### 对比文献 (可选引用)
7. **[Paquin2019]** Paquin, C., Stebila, D., & Tamvada, G. (2019). Benchmarking Post-Quantum Cryptography in TLS. ePrint 2019/1447.
8. **[Hülsing2020]** Hülsing, A., et al. (2020). Post-quantum WireGuard. ePrint 2020/379.

---

## 🎯 现有工作的6大局限性 (对应2.4节6大创新)

### 局限性1: 缺少PQ-NTOR的完整实现
**现状**:
- Berger: 仅理论估算 (基于liboqs基准)
- Proposal 269/355: 仅设计讨论
- QSOR: 仿真测试,非真实Tor

**本文创新**: ✅ 基于Kyber-512完整实现,实测181.64 µs

---

### 局限性2: 缺少SAGIN环境的系统性评估
**现状**:
- Berger: 假设传统互联网
- 所有PQ-Tor研究: 未涉及卫星/UAV/非地面网络
- **搜索结果**: ❌ PQ-Tor + SAGIN文献为零

**本文创新**: ✅ 12种SAGIN拓扑 (LEO/MEO/GEO + UAV + 地面)

---

### 局限性3: 缺少高延迟、高抖动场景性能数据
**现状**:
- Berger: 孤立密码学基准,未考虑网络影响
- QSOR: 仿真环境,未模拟真实网络条件
- PQ-TLS研究: 聚焦低延迟场景

**本文创新**: ✅ 延迟30-500ms全覆盖,基于真实NOMA参数

---

### 局限性4: 缺少真实分布式部署验证
**现状**:
- Berger: 本地Tor网络模拟
- QSOR: SweetOnions仿真器
- Ghosh: 理论分析,无实现

**本文创新**: ✅ 7飞腾派真实硬件,分布式部署,100%成功率

---

### 局限性5: 缺少系统性拓扑覆盖
**现状**:
- 所有PQ-Tor研究: 单一地面网络假设
- 无多拓扑对比分析

**本文创新**: ✅ 12拓扑 × 20迭代 = 240次系统性实验

---

### 局限性6: 缺少ARM64等边缘平台评估
**现状**:
- Berger: x86_64 + Raspberry Pi 5 (ARM Cortex-A76)
- 主流PQ研究: 聚焦X86服务器

**本文创新**: ✅ 飞腾派 (ARM Cortex-A72),资源受限场景验证

---

## ✍️ 2.3节写作建议

### 2.3.1 PQ-Tor结合SAGIN工作 (300-500字)

**建议论述**:
```
本文系统调研发现,将后量子密码应用于SAGIN环境下匿名通信系统
的研究完全空白。通过多组关键词搜索 ("post-quantum Tor
satellite", "PQ-Tor SAGIN", "quantum-resistant onion routing
satellite" 等),未检索到任何相关文献。

现有工作主要分为两条独立路线:
(1) PQ-Tor理论设计 - 不考虑SAGIN特殊网络环境
(2) Tor在SAGIN部署 - 不考虑量子威胁 (如SaTor[18])

这两条路线缺乏交叉,形成明显研究空白,而这正是本文的核心
创新点。以下重点分析非SAGIN环境下的PQ-Tor研究及其局限性。
```

---

### 2.3.2 非SAGIN网络下的PQ-Tor研究 (1200-1600字)

**结构建议**:

**第1段: Berger et al. (2025)详细介绍** (500-600字)
- 工作内容: PQ迁移路线图,ML-KEM推荐,性能估算
- 性能数据: 列出关键数据 (见文献1详情)
- **重点**: 6大局限性逐条分析

**第2段: Tor Proposals (269, 355)** (300-400字)
- Proposal 269: 混合握手设计 (2016,已7年未实施)
- Proposal 355: PQ方案探索 (2025,仍为讨论)
- 局限: 提案阶段,无实现与验证

**第3段: 其他学术研究** (200-300字)
- QSOR (Tujner 2020): 仿真测试
- HybridOR (Ghosh 2015): 理论设计
- 局限: 仿真/理论,与当前标准脱节

**第4段: 本小节总结** (200-300字)
- 列出6大共同不足
- 引出: 这些不足正是本文工作的切入点

---

### 2.3.3 研究空白: PQ + SAGIN的缺失 (600-800字)

**第1段**: 两大分支总结
**第2段**: 6大研究空白详细分析 (见上文)
**第3段**: 结合必要性论证

---

## 📋 写作检查清单

在撰写2.3节时,请确保:

- [ ] **2.3.1节**: 明确指出PQ-Tor+SAGIN是完全空白
- [ ] **2.3.2节**: Berger论文的6大局限性逐条分析
- [ ] **2.3.2节**: 提案仍处于讨论阶段,7-9年未实施
- [ ] **2.3.3节**: 6大研究空白与2.4节6大创新一一对应
- [ ] **文献引用**: 核心文献[Berger2025]必须详细引用
- [ ] **过渡衔接**: 2.3.3节末尾自然过渡到2.4节
- [ ] **创新凸显**: 每个局限性后明确标注"本文创新"

---

## 📎 附录: 搜索关键词记录

### 已验证的空白搜索
- ✅ "post-quantum Tor satellite network" → 无结果
- ✅ "PQ-Tor SAGIN space-air-ground" → 无结果
- ✅ "quantum-resistant onion routing satellite" → 无结果
- ✅ "Berger PQ-Tor SAGIN satellite 2024" → 无结果

### 有效搜索 (找到文献)
- ✅ "Tor Proposal 269 hybrid handshake" → Proposal 269
- ✅ "Post Quantum Migration of Tor" → Berger et al. 2025
- ✅ "QSOR Quantum-safe Onion Routing" → Tujner et al. 2020
- ✅ "Post-Quantum Forward-Secure Onion Routing" → Ghosh & Kate 2015
- ✅ "Tor Proposal 355 revisiting post-quantum" → Proposal 355

---

## 📚 文献来源链接汇总

### 核心PQ-Tor文献
1. Berger et al. (2025): https://www.mdpi.com/2624-800X/5/2/13
2. Proposal 269: https://spec.torproject.org/proposals/269-hybrid-handshake.html
3. Proposal 355: https://spec.torproject.org/proposals/355-revisiting-pq.html
4. QSOR: https://arxiv.org/abs/2001.03418
5. HybridOR: https://eprint.iacr.org/2015/008
6. Proposal 263: https://spec.torproject.org/proposals/263-ntru-for-pq-handshake.html

### PQ网络协议对比
7. PQ-TLS Benchmark: https://github.com/xvzcf/pq-tls-benchmark
8. PQ-QUIC AWS: https://aws.amazon.com/blogs/security/enable-post-quantum-key-exchange-in-quic-with-the-s2n-quic-library/
9. PQ-WireGuard: https://github.com/kudelskisecurity/pq-wireguard
10. Katzenpost: https://katzenpost.network/

### SAGIN相关 (未结合PQ-Tor)
11. SAGIN Survey: https://arxiv.org/abs/2307.14697
12. Quantum Secure Anonymous Networks: https://arxiv.org/abs/2405.06126

---

**调研完成时间**: 2025-12-03
**文献总数**: 核心6篇 + 对比5个方向 = 11个参考方向
**下一步**: 基于此报告撰写2.3节正文

---

## Sources (文献调研来源)

- [Post Quantum Migration of Tor - MDPI](https://www.mdpi.com/2624-800X/5/2/13)
- [Post Quantum Migration of Tor - arXiv](https://arxiv.org/abs/2503.10238)
- [Tor Proposal 269 - Transitionally Secure Hybrid Handshakes](https://spec.torproject.org/proposals/269-hybrid-handshake.html)
- [Tor Proposal 355 - Revisiting Post-Quantum](https://spec.torproject.org/proposals/355-revisiting-pq.html)
- [QSOR: Quantum-Safe Onion Routing](https://arxiv.org/abs/2001.03418)
- [Post-Quantum Forward-Secure Onion Routing](https://eprint.iacr.org/2015/008)
- [Tor Proposal 263 - NTRU for PQ Handshake](https://spec.torproject.org/proposals/263-ntru-for-pq-handshake.html)
- [Katzenpost Mix Network](https://katzenpost.network/)
- [PQ-TLS Benchmark GitHub](https://github.com/xvzcf/pq-tls-benchmark)
- [AWS PQ-QUIC Blog](https://aws.amazon.com/blogs/security/enable-post-quantum-key-exchange-in-quic-with-the-s2n-quic-library/)
- [PQ-WireGuard Implementation](https://github.com/kudelskisecurity/pq-wireguard)
- [Quantum Secure Anonymous Communication Networks](https://arxiv.org/abs/2405.06126)
- [SAGIN Survey](https://arxiv.org/abs/2307.14697)
