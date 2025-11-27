# PQ-NTOR in SAGIN - LaTeX 论文工作区

**创建日期**: 2025-11-27
**状态**: Section 5 (Evaluation) 已完成，其他章节待完善

---

## 📁 目录结构

```
latex/
├── main.tex                    # 主 LaTeX 文档
├── usenix-2e.sty              # USENIX 会议格式样式文件
├── references.bib             # BibTeX 参考文献
├── compile.sh                 # 自动编译脚本
├── README.md                  # 本文件
│
├── sections/                  # 各章节 LaTeX 文件
│   ├── introduction.tex       # 第1章：引言 [占位符]
│   ├── background.tex         # 第2章：背景 [占位符]
│   ├── design.tex             # 第3章：PQ-NTOR设计 [占位符]
│   ├── implementation.tex     # 第4章：系统实现 [占位符]
│   ├── evaluation.tex         # 第5章：评估 [✅ 已完成]
│   ├── related_work.tex       # 第6章：相关工作 [占位符]
│   └── conclusion.tex         # 第7章：结论 [占位符]
│
├── figures/                   # 图片文件夹（待添加）
├── tables/                    # 表格文件夹（可选）
└── data/                      # 数据文件夹（可选）
```

---

## 🚀 快速开始

### 1. 安装 LaTeX

#### Ubuntu / Debian / WSL

```bash
# 完整安装（推荐，约 5GB）
sudo apt-get update
sudo apt-get install texlive-full

# 或轻量级安装（约 500MB）
sudo apt-get install texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended texlive-fonts-extra
```

#### macOS

```bash
brew install --cask mactex
```

#### Windows

下载并安装 [MiKTeX](https://miktex.org/) 或 [TeX Live](https://www.tug.org/texlive/)

### 2. 编译论文

```bash
cd /home/ccc/pq-ntor-experiment/essay/latex

# 完整编译（包括参考文献）
./compile.sh full

# 快速编译（仅预览，跳过参考文献）
./compile.sh quick

# 清理临时文件
./compile.sh clean
```

### 3. 查看生成的 PDF

```bash
# 编译成功后会生成 main.pdf
ls -lh main.pdf

# 在 WSL 中打开 PDF（如果配置了 Windows 关联）
explorer.exe main.pdf

# 或使用 Linux PDF 阅读器
evince main.pdf
# 或
okular main.pdf
```

---

## 📝 当前状态

### ✅ 已完成

| 章节 | 文件 | 状态 | 内容 |
|------|------|------|------|
| **Section 5** | `sections/evaluation.tex` | ✅ **完成** | 实验评估（5.1-5.2完整，5.3-5.5占位符） |
| 主文档 | `main.tex` | ✅ 完成 | 论文框架和结构 |
| 参考文献 | `references.bib` | ✅ 完成 | 核心引用（Berger, NIST, liboqs等） |
| 编译脚本 | `compile.sh` | ✅ 完成 | 自动化编译工具 |

### ⏳ 待完成

| 章节 | 文件 | 优先级 | 说明 |
|------|------|--------|------|
| Section 1 | `sections/introduction.tex` | 🔴 高 | 需要基于你的 docx 补充内容 |
| Section 2 | `sections/background.tex` | 🟡 中 | Tor、PQC、SAGIN 背景 |
| Section 3 | `sections/design.tex` | 🟡 中 | PQ-NTOR 协议设计 |
| Section 4 | `sections/implementation.tex` | 🟡 中 | 系统实现细节 |
| Section 6 | `sections/related_work.tex` | 🟢 低 | 相关工作综述 |
| Section 7 | `sections/conclusion.tex` | 🟢 低 | 结论与未来工作 |
| **图表** | `figures/` | 🔴 高 | 性能图、拓扑图、架构图 |

---

## 📊 Section 5 (Evaluation) 详细内容

已完成的 Section 5 包括：

### ✅ 5.1 Experimental Setup（实验设置）

- **5.1.1 Hardware Configuration** - 硬件配置表（x86_64 + ARM64）
- **5.1.2 Software Stack** - 软件栈详细表格
- **5.1.3 Network Topologies** - **12种拓扑**的详细规格
  - Table 3: 拓扑分类
  - Table 4: 12种拓扑详细参数（跳数、延迟、带宽、丢包率）
  - 卫星链路参数（LEO/MEO/GEO）
- **5.1.4 Performance Metrics** - 性能指标定义
- **5.1.5 Experimental Methodology** - 实验方法论（三阶段）

### ✅ 5.2 Phase 1: PQ-NTOR Implementation Benchmarks

- **5.2.1 Methodology** - 测试方法详细描述
- **5.2.2 Performance Results** - 性能结果（Table 5: 31 μs 握手）
- **5.2.3 Comparison with Prior Work** - 与 Berger 论文对比（Table 6）
- **5.2.4 Analysis and Discussion** - 深入分析

### ⏳ 5.3 Phase 2: SAGIN Network Integration

**[占位符]** - 等待飞腾派实验完成后填充

### ⏳ 5.4 Phase 3: Multi-Platform Deployment

**[占位符]** - 等待飞腾派部署完成后填充

### ⏳ 5.5 Discussion

**[占位符]** - 所有实验完成后撰写

---

## 🎨 核心数据亮点

LaTeX 版本已包含的关键数据：

| 指标 | 数值 | 来源 |
|------|------|------|
| **Full Handshake** | **31 μs** | Table 5 |
| **vs Berger论文** | **5.2× 更快** | Table 6 |
| **吞吐量** | **32,258 hs/s** | Section 5.2.2 |
| **拓扑数量** | **12种** | Table 4 |
| **测试规模** | **240次**（规划） | Section 5.1.5 |

---

## 🔧 编译说明

### 完整编译流程

```bash
./compile.sh full
```

执行步骤：
1. 第一次 `pdflatex` - 生成 .aux 文件
2. `bibtex` - 处理参考文献
3. 第二次 `pdflatex` - 解决引用
4. 第三次 `pdflatex` - 最终版本

### 快速编译（开发时使用）

```bash
./compile.sh quick
```

仅执行一次 `pdflatex`，跳过参考文献处理，适合快速预览内容修改。

### 常见编译问题

#### 问题1: `pdflatex: command not found`

**解决**: 安装 TeX Live

```bash
sudo apt-get install texlive-full
```

#### 问题2: 编译卡住或报错

**解决**: 使用 `-interaction=nonstopmode`（脚本已包含）

#### 问题3: 参考文献不显示

**解决**: 确保执行完整编译（`./compile.sh full`），需要多次编译

---

## 📚 下一步工作

### 优先级1: 完善 Section 1 (Introduction)

基于你的 `第一章第二次修改.docx`，补充到 `sections/introduction.tex`

### 优先级2: 生成图表

需要创建以下图表并放入 `figures/` 目录：

1. **Phase 1 性能图表**:
   - Box plot: 4个操作的延迟分布
   - CDF: Full handshake 累积分布函数
   - Bar chart: 与 Berger 论文对比

2. **Phase 2 拓扑图**:
   - 12种拓扑的网络示意图
   - SAGIN 架构图（LEO/MEO/GEO）

3. **Phase 3 对比图**:
   - Classic vs PQ-NTOR CDF
   - ARM64 vs x86_64 性能对比

### 优先级3: 完成其他章节

按顺序：Section 3 (Design) → Section 4 (Implementation) → Section 2 (Background) → Section 6 (Related Work) → Section 7 (Conclusion)

---

## 📖 LaTeX 写作提示

### 表格

```latex
\begin{table}[t]
\centering
\caption{表格标题}
\label{tab:yourlabel}
\small
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{列1} & \textbf{列2} & \textbf{列3} \\
\midrule
数据1 & 数据2 & 数据3 \\
\bottomrule
\end{tabular}
\end{table}
```

### 图片

```latex
\begin{figure}[t]
\centering
\includegraphics[width=0.8\columnwidth]{figures/yourfigure.pdf}
\caption{图片标题}
\label{fig:yourlabel}
\end{figure}
```

### 引用

```latex
% 引用表格
见 Table~\ref{tab:yourlabel}

% 引用图片
如 Figure~\ref{fig:yourlabel} 所示

% 引用章节
详见 Section~\ref{sec:evaluation}

% 引用文献
根据 Berger et al.~\cite{berger2025postquantum}
```

---

## 🎯 投稿目标

- **首选**: USENIX Security 2026
- **备选**: IEEE INFOCOM 2026
- **保底**: ACM CCS 2026

当前已使用 USENIX 格式（`usenix-2e.sty`）

---

## 📞 帮助与支持

### 检查编译日志

```bash
# 查看详细错误信息
less main.log
```

### 验证文件结构

```bash
# 列出所有文件
find . -type f -name "*.tex" -o -name "*.bib"
```

---

**Last Updated**: 2025-11-27
**Status**: Section 5 完成，准备编译测试
**Next Steps**: 安装 LaTeX → 编译 PDF → 补充其他章节
