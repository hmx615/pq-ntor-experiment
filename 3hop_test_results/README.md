# 三跳电路测试结果可视化

## 📊 包含文件

### 报告文档
- **3HOP_CIRCUIT_TEST_REPORT.md** - 完整测试报告（中文）

### 可视化脚本
- **visualize_3hop.py** - 图表生成脚本（可重新运行）

### 图表文件（PNG + PDF）

#### 1. 阶段分解图 (Stage Breakdown)
- `figure_3hop_stage_breakdown.png` (187 KB)
- `figure_3hop_stage_breakdown.pdf` (26 KB, 矢量图)

**内容**：饼图+柱状图，展示三跳电路各阶段时间占比
- 目录获取: 61.3%
- 第1跳: 13.1%
- 第2跳: 12.5%
- 第3跳: 12.4%

---

#### 2. 握手 vs 电路对比图 (Handshake vs Circuit)
- `figure_handshake_vs_circuit.png` (142 KB)
- `figure_handshake_vs_circuit.pdf` (34 KB)

**内容**：柱状图，对比三种场景
- 单次PQ-NTOR握手: 181.64 µs
- 完整三跳电路: 1252.57 µs (6.9× slower)
- 仅3次握手部分: 475.01 µs

---

#### 3. 延迟分布箱线图 (Latency Distribution)
- `figure_latency_distribution.png` (106 KB)
- `figure_latency_distribution.pdf` (23 KB)

**内容**：箱线图，展示各阶段延迟分布
- 显示中位数、四分位距、离群点
- 可看出目录获取方差最大

---

#### 4. 网络 vs 加密开销 (Overhead Analysis)
- `figure_overhead_analysis.png` (144 KB)
- `figure_overhead_analysis.pdf` (27 KB)

**内容**：百分比柱状图
- 网络开销（目录）: 61.3% (767.80 µs)
- 加密开销（3握手）: 38.0% (475.01 µs)

---

#### 5. 综合性能汇总表 (Performance Summary)
- `figure_performance_summary.png` (269 KB)
- `figure_performance_summary.pdf` (33 KB)

**内容**：性能数据表格
- 单次握手 vs 三跳电路对比
- 各阶段详细分解
- 统计指标（均值、中位数、方差等）

---

## 🎯 核心数据

| 指标 | 数值 |
|------|------|
| 平均电路构建时间 | 1252.57 µs (1.25 ms) |
| 成功率 | 100% |
| 迭代次数 | 10 |
| 测试平台 | 飞腾派 ARM64 |
| 算法 | PQ-NTOR (Kyber-512) |

---

## 📈 使用建议

### 论文发表
使用 **PDF版本**（矢量图）：
- 无损缩放
- 文件小
- 打印质量高

### 演示文稿
使用 **PNG版本**：
- 兼容性好
- 易于嵌入PPT/Keynote
- 高分辨率（300 DPI）

---

## 🔄 重新生成图表

如果需要修改图表样式或数据，运行：

```bash
cd /home/ccc/pq-ntor-experiment/3hop_test_results
python3 visualize_3hop.py
```

修改 `visualize_3hop.py` 中的数据或样式参数即可自定义图表。

---

## 📋 测试环境

- **系统**: Linux Phytium-Pi 5.10.209
- **架构**: aarch64 (ARM64)
- **编译器**: gcc 9.4.0
- **测试日期**: 2025-11-30
- **测试类型**: 单机localhost测试

---

## ✅ 验证结果

- ✅ 三跳电路构建成功率 100%
- ✅ 性能数据完整可靠
- ✅ 可视化图表符合发表标准
- ✅ 准备进行7π分布式测试

---

**版本**: v1.0
**生成时间**: 2025-11-30 14:29
**状态**: 单机验证完成
