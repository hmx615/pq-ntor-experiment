# Section 2.2.2: Tor/匿名通信在SAGIN/卫星/非地面网络中的部署 - 文献调研报告

**调研日期**: 2025-12-03
**调研目的**: 为论文第2.2.2节提供文献支撑
**调研方向**: Tor在卫星网络、SAGIN、非地面网络中的部署、性能、安全威胁及挑战

---

## 📋 执行摘要

本次调研共识别出**10篇核心文献**,涵盖以下四个方向:
1. **卫星网络中的Tor研究** (3篇)
2. **卫星Tor的安全威胁** (2篇)
3. **空地一体化网络中的匿名通信** (3篇)
4. **量子威胁与后量子密码** (2篇)

**关键发现**:
- ✅ **找到重点文献**: Singh et al. (2024) NDSS - LEO卫星网络流量指纹攻击
- ⚠️ **未找到**: Albrecht et al. (2023) 关于卫星网络匿名性的论文(可能不存在或命名不同)
- 🎯 **核心贡献**: SaTor系统展示了Tor在LEO卫星网络的可行性,延迟降低40ms
- 🔴 **研究空白**: 现有工作均未考虑量子威胁对卫星Tor的影响

---

## 📚 一、卫星网络中的Tor研究 (除SaTor外)

### 1.1 ⭐ SaTor: Satellite Routing in Tor to Reduce Latency (2024)

**作者**: Li & Elahi (已在核心文献中)
**来源**: arXiv:2406.15055
**关键词**: Tor, LEO Satellite, Starlink, Latency Reduction, ISL

**摘要核心点**:
- SaTor是首个将LEO卫星路由应用于Tor网络的系统
- 通过为部分Tor中继配备卫星连接(如Starlink),创建双归属中继
- 利用星间链路(ISL)在真空中传输,实现低延迟路由

**性能数据**:
- **延迟降低**: 70%的连接可降低约40ms延迟
- **测试规模**: 7,280条电路,100k+ Tor电路模拟
- **实验时间**: 2024年8月,使用Starlink真实数据
- **卫星延迟**: 基于LENS数据集(2024年4-5月)
- **ISL路由**: 保持大部分传输路径在太空真空中,延迟优于单跳弯管路由

**技术细节**:
- 双探测机制: 通过地面和卫星接口同时测量延迟
- 动态路径选择: 根据实时延迟选择最优路由
- Starlink参数: 5,536颗卫星,轨道高度550km,覆盖全球

**局限性**:
- ❌ 未考虑量子威胁
- ❌ 仅针对Starlink单一卫星星座
- ❌ 依赖ISL可用性(70%客户每天至少遇到一次延迟峰值)

**引用价值**: ⭐⭐⭐⭐⭐ (核心文献,已在2.2.1节引用)

---

### 1.2 Onion Routing in Satellite Networks (综合调研)

**来源**: Multiple sources (Onion Router Publications, Blockstream Satellite API)
**关键词**: Onion Routing, Satellite Communication, Privacy, Anonymous Broadcast

**技术应用**:
1. **Blockstream Satellite API**
   - 提供全球卫星广播服务
   - 通过洋葱路由增强隐私保护
   - 结合闪电网络支付匿名化
   - **隐私特点**: 广播数据无法确定源和目的地

2. **6G IoT卫星网络中的洋葱路由**
   - 基于区块链的安全洋葱路由框架
   - 用于IoT环境数据分发
   - 通过卫星通信自动同步全球数据

3. **历史背景**
   - 匿名连接可保护用户在有线、蜂窝、卫星电话网络中的身份和位置
   - 洋葱路由专利(US6266704B1)涵盖卫星通信场景

**性能挑战**:
- 卫星链路高延迟(30-500ms)
- 有限带宽限制
- 星座管理复杂性

**引用价值**: ⭐⭐⭐ (背景补充)

---

### 1.3 LEO Satellite Network Performance and Routing

**来源**: Multiple research (APNIC Blog, IEEE, ACM)
**关键词**: LEO Constellation, Inter-Satellite Link, Routing Latency, Performance Measurement

**关键发现**:
1. **LEO卫星特性**
   - 轨道高度: 500-2,000km
   - 延迟优势: 远低于地球同步卫星
   - 星座规模: Starlink 5,650+卫星 (截至2023年12月)

2. **ISL性能**
   - 激光链路: 真空光速传输
   - 延迟问题: 完全依赖ISL的客户延迟远高于理论值
   - 稳定性: 70%客户每天至少遇到一次延迟峰值

3. **路由算法**
   - SGRP: 最短延迟路径传输
   - HSRP: 满足延迟约束的分层路由
   - ORPHSN: 多指标优化(传播延迟、队列延迟、链路利用率)

4. **匿名性挑战**
   - 拓扑高度动态
   - 星载计算和存储能力有限
   - 不支持高复杂度加密协议
   - 流量数据保护较弱

**性能数据**:
- ISL路由: 可能降低延迟,但实际性能不稳定
- 资源限制: 卫星无法运行复杂加密算法
- 拓扑变化: 星座持续移动,路由需动态适应

**引用价值**: ⭐⭐⭐⭐ (技术背景)

---

## 🔒 二、卫星Tor的安全威胁

### 2.1 ⭐⭐⭐ Connecting the Dots in the Sky: Website Fingerprinting in LEO Satellite Internet (Singh et al., 2024)

**作者**: Prabhjot Singh, Diogo Barradas, Tariq Elahi, Noura Limam
**机构**: University of Waterloo, University of Edinburgh
**来源**: NDSS Symposium 2024
**关键词**: Website Fingerprinting, Starlink, Tor, LEO Satellite, Traffic Analysis

**研究目标**:
检验通过LEO卫星(Starlink)传输的Tor流量是否容易受到网站指纹攻击

**实验设计**:
- **测试平台**: Starlink卫星连接 + 传统光纤连接对比
- **攻击场景**: 网站指纹攻击(Website Fingerprinting)
- **防御机制**: 部署WF防御并评估带宽开销

**核心发现**:
1. **攻击有效性**:
   - Tor流量通过Starlink传输与光纤一样易受指纹攻击
   - LEO网络特性(延迟、抖动)并未降低攻击成功率

2. **防御效果**:
   - 部署WF防御可大幅降低攻击成功率
   - Starlink上的防御带宽开销仅略高于光纤

3. **安全启示**:
   - 卫星链路的物理特性不能提供额外匿名性保护
   - 需要专门的流量混淆防御机制

**性能数据**:
- 攻击成功率: Starlink ≈ 光纤(具体数值见论文)
- 防御开销: 带宽增加 <5%(推测)
- 测试规模: 多轮Starlink真实网络测试

**局限性**:
- ❌ 未考虑量子计算威胁
- ❌ 仅针对Starlink单一卫星网络
- ❌ 未涉及ISL链路的流量分析

**引用价值**: ⭐⭐⭐⭐⭐ (重点文献,直接支撑2.2.2节安全威胁分析)

**文献链接**:
- NDSS版本: https://www.ndss-symposium.org/ndss-paper/auto-draft-442/
- UWaterloo版本: https://uwspace.uwaterloo.ca/items/f1fece74-5eb5-4b2f-b6e3-e45f454e0a27

---

### 2.2 ⭐⭐⭐ RECORD: A RECeption-Only Region Determination Attack on LEO Satellite Users (2024)

**来源**: USENIX Security 2024
**关键词**: Location Privacy, LEO Satellite, Passive Attack, Traffic Analysis

**攻击方法**:
- **类型**: 被动攻击,利用LEO卫星下行链路
- **目标**: 定位卫星用户地理位置
- **机制**: 利用移动卫星通信特性

**攻击效果**:
- **时间**: 仅需2.3小时流量观察
- **精度**: 将用户位置缩小到半径11km
- **对比**: 初始卫星波束直径4700km → 11km (精度提升400+倍)

**隐私威胁**:
- 严重威胁卫星用户位置隐私
- 被动攻击难以检测
- 适用于所有LEO卫星星座

**对Tor的影响**:
- 即使Tor提供流量匿名性,卫星链路泄露位置信息
- 位置信息可用于去匿名化攻击
- 需要额外的位置隐私保护机制

**局限性**:
- ❌ 未考虑量子威胁
- ❌ 未测试与Tor结合的场景

**引用价值**: ⭐⭐⭐⭐ (补充安全威胁维度)

**文献链接**: https://www.usenix.org/conference/usenixsecurity24/presentation/jedermann

---

### 2.3 A Survey on Satellite Communication System Security (2024)

**来源**: MDPI Sensors 2024
**关键词**: Satellite Security, Eavesdropping, Traffic Analysis, LEO Vulnerability

**安全威胁综述**:

1. **窃听攻击 (Eavesdropping)**
   - **原因**: 卫星通信无线特性,信号开放
   - **范围**: 用户链路、星间链路(ISL)、馈线链路
   - **风险**: 数据易被拦截

2. **流量分析攻击**
   - 攻击者可分析流量模式
   - 结合数据窃听实施完整性攻击
   - 插入、修改、伪造窃取的数据

3. **物理层威胁**
   - 干扰(Jamming)
   - 欺骗(Spoofing)
   - DDoS攻击

4. **资源限制漏洞**
   - **计算能力有限**: 卫星无法运行高复杂度加密
   - **存储受限**: 限制密钥管理能力
   - **带宽受限**: 影响加密协议性能

5. **跨域监听**
   - 海外VLEO/LEO卫星可窃听本国卫星系统
   - 用户链路和馈线链路数据泄露

**安全方案**:
- 物理层安全(PLS)设计
- 轻量级加密协议
- 量子密钥分发(QKD)

**对Tor的启示**:
- 卫星链路固有的安全脆弱性
- 需要考虑链路层和物理层威胁
- 量子威胁是未来挑战

**引用价值**: ⭐⭐⭐⭐ (安全威胁综述)

**文献链接**: https://www.mdpi.com/1424-8220/24/9/2897

---

## 🌐 三、空地一体化网络中的匿名通信

### 3.1 ⭐⭐⭐ On-Demand Anonymous Access and Roaming Authentication Protocols for 6G Satellite–Ground Integrated Networks (2023)

**来源**: PMC (PubMed Central) 2023
**关键词**: 6G SGIN, Anonymous Authentication, Roaming, Unlinkability, Batch Authentication

**研究背景**:
- 6G卫星地面一体化网络(SGIN)安全和隐私挑战
- 高安全需求用户的匿名通信需求

**技术方案**:

1. **匿名不可链接认证协议**
   - **目标用户**: 高安全和隐私需求
   - **技术**: 双线性配对短群签名算法
   - **特性**:
     - 用户不可链接性
     - 匿名认证
     - 抗多种攻击

2. **批量认证协议**
   - **目标用户**: 大量UE,需要低延迟
   - **目的**: 提高认证效率
   - **场景**: 频繁卫星地球链路切换

3. **漫游认证**
   - 解决卫星地球链路频繁切换问题
   - 防止身份泄露
   - 防止中间人攻击

**性能考量**:
- 轻量级设计,适应卫星有限计算能力
- 低延迟认证,满足实时通信需求
- 高效批量处理,支持大规模用户

**对Tor的启示**:
- SAGIN需要专门的匿名认证机制
- 频繁链路切换影响匿名性
- 批量认证可降低延迟开销

**局限性**:
- ❌ 未考虑量子威胁
- ❌ 未涉及端到端匿名通信(如Tor)

**引用价值**: ⭐⭐⭐⭐ (SAGIN匿名性需求)

**文献链接**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10255450/

---

### 3.2 ⭐⭐ Preface: Security and Privacy for Space-Air-Ground Integrated Networks (2024)

**来源**: Security and Safety (S&S) Journal 2024
**关键词**: SAGIN Security, Privacy, UAV, Anonymity, Zero-Knowledge Proof

**SAGIN安全挑战**:

1. **架构特性**
   - 集成卫星(多轨道)、无人机、地面网络
   - 动态和去中心化特性
   - 复杂的多层网络集成

2. **安全威胁**
   - 欺骗(Spoofing)
   - 未授权访问
   - 卫星和无人机持续移动增加攻击面
   - 窃听风险

3. **隐私挑战**
   - 模型更新可能被未授权方拦截(联邦学习场景)
   - 动态拓扑增加成员推断攻击风险
   - 异构计算能力导致隐私保护不均

4. **匿名性方案**
   - **UAV隐私**: 匿名证书 + 零知识证明
   - **认证方法**: 实现互认证、身份匿名、抗多种攻击

5. **新型安全技术**
   - 隐蔽通信: 利用无线信道不确定性隐藏传输
   - 降低被第三方检测概率
   - 维持可靠通信

**对Tor的启示**:
- SAGIN固有的隐私脆弱性
- 需要多层防护机制
- 零知识证明可增强匿名性

**引用价值**: ⭐⭐⭐ (SAGIN安全背景)

**文献链接**: https://sands.edpsciences.org/articles/sands/full_html/2024/01/sands20240006/sands20240006.html

---

### 3.3 ⭐⭐ Anonymous Mutual and Batch Authentication with Location Privacy of UAV in FANET (2022)

**来源**: MDPI Sensors 2022
**关键词**: UAV, FANET, Anonymous Authentication, Short Randomizable Signature, Zero-Knowledge Proof

**技术方案**:
- **短可随机化签名**: 实现UAV匿名认证
- **零知识证明**: 保护UAV隐私
- **批量认证**: 降低计算开销
- **位置隐私**: 防止UAV位置泄露

**性能优势**:
- 仅需少量通信轮次
- 高效的计算性能
- 适合资源受限的UAV

**对Tor的启示**:
- 空中网络匿名认证机制
- 零知识证明在移动节点中的应用
- 批量处理降低延迟

**引用价值**: ⭐⭐⭐ (UAV匿名性技术)

**文献链接**: https://www.mdpi.com/2504-446X/6/1/14

---

## 🔐 四、量子威胁与后量子密码

### 4.1 ⭐⭐⭐⭐ Quantum-Secured Space-Air-Ground Integrated Networks: Concept, Framework, and Case Study (2022)

**作者**: Multiple authors
**来源**: IEEE (arXiv:2204.08673)
**关键词**: Quantum Key Distribution, QKD, SAGIN, Post-Quantum Security, Satellite QKD

**研究贡献**:
- 首次提出量子安全SAGIN概念
- 设计QKD over SAGIN架构
- 案例研究验证可行性

**量子威胁分析**:
1. **RSA和ECC的脆弱性**
   - 量子计算机可运行Shor算法
   - 高效解决大数分解和离散对数问题
   - 现有密码系统将被破解

2. **卫星通信的特殊风险**
   - 大规模量子计算机可破解卫星加密
   - 攻击可大规模传播恶意软件
   - 难以检测

**量子安全方案**:
1. **量子密钥分发(QKD)**
   - 基于量子力学提供信息论安全
   - 适用于SAGIN空间、空中、地面节点
   - 克服光纤传输距离限制
   - 实现全球范围安全通信

2. **卫星QKD**
   - 为长距离密钥交换提供量子安全层
   - 卫星搭载QKD系统
   - 地面站之间安全传输密钥
   - 结合PQC增强安全性

3. **QKD-PQC混合架构**
   - BBM92 QKD原语 + AES-256
   - 提供量子抗性安全
   - 模块化架构,任一原语失败仍保持安全

**技术挑战**:
- 自由空间量子信道高损耗
- 退相干、大气湍流、吸收、散射
- 海上链路的折射畸变

**对Tor的启示**:
- 量子威胁是SAGIN的紧迫挑战
- QKD可增强Tor密钥分发安全
- PQC是实用的量子抗性方案
- 混合架构提供冗余安全保障

**局限性**:
- ✅ 已考虑量子威胁
- ❌ 未专门研究Tor集成
- ❌ QKD实现复杂度高

**引用价值**: ⭐⭐⭐⭐⭐ (量子威胁核心文献)

**文献链接**:
- arXiv: https://arxiv.org/abs/2204.08673
- IEEE: https://ieeexplore.ieee.org/document/9915359/

---

### 4.2 ⭐⭐⭐ Quantum-Safe Networks for 6G: An Integrated Survey on PQC, QKD, and Satellite QKD (2025)

**来源**: Scifiniti Journal 2025
**关键词**: 6G, Post-Quantum Cryptography, QKD, Satellite QKD, Quantum Threats

**量子威胁概述**:
- **紧迫性**: 量子计算发展指数级增加安全风险
- **目标**: 传统加密系统(RSA, ECC)完全失效
- **影响**: 依赖安全通信的卫星系统高度脆弱

**后量子密码(PQC)**:
- **定义**: 抗量子和经典计算机攻击的算法
- **优势**: 可集成到现有基础设施
- **挑战**:
  - 密钥尺寸更大
  - 与现有系统集成困难

**6G安全方案**:
1. **PQC部署**
   - 提前部署量子安全密码
   - 确保加密数据即使在量子时代仍安全

2. **QKD集成**
   - 克服范围限制
   - 解决网络设计集成问题

3. **AI辅助安全**
   - 实时威胁检测
   - 自适应认证
   - 隐私保护机制
   - 动态频谱管理

**技术限制**:
- PQC密钥尺寸大
- QKD范围受限
- 需要复杂的网络设计

**对Tor的启示**:
- 6G时代Tor必须采用PQC
- 卫星QKD可增强密钥分发
- AI可辅助流量分析防御

**引用价值**: ⭐⭐⭐⭐ (6G量子安全综述)

**文献链接**: https://scifiniti.com/3104-4719/2/2025.0016

---

### 4.3 ⭐ Quantum Computing Could Break Satellite Security (2024)

**来源**: IOT Insider 2024
**关键词**: Quantum Threat, Satellite Security, Post-Quantum Cryptography

**核心警告**:
- 量子计算机将破解所有现有卫星加密系统
- 攻击可大规模传播,难以检测
- 需要立即部署后量子加密

**时间紧迫性**:
- 量子计算机快速发展
- 现有卫星系统生命周期长
- 需提前部署防御措施

**解决方案**:
- 后量子密码算法
- 相信对经典和量子计算机都安全
- 可能无法破解

**引用价值**: ⭐⭐ (科普文章,强调紧迫性)

**文献链接**: https://www.iotinsider.com/iot-insights/technical-insights/quantum-computing-could-break-satellite-security-are-we-prepared/

---

## 📊 五、性能数据汇总

### 5.1 延迟性能

| 系统/场景 | 延迟范围 | 数据来源 |
|---------|---------|---------|
| LEO卫星(一般) | 30-500ms | 文献综述 |
| Starlink卫星 | 单跳<50ms | SaTor 2024 |
| SaTor优化 | 降低40ms (70%连接) | SaTor 2024 |
| ISL路由 | 比弯管路由低 | 文献综述 |
| ISL峰值 | 70%客户每天至少1次峰值 | APNIC 2024 |

### 5.2 带宽性能

| 系统/场景 | 带宽特征 | 数据来源 |
|---------|---------|---------|
| LEO卫星 | 受限于卫星链路 | 文献综述 |
| Starlink | 支持高速互联网 | SaTor 2024 |
| WF防御开销 | 带宽增加<5% (推测) | Singh et al. 2024 |
| ISL带宽 | 激光通信显著提升 | 文献综述 |

### 5.3 安全性能

| 攻击类型 | 成功率/精度 | 数据来源 |
|---------|------------|---------|
| 网站指纹(Starlink) | ≈ 光纤 | Singh et al. 2024 |
| 位置追踪(RECORD) | 11km (2.3h观察) | USENIX 2024 |
| 量子攻击(未来) | 破解RSA/ECC | 多篇文献 |

### 5.4 认证性能

| 方案 | 延迟 | 计算开销 | 数据来源 |
|-----|------|---------|---------|
| 批量认证 | 低延迟 | 高效 | SGIN 2023 |
| 匿名认证 | 少量轮次 | 轻量级 | FANET 2022 |
| 零知识证明 | 较低 | 中等 | 多篇文献 |

---

## 🎯 六、研究空白与挑战

### 6.1 已识别的研究空白

1. **量子威胁未被考虑** ⭐⭐⭐⭐⭐
   - SaTor、Singh et al.、所有Tor相关文献均未考虑量子威胁
   - QKD文献未专门研究Tor集成
   - **研究机会**: Post-Quantum Tor on SAGIN

2. **性能-安全权衡不足** ⭐⭐⭐⭐
   - 缺乏Tor在SAGIN的全面性能评估
   - 未量化匿名性与延迟的权衡
   - 未考虑PQC对性能的影响

3. **多星座场景缺失** ⭐⭐⭐
   - 现有研究主要针对Starlink单一星座
   - 缺乏跨星座Tor路由研究
   - 未考虑异构SAGIN环境

4. **实际部署挑战** ⭐⭐⭐
   - 缺乏真实SAGIN环境的Tor测试
   - 未考虑卫星资源限制
   - 缺少工程化实现指南

### 6.2 SAGIN-Tor面临的挑战

#### 技术挑战
1. **高延迟** (30-500ms)
   - 影响Tor电路建立时间
   - 增加用户感知延迟
   - 可能触发超时重传

2. **强链路抖动**
   - 卫星移动导致延迟波动
   - 影响流量模式
   - 可能降低或增强指纹攻击

3. **窄带宽**
   - 限制Tor吞吐量
   - 防御开销更显著
   - 影响用户体验

4. **拓扑动态性**
   - 卫星持续移动
   - 链路频繁切换
   - 路由算法复杂

5. **资源受限**
   - 卫星计算能力有限
   - 不支持复杂加密
   - PQC密钥尺寸大

#### 安全挑战
1. **流量指纹攻击** (已证实)
   - Singh et al.证明Starlink易受攻击
   - 需要额外防御机制

2. **位置隐私泄露** (已证实)
   - RECORD攻击可定位用户
   - 卫星链路固有脆弱性

3. **窃听风险** (高)
   - 无线链路开放性
   - ISL也可能被监听

4. **量子威胁** (未来)
   - 现有Tor密码系统脆弱
   - 需要紧急升级PQC

### 6.3 为什么SAGIN需要Tor

1. **全球覆盖需求**
   - 偏远地区互联网接入
   - 海洋、极地、灾区通信
   - 传统地面Tor无法覆盖

2. **军事与关键通信**
   - 战场匿名通信
   - 敏感信息传输
   - 防止流量分析

3. **隐私保护需求**
   - 卫星用户位置隐私
   - 防止ISP监控
   - 抵御国家级审查

4. **未来网络架构**
   - 6G融合地面/空中/太空
   - 需要端到端匿名性
   - 量子安全通信

---

## 📖 七、文献引用建议

### 7.1 2.2.2节写作框架

```
2.2.2 Tor in Satellite and SAGIN Networks

[引言] Tor需要在SAGIN中部署的背景
引用: SaTor (2024), SAGIN综述

[子节1] Tor在卫星网络的可行性
- SaTor系统设计与性能 [SaTor 2024]
- LEO延迟优势与ISL技术 [多篇文献]
- 性能数据: 延迟降低40ms

[子节2] 安全威胁与挑战
- 网站指纹攻击 [Singh et al. 2024]
- 位置隐私泄露 [RECORD 2024]
- 窃听与流量分析 [Security Survey 2024]

[子节3] SAGIN匿名通信需求
- 6G SGIN认证协议 [PMC 2023]
- UAV匿名性方案 [FANET 2022]
- 隐私保护挑战 [S&S 2024]

[子节4] 量子威胁与研究空白
- 量子安全SAGIN [IEEE 2022]
- PQC与QKD方案 [6G Survey 2025]
- 研究空白: 现有Tor工作均未考虑量子威胁
- 引出本文贡献: 首个PQ-NTOR在SAGIN的研究
```

### 7.2 高优先级引用文献

1. **Singh et al. (2024)** - NDSS ⭐⭐⭐⭐⭐
   - 直接证明卫星Tor的安全威胁
   - 提供实验数据

2. **Quantum-Secured SAGIN (2022)** - IEEE ⭐⭐⭐⭐⭐
   - 量子威胁权威分析
   - 铺垫PQ-NTOR必要性

3. **Satellite Security Survey (2024)** - MDPI ⭐⭐⭐⭐
   - 全面安全威胁分析
   - 技术背景支撑

4. **6G SGIN Authentication (2023)** - PMC ⭐⭐⭐⭐
   - SAGIN匿名性需求
   - 认证协议参考

5. **SaTor (2024)** - arXiv ⭐⭐⭐
   - 核心技术参考(已在2.2.1引用)
   - 性能数据来源

### 7.3 参考文献格式 (IEEE风格)

```bibtex
@inproceedings{singh2024connecting,
  title={Connecting the Dots in the Sky: Website Fingerprinting in Low Earth Orbit Satellite Internet},
  author={Singh, Prabhjot and Barradas, Diogo and Elahi, Tariq and Limam, Noura},
  booktitle={NDSS Symposium 2024},
  year={2024},
  organization={NDSS}
}

@article{quantum_sagin_2022,
  title={Quantum-Secured Space-Air-Ground Integrated Networks: Concept, Framework, and Case Study},
  author={Multiple Authors},
  journal={IEEE Transactions},
  year={2022},
  note={arXiv:2204.08673}
}

@article{satellite_security_survey_2024,
  title={A Survey on Satellite Communication System Security},
  journal={MDPI Sensors},
  volume={24},
  number={9},
  year={2024},
  publisher={MDPI}
}

@article{sgin_auth_2023,
  title={On-Demand Anonymous Access and Roaming Authentication Protocols for 6G Satellite–Ground Integrated Networks},
  journal={PMC},
  year={2023}
}

@misc{sator2024,
  title={SaTor: Satellite Routing in Tor to Reduce Latency},
  author={Li and Elahi},
  year={2024},
  howpublished={arXiv:2406.15055}
}

@inproceedings{record2024,
  title={RECORD: A RECeption-Only Region Determination Attack on LEO Satellite Users},
  booktitle={USENIX Security Symposium},
  year={2024}
}

@article{quantum_safe_6g_2025,
  title={Quantum-Safe Networks for 6G: An Integrated Survey on PQC, QKD, and Satellite QKD with Future Perspectives},
  journal={Scifiniti},
  year={2025}
}

@article{sagin_privacy_2024,
  title={Preface: Security and Privacy for Space-Air-Ground Integrated Networks},
  journal={Security and Safety (S\&S)},
  year={2024}
}

@article{uav_auth_2022,
  title={Anonymous Mutual and Batch Authentication with Location Privacy of UAV in FANET},
  journal={MDPI Sensors},
  year={2022}
}
```

---

## 📝 八、论文写作建议

### 8.1 关键论点

1. **Tor在SAGIN的必要性**
   - 全球覆盖需求
   - 隐私保护需求
   - 军事与关键通信
   - 未来6G融合架构

2. **Tor在SAGIN的可行性**
   - SaTor证明了技术可行性
   - LEO延迟可接受(40ms改善)
   - ISL技术提供低延迟路径

3. **Tor在SAGIN的安全威胁**
   - 流量指纹攻击(已证实)
   - 位置隐私泄露(已证实)
   - 窃听风险(固有脆弱性)

4. **量子威胁的紧迫性**
   - 所有现有工作未考虑
   - 量子计算快速发展
   - SAGIN生命周期长,需提前部署

5. **研究空白与本文贡献**
   - 首个研究PQ-NTOR在SAGIN的工作
   - 填补量子安全空白
   - 提供实际性能评估

### 8.2 段落写作模板

#### 模板1: 引入安全威胁
```
Recent research has revealed significant security threats to Tor over
satellite networks. Singh et al. [X] demonstrated that Tor traffic over
Starlink is equally susceptible to website fingerprinting attacks as
traditional fiber connections. Furthermore, the RECORD attack [Y] showed
that passive adversaries can determine a user's location to within 11 km
by observing just 2.3 hours of LEO satellite traffic. These findings
highlight the need for additional security mechanisms beyond Tor's
existing protections.
```

#### 模板2: 强调量子威胁
```
While existing research on Tor in satellite networks (e.g., SaTor [X],
Singh et al. [Y]) has focused on performance and classical security
threats, a critical gap remains: none of these works have considered the
quantum computing threat. Quantum-secured SAGIN research [Z] has shown
that quantum computers can break current cryptographic systems like RSA
and ECC, which are used in Tor's handshake protocols. Given the long
lifespan of satellite systems and the rapid development of quantum
computing, this represents a pressing challenge for deploying Tor in
SAGIN environments.
```

#### 模板3: 铺垫本文贡献
```
These challenges motivate our work on Post-Quantum NTOR (PQ-NTOR) for
SAGIN. To the best of our knowledge, this is the first study to evaluate
the feasibility and performance of a post-quantum Tor handshake protocol
in the context of satellite and space-air-ground integrated networks. We
address both the classical security threats (traffic analysis, location
privacy) and the emerging quantum threat, while considering SAGIN's unique
constraints of high latency, link jitter, and limited bandwidth.
```

### 8.3 简洁性原则(符合写作风格指南)

遵循`WRITING_STYLE_GUIDE.md`中的原则:

1. **句子长度**: 15-25词
2. **动词简洁**: 使用简单直接的动词
   - demonstrated (不用 has been shown)
   - showed (不用 has revealed)
   - threatens (不用 poses threats to)

3. **修饰词精简**: 只保留必要修饰
   - "Tor traffic over Starlink" (不用 "Tor traffic transmitted through Starlink satellite connections")

4. **从句简化**: 使用破折号或并列结构
   - "Tor over satellite networks—given its high latency—remains challenging"
   - (不用 "Tor over satellite networks, which has high latency, remains challenging")

---

## 🔍 九、关于Albrecht et al. (2023)的说明

**搜索结果**: 未找到Albrecht et al. (2023)关于卫星网络匿名性的论文

**可能原因**:
1. 论文可能不存在或命名不同
2. 可能是会议论文,未在主流搜索引擎索引
3. 可能作者名拼写不同(Albrecht有多种拼写)
4. 可能发表在小众期刊或技术报告

**替代文献**:
- 使用Singh et al. (2024) NDSS作为主要卫星网络安全威胁文献
- 使用Satellite Security Survey (2024)补充安全威胁分析
- 使用RECORD (2024)补充位置隐私威胁

**建议**:
- 如果该文献确实重要,请提供更多信息(DOI、会议名、论文题目)
- 或者从已找到的文献中选择替代引用

---

## 📊 十、总结

### 10.1 调研成果

- ✅ **文献数量**: 10篇核心文献(超过预期6-10篇)
- ✅ **重点文献**: Singh et al. (2024) NDSS - 已找到
- ⚠️ **重点文献**: Albrecht et al. (2023) - 未找到,已用替代文献
- ✅ **覆盖方向**: 全部4个调研方向
- ✅ **性能数据**: 延迟、带宽、攻击精度等多维度数据
- ✅ **研究空白**: 明确识别量子威胁空白

### 10.2 核心发现

1. **Tor在卫星网络可行** (SaTor 2024)
   - 延迟可降低40ms
   - ISL技术提供低延迟路径

2. **安全威胁真实存在** (Singh 2024, RECORD 2024)
   - 网站指纹攻击有效
   - 位置隐私可被泄露

3. **SAGIN需要匿名通信** (多篇文献)
   - 全球覆盖需求
   - 隐私保护需求
   - 军事与关键通信

4. **量子威胁被忽视** (研究空白)
   - 所有Tor相关工作未考虑
   - 紧迫的安全挑战
   - 为PQ-NTOR铺垫

### 10.3 下一步工作

1. **撰写2.2.2节**
   - 使用本报告的文献和数据
   - 遵循写作风格指南
   - 强调研究空白

2. **补充文献**
   - 如需要Albrecht et al.,继续搜索或联系作者
   - 考虑添加更多Tor安全威胁文献

3. **更新参考文献管理**
   - 将BibTeX条目添加到`参考文献管理.md`
   - 确保引用格式一致

---

## 📚 附录: 完整文献列表

### A.1 卫星网络中的Tor研究
1. SaTor (2024) - arXiv ⭐⭐⭐⭐⭐
2. Onion Routing综合调研 ⭐⭐⭐
3. LEO Satellite Performance ⭐⭐⭐⭐

### A.2 卫星Tor的安全威胁
4. Singh et al. (2024) - NDSS ⭐⭐⭐⭐⭐
5. RECORD (2024) - USENIX ⭐⭐⭐⭐
6. Satellite Security Survey (2024) - MDPI ⭐⭐⭐⭐

### A.3 空地一体化网络匿名通信
7. 6G SGIN Authentication (2023) - PMC ⭐⭐⭐⭐
8. SAGIN Security Preface (2024) - S&S ⭐⭐⭐
9. UAV FANET Authentication (2022) - MDPI ⭐⭐⭐

### A.4 量子威胁与后量子密码
10. Quantum-Secured SAGIN (2022) - IEEE ⭐⭐⭐⭐⭐
11. Quantum-Safe 6G (2025) - Scifiniti ⭐⭐⭐⭐
12. Quantum Threat Overview (2024) - IOT Insider ⭐⭐

---

**文档状态**: ✅ 完成
**最后更新**: 2025-12-03
**维护者**: PQ-NTOR SAGIN 项目组

---

## 🔗 Sources

### 主要搜索来源:

- [SaTor: Satellite Routing in Tor to Reduce Latency](https://arxiv.org/html/2406.15055v2)
- [Connecting the Dots in the Sky: Website Fingerprinting in Low Earth Orbit Satellite Internet - NDSS Symposium](https://www.ndss-symposium.org/ndss-paper/auto-draft-442/)
- [Website Fingerprinting on LEO Satellite Internet - UWaterloo](https://uwspace.uwaterloo.ca/items/f1fece74-5eb5-4b2f-b6e3-e45f454e0a27)
- [On-Demand Anonymous Access and Roaming Authentication Protocols for 6G Satellite–Ground Integrated Networks - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10255450/)
- [A Survey on Satellite Communication System Security - MDPI](https://www.mdpi.com/1424-8220/24/9/2897)
- [RECORD: A RECeption-Only Region Determination Attack on LEO Satellite Users - USENIX](https://www.usenix.org/conference/usenixsecurity24/presentation/jedermann)
- [Preface: Security and privacy for space-air-ground integrated networks - S&S](https://sands.edpsciences.org/articles/sands/full_html/2024/01/sands20240006/sands20240006.html)
- [Quantum-Secured Space-Air-Ground Integrated Networks - arXiv](https://arxiv.org/abs/2204.08673)
- [Quantum-Secured Space-Air-Ground Integrated Networks - IEEE](https://ieeexplore.ieee.org/document/9915359/)
- [Quantum-Safe Networks for 6G - Scifiniti](https://scifiniti.com/3104-4719/2/2025.0016)
- [Anonymous Mutual and Batch Authentication with Location Privacy of UAV in FANET - MDPI](https://www.mdpi.com/2504-446X/6/1/14)
- [Quantum computing could break satellite security - IOT Insider](https://www.iotinsider.com/iot-insights/technical-insights/quantum-computing-could-break-satellite-security-are-we-prepared/)
- [Blockstream Satellite API](https://blockstream.com/satellite-api/)
- [Democratizing LEO satellite network measurement - APNIC](https://blog.apnic.net/2024/07/24/democratizing-leo-satellite-network-measurement/)
- [Security Requirements and Challenges of 6G Technologies and Applications - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8914636/)
