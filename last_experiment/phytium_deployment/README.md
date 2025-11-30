# 飞腾派测试部署指南

**目标**: 在飞腾派上运行PQ-NTOR单机性能测试，验证ARM64兼容性

---

## 🚀 方法一: 自动化部署（推荐）

### 前置条件
确保WSL已安装sshpass（可选，无则使用交互式）

### 执行部署
```bash
cd /home/ccc/pq-ntor-experiment/last_experiment/phytium_deployment
./deploy_to_phytium.sh
```

输入密码: `user`

---

## 🔧 方法二: 手动部署

### 步骤1: 从WSL复制文件到飞腾派

```bash
# 在WSL中执行
cd /home/ccc/pq-ntor-experiment/last_experiment

# 使用scp复制文件（密码: user）
scp test_pq_ntor_single_machine.py user@192.168.5.110:~/pq-ntor-test/
scp topology_tc_params.json user@192.168.5.110:~/pq-ntor-test/

# 复制benchmark程序（如果已编译）
scp ../c/benchmark_pq_ntor user@192.168.5.110:~/pq-ntor-test/
```

### 步骤2: SSH登录飞腾派

```bash
ssh user@192.168.5.110
# 密码: user
```

### 步骤3: 在飞腾派上检查环境

```bash
# 检查架构
uname -m
# 预期输出: aarch64 (ARM64)

# 检查Python版本
python3 --version
# 预期输出: Python 3.x

# 进入测试目录
cd ~/pq-ntor-test
ls -lh
```

### 步骤4: 编译benchmark程序（如果需要）

如果benchmark_pq_ntor未复制或需要重新编译：

```bash
# 方法A: 从WSL复制源码并编译
# (需要先将整个c目录复制到飞腾派)

# 方法B: 如果benchmark程序是x86_64架构，需要在飞腾派上重新编译
cd ~/pq-ntor-test
# 复制c源码目录...
make benchmark_pq_ntor
```

### 步骤5: 运行测试

```bash
cd ~/pq-ntor-test
python3 test_pq_ntor_single_machine.py
```

**预期输出**:
```
======================================================================
                    PQ-NTOR 性能测试开始
======================================================================

测试配置:
  - 拓扑数量: 12
  - 每拓扑测试次数: 100
  - Benchmark程序: ../c/benchmark_pq_ntor

正在测试 topo01 (31.81 Mbps, 5.42 ms, 2.0% 丢包)...
  → 握手时间: 30.70 µs (测试100次)

...

测试完成！结果已保存到 results/ 目录
```

### 步骤6: 查看结果

```bash
# CSV报告
cat results/performance_summary.csv

# JSON数据
cat results/handshake_times.json

# 如果飞腾派有GUI，可以查看图表
xdg-open results/comparison_plots.png
```

---

## 📊 预期测试结果

### ARM64性能预估

飞腾派（ARM Cortex-A72）预期性能：
- **握手时间**: 可能比WSL (x86_64)慢20-50%
- **预估范围**: 40-60 µs（取决于CPU频率）
- **WSL参考**: 30-32 µs

### 性能对比

| 平台 | 架构 | 预期握手时间 | 说明 |
|------|------|-------------|------|
| WSL2 | x86_64 | 30-32 µs | 已测试 ✓ |
| 飞腾派 | ARM64 | 40-60 µs | 待测试 |

---

## 🐛 故障排除

### 问题1: benchmark_pq_ntor未找到

**错误信息**:
```
错误: 找不到PQ-NTOR测试程序
```

**解决方案**:
```bash
# 在飞腾派上，修改测试脚本中的路径
# 将 BENCHMARK_PATH = "../c/benchmark_pq_ntor"
# 改为 BENCHMARK_PATH = "./benchmark_pq_ntor"

# 或者从WSL复制到当前目录
scp user@192.168.5.110:~/pq-ntor-test/benchmark_pq_ntor ./
```

### 问题2: Python模块缺失

**错误信息**:
```
ModuleNotFoundError: No module named 'matplotlib'
```

**解决方案**:
```bash
# 在飞腾派上安装
pip3 install matplotlib
# 或者跳过图表生成（不影响数据收集）
```

### 问题3: 架构不兼容

如果benchmark程序是x86_64编译的：

**错误信息**:
```
cannot execute binary file: Exec format error
```

**解决方案**:
```bash
# 需要在飞腾派上重新编译
# 1. 复制整个c源码目录
# 2. 在飞腾派上编译:
cd ~/pq-ntor-test/c
make clean
make benchmark_pq_ntor
```

---

## 📁 部署包内容

```
phytium_deployment/
├── README.md                          # 本文档
├── deploy_to_phytium.sh              # 自动化部署脚本
├── test_pq_ntor_single_machine.py    # 测试脚本
└── topology_tc_params.json           # 拓扑参数
```

---

## 🎯 测试目标

1. ✅ **验证ARM64兼容性**: 确认测试脚本在飞腾派上运行
2. ✅ **性能基准测试**: 获取ARM平台PQ-NTOR性能数据
3. ✅ **对比分析**: WSL (x86) vs 飞腾派 (ARM) 性能差异

---

## 📞 下一步

测试完成后：

1. **收集结果文件**:
   ```bash
   # 从飞腾派复制结果回WSL
   scp -r user@192.168.5.110:~/pq-ntor-test/results ./phytium_results/
   ```

2. **对比分析**:
   - WSL结果: `/home/ccc/pq-ntor-experiment/last_experiment/results/`
   - 飞腾派结果: `./phytium_results/`

3. **决定下一步**:
   - 如果兼容性OK → 可以进行7派分布式实验
   - 如果性能符合预期 → 可以使用当前数据写论文

---

**创建时间**: 2025-11-29
**适用设备**: 飞腾派 (ARM64)
**测试目的**: ARM架构兼容性验证
