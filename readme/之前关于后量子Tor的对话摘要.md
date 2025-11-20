# 🔐 之前关于后量子密码 Tor 修改的对话摘要

> **文件来源**: `~/.claude/projects/--wsl-localhost-Ubuntu-22-04-home-ccc/20cdfc37-ad45-46b7-850d-d20d76dcc082.jsonl`
> **会话时间**: 2025-10-28

---

## 📌 讨论主题总结

您咨询了如何将 **Tor 0.4.7.13** 的 **Ntor 握手协议**修改为使用**后量子密码**（特别是 Ring-LWE/Kyber）的可行性和具体实施方案。

---

## 🔍 核心发现

### 1. Tor Ntor 握手现状

**当前使用的密码学原语**:
- **Curve25519** - 椭圆曲线 Diffie-Hellman 密钥交换
- **Ed25519** - 椭圆曲线数字签名
- **HMAC-SHA256/SHA3-256** - 消息认证码
- **SHAKE-256** - 密钥派生函数 (KDF)
- 直接在Tor源代码上进行修改风险太大，务必不要用这种方式！

## 🛠️ 推荐使用的后量子密码库

| 库 | 优势 | 劣势 | 推荐度 |
|---|------|------|--------|
| **liboqs** | NIST标准化、多算法、活跃维护 | 体积较大(~10MB) | ⭐⭐⭐⭐⭐ |
| **PQClean** | 代码简洁、易审计 | 功能较少 | ⭐⭐⭐⭐ |
| **libpqcrypto** | 性能优化、NaCl风格API | 文档较少 | ⭐⭐⭐ |

**首选 liboqs**，因为它支持多种算法，便于后续切换和对比。

---

## 📊 学术研究实验设计

如果您的目标是发表论文，建议的实验项目结构：

```
pq-ntor-experiment/
├── src/
│   ├── original_ntor.c       # 原版 Ntor（从 Tor 提取）
│   ├── pq_ntor.c             # Ring-LWE 版本
│   └── crypto_utils.c        # KDF/MAC 工具
├── benchmark/
│   ├── performance_test.c    # 性能对比测试
│   └── correctness_test.c    # 正确性验证
├── results/
│   ├── performance.csv       # 性能数据
│   ├── key_sizes.csv         # 密钥大小对比
│   └── plots/                # 生成的图表
└── scripts/
    ├── generate_plots.py     # 生成论文图表
    └── run_experiments.sh    # 一键运行所有实验
```

**需要收集的实验数据**:
1. 握手时间对比 (ms/handshake)
2. 密钥大小对比 (bytes)
3. 通信开销对比 (bytes)
4. CPU 使用率
5. 内存占用

---

## 📅 完整时间线

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| Week 1-2 | 独立原型开发 (C + Python参考实现) | 2 周 |
| Week 3-4 | 验证与优化 (测试向量、性能测试) | 2 周 |
| Week 5-8 | 集成到 Tor (调度器、测试、兼容性) | 4 周 |
| Week 9-10 | 端到端测试 (私有 Tor 网络测试) | 2 周 |
| **总计** | | **10 周 (2.5 个月)** |

---


## 🚀 下一步行动建议

### 选项 A: 快速原型 (1-2天)
先用 **Python + liboqs** 实现最小原型验证密码学流程

### 选项 B: 独立库开发 (2周)
完整实现独立的 PQ-Ntor C 库，包含测试和文档

### 选项 C: 直接集成 Tor (高风险)
直接修改 Tor 源码（不推荐，除非已有成熟实现）

---

## 📚 相关文件位置

**Tor 源码路径**:
- `/home/ccc/tor-tor-0.4.7.13/`

**核心握手实现**:
- `/home/ccc/tor-tor-0.4.7.13/src/core/crypto/hs_ntor.c` (隐藏服务)
- `/home/ccc/tor-tor-0.4.7.13/src/core/crypto/onion_ntor.c` (常规电路)
- `/home/ccc/tor-tor-0.4.7.13/src/core/crypto/onion_ntor_v3.c` (扩展版本)

**调度器**:
- `/home/ccc/tor-tor-0.4.7.13/src/core/crypto/onion_crypto.c`

---

## 💬 我当时的最终建议

**推荐从阶段 1 开始** - 先独立开发 PQ-Ntor 库，原因：

1. **降低风险** 🛡️ - 在简单环境中验证 Ring-LWE 集成
2. **提高成功率** 🎯 - 独立项目代码量小，可快速迭代
3. **灵活性强** 🔄 - 验证后可选择多种集成方式
4. **可复用性高** ♻️ - 独立库可用于其他项目和学术发表

---


**生成时间**: 2025-10-28
**总会话数**: 285 条消息
**文件大小**: 780 KB
