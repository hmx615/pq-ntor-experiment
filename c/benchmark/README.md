# PQ-Ntor Performance Benchmark

这个目录包含 PQ-Ntor 握手协议的性能基准测试工具。

## 📁 文件说明

### 源代码
- **benchmark_pq_ntor.c** - 性能基准测试程序（C语言）
- **visualize.py** - 数据可视化脚本（Python）

### 生成的文件
- **benchmark_results.csv** - 原始性能数据（CSV格式）
- **PERFORMANCE_REPORT.md** - 完整性能测试报告
- **performance_table.tex** - LaTeX 表格（可直接用于论文）
- **operation_times.png** - 各操作时间对比柱状图
- **handshake_breakdown.png** - 握手时间分布饼图
- **ntor_comparison.png** - 与原始 Ntor 对比图
- **overhead_analysis.png** - 通信vs计算开销分析图

## 🚀 快速开始

### 方法1：一键运行（推荐）

```bash
cd ~/pq-ntor-experiment/c
make visualize
```

这将自动：
1. 编译基准测试程序
2. 运行 1000 次测试
3. 生成 CSV 数据
4. 创建所有可视化图表
5. 生成 LaTeX 表格

### 方法2：分步运行

```bash
# 1. 编译基准测试程序
make benchmark

# 2. 运行基准测试
./benchmark_pq_ntor

# 3. 生成可视化（需要 Python 3 + matplotlib）
cd benchmark
python3 visualize.py
```

## 📊 测试配置

### 默认参数
- **测试次数**: 1000 次
- **预热次数**: 10 次
- **算法**: Kyber512
- **测量精度**: 微秒（μs）

### 修改配置

编辑 `benchmark_pq_ntor.c` 文件：

```c
#define NUM_ITERATIONS 1000   // 修改测试次数
#define WARMUP_ITERATIONS 10  // 修改预热次数
```

### 测试 Kyber768

```bash
cd ~/pq-ntor-experiment/c
make clean
make benchmark CFLAGS='-Wall -Wextra -O2 -g -std=c99 -DUSE_KYBER768'
./benchmark_pq_ntor
```

## 📈 结果解读

### 关键指标

运行后将看到：

```
======================================================================
Summary (in milliseconds)
======================================================================
Operation                      Avg (ms)   Median (ms)   Min (ms)   Max (ms)
----------------------------------------------------------------------
Client create onionskin           0.006      0.006         0.005      0.065
Server create reply               0.013      0.012         0.012      0.290
Client finish handshake           0.010      0.010         0.010      0.055
----------------------------------------------------------------------
FULL HANDSHAKE (total)            0.029      0.028         0.028      0.079
```

**重要数据**：
- **平均握手时间**: 0.029 ms = 29 微秒
- **吞吐量**: ~34,500 次握手/秒（单核）
- **稳定性**: 标准差 3.13 μs（非常稳定）

### CSV 数据格式

```csv
Operation,Min(μs),Max(μs),Avg(μs),Median(μs),StdDev(μs),Min(ms),Avg(ms)
Client Create Onionskin,5.00,65.00,6.06,6.00,2.45,0.005,0.006
Server Create Reply,12.00,290.00,13.14,12.00,9.94,0.012,0.013
...
```

## 📊 可视化说明

### 1. operation_times.png
各操作时间对比（最小值/平均值/最大值柱状图）

**用途**: 识别性能瓶颈，展示各步骤耗时

### 2. handshake_breakdown.png
握手时间分布饼图

**用途**: 显示各操作占总时间的百分比

**关键发现**:
- Server reply 占 45%（主要瓶颈）
- Client finish 占 34%
- Client create 占 21%

### 3. ntor_comparison.png
与原始 Ntor 协议对比

**用途**: 展示 PQ-Ntor 相对于经典 Ntor 的开销

**关键数据**:
- 计算时间: PQ-Ntor 更快（由于高度优化的 Kyber）
- 通信开销: PQ-Ntor 10.9× larger

### 4. overhead_analysis.png
通信开销 vs 计算开销双 Y 轴图

**用途**: 综合展示 PQ-Ntor 的主要成本

**关键洞察**:
- 通信开销增加显著（10.9×）
- 计算开销可接受（< 0.03 ms）

## 🔧 依赖要求

### 编译基准测试
- GCC 或 Clang
- liboqs (已安装在 `~/_oqs/`)
- OpenSSL 3.0+
- libm (math library)

### 生成可视化
- Python 3.6+
- matplotlib (`pip3 install matplotlib`)
- numpy (`pip3 install numpy`)

## 📝 在论文中使用

### LaTeX 表格

直接包含生成的表格：

```latex
\input{benchmark/performance_table.tex}
```

或复制其中内容到你的论文中。

### 图片引用

在 LaTeX 中插入图片：

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{benchmark/ntor_comparison.png}
  \caption{PQ-Ntor vs Original Ntor Performance Comparison}
  \label{fig:ntor-comparison}
\end{figure}
```

### 数据引用

关键数据可直接引用：

> "Our implementation achieves an average handshake time of 0.029 ms
> with Kyber512, corresponding to a throughput of 34,500 handshakes
> per second on a single core."

> "Compared to the original Ntor protocol, PQ-Ntor introduces a 10.9×
> increase in communication overhead (1620 bytes vs 148 bytes), but
> maintains sub-millisecond latency."

## 🐛 故障排除

### 编译错误

**错误**: `undefined reference to 'sqrt'`
**解决**: 确保 Makefile 中包含 `-lm` 标志

**错误**: `liboqs.so: cannot open shared object file`
**解决**: 检查 `~/_oqs/lib/` 是否存在，或重新安装 liboqs

### Python 错误

**错误**: `ModuleNotFoundError: No module named 'matplotlib'`
**解决**:
```bash
pip3 install matplotlib numpy --user
```

**错误**: `benchmark_results.csv not found`
**解决**: 先运行基准测试
```bash
cd ~/pq-ntor-experiment/c
./benchmark_pq_ntor
```

### 性能异常

**问题**: 测试结果波动很大

**可能原因**:
1. 系统负载高 → 关闭其他程序
2. 虚拟化开销 → 在物理机上测试
3. 热节流 → 确保散热良好

**解决**: 增加测试次数
```c
#define NUM_ITERATIONS 10000  // 更多迭代平滑波动
```

## 📚 进一步阅读

- **完整性能报告**: `PERFORMANCE_REPORT.md`
- **实现文档**: `../README.md`
- **协议规范**: `../src/pq_ntor.h`

## 🤝 贡献

发现问题或有改进建议？

1. 提交 issue 描述问题
2. 提供测试环境信息（CPU、OS、编译器版本）
3. 附上错误日志或异常输出

## 📄 许可证

与主项目相同。

---

**最后更新**: 2025-10-30
**基准测试版本**: 1.0
