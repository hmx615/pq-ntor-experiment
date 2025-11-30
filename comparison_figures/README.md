# 性能对比可视化图表

本目录包含完整的PQ-NTOR性能对比分析可视化图表，可直接用于论文写作。

## 📊 图表列表

### Figure 1: 跨平台性能对比
**文件**: `fig1_platform_comparison.{png,pdf}`

**内容**:
- (a) 绝对性能对比: X86 vs ARM64 (RPi 4) vs ARM64 (飞腾派)
- (b) 开销倍数对比: PQ-NTOR相对Classic NTOR的倍数

**关键数据**:
- 飞腾派PQ-NTOR: **181.64 µs**
- 飞腾派开销倍数: **3.0-4.5×** (在文献范围2-6×内)
- 优于Raspberry Pi 4 (262.6 µs)

**用途**: 论文中平台对比章节

---

### Figure 2: SAGIN拓扑性能热图
**文件**: `fig2_sagin_heatmap.{png,pdf}`

**内容**:
- (a) 总电路构建时间热图 (延迟×带宽)
- (b) 密码学开销占比热图

**关键发现**:
- **LAN**: 33.8% 密码学开销
- **LEO卫星**: 0.9% 密码学开销
- **GEO卫星**: 0.07% 密码学开销
- **结论**: PQ-NTOR在高延迟SAGIN环境中密码学开销可忽略

**用途**: 论文中SAGIN适用性分析章节

---

### Figure 3: 可扩展性分析
**文件**: `fig3_scalability.{png,pdf}`

**内容**:
- (a) LAN环境下1-10跳性能
- (b) LEO卫星环境下1-10跳性能

**关键观察**:
- 3跳电路时间: 1.25 ms (LAN, 实测)
- PQ-NTOR开销随跳数线性增长
- 高延迟环境下网络延迟主导

**用途**: 论文中可扩展性评估章节

---

### Figure 4: 7π分布式架构
**文件**: `fig4_architecture.{png,pdf}`

**内容**:
- 7台飞腾派节点拓扑图
- 节点角色与IP地址
- 数据流向与性能指标

**节点配置**:
```
192.168.5.110 - Client    (测试客户端)
192.168.5.111 - Directory (目录服务器)
192.168.5.112 - Guard     (入口节点)
192.168.5.113 - Middle    (中间节点)
192.168.5.114 - Exit      (出口节点)
192.168.5.115 - Target    (HTTP目标)
192.168.5.116 - Monitor   (监控节点)
```

**用途**: 论文中系统架构章节

---

### Figure 5: 性能分解汇总
**文件**: `fig5_breakdown_summary.{png,pdf}`

**内容**:
- (a) PQ-NTOR握手时间分解
- (b) 三跳电路构建时间分解
- (c) 跨场景性能对比 (LAN/LEO/GEO)
- (d) 关键发现与贡献汇总

**核心数据**:
- Kyber-512操作: ~145 µs (80%)
- X25519 DH: ~25 µs (14%)
- HMAC-SHA256: ~11 µs (6%)

**用途**: 论文中性能评估汇总章节

---

## 🎨 图表特性

### 格式
- **PNG**: 高分辨率位图 (300 DPI)
- **PDF**: 矢量图，适合学术出版

### 风格
- 配色方案: 专业学术风格
- 字体: 清晰易读
- 图例: 完整准确
- 标注: 关键数据高亮

### 可重现性
所有图表由 `visualize_comparison.py` 生成，数据来源可追溯：
- 实测数据: `c/benchmark_results.csv`, `3hop_test_results/`
- 文献数据: `LITERATURE_PERFORMANCE_DATA.md`
- 预测数据: `7PI_FINAL_TEST_PLAN.md`

---

## 📖 论文使用建议

### Abstract
引用: Figure 1(b) - 3.0-4.5×开销倍数

### Introduction
引用: Figure 4 - 7π架构创新性

### Related Work
引用: Figure 1(a) - 与文献对比

### System Design
引用: Figure 4 - 完整架构图

### Implementation
引用: Figure 5(a,b) - 性能分解细节

### Evaluation
引用: Figure 1, 2, 3, 5 - 完整评估结果

### Discussion
引用: Figure 2(b) - SAGIN适用性论证

---

## 🔄 更新方法

### 重新生成所有图表
```bash
python3 ../visualize_comparison.py
```

### 修改数据
编辑 `visualize_comparison.py` 中的数据数组，然后重新运行。

### 添加新图表
在 `visualize_comparison.py` 中添加新函数 `create_figureN_xxx()`，然后在main中调用。

---

## ✅ 质量检查清单

- [x] 所有数据标签清晰可读
- [x] 图例完整准确
- [x] 配色专业（色盲友好）
- [x] 轴标签单位明确
- [x] 标题简洁准确
- [x] PNG和PDF格式都可用
- [x] 文件大小合理 (<5MB)
- [x] 可直接插入LaTeX/Word

---

**生成时间**: 2025-11-30
**数据来源**: 飞腾派ARM64实测 + 文献调研
**状态**: ✅ 可用于论文写作
