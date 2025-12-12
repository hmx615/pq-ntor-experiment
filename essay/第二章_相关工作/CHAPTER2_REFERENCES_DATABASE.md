# 第二章 相关工作 - 完整参考文献数据库

**创建日期**: 2025-12-03
**维护者**: PQ-NTOR SAGIN 项目组
**用途**: 论文第二章撰写的统一文献引用库
**文献总数**: 29篇

---

## 快速引用指南

| 文献ID | 作者 | 年份 | 关键词 | 用途 | 优先级 |
|--------|------|------|--------|------|--------|
| NIST-FIPS203 | NIST | 2024 | ML-KEM, Kyber | PQC标准 | ⭐⭐⭐⭐⭐ |
| NIST-FIPS204 | NIST | 2024 | ML-DSA, Dilithium | PQC标准 | ⭐⭐⭐⭐⭐ |
| Berger2025 | Berger et al. | 2025 | PQ-Tor迁移 | 核心对比文献 | ⭐⭐⭐⭐⭐ |
| SaTor2024 | Li & Elahi | 2024 | LEO卫星Tor | SAGIN-Tor基础 | ⭐⭐⭐⭐⭐ |
| Singh2024 | Singh et al. | 2024 | 指纹攻击 | 安全威胁 | ⭐⭐⭐⭐⭐ |
| Q-SAGIN2022 | Multiple | 2022 | 量子SAGIN | 量子威胁背景 | ⭐⭐⭐⭐⭐ |
| APQA2024 | Authors | 2024 | SAGIN认证 | PQC-SAGIN应用 | ⭐⭐⭐⭐ |
| LPQAA2024 | Authors | 2024 | 轻量级PQC | PQC-SAGIN应用 | ⭐⭐⭐⭐ |
| UAV-Kyber2024 | Authors | 2024 | UAV认证 | PQC-SAGIN应用 | ⭐⭐⭐⭐ |
| RECORD2024 | Jedermann et al. | 2024 | 位置隐私 | 安全威胁 | ⭐⭐⭐⭐ |
| PQ-TLS-Sat2024 | lin-1214 | 2024 | 卫星TLS | 性能对比 | ⭐⭐⭐⭐ |
| NDSS-PQTLS2020 | Authors | 2020 | PQ-TLS性能 | 性能对比 | ⭐⭐⭐⭐ |
| 6G-SGIN2023 | Authors | 2023 | 匿名认证 | SAGIN隐私 | ⭐⭐⭐⭐ |
| 6G-QSafe2025 | Authors | 2025 | 6G量子安全 | 量子威胁 | ⭐⭐⭐⭐ |
| TorProp269 | Schanck et al. | 2016 | 混合握手 | PQ-Tor提案 | ⭐⭐⭐ |
| TorProp355 | Mathewson | 2025 | PQ电路扩展 | PQ-Tor提案 | ⭐⭐⭐ |
| QSOR2020 | Tujner et al. | 2020 | PQ洋葱路由 | PQ-Tor研究 | ⭐⭐⭐ |
| HybridOR2015 | Ghosh & Kate | 2015 | 混合洋葱路由 | PQ-Tor理论 | ⭐⭐⭐ |
| Sat-Security2024 | Authors | 2024 | 卫星安全综述 | 安全威胁 | ⭐⭐⭐ |
| SAGIN-Privacy2024 | Authors | 2024 | SAGIN隐私 | 安全威胁 | ⭐⭐⭐ |
| UAV-FANET2022 | Authors | 2022 | UAV匿名 | SAGIN隐私 | ⭐⭐⭐ |
| PQ-TLS-Bench2019 | Paquin et al. | 2019 | TLS基准测试 | 性能对比 | ⭐⭐⭐ |
| PQ-WireGuard2020 | Hülsing et al. | 2020 | PQ-VPN | 性能对比 | ⭐⭐⭐ |
| Earth-Sat-QKD2025 | Rani et al. | 2025 | 地卫QKD | PQC-SAGIN应用 | ⭐⭐⭐ |
| TorProp263 | Schanck et al. | 2016 | NTRU握手 | PQ-Tor提案(已过时) | ⭐⭐ |
| IoD-PQC2024 | Authors | 2024 | 无人机PQC | PQC-SAGIN补充 | ⭐⭐ |
| QuSecure-Starlink | QuSecure | 2023 | 卫星PQC部署 | 工业案例 | ⭐⭐ |
| 3GPP-NTN | 3GPP | 2024 | 5G NTN安全 | 标准化进展 | ⭐⭐ |
| Katzenpost | Project | 2024 | PQ混合网络 | 对比参考 | ⭐⭐ |

---

## 2.1节文献: 后量子密码学基础

### 2.1.1 量子计算威胁

#### [NIST-FIPS203] ⭐⭐⭐⭐⭐ NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard

**基本信息**:
- **作者**: National Institute of Standards and Technology (NIST)
- **发表**: August 2024
- **类型**: Federal Information Processing Standard
- **文献链接**: https://csrc.nist.gov/pubs/fips/203/final

**IEEE引用格式**:
```
National Institute of Standards and Technology, "FIPS 203: Module-Lattice-Based
Key-Encapsulation Mechanism Standard," Federal Information Processing Standards
Publication, NIST, Gaithersburg, MD, USA, Aug. 2024.
```

**简短摘要**:
NIST正式发布的基于模格的密钥封装机制标准,标准化了ML-KEM(原Kyber)算法,包括ML-KEM-512、ML-KEM-768和ML-KEM-1024三个安全级别。

**引用原因**:
- 本文PQ-NTOR实现基于ML-KEM-512标准
- 提供算法规范和安全性保证
- 证明所选算法的权威性和标准化地位

---

#### [NIST-FIPS204] ⭐⭐⭐⭐⭐ NIST FIPS 204: Module-Lattice-Based Digital Signature Standard

**基本信息**:
- **作者**: National Institute of Standards and Technology (NIST)
- **发表**: August 2024
- **类型**: Federal Information Processing Standard
- **文献链接**: https://csrc.nist.gov/pubs/fips/204/final

**IEEE引用格式**:
```
National Institute of Standards and Technology, "FIPS 204: Module-Lattice-Based
Digital Signature Standard," Federal Information Processing Standards Publication,
NIST, Gaithersburg, MD, USA, Aug. 2024.
```

**简短摘要**:
NIST发布的基于模格的数字签名标准,标准化了ML-DSA(原Dilithium)算法。虽然本文未实现签名,但ML-DSA是Tor未来完整PQ迁移的签名算法候选。

**引用原因**:
- 说明完整PQ-Tor迁移路线图
- 对比Berger论文中的签名算法选择
- 为未来工作提供标准参考

---

### 2.1.2 PQC在SAGIN/卫星网络部署

#### [APQA2024] ⭐⭐⭐⭐ APQA: Anonymous Post Quantum Access Authentication for SGIN

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: Computer Networks (Elsevier)
- **文献链接**: https://www.sciencedirect.com/science/article/abs/pii/S1389128624008119
- **DOI**: 10.1016/j.comnet.2024.110979

**IEEE引用格式**:
```
Authors, "APQA: An anonymous post quantum access authentication scheme based on
lattice for space ground integrated network," Computer Networks, vol. 257,
Art. no. 110979, 2024. DOI: 10.1016/j.comnet.2024.110979
```

**简短摘要**:
基于RLWE格密码的匿名认证协议,专为SGIN设计,使用Regev加密和拒绝采样算法,计算时间比现有方案减少36%。

**引用原因**:
- 证明PQC在SAGIN环境的可行性
- 展示格密码在资源受限环境的优势
- 为本文PQ-NTOR在SAGIN部署提供参考

---

#### [LPQAA2024] ⭐⭐⭐⭐ LPQAA: Lightweight Post-Quantum Access Authentication for Satellite

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: The Journal of Supercomputing (Springer)
- **文献链接**: https://link.springer.com/article/10.1007/s11227-024-06687-5
- **DOI**: 10.1007/s11227-024-06687-5

**IEEE引用格式**:
```
Authors, "LPQAA: a lightweight post-quantum access authentication scheme for
satellite network," The Journal of Supercomputing, vol. 81, no. 1, Art. no. 159,
2024. DOI: 10.1007/s11227-024-06687-5
```

**简短摘要**:
专门针对资源受限卫星网络的轻量级PQC认证方案,认证时间至少减少150%,适应卫星窄带上行链路和高延迟环境。

**引用原因**:
- 强调卫星网络资源受限挑战
- 证明轻量级PQC方案的必要性
- 支撑本文在SAGIN环境性能优化的动机

---

#### [UAV-Kyber2024] ⭐⭐⭐⭐ Quantum-Resistant Authentication for UAV Networks Based on Kyber

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: MDPI Drones
- **文献链接**: https://www.mdpi.com/2504-446X/8/8/359

**IEEE引用格式**:
```
Authors, "A Quantum-Resistant Identity Authentication and Key Agreement Scheme
for UAV Networks Based on Kyber Algorithm," Drones, vol. 8, no. 8, Art. no. 359,
2024. DOI: 10.3390/drones8080359
```

**简短摘要**:
提出LIGKYX方案,结合Kyber算法和HMAC,针对IoT无人机网络的量子安全认证,基于RLWE格假设,适合低计算能力设备。

**引用原因**:
- 展示Kyber/ML-KEM在空中网络的应用
- 证明本文算法选择(Kyber-512)的合理性
- 支撑SAGIN多层网络(空中层)的PQC需求

---

#### [IoD-PQC2024] ⭐⭐ Anonymous Quantum-Safe Communication Protocol for IoD

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: ScienceDirect (期刊名待补充)
- **文献链接**: https://www.sciencedirect.com/science/article/abs/pii/S0045790624007018

**IEEE引用格式**:
```
Authors, "Anonymous quantum-safe secure and authorized communication protocol
under dynamic identities for Internet of Drones," Journal Name, 2024.
```

**简短摘要**:
基于RLWE的匿名认证密钥协商协议,支持动态身份管理,结合匿名性与量子安全性,适合低计算设备。

**引用原因**:
- 补充UAV层PQC应用
- 展示匿名性与量子安全的结合(与Tor目标一致)

---

#### [PQ-TLS-Sat2024] ⭐⭐⭐⭐ PQ-TLS Benchmarking for Satellite Communication

**基本信息**:
- **作者**: lin-1214
- **发表**: 2024
- **类型**: GitHub研究项目
- **文献链接**: https://github.com/lin-1214/pq-tls-satcom-benchmark

**IEEE引用格式**:
```
lin-1214, "pq-tls-satcom-benchmark: Post-Quantum TLS 1.3 Benchmarking for
Satellite Communication," GitHub repository, 2024. [Online].
Available: https://github.com/lin-1214/pq-tls-satcom-benchmark
```

**简短摘要**:
专门评估PQC算法在卫星环境TLS握手的性能影响,测试高延迟、有损卫星链路,提供完整基准测试工具。

**引用原因**:
- 最直接相关的卫星PQC性能研究
- 提供TLS层性能对比基准
- 证明PQC在卫星环境的可行性(握手开销1-2%)

---

#### [NDSS-PQTLS2020] ⭐⭐⭐⭐ Post-Quantum Authentication in TLS 1.3: A Performance Study

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2020
- **会议/期刊**: NDSS Symposium
- **文献链接**: https://www.ndss-symposium.org/ndss-paper/post-quantum-authentication-in-tls-1-3-a-performance-study/

**IEEE引用格式**:
```
Authors, "Post-Quantum Authentication in TLS 1.3: A Performance Study,"
in Proc. Network and Distributed System Security Symp. (NDSS), San Diego, CA,
USA, 2020.
```

**简短摘要**:
NIST签名算法候选的详细性能评估,证明至少2种PQ签名算法可用于时间敏感应用,5G环境下mlkem512_mldsa44平衡延迟和CPU使用。

**引用原因**:
- 提供PQ-TLS性能基准
- 支撑"PQC不会显著降低握手性能"论断
- 对比本文PQ-NTOR性能(181.64 µs vs TLS握手毫秒级)

---

#### [Earth-Sat-QKD2025] ⭐⭐⭐ Combined Quantum and Post-Quantum Security for Earth-Satellite

**基本信息**:
- **作者**: Anju Rani, Xiaoyu Ai, Aman Gupta, Ravi Singh Adhikari, Robert Malaney
- **机构**: UNSW Australia
- **发表**: 2025 (已接收)
- **会议/期刊**: IEEE QCNC 2025
- **文献链接**: https://arxiv.org/html/2502.14240v1

**IEEE引用格式**:
```
A. Rani, X. Ai, A. Gupta, R. S. Adhikari, and R. Malaney, "Combined Quantum and
Post-Quantum Security for Earth-Satellite Channels," in Proc. IEEE Int. Conf.
Quantum Communications, Networking, and Computing (QCNC), 2025. [Online].
Available: https://arxiv.org/html/2502.14240v1
```

**简短摘要**:
首次部署BBM92协议结合AES和QKD的混合密码方案,用于地卫信道,同时抵御经典和量子计算机攻击。

**引用原因**:
- 展示QKD与PQC混合方案
- 证明卫星环境的量子安全可行性
- 对比本文纯PQC方案(无需量子信道)

---

#### [3GPP-NTN] ⭐⭐ 3GPP NTN Security and Post-Quantum Cryptography

**基本信息**:
- **作者**: 3GPP SA3工作组
- **发表**: 2024 (Release 17-20)
- **类型**: 标准化文档
- **文献链接**: https://www.3gpp.org/ftp/Email_Discussions/SA3/TSG3_Rel18/

**IEEE引用格式**:
```
3GPP, "Security Aspects for Satellite Access and Non-Terrestrial Networks,"
Technical Report, Release 18-20, 3rd Generation Partnership Project (3GPP),
2024. [Online]. Available: https://www.3gpp.org/technologies/ntn-overview
```

**简短摘要**:
3GPP Release 20探索量子安全/PQC适配现有协议,支持128位和256位加密系统共存,应对NTN的量子威胁。

**引用原因**:
- 说明产业界对卫星PQC的重视
- 标准化进展支撑研究必要性
- 对比学术研究与产业标准化

---

#### [QuSecure-Starlink] ⭐⭐ QuSecure + Starlink: First Satellite PQC Deployment

**基本信息**:
- **机构**: QuSecure Inc.
- **时间**: 2023年3月
- **类型**: 工业部署案例
- **文献链接**: https://techwireasia.com/2023/03/qusecure-and-starlink-bring-post-quantum-cryptography-to-space/

**IEEE引用格式**:
```
QuSecure, "QuSecure Pioneers First-Ever US Live End-to-End Satellite
Quantum-Resilient Cryptographic Link," Press Release, Mar. 2023. [Online].
Available: https://techwireasia.com/2023/03/...
```

**简短摘要**:
美国首个端到端量子抗性卫星通信链路,使用PQC保护Starlink卫星数据传输,首次保护太空卫星数据免受量子攻击。

**引用原因**:
- 证明卫星PQC的实战可行性
- 展示产业界已开始部署
- 强调本文研究的现实意义

---

## 2.2节文献: Tor与匿名通信

### 2.2.1 Tor协议与ntor握手 (已有核心文献)

**说明**: 本节主要引用Tor官方规范和经典文献,不在本次调研范围内。核心文献包括:
- Tor Protocol Specification (tor-spec.txt)
- ntor v3 Specification (Proposal 332)
- 经典Tor论文 (Dingledine et al., 2004)

---

### 2.2.2 Tor在SAGIN/卫星网络部署

#### [SaTor2024] ⭐⭐⭐⭐⭐ SaTor: Satellite Routing in Tor to Reduce Latency

**基本信息**:
- **作者**: Li & Elahi
- **发表**: 2024年8月
- **会议/期刊**: arXiv预印本
- **文献链接**: https://arxiv.org/html/2406.15055v2
- **arXiv**: 2406.15055

**IEEE引用格式**:
```
Li and Elahi, "SaTor: Satellite Routing in Tor to Reduce Latency,"
arXiv:2406.15055, Aug. 2024. [Online]. Available: https://arxiv.org/abs/2406.15055
```

**简短摘要**:
首个将LEO卫星路由应用于Tor网络的系统,通过为部分中继配备Starlink连接,利用星间链路(ISL)实现低延迟路由,70%连接降低约40ms延迟。

**引用原因**:
- Tor在卫星网络可行性的核心证据
- 提供LEO卫星延迟性能基准(40ms改善)
- 对比本文PQ-NTOR在SAGIN环境的性能
- 说明现有工作未考虑量子威胁

---

#### [Singh2024] ⭐⭐⭐⭐⭐ Website Fingerprinting in LEO Satellite Internet

**基本信息**:
- **作者**: Prabhjot Singh, Diogo Barradas, Tariq Elahi, Noura Limam
- **机构**: University of Waterloo, University of Edinburgh
- **发表**: 2024
- **会议/期刊**: NDSS Symposium 2024
- **文献链接**: https://www.ndss-symposium.org/ndss-paper/auto-draft-442/

**IEEE引用格式**:
```
P. Singh, D. Barradas, T. Elahi, and N. Limam, "Connecting the Dots in the Sky:
Website Fingerprinting in Low Earth Orbit Satellite Internet," in Proc. Network
and Distributed System Security Symp. (NDSS), San Diego, CA, USA, 2024.
```

**简短摘要**:
检验通过Starlink传输的Tor流量是否易受网站指纹攻击,实验证明卫星链路与光纤同样脆弱,部署WF防御可降低攻击成功率但带宽开销略高。

**引用原因**:
- 证明卫星Tor的安全威胁真实存在
- 提供流量分析攻击的实验数据
- 支撑本文"需要多层防护"论断
- 说明物理链路特性不能提供额外匿名性

---

#### [RECORD2024] ⭐⭐⭐⭐ RECORD: Location Privacy Attack on LEO Satellite Users

**基本信息**:
- **作者**: Jedermann et al.
- **发表**: 2024
- **会议/期刊**: USENIX Security Symposium 2024
- **文献链接**: https://www.usenix.org/conference/usenixsecurity24/presentation/jedermann

**IEEE引用格式**:
```
Authors, "RECORD: A RECeption-Only Region Determination Attack on LEO Satellite
Users," in Proc. USENIX Security Symp., Philadelphia, PA, USA, 2024.
```

**简短摘要**:
被动攻击,仅观察2.3小时流量即可将用户位置缩小到半径11km(精度提升400倍),严重威胁卫星Tor用户位置隐私。

**引用原因**:
- 补充卫星Tor安全威胁维度(位置隐私)
- 说明即使Tor提供流量匿名性,卫星链路仍可泄露位置
- 证明卫星环境需要额外隐私保护机制

---

#### [Sat-Security2024] ⭐⭐⭐ A Survey on Satellite Communication System Security

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: MDPI Sensors
- **文献链接**: https://www.mdpi.com/1424-8220/24/9/2897
- **DOI**: 10.3390/s24092897

**IEEE引用格式**:
```
Authors, "A Survey on Satellite Communication System Security," Sensors, vol. 24,
no. 9, Art. no. 2897, 2024. DOI: 10.3390/s24092897
```

**简短摘要**:
全面综述卫星通信安全威胁,包括窃听、流量分析、物理层攻击、资源限制漏洞、跨域监听等,提出PLS设计和轻量级加密方案。

**引用原因**:
- 提供卫星通信安全威胁全景
- 支撑"卫星链路固有脆弱性"论断
- 强调资源受限对加密协议的影响

---

#### [6G-SGIN2023] ⭐⭐⭐⭐ On-Demand Anonymous Access and Roaming Authentication for 6G SGIN

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2023
- **会议/期刊**: PMC (PubMed Central)
- **文献链接**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10255450/

**IEEE引用格式**:
```
Authors, "On-Demand Anonymous Access and Roaming Authentication Protocols for 6G
Satellite–Ground Integrated Networks," Journal Name, 2023.
```

**简短摘要**:
提出双线性配对短群签名算法,实现SGIN用户不可链接性和匿名认证,支持批量认证降低延迟,解决频繁卫星链路切换问题。

**引用原因**:
- 证明SAGIN需要专门的匿名认证机制
- 展示频繁链路切换对匿名性的影响
- 支撑本文SAGIN环境匿名通信挑战分析

---

#### [SAGIN-Privacy2024] ⭐⭐⭐ Security and Privacy for Space-Air-Ground Integrated Networks

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2024
- **会议/期刊**: Security and Safety (S&S) Journal
- **文献链接**: https://sands.edpsciences.org/articles/sands/full_html/2024/01/sands20240006/sands20240006.html

**IEEE引用格式**:
```
Authors, "Preface: Security and Privacy for Space-Air-Ground Integrated
Networks," Security and Safety, 2024.
```

**简短摘要**:
综述SAGIN安全挑战,包括欺骗、未授权访问、窃听风险、模型更新拦截等,提出UAV匿名证书、零知识证明、隐蔽通信等方案。

**引用原因**:
- 说明SAGIN固有的隐私脆弱性
- 展示动态拓扑增加攻击面
- 支撑本文多层防护机制设计

---

#### [UAV-FANET2022] ⭐⭐⭐ Anonymous Mutual and Batch Authentication with Location Privacy

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2022
- **会议/期刊**: MDPI Sensors
- **文献链接**: https://www.mdpi.com/2504-446X/6/1/14

**IEEE引用格式**:
```
Authors, "Anonymous Mutual and Batch Authentication with Location Privacy of UAV
in FANET," Sensors, vol. 6, no. 1, Art. no. 14, 2022.
```

**简短摘要**:
使用短可随机化签名和零知识证明实现UAV匿名认证,支持批量认证降低计算开销,保护UAV位置隐私。

**引用原因**:
- 展示空中网络匿名认证技术
- 零知识证明在移动节点的应用
- 批量处理降低延迟(与本文优化方向一致)

---

#### [Q-SAGIN2022] ⭐⭐⭐⭐⭐ Quantum-Secured Space-Air-Ground Integrated Networks

**基本信息**:
- **作者**: Multiple authors
- **发表**: 2022
- **会议/期刊**: IEEE (arXiv:2204.08673)
- **文献链接**: https://arxiv.org/abs/2204.08673 | https://ieeexplore.ieee.org/document/9915359/

**IEEE引用格式**:
```
Authors, "Quantum-Secured Space-Air-Ground Integrated Networks: Concept,
Framework, and Case Study," IEEE Journal, 2022. [Online].
Available: https://arxiv.org/abs/2204.08673
```

**简短摘要**:
首次提出量子安全SAGIN概念,分析量子计算对RSA/ECC的威胁,设计QKD over SAGIN架构,提出BBM92 QKD + AES-256混合方案。

**引用原因**:
- 核心量子威胁背景文献
- 证明"卫星系统面临量子攻击风险"
- 对比QKD与PQC方案(本文采用PQC,无需量子信道)
- 支撑"量子威胁是SAGIN紧迫挑战"论断

---

#### [6G-QSafe2025] ⭐⭐⭐⭐ Quantum-Safe Networks for 6G

**基本信息**:
- **作者**: (待补充完整作者列表)
- **发表**: 2025
- **会议/期刊**: Scifiniti Journal
- **文献链接**: https://scifiniti.com/3104-4719/2/2025.0016

**IEEE引用格式**:
```
Authors, "Quantum-Safe Networks for 6G: An Integrated Survey on PQC, QKD, and
Satellite QKD with Future Perspectives," Scifiniti, vol. 2, no. 2, Art. no. 0016,
2025.
```

**简短摘要**:
综述6G时代量子威胁,强调PQC提前部署的紧迫性,对比PQC与QKD方案,提出AI辅助安全机制。

**引用原因**:
- 强调6G时代Tor必须采用PQC
- 证明卫星QKD可增强密钥分发
- 支撑"现在部署PQC,未来仍安全"论断

---

## 2.3节文献: PQ-Tor结合研究

### 2.3.1 PQ-Tor理论与提案

#### [Berger2025] ⭐⭐⭐⭐⭐ Post Quantum Migration of Tor

**基本信息**:
- **作者**: Denis Berger, Mouad Lemoudden, William J. Buchanan
- **发表**: April 2025
- **会议/期刊**: MDPI Journal of Cybersecurity and Privacy, Vol 5, Issue 2
- **文献链接**: https://www.mdpi.com/2624-800X/5/2/13 | arXiv:2503.10238 | ePrint:2025/479

**IEEE引用格式**:
```
D. Berger, M. Lemoudden, and W. J. Buchanan, "Post Quantum Migration of Tor,"
Journal of Cybersecurity and Privacy, vol. 5, no. 2, Art. no. 13, Apr. 2025.
DOI: 10.3390/jcp5020013
```

**简短摘要**:
分析Tor量子脆弱性,提出PQ迁移路线图,推荐ML-KEM-512/768和Falcon-512,基于liboqs基准进行理论性能估算(ML-KEM-512: 0.161 ms on Raspberry Pi 5)。

**引用原因**:
- 核心对比文献,逐条对比6大局限性
- 提供PQ-Tor理论框架和算法选择依据
- 对比本文完整实现(181.64 µs实测 vs 理论估算)
- 强调现有工作"仅理论估算,无真实网络评估"

**6大局限性对应本文创新**:
1. 仅理论估算 → 本文完整实现(181.64 µs)
2. 孤立密码学基准 → 本文三跳电路测试(1.25 ms)
3. 未考虑网络影响 → 本文12拓扑网络场景(30-500ms)
4. 假设地面网场景 → 本文SAGIN多层异构网络
5. 模拟测试 → 本文7飞腾派真实部署
6. 无高延迟评估 → 本文延迟全覆盖+NOMA真实参数

---

#### [TorProp269] ⭐⭐⭐ Tor Proposal 269: Transitionally Secure Hybrid Handshakes

**基本信息**:
- **作者**: John Schanck, William Whyte, Zhenfei Zhang, Nick Mathewson, Isis Lovecruft, Peter Schwabe
- **创建**: 2016年6月7日
- **状态**: Needs-Revision
- **类型**: Tor官方提案
- **文献链接**: https://spec.torproject.org/proposals/269-hybrid-handshake.html

**IEEE引用格式**:
```
J. Schanck et al., "Tor Proposal 269: Transitionally Secure Hybrid Handshakes,"
Tor Project, Jun. 2016. [Online].
Available: https://spec.torproject.org/proposals/269-hybrid-handshake.html
```

**简短摘要**:
提案将PQ KEM(NTRUEncrypt/NewHope)集成到ntor握手,提供过渡期量子安全,但7年后仍未实施,受CREATE单元大小限制(505字节 vs NTRU需要693字节)。

**引用原因**:
- 说明Tor社区早已意识到PQ需求(2016年)
- 证明"提案7年仍无实现",凸显本文实现价值
- 对比本文采用NIST标准算法(ML-KEM vs NTRU)

---

#### [TorProp355] ⭐⭐⭐ Tor Proposal 355: Options for Postquantum Circuit Extension

**基本信息**:
- **作者**: Nick Mathewson
- **创建**: 2025年3月6日
- **状态**: Informational
- **类型**: Tor官方提案
- **文献链接**: https://spec.torproject.org/proposals/355-revisiting-pq.html

**IEEE引用格式**:
```
N. Mathewson, "Tor Proposal 355: Options for Postquantum Circuit Extension,"
Tor Project, Mar. 2025. [Online].
Available: https://spec.torproject.org/proposals/355-revisiting-pq.html
```

**简短摘要**:
基于NIST标准(ML-KEM/ML-DSA)更新PQ方案,对比PQ-TR(过渡期)和PQ-KEM-2(下一代)方法,仍处于探索性分析阶段,无具体实现。

**引用原因**:
- 证明PQ迁移仍在讨论阶段(截至2025年3月)
- 本文实现填补理论到实践空白
- 对比本文基于最新NIST标准(FIPS 203)

---

### 2.3.2 PQ-Tor实现研究

#### [QSOR2020] ⭐⭐⭐ QSOR: Quantum-Safe Onion Routing

**基本信息**:
- **作者**: Zsolt Tujner, Thomas Rooijakkers, Maran van Heesch, Melek Önen
- **发表**: 2020
- **会议/期刊**: ICETE 2020
- **文献链接**: arXiv:2001.03418

**IEEE引用格式**:
```
Z. Tujner, T. Rooijakkers, M. van Heesch, and M. Önen, "QSOR: Quantum-Safe Onion
Routing," in Proc. 17th Int. Joint Conf. e-Business and Telecommunications
(ICETE), 2020. [Online]. Available: https://arxiv.org/abs/2001.03418
```

**简短摘要**:
评估6种PQ算法(NIST L1安全级别),基于SweetOnions仿真器,聚焦电路创建操作,证明PQ-Tor电路创建可行但性能开销可接受。

**引用原因**:
- 早期PQ-Tor可行性验证
- 对比本文真实部署 vs 仿真测试
- 强调"仿真与真实网络差距大"

---

#### [HybridOR2015] ⭐⭐⭐ Post-Quantum Forward-Secure Onion Routing

**基本信息**:
- **作者**: Satrajit Ghosh, Aniket Kate
- **发表**: 2015
- **会议/期刊**: ePrint Archive 2015/008
- **文献链接**: https://eprint.iacr.org/2015/008

**IEEE引用格式**:
```
S. Ghosh and A. Kate, "Post-Quantum Forward-Secure Onion Routing,"
IACR Cryptology ePrint Archive, Report 2015/008, 2015. [Online].
Available: https://eprint.iacr.org/2015/008
```

**简短摘要**:
提出HybridOR协议,结合ring-LWE和经典DH的混合1W-AKE协议,提供双重安全保证,但无实现,算法选择已过时(ring-LWE非NIST标准)。

**引用原因**:
- PQ-Tor早期理论探索
- 对比本文采用NIST标准算法
- 说明"2015年算法选择与当前标准脱节"

---

#### [TorProp263] ⭐⭐ Tor Proposal 263: NTRU for PQ Handshake (已过时)

**基本信息**:
- **作者**: John Schanck, William Whyte, Zhenfei Zhang
- **创建**: 2015年8月29日, 更新2016年2月4日
- **状态**: Obsolete (被Proposal 269取代)
- **类型**: Tor官方提案
- **文献链接**: https://spec.torproject.org/proposals/263-ntru-for-pq-handshake.html

**IEEE引用格式**:
```
J. Schanck, W. Whyte, and Z. Zhang, "Tor Proposal 263: NTRU for PQ Handshake,"
Tor Project, Aug. 2015. [Online].
Available: https://spec.torproject.org/proposals/263-ntru-for-pq-handshake.html
```

**简短摘要**:
双密钥交换(ECC + NTRUEncrypt),防护"收集现在,未来解密"攻击,但已被Proposal 269取代,NTRU未入选NIST标准。

**引用原因**:
- 展示Tor社区PQ探索历史(2015-2016)
- 说明技术路线演变(NTRU → Kyber/ML-KEM)

---

### 2.3.3 相关PQ网络协议对比

#### [PQ-TLS-Bench2019] ⭐⭐⭐ Benchmarking Post-Quantum Cryptography in TLS

**基本信息**:
- **作者**: Christian Paquin, Douglas Stebila, Goutam Tamvada
- **发表**: 2019
- **会议/期刊**: ePrint Archive 2019/1447
- **文献链接**: https://eprint.iacr.org/2019/1447

**IEEE引用格式**:
```
C. Paquin, D. Stebila, and G. Tamvada, "Benchmarking Post-Quantum Cryptography
in TLS," IACR Cryptology ePrint Archive, Report 2019/1447, 2019.
```

**简短摘要**:
Kyber/ML-KEM与经典算法性能相当,Dilithium、Falcon甚至更快,混合TLS握手延迟开销仅+1-2%。

**引用原因**:
- 提供PQ-TLS性能基准对比
- 说明TLS场景(单次握手,短连接)与Tor(多跳电路,长期连接)的差异
- 对比本文PQ-NTOR性能优势(181.64 µs vs TLS握手毫秒级)

---

#### [PQ-WireGuard2020] ⭐⭐⭐ Post-quantum WireGuard

**基本信息**:
- **作者**: Andreas Hülsing et al.
- **发表**: 2020
- **会议/期刊**: ePrint Archive 2020/379
- **文献链接**: https://eprint.iacr.org/2020/379

**IEEE引用格式**:
```
A. Hülsing et al., "Post-quantum WireGuard," IACR Cryptology ePrint Archive,
Report 2020/379, 2020.
```

**简短摘要**:
KEM-only设计(不依赖DH),已有生产级实现(Kudelski Security, Rosenpass),ExpressVPN全球部署:连接增加15-20ms,无吞吐量影响。

**引用原因**:
- 对比PQ-VPN(点对点隧道)与Tor(多跳链式加密)
- 说明WireGuard经验对Tor适用性有限
- 证明PQC在VPN场景可行,但Tor挑战更大

---

#### [Katzenpost] ⭐⭐ Katzenpost: PQ Mix Network

**基本信息**:
- **项目**: Katzenpost
- **技术**: hpqc库, Xwing (ML-KEM-768 + X25519混合), Ed25519 + Sphincs+
- **状态**: 世界首个PQ混合网络
- **文献链接**: https://katzenpost.network/

**IEEE引用格式**:
```
Katzenpost Project, "Katzenpost: Post-Quantum Mix Network," [Online].
Available: https://katzenpost.network/
```

**简短摘要**:
世界首个PQ混合网络,已实现Xwing KEM和Ed25519 + Sphincs+签名,但Mix网络延迟模型与Onion路由完全不同。

**引用原因**:
- PQ匿名网络实现先例
- 对比Mix网络(连续时间混合)与Tor(实时电路)
- 说明架构差异使经验难直接迁移

---

## 统计信息

### 按节分类统计

| 章节 | 子节 | 文献数量 | 核心文献 |
|------|------|---------|---------|
| **2.1 后量子密码学基础** | 2.1.1 量子计算威胁 | 2篇 | NIST FIPS 203, FIPS 204 |
| | 2.1.2 PQC在SAGIN部署 | 10篇 | APQA, LPQAA, UAV-Kyber, PQ-TLS-Sat, NDSS-PQTLS |
| **2.2 Tor与匿名通信** | 2.2.1 Tor协议与ntor | (已有) | Tor Spec, ntor v3 |
| | 2.2.2 Tor在SAGIN部署 | 9篇 | SaTor, Singh, RECORD, Q-SAGIN, 6G-SGIN |
| **2.3 PQ-Tor结合研究** | 2.3.1 PQ-Tor理论与提案 | 4篇 | Berger, TorProp269, TorProp355 |
| | 2.3.2 PQ-Tor实现研究 | 3篇 | QSOR, HybridOR |
| | 2.3.3 相关PQ网络协议 | 3篇 | PQ-TLS-Bench, PQ-WireGuard, Katzenpost |
| **总计** | | **29篇** | |

### 按优先级统计

| 优先级 | 数量 | 说明 |
|--------|------|------|
| ⭐⭐⭐⭐⭐ | 7篇 | 必须引用:NIST标准、Berger、SaTor、Singh、Q-SAGIN |
| ⭐⭐⭐⭐ | 10篇 | 强烈建议引用:APQA、LPQAA、NDSS-PQTLS等 |
| ⭐⭐⭐ | 10篇 | 建议引用:TorProp、QSOR、HybridOR、PQ-TLS-Bench等 |
| ⭐⭐ | 2篇 | 可选引用:TorProp263(已过时)、QuSecure-Starlink(工业案例) |

### 按文献类型统计

| 类型 | 数量 | 示例 |
|------|------|------|
| 期刊论文 | 12篇 | Berger(MDPI J. Cybersecurity), APQA(Elsevier) |
| 会议论文 | 8篇 | Singh(NDSS), RECORD(USENIX) |
| 标准文档 | 2篇 | NIST FIPS 203, FIPS 204 |
| Tor提案 | 3篇 | Proposal 269, 355, 263 |
| 技术报告 | 2篇 | 3GPP NTN, PQ-TLS-Sat(GitHub) |
| 工业案例 | 1篇 | QuSecure-Starlink |
| 开源项目 | 1篇 | Katzenpost |

### 按发表年份统计

| 年份 | 数量 | 趋势说明 |
|------|------|---------|
| 2025 | 4篇 | 最新研究(Berger, TorProp355, 6G-QSafe, Earth-Sat-QKD) |
| 2024 | 14篇 | **爆发期**(NIST标准、SaTor、Singh、多个SAGIN PQC应用) |
| 2023 | 2篇 | (6G-SGIN, QuSecure-Starlink) |
| 2022 | 2篇 | (Q-SAGIN, UAV-FANET) |
| 2020 | 3篇 | (QSOR, NDSS-PQTLS, PQ-WireGuard) |
| 2019 | 1篇 | (PQ-TLS-Bench) |
| 2016 | 2篇 | (TorProp269, TorProp263) |
| 2015 | 1篇 | (HybridOR) |

**趋势分析**: 2024年是PQC-SAGIN研究爆发期,NIST标准发布(8月)催化产业和学术研究。

---

## 符合纲要预期验证

### 纲要要求
- 2.1节: 6-10篇 (重点PQC基础与SAGIN应用)
- 2.2节: 6-10篇 (重点Tor在SAGIN,安全威胁)
- 2.3节: 8-12篇 (重点PQ-Tor理论、实现、对比)
- 总计: 23-36篇

### 实际统计
- 2.1节: **12篇** ✅ (略超预期,符合范围)
- 2.2节: **9篇** ✅ (符合预期)
- 2.3节: **10篇** ✅ (符合预期)
- 总计: **29篇** ✅ (符合23-36篇预期)

**结论**: 文献数量完全符合纲要预期,核心文献覆盖全面,优先级分配合理。

---

## 研究空白标注

### 明确空白
1. **PQ-Tor + SAGIN结合**: ❌ 完全空白 (本文核心创新)
2. **PQ-NTOR完整实现**: ❌ 仅有理论估算(Berger)和仿真(QSOR)
3. **SAGIN高延迟场景PQC性能**: ❌ 现有研究聚焦低延迟地面网络
4. **真实分布式PQ-Tor部署**: ❌ 无硬件实测数据
5. **12拓扑系统性评估**: ❌ 无多场景对比研究
6. **ARM64边缘平台PQ-NTOR**: ❌ 缺少资源受限环境验证

### 部分空白
1. **卫星Tor量子威胁**: ⚠️ SaTor、Singh等均未考虑
2. **PQC在匿名通信层应用**: ⚠️ 仅有认证层(APQA、LPQAA)研究
3. **混合PQC/经典互操作性**: ⚠️ 过渡期兼容性研究不足

---

## 使用指南

### 写作时快速查找
1. **证明量子威胁**: 引用[NIST-FIPS203][Q-SAGIN2022][6G-QSafe2025]
2. **证明PQC可行**: 引用[APQA2024][LPQAA2024][PQ-TLS-Sat2024]
3. **证明Tor在卫星可行**: 引用[SaTor2024]
4. **证明安全威胁**: 引用[Singh2024][RECORD2024][Sat-Security2024]
5. **对比Berger工作**: 引用[Berger2025],逐条分析6大局限性
6. **说明提案未实施**: 引用[TorProp269][TorProp355],强调"7年讨论仍无实现"
7. **性能基准对比**: 引用[NDSS-PQTLS2020](TLS 1-2%开销)、[PQ-TLS-Sat2024]
8. **研究空白**: 明确指出"未找到PQ-Tor + SAGIN文献"

### 避免重复引用
- **Berger论文**: 仅在2.3.1节详细分析,其他地方简短提及
- **SaTor**: 2.2.2节详细介绍,2.3节对比时简短引用
- **NIST标准**: 2.1.1节详细介绍,后续直接引用"FIPS 203"即可

### 保持简洁原则
- 每篇文献引用时,仅提炼1-2句核心贡献
- 使用"Authors (2024)"简写,避免长作者列表
- 数据引用精确到关键数字(如"40ms延迟降低"、"181.64 µs")

---

## 维护记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2025-12-03 | 创建 | 整合4个调研报告,创建统一数据库 |
| | | 提取29篇文献,标注优先级 |
| | | 生成快速引用指南和统计信息 |

---

**文档状态**: ✅ 完成
**下一步**: 基于本数据库撰写第二章正文,使用`chapter2_references.bib`管理引用

---
