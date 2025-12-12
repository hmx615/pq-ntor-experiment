# 第一章和第二章内容整理

**创建日期**: 2025-12-01
**状态**: 内容已提取，待转换为LaTeX

---

## 📖 第一章 Introduction

### 📝 简化版（推荐使用）

With the rapid growth of the Internet in the 21st century, its supporting infrastructure has also improved. People now have a stronger demand for Internet security and personal privacy, making anonymous communication a fundamental part of modern digital systems.

The Tor network is the most mature anonymous communication system. It was proposed in 1995, released publicly in 2002, and now serves over 20 million daily users.

Meanwhile, the Space-Air-Ground Integrated Network (SAGIN) builds global communication coverage by combining LEO, MEO, and GEO satellites with airborne and ground platforms. Because SAGIN is open and highly distributed, its satellite links face significant risks from passive monitoring. Anonymous communication systems like Tor can help reduce these risks.

Tor protects user privacy through multilayer encryption and relay-based anonymity. It secures personal information, keeps data confidential, and prevents attackers from tracking communication paths or learning the network structure. This makes integrating Tor into SAGIN both valuable and technically feasible.

However, the rise of quantum computing threatens traditional public-key systems such as ECC and RSA, which are essential to Tor's Ntor handshake protocol. If quantum computers break these schemes, user identities, communication content, access patterns, and even the global anonymous communication system could be fully exposed.

Whether SAGIN can support a Post-Quantum Tor (PQ-Tor)—given its high latency (30–500 ms), strong link jitter, and narrow bandwidth—remains an open question. Studying this problem is important for future technical improvements and system design.

---

### 📝 原版（供参考）

<details>
<summary>点击展开原版内容</summary>

With the rapid development of the Internet in the 21st century, its supporting infrastructure has also advanced significantly. Today, people demand Internet security and personal privacy more frequently than ever before, turning anonymous communication from a secondary requirement into a fundamental component of modern digital infrastructure.

The Tor network is the most mature system for anonymous communication. It was first proposed in 1995, released as a public test version in 2002, and now serves more than 20 million daily users worldwide.

Meanwhile, the Space-Air-Ground Integrated Network (SAGIN) constructs a globally connected communication architecture by integrating Low Earth Orbit (LEO), Medium Earth Orbit (MEO), and Geostationary Earth Orbit (GEO) satellite constellations along with airborne and ground platforms. However, because SAGIN is open and highly distributed, its satellite links face a high risk of passive monitoring attacks. Anonymous communication systems such as Tor can help reduce these risks effectively.

With its multilayer encryption and relay-based anonymity, Tor can protect personal information, ensure data confidentiality, prevent attackers from extracting sensitive content, tracking communication paths, or inferring network topology. This makes the integration of Tor with SAGIN both promising and technically significant.

However, the rise of quantum computing has posed severe threats to traditional public-key cryptographic systems such as ECC and RSA. These systems form the core cryptographic primitives of Tor's Ntor handshake protocol. Once the Tor network is broken by quantum computing, users' identities, communication contents, and access traces, as well as the global anonymous communication infrastructure, will be fully exposed.

Whether SAGIN can support a Post-Quantum Tor (PQ-Tor) under its unique technical constraints—such as high latency (30–500 ms), strong link jitter, and narrow channel bandwidth—remains an open question. At the same time, exploring this issue lays an important foundation for subsequent technical optimization and system construction.

</details>

---

## 📖 第二章 Background

### 2.1 Tor体系结构（中文原版）

Tor（The Onion Router）作为当前应用最广的匿名通信系统，其匿名性保障依赖于洋葱路由机制构建的多跳加密传输路径。在数据发送前，客户端为电路中每一跳中继节点依次封装加密层，使得当数据沿路径逐跳解密和转发时，任何单个中继节点仅能获得前一跳与后一跳的信息，从而实现源地址与目的地址的有效解耦[1]。Tor 电路的初始化依赖控制层的 CREATE 与 EXTEND 消息，自入口节点（Guard）开始，客户端与各中继逐步完成密钥协商，通过子电路扩展方式构建完整三跳路径，并最终形成独立共享的会话密钥用于对数据单元（cell）的加密传输，以确保节点链路之间的机密性与完整性[1]。

目前 Tor 默认采用的电路密钥交换协议为 Ntor 握手，该协议自 2014 年起取代原有 TAP，并在长期部署中表现出高效与安全性平衡特点。Ntor 基于 X25519 椭圆曲线 Diffie-Hellman（ECDH）机制构建共享密钥，具备前向保密特性，客户端通过节点长期身份密钥与临时密钥结合计算会话密钥，避免密钥重用导致的关联性风险。Ntor 对性能优化使其能够支持 Tor 网络中快速创建大量短生命周期电路，成为维持 Tor 实际可用性的关键因素[2]。

近年来，量子计算技术取得了显著进展。多家科研机构已展示可扩展量子比特结构，IBM 等企业提出了百至千量级量子芯片路线图，量子退相干与误差校正技术也在持续突破，这使得传统依赖离散对数与大数分解难题的密码协议安全前景面临威胁[3]。在理论层面，Shor 于 1997 年提出的算法已被证明可在多项式时间内求解离散对数问题与整数分解问题，量子计算机一旦规模化，将能够直接破解当前广泛使用的 ECC 与 RSA 密钥体系[4]。

因此，Ntor 所依赖的 Curve25519 离散对数难题假设在量子计算条件下将不再成立。攻击者若在未来具备足够规模的量子能力，则可恢复握手阶段的私钥信息，从而回溯分析先前被动记录的通信流量。此威胁不仅破坏前向保密性，也将匿名性防护削弱至严重程度，使得入口—出口关联攻击成为可能。因此，在量子攻击模型下，现有 Tor 电路构建安全性面临根本性挑战。

围绕上述风险，研究者已开展广泛分析与形式化验证。Goldberg、Stebila 等学者对 Ntor 安全性进行了系统定义，并指出其在抗量子能力上的结构性缺陷[5]；Tor Research Safety Board 与 Tor Project 官方社区文档均强调应逐步引入具备量子韧性的密钥交换方案，如 NIST PQC 标准化算法 Kyber 或混合 KEX 模式[6-7]。结合后量子加密标准化进程可预期，Tor 必须从经典 ECDH 迁移至抗量子算法或混合密钥交换机制，确保在量子计算时代仍能维持匿名通信能力。

综上，Tor 体系中的电路构建与密钥协商机制是匿名性保障的基础，而现有 Ntor 握手在面对量子计算威胁时已不再安全。对其替代与升级不仅是协议改进的问题，更是 Tor 网络在未来持续保持匿名通信能力的关键需求，因此开展面向后量子时代的握手协议研究具有重要理论意义与实践价值。

**参考文献**:
- [1] Dingledine R, Mathewson N, Syverson P. Tor: The Second-Generation Onion Router[C]//USENIX Security Symposium. 2004.
- [2] Mathewson N, Möller J. Tor Proposal 216: Ntor protocol[R]. Tor Project, 2014.
- [3] IBM. IBM Quantum Development Roadmap[R]. IBM Research, 2023.
- [4] Shor P. Algorithms for quantum computation: discrete logarithms and factoring[C]//FOCS. 1997.
- [5] Goldberg I, Stebila D. Anonymity and ECDH: The Ntor Protocol in Tor[C]//EuroS&P Workshops. 2015.
- [6] Tor Project. Post-Quantum Handshake Integration Discussion[R]. Tor Community Forum, 2022.
- [7] Chen L, et al. Report on Post-Quantum Cryptography[R]. NISTIR 8105, 2016.

---

### 2.1 Tor Architecture（英文简化版 - 待撰写）

**待完成**: 基于中文版转换，应用简化写作风格

**核心要点**:
1. Tor anonymity through onion routing and multi-hop circuits
2. Circuit establishment using CREATE and EXTEND messages
3. Ntor handshake protocol (X25519 ECDH)
4. Quantum threat to Curve25519
5. Need for post-quantum migration

---

### 2.2 后量子密码与Kyber（中文原版）

Kyber算法的抗量子安全核心与规模化部署能力，根源在于LWE与Module-LWE（MLWE）问题的协同支撑。作为抗量子安全的根基，LWE问题的困难性可严格归约于格上的最坏情况困难问题，目前尚无量子算法能在多项式时间内破解它，这一固有数学属性筑牢了安全防线[1]；而MLWE作为LWE的优化形态，以"多项式环元素作为基本运算单元"为设计核心，在完全继承LWE抗量子安全性的同时，大幅提升运算效率并压缩密钥与密文尺寸，为算法落地提供了实用条件[2]。

作为Kyber算法族中对应128位安全级别的核心参数集，Kyber512既延续了底层数学安全性，又通过工程化优化形成成熟特性。其安全性核心完全依托MLWE问题，抗量子属性与数学根基稳固可靠[2]。针对后量子算法普遍存在的效率瓶颈，Kyber512针对性优化机制：一方面用数论变换（NTT）加速核心多项式乘法，将运算复杂度从O(n²)降至O(nlogn)[3]；另一方面采用紧凑化密钥与密文设计，在资源受限设备上仅需少量内存即可完成加密运算[2]。同时，它构建了多维度安全防护体系，通过恒定时间运算与掩码技术抵御侧信道攻击，并精准控制多项式采样参数与噪声范围，将解密失败率压低至约2⁻¹³⁹的极低水平（在特定参数集下的理论值）[4]。更重要的是，其多项式次数256、模数3329等参数配置及"密钥生成-加密-解密"三步流程，均经NIST后量子密码标准化多轮严苛审查，规范化设计使其能轻松集成到现有系统，无需大幅改造架构[5]。

依托理论安全与工程成熟的双重优势，Kyber512凭借高效、轻量及抗量子特性，已在IoT、VPN、TLS三大核心场景实现实质性落地。在IoT领域，它精准适配资源受限设备：华为Watch D Pro血压监测模块集成Kyber硬件加速器，512位密钥封装的加密延迟满足心电图信号实时传输需求；糖尿病管理系统经FPGA加速后，其单次密钥封装时间从12.7ms降至2.3ms[6]；图灵量子TQ03-QRNGC-64芯片借其能力为终端提供抗量子服务，虹膜识别设备中它加密的特征尺寸仅6.0kb、耗时低至0.755ms[6]。在VPN领域，它通过硬件适配与协议集成提供保障，图灵量子同款芯片可嵌入VPN设备，国芯科技CCUPHPQ01密码卡支持该算法且解密速度达1800次/秒，不过OpenVPN测试中存在客户端优先选用X25519的适配问题。在TLS领域，它以X25519-Kyber512混合套件集成于TLS 1.3协议[7]，Cloudflare、GitLab等平台已部署，该模式既保留传统算法效率，又以抗量子特性防护密钥交换环节，适配TLS对延迟和传输量的要求[7]。

**参考文献**:
- [1] Regev O. On lattices, learning with errors, random linear codes, and cryptography[J]. Journal of the ACM (JACM), 2009, 56(6): 1-40.
- [2] Bos J, Costello C, Naehrig M, et al. CRYSTALS-Kyber: A CCA-secure module-lattice-based KEM[J]. Journal of Cryptology, 2023, 36(2): 1-47.
- [3] Van Assche G, Vercauteren F. Number Theoretic Transforms and their Applications in Cryptography[M]//Advances in Cryptology - ASIACRYPT 2005. Springer, Berlin, Heidelberg, 2005: 324-340.
- [4] NIST. Post-Quantum Cryptography Standardization: CRYSTALS-Kyber Security Analysis Report[R]. Gaithersburg: National Institute of Standards and Technology, 2022.
- [5] NIST. FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard[R]. Gaithersburg: National Institute of Standards and Technology, 2024.
- [6] Li Y, Zhang H, Wang Z. FPGA Acceleration of CRYSTALS-Kyber for IoT Applications[J]. IEEE Internet of Things Journal, 2023, 10(15): 13245-13256.
- [7] IETF. RFC 9580: Using CRYSTALS-Kyber in the Transport Layer Security (TLS) Protocol[R]. Fremont: Internet Engineering Task Force, 2023.

---

### 2.2 Post-Quantum Cryptography and Kyber（英文简化版 - 待撰写）

**待完成**: 基于中文版转换，应用简化写作风格

**核心要点**:
1. Quantum threat to classical cryptography (ECC, RSA)
2. LWE and MLWE problem foundations
3. Kyber512 design and security properties
4. Efficiency optimizations (NTT, compact keys)
5. Real-world deployments (IoT, VPN, TLS)
6. NIST PQC standardization (FIPS 203)

---

### 2.3 SAGIN Networks（待补充）

**待完成**: 撰写SAGIN相关背景

**核心要点**（建议）:
1. SAGIN architecture overview (LEO/MEO/GEO + UAV + Ground)
2. Network characteristics (high latency, variable bandwidth)
3. Security challenges (passive monitoring, link vulnerability)
4. Integration requirements for Tor
5. Performance constraints and optimization needs

---

## 📋 转换工作计划

### 优先级1: 第一章英文定稿

**任务**:
- [x] 提取简化版内容
- [ ] 进一步润色（如需要）
- [ ] 转换为LaTeX格式
- [ ] 集成到`essay/latex/sections/introduction.tex`

**预计时间**: 0.5天

---

### 优先级2: 第二章英文转换

**任务**:
- [x] 提取中文版内容
- [ ] 翻译为英文（应用简化写作风格）
- [ ] 拆分为三个子章节
  - [ ] 2.1 Tor Architecture
  - [ ] 2.2 Post-Quantum Cryptography and Kyber
  - [ ] 2.3 SAGIN Networks
- [ ] 转换为LaTeX格式
- [ ] 集成到`essay/latex/sections/background.tex`

**预计时间**: 2-3天

---

### 优先级3: 参考文献整合

**任务**:
- [ ] 整理第一章引用（如有）
- [ ] 整理第二章引用（已有14条）
- [ ] 添加到`essay/latex/references.bib`
- [ ] 统一引用格式

**预计时间**: 0.5天

---

## 🔄 写作流程建议

### 步骤1: 中文 → 英文初稿

对于第二章中文内容，建议流程：

1. **段落拆分**: 将长段落拆分为短段落
2. **句子简化**: 应用简化写作风格
3. **专业术语**: 统一英文术语（如MLWE, NTT等）
4. **引用检查**: 确保所有引用准确

### 步骤2: 英文初稿 → 润色稿

1. **句长检查**: 每句15-25词
2. **动词优化**: 使用简单直接的动词
3. **逻辑连贯**: 添加过渡句
4. **术语一致性**: 全文统一

### 步骤3: 润色稿 → LaTeX集成

1. **格式转换**: Markdown → LaTeX
2. **引用添加**: `\cite{}`标签
3. **编译测试**: 确保无错误
4. **PDF检查**: 版式和格式

---

## 📊 进度跟踪

| 章节 | 状态 | 负责人 | 预计完成 |
|------|------|--------|---------|
| 第一章（简化版） | ✅ 完成 | ChatGPT5 | 已完成 |
| 第二章 2.1（中文） | ✅ 完成 | 团队 | 已完成 |
| 第二章 2.2（中文） | ✅ 完成 | 团队 | 已完成 |
| 第二章 2.3（SAGIN） | ⏳ 待撰写 | 待定 | - |
| 第一章（LaTeX） | ⏳ 待转换 | 待定 | - |
| 第二章（英文版） | ⏳ 待翻译 | 待定 | - |
| 第二章（LaTeX） | ⏳ 待转换 | 待定 | - |

---

## 💡 下一步建议

### 立即可做

1. **第二章2.3 SAGIN部分撰写**（中文）
   - 参考`7PI_FINAL_TEST_PLAN.md`中的SAGIN拓扑描述
   - 参考`SAGIN_PQ-NTOR实验设计方案.md`

2. **第二章英文翻译**
   - 2.1 Tor Architecture
   - 2.2 Post-Quantum Cryptography and Kyber
   - 使用简化写作风格

3. **LaTeX集成**
   - 更新`essay/latex/sections/introduction.tex`
   - 更新`essay/latex/sections/background.tex`

---

**维护者**: PQ-NTOR SAGIN 项目组
**创建日期**: 2025-12-01
**最后更新**: 2025-12-01
**状态**: ✅ 内容已提取整理，等待翻译和LaTeX转换
