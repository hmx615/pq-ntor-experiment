# PQ-NTOR SAGIN 论文写作风格指南

**创建日期**: 2025-12-01
**目的**: 记录团队写作风格规范，确保论文语言一致性

---

## 📝 核心写作原则

### ✅ **使用尽可能简单的语法来表达清楚意思**

这是我们团队的核心写作理念。具体体现在：

1. **句子结构简洁**
   - ❌ 避免：复杂的从句嵌套、过长的修饰语
   - ✅ 推荐：主谓宾清晰、一句话表达一个核心观点

2. **词汇选择直接**
   - ❌ 避免：过度学术化的生僻词、冗余的修饰词
   - ✅ 推荐：常用词汇、准确的专业术语

3. **逻辑清晰**
   - ❌ 避免：隐晦的逻辑跳跃、模糊的因果关系
   - ✅ 推荐：明确的过渡词、清晰的论证链条

---

## 🔍 第一章写作风格对比分析

### 原版 vs 简化版（ChatGPT5修改）

通过对比第一章的两个版本，我们可以总结出具体的简化策略：

#### **原版特点**（较复杂）:
```
With the rapid development of the Internet in the 21st century,
its supporting infrastructure has also advanced significantly.
```

#### **简化版特点**（推荐）:
```
With the rapid growth of the Internet in the 21st century,
its supporting infrastructure has also improved.
```

**改进点**:
- `development` → `growth` (更常用)
- `advanced significantly` → `improved` (更简洁)

---

### 句子简化对照表

| 原版 | 简化版 | 改进说明 |
|------|--------|---------|
| turning anonymous communication from a secondary requirement into a fundamental component of modern digital infrastructure | making anonymous communication a fundamental part of modern digital systems | 去除冗余修饰，简化结构 |
| The Tor network is the most mature system for anonymous communication | The Tor network is the most mature anonymous communication system | 调整语序，更直接 |
| extracting sensitive content | tracking communication paths or learning the network structure | 使用更具体的动词 |
| Whether SAGIN can support a Post-Quantum Tor (PQ-Tor) under its unique technical constraints | Whether SAGIN can support a Post-Quantum Tor (PQ-Tor)—given its high latency... | 使用破折号简化从句 |
| exploring this issue lays an important foundation for subsequent technical optimization and system construction | Studying this problem is important for future technical improvements and system design | 简化动名词结构，使用更直接的词汇 |

---

## 📐 具体写作规则

### 1. 句子长度控制

**推荐**: 每句 15-25 词

**示例**:
```
✅ GOOD (18 words):
Tor protects user privacy through multilayer encryption and relay-based
anonymity, securing personal information and data confidentiality.

❌ TOO LONG (35 words):
With its multilayer encryption and relay-based anonymity, Tor can protect
personal information, ensure data confidentiality, prevent attackers from
extracting sensitive content, tracking communication paths, or inferring
network topology.
```

---

### 2. 动词选择

**推荐**: 使用简单、直接的动词

| 复杂表达 | 简化表达 |
|---------|---------|
| has advanced significantly | has improved |
| turning ... from ... into ... | making ... |
| posed severe threats to | threatens |
| extracting sensitive content | accessing sensitive data |
| inferring network topology | learning network structure |
| lays an important foundation for | is important for |

---

### 3. 修饰词使用

**原则**: 只保留必要的修饰词

**示例**:
```
❌ WORDY:
the rapid development of the Internet in the 21st century

✅ CONCISE:
the rapid growth of the Internet
(时间背景在上下文中已明确，可省略)
```

---

### 4. 从句简化

**策略**: 使用破折号、分号、并列结构代替复杂从句

**示例**:
```
❌ COMPLEX:
Whether SAGIN can support a Post-Quantum Tor under its unique technical
constraints such as high latency, strong link jitter, and narrow channel
bandwidth remains an open question.

✅ SIMPLIFIED:
Whether SAGIN can support a Post-Quantum Tor—given its high latency
(30–500 ms), strong link jitter, and narrow bandwidth—remains an open
question.
```

---

### 5. 专业术语使用

**原则**:
- ✅ 首次出现时给出全称+缩写
- ✅ 后续使用缩写
- ✅ 技术术语保持准确性，不过度简化

**示例**:
```
✅ CORRECT:
Space-Air-Ground Integrated Network (SAGIN)
...
Because SAGIN is open and highly distributed...

✅ CORRECT:
Post-Quantum Tor (PQ-Tor)
```

---

## 📊 第二章写作风格分析

### 中文写作特点（需转换为英文时注意）

第二章目前是中文版本，包含三个部分：

1. **Tor体系结构** (`tor体系结构.docx`)
2. **后量子密码与Kyber** (`2.3后量子密码与kyber.docx`)
3. **SAGIN相关**（待补充）

#### 中文版特点:
- 学术化表达较重
- 句子结构复杂
- 大量使用专业术语

#### 转换为英文时的简化策略:

**原则**: 中文学术表达 → 英文简洁表达

**示例**（Tor体系结构部分）:

| 中文原文 | 直译（复杂） | 简化英文（推荐） |
|---------|------------|----------------|
| Tor作为当前应用最广的匿名通信系统，其匿名性保障依赖于洋葱路由机制构建的多跳加密传输路径 | Tor, as the most widely used anonymous communication system, relies on multi-hop encrypted transmission paths constructed by the onion routing mechanism for its anonymity guarantee | Tor is the most widely used anonymous communication system. It ensures anonymity through multi-hop encrypted paths using onion routing |

**改进点**:
1. 长句拆分为两个短句
2. 去除冗余的"as"从句
3. 简化"依赖于...构建的...保障"为"ensures...through..."

---

## 🎯 写作检查清单

在完成每一段落后，检查以下要点：

- [ ] 每句话是否控制在 15-25 词？
- [ ] 是否使用了最简单的动词表达？
- [ ] 是否有冗余的修饰词可以删除？
- [ ] 复杂从句是否可以简化为并列结构或短句？
- [ ] 专业术语是否首次出现时定义？
- [ ] 逻辑连接是否清晰（使用过渡词）？
- [ ] 段落主题是否明确（第一句即点明）？

---

## 💡 常用句式模板

### Introduction 常用句式

```
✅ 问题陈述:
[Problem] poses a significant challenge to [System].
Example: Quantum computing poses a significant challenge to traditional
cryptographic systems.

✅ 研究空白:
Whether [System] can support [Feature] under [Constraints] remains an
open question.
Example: Whether SAGIN can support PQ-Tor under high latency remains
an open question.

✅ 贡献声明:
This paper presents the first [Achievement].
Example: This paper presents the first comprehensive evaluation of
PQ-NTOR on ARM64 platforms.
```

### Background 常用句式

```
✅ 技术描述:
[System] ensures [Goal] through [Method].
Example: Tor ensures anonymity through multilayer encryption and
relay-based routing.

✅ 安全威胁:
[Attack] threatens [Component] by [Method].
Example: Quantum computing threatens ECC-based systems by solving
discrete logarithm problems efficiently.

✅ 技术演进:
[System] has evolved from [Old] to [New].
Example: Tor has evolved from TAP handshake to the current Ntor protocol.
```

---

## 📚 参考文献风格

### 引用格式

**原则**: 简洁引用，避免过度解释

```
✅ CONCISE:
The Tor network uses the Ntor handshake protocol for circuit
establishment [2].

❌ VERBOSE:
According to the research conducted by Mathewson and Möller in their
2014 proposal, the Tor network utilizes the Ntor handshake protocol
for the purpose of circuit establishment [2].
```

---

## 🔄 版本控制

### 文档版本记录

| 版本 | 日期 | 修改内容 | 负责人 |
|------|------|---------|--------|
| v1.0 | 2025-12-01 | 初版创建，总结第一章写作风格 | Claude |
| v1.1 | 2025-12-01 | 添加第二章中文转英文策略 | 待定 |

---

## 📖 相关文档

### 已有写作成果

1. **第一章第三次修改** (`essay/第一章第三次修改.docx`)
   - 包含原版和简化版
   - 简化版由ChatGPT5修改

2. **第二章内容** (`essay/第二章/`)
   - Tor体系结构 (`tor体系结构.docx`)
   - 后量子密码与Kyber (`2.3后量子密码与kyber.docx`)
   - SAGIN相关（待补充）

3. **Section 5 评估** (`essay/Section_5_Evaluation.md`)
   - 已完成的实验评估章节

---

## 🚀 下一步工作

### 待完成任务

1. **第二章英文版撰写**
   - 基于中文版转换
   - 应用简化写作风格
   - 分为三个子章节：
     - 2.1 Tor Architecture
     - 2.2 Post-Quantum Cryptography and Kyber
     - 2.3 SAGIN Networks

2. **第一章定稿**
   - 基于简化版进一步润色
   - 确保与后续章节风格一致

3. **其他章节规划**
   - Section 3: PQ-NTOR Design
   - Section 4: Implementation
   - Section 6: Related Work
   - Section 7: Conclusion

---

**维护者**: PQ-NTOR SAGIN 项目组
**最后更新**: 2025-12-01
**状态**: ✅ 写作风格指南完成，可用于后续写作参考
