# PQC在SAGIN部署文献调研 - 快速总结

## 核心发现 (TL;DR)

### 找到的文献
- **8篇核心学术论文** (2020-2025)
- **4项工业部署案例** (QuSecure+Starlink, SEALSQ, SoftBank, ESA)
- **3GPP标准化文档** (Release 17-20)

### 关键结论
1. **研究现状**: 2023-2025年爆发期,主要集中在**认证与密钥协商**
2. **技术成熟度**: NIST标准化完成(2024),卫星TLS性能开销<2%
3. **研究空白**: **PQC在卫星匿名通信(Tor)几乎空白** → 本文核心创新点
4. **最佳算法**: Kyber(KEM) + Falcon(签名)适合卫星环境

---

## 一、8篇核心文献速查

### SAGIN认证协议 (3篇)

**[1] APQA - Computer Networks 2024**
- 基于RLWE格密码的匿名认证
- **性能**: 计算时间减少36%
- **应用**: 空地一体网络(SGIN)

**[2] LPQAA - Journal of Supercomputing 2024**
- 轻量级卫星网络认证
- **性能**: 认证时间减少150%
- **特点**: 专门优化资源受限环境

**[3] Q-SAGIN - IEEE 2022**
- 量子安全SAGIN框架(QKD+PQC)
- **局限**: 主要讨论QKD,PQC为辅

### UAV/无人机 (2篇)

**[4] LIGKYX - MDPI 2024**
- Kyber + HMAC认证方案
- **应用**: IoT无人机网络

**[5] Anonymous IoD - ScienceDirect 2024**
- RLWE格密码 + 匿名性
- **特点**: 动态身份管理

### TLS性能评估 (2篇)

**[6] pq-tls-satcom-benchmark - GitHub 2024**
- **重要**: 卫星TLS握手性能基准测试工具
- **对比基线**: 本文可直接参考

**[7] PQ-TLS Performance - NDSS 2020**
- **核心数据**: 混合握手仅+1-2%延迟
- Kyber < McEliece (低带宽场景)

### 地-卫混合安全 (1篇)

**[8] Combined Security - IEEE QCNC 2025**
- BBM92协议: AES(PQC) + QKD
- **创新**: 首个混合方案实际部署

---

## 二、工业部署案例

| 时间 | 机构 | 技术 | 意义 |
|------|------|------|------|
| 2023.03 | QuSecure + Starlink | PQC保护卫星链路 | 美国首个端到端量子抗性卫星通信 |
| 2025.11 | SEALSQ WISeSat | PQC芯片卫星 | 5颗卫星星座计划 |
| 2023 | SoftBank | 4G/5G混合加密试验 | 现有基础设施性能影响极小 |
| 进行中 | ESA E2EQSS | 欧洲卫星PQC项目 | 欧空局官方项目 |

---

## 三、关键性能数据

| 指标 | 数值 | 来源 |
|------|------|------|
| **TLS握手延迟开销** | +1-2% | NDSS 2020 |
| **Kyber-512操作时间** | 数十微秒 | 多源 |
| **Dilithium密钥大小** | ~2KB | CRYSTALS |
| **混合方案能耗增加** | 2.3倍 | 相比Curve25519 |
| **APQA计算时间减少** | 36% | APQA论文 |
| **LPQAA认证加速** | 150% | LPQAA论文 |

**卫星延迟参考**:
- LEO: 20-40ms
- GEO: 250-600ms

---

## 四、研究空白分析

### 已有研究 (成熟)
- PQC认证协议 (SAGIN/卫星)
- TLS/DTLS性能评估 (一般网络)
- UAV/IoT轻量级PQC
- 卫星QKD (非PQC)

### 研究空白 (本文机会)

#### **严重空白: PQC + 匿名通信**
- **现状**: 仅1篇综述理论研究(HybridOR协议)
- **缺失**:
  - 无PQC-Tor over Satellite实现
  - 无卫星环境Onion Routing性能评估
  - 无SAGIN匿名通信PQC部署方案

#### **本文创新点**
1. **首个** PQC-NTOR在SAGIN的应用研究
2. 高延迟/窄带宽环境的Onion Routing适配
3. 匿名性 + 量子抗性的双重安全目标

---

## 五、PQC算法选择建议

### 卫星环境推荐

| 算法 | 类型 | NIST状态 | 适用性 | 原因 |
|------|------|----------|--------|------|
| **Kyber** | KEM | FIPS 203 | 高 | 密钥小、速度快、低延迟 |
| **Falcon** | 签名 | 候选 | 高 | 密钥小于Dilithium |
| Dilithium | 签名 | FIPS 204 | 中 | 密钥2KB,CPU中等 |
| SPHINCS+ | 签名 | FIPS 205 | 低 | 密钥极大,不适合卫星 |

**本文NTOR选择**: Kyber-512 (与Classic NTOR的Curve25519对应)

---

## 六、论文第2.1.2节写作框架

### 建议段落结构

**段落1: SAGIN量子威胁 (2-3句)**
- 引用Q-SAGIN概念[文献3]
- 引用3GPP Release 20标准化
- 数据: 量子计算对ECC/RSA的威胁时间表

**段落2: PQC部署现状 (3-4句)**
- NIST标准化完成(2024, FIPS 203-205)
- 工业部署: QuSecure+Starlink(2023), SoftBank试验
- 性能可行性: TLS握手<2%开销[文献7]

**段落3: 现有研究方向 (4-5句)**
- **认证协议**: APQA[文献1], LPQAA[文献2], UAV方案[文献4,5]
- **TLS层**: 卫星基准测试[文献6], 性能研究[文献7]
- **混合方案**: 地-卫混合安全[文献8]
- 数据: APQA减少36%计算,LPQAA加速150%

**段落4: 部署挑战 (3-4句)**
- **带宽**: Dilithium密钥2KB vs 卫星窄带上行
- **延迟**: GEO 600ms RTT影响握手
- **资源**: 在轨卫星计算/内存/功耗受限
- 解决方向: 轻量级格密码,网络协作计算

**段落5: 研究空白引出本文 (2-3句)**
- **现有工作**: 集中在认证/TLS层,匿名通信层空白
- **研究缺失**: 无PQC-Onion Routing在SAGIN的研究
- **本文创新**: 首个PQC-NTOR的卫星/SAGIN适配与性能评估

### 参考文献标注示例

```
SAGIN面临量子计算威胁,现有ECC/RSA加密将在10-15年内被破解[Q-SAGIN]。
3GPP Release 20已将PQC纳入NTN标准化路线图[3GPP TR]。工业界已开始
部署,如QuSecure在2023年实现首个Starlink卫星PQC链路[QuSecure]。

现有研究主要集中在认证协议,如基于RLWE的APQA方案将计算时间减少36%[APQA],
LPQAA针对卫星资源受限优化认证速度提升150%[LPQAA]。TLS层性能研究表明,
混合ECDHE+Kyber握手仅增加1-2%延迟[NDSS 2020],Kyber-512操作时间
仅数十微秒[benchmark],证明PQC在卫星环境的可行性。

然而,PQC在匿名通信层的研究几乎空白。现有工作未涉及PQC-Onion Routing
在高延迟、窄带宽SAGIN环境的适配。本文首次研究PQC-NTOR在卫星网络的
部署,填补该领域空白。
```

---

## 七、重要数据引用

### 直接可用的性能数据

**TLS握手开销**:
```
混合TLS握手(ECDHE + Kyber): 仅增加1-2%延迟 [NDSS 2020]
Kyber-512: 数十微秒 (Intel Haswell + AVX2)
Dilithium2: 数百微秒 (签名/验证)
```

**认证协议性能**:
```
APQA: 计算时间减少36% [Computer Networks 2024]
LPQAA: 认证时间减少150% [J. Supercomputing 2024]
```

**带宽开销**:
```
Dilithium密钥: ~2KB
Kyber密文: ~1KB
传统ECC: ~64 bytes (25x差距)
```

---

## 八、Sources (完整引用链接)

### 学术文献
- [APQA] https://www.sciencedirect.com/science/article/abs/pii/S1389128624008119
- [LPQAA] https://link.springer.com/article/10.1007/s11227-024-06687-5
- [Q-SAGIN] https://ieeexplore.ieee.org/document/9915359/
- [LIGKYX] https://www.mdpi.com/2504-446X/8/8/359
- [Anonymous IoD] https://www.sciencedirect.com/science/article/abs/pii/S0045790624007018
- [pq-tls-benchmark] https://github.com/lin-1214/pq-tls-satcom-benchmark
- [NDSS 2020] https://www.ndss-symposium.org/ndss-paper/post-quantum-authentication-in-tls-1-3-a-performance-study/
- [QCNC 2025] https://arxiv.org/html/2502.14240v1

### 工业与标准
- [QuSecure+Starlink] https://techwireasia.com/2023/03/qusecure-and-starlink-bring-post-quantum-cryptography-to-space/
- [SEALSQ] https://www.sealsq.com/investors/news-releases/sealsq-to-secure-space-transactions-with-post-quantum-technology-to-support-the-next-wisesat-launch-scheduled-for-november-2025
- [3GPP NTN] https://www.3gpp.org/technologies/ntn-overview
- [ESA E2EQSS] https://connectivity.esa.int/projects/e2eqss

### 技术资源
- [NIST PQC] https://csrc.nist.gov/projects/post-quantum-cryptography
- [CRYSTALS] https://pq-crystals.org/

---

**最后更新**: 2025-12-03
**文献数量**: 8篇核心论文 + 4项部署案例
**关键结论**: **PQC在SAGIN匿名通信是空白 → 本文核心创新**
