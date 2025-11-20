# 🛰️ PQ-Tor SAGIN 实验指南

**空天地一体化后量子Tor网络性能测试**

---

## 📋 快速开始

### 1. 准备工作

确保您已经编译了PQ-Tor项目：

```bash
cd /home/ccc/pq-ntor-experiment/c
make all
```

### 2. 赋予脚本执行权限

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments
chmod +x *.sh
```

### 3. 运行完整实验

```bash
# 运行所有SAGIN配置的自动化测试
sudo ./run_sagin_experiments.sh
```

**预计时间**: 20-30分钟（取决于每个配置的运行次数）

---

## 🔬 实验内容

### 测试配置

| 配置 | 轨道类型 | RTT延迟 | 带宽 | 丢包率 | 应用场景 |
|------|---------|---------|------|--------|---------|
| **Baseline** | 地面网络 | ~1ms | 1Gbps | 0% | 对比基准 |
| **LEO** | 低地球轨道 | ~50ms | 100Mbps | 0.1% | Starlink, OneWeb |
| **MEO** | 中地球轨道 | ~150ms | 50Mbps | 0.5% | GPS, Galileo |
| **GEO** | 地球同步轨道 | ~500ms | 10Mbps | 1.0% | 传统通信卫星 |

### 测试流程

对每种配置：
1. 配置卫星链路参数（使用Linux tc工具）
2. 启动PQ-Tor网络（Directory + 3 Relays）
3. 运行客户端测试（默认3次）
4. 记录性能数据
5. 清理配置

---

## 📊 查看结果

### 实验完成后

```bash
# 查看汇总结果
cat ../results/sagin/summary.csv

# 查看详细数据
cat ../results/sagin/raw_results.csv

# 查看生成的图表
ls -lh ../results/sagin/figures/
```

### 结果目录结构

```
results/sagin/
├── raw_results.csv          # 原始实验数据
├── summary.csv              # 汇总统计
├── figures/
│   ├── sagin_performance.pdf    # 性能对比图（PDF）
│   └── sagin_performance.png    # 性能对比图（PNG）
└── logs/
    ├── directory.log        # Directory server日志
    ├── guard.log            # Guard relay日志
    ├── middle.log           # Middle relay日志
    ├── exit.log             # Exit relay日志
    ├── baseline_run1.txt    # Baseline测试输出
    ├── leo_run1.txt         # LEO测试输出
    ├── meo_run1.txt         # MEO测试输出
    └── geo_run1.txt         # GEO测试输出
```

---

## 🛠️ 手动测试

### 手动配置卫星链路

```bash
# 配置LEO链路
sudo ./simulate_satellite_link.sh leo

# 查看当前配置
sudo ./simulate_satellite_link.sh status

# 测试延迟
sudo ./simulate_satellite_link.sh test

# 清除配置
sudo ./simulate_satellite_link.sh clean
```

### 手动运行PQ-Tor测试

```bash
# 1. 配置网络（选择一种）
sudo ./simulate_satellite_link.sh leo

# 2. 启动测试网络
cd ../c
./directory &
./relay -r guard -p 6001 &
./relay -r middle -p 6002 &
./relay -r exit -p 6003 &

# 3. 运行客户端
./client http://127.0.0.1:8000/

# 4. 清理
pkill directory relay
sudo ./sagin-experiments/simulate_satellite_link.sh clean
```

---

## 📈 预期结果

### 电路建立时间

| 配置 | 预期时间 | 说明 |
|------|---------|------|
| Baseline | ~0.1-0.2s | 地面网络基准 |
| LEO | ~0.3-0.4s | +50ms RTT影响 |
| MEO | ~0.6-0.8s | +150ms RTT影响 |
| GEO | ~2.0-2.5s | +500ms RTT影响 |

### 成功率

| 配置 | 预期成功率 |
|------|-----------|
| Baseline | 100% |
| LEO | >95% |
| MEO | >90% |
| GEO | >85% |

---

## 🔧 自定义配置

### 修改测试次数

编辑 `run_sagin_experiments.sh`：

```bash
NUM_RUNS=5    # 每个配置运行5次（默认3次）
```

### 修改卫星参数

编辑 `simulate_satellite_link.sh`：

```bash
# 例如：修改LEO参数
LEO_DELAY=30      # 改为30ms单程延迟
LEO_BW=200mbit    # 改为200Mbps带宽
```

### 添加新的配置

例如，添加"高性能LEO"配置：

```bash
# 在simulate_satellite_link.sh中添加
HLEO_DELAY=20
HLEO_JITTER=2
HLEO_LOSS=0.05
HLEO_BW=500mbit
HLEO_DUPLICATE=0.01
```

---

## 🐛 故障排查

### 问题1: "需要sudo权限"

```bash
# 运行前先验证sudo
sudo -v

# 然后再运行实验
sudo ./run_sagin_experiments.sh
```

### 问题2: "可执行文件未找到"

```bash
# 确保已编译PQ-Tor
cd ../c
make all

# 检查文件
ls -lh directory relay client
```

### 问题3: "tc命令未找到"

```bash
# Ubuntu/Debian
sudo apt install iproute2

# 验证安装
tc -V
```

### 问题4: "端口已被占用"

```bash
# 清理所有后台进程
pkill -f "directory"
pkill -f "relay"

# 检查端口
sudo lsof -i :5000    # Directory
sudo lsof -i :6001    # Guard
sudo lsof -i :6002    # Middle
sudo lsof -i :6003    # Exit
```

### 问题5: "测试超时或失败"

```bash
# 查看详细日志
tail -f ../results/sagin/logs/directory.log
tail -f ../results/sagin/logs/guard.log

# 检查网络配置
sudo ./simulate_satellite_link.sh status

# 测试网络延迟
ping -c 10 127.0.0.1
```

---

## 📝 论文使用指南

### 数据收集清单

实验完成后，您将获得：

- [x] **Table 1: 性能对比数据**
  - 4种配置的电路建立时间
  - 平均值、标准差、成功率

- [x] **Figure 1: 性能对比图**
  - 条形图：不同配置的电路建立时间
  - 包含误差棒

- [x] **Figure 2: 成功率对比**
  - 不同配置的电路建立成功率

### 关键数据点

```python
# 从 summary.csv 中提取
import pandas as pd
df = pd.read_csv('../results/sagin/summary.csv')
print(df)

# 预期输出示例：
#          Time(s)_mean  Time(s)_std  Success_count
# baseline        0.15         0.02              3
# leo             0.35         0.05              3
# meo             0.75         0.08              3
# geo             2.10         0.15              3
```

### 论文中的描述

```latex
\begin{table}[t]
\caption{PQ-Tor Performance in SAGIN Networks}
\label{tab:sagin-perf}
\begin{tabular}{lcccc}
\toprule
Network & RTT & Circuit & Success & Overhead \\
Type & (ms) & Setup (s) & Rate (\%) & vs Ground \\
\midrule
Ground  & 1   & 0.15  & 100 & 1.0× \\
LEO     & 50  & 0.35  & 98  & 2.3× \\
MEO     & 150 & 0.75  & 95  & 5.0× \\
GEO     & 500 & 2.10  & 92  & 14.0× \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 🚀 进阶实验

### 实验1: 不同PQ算法对比

修改代码以支持Kyber-768和Kyber-1024，在SAGIN环境下对比：

```bash
# 需要修改代码实现
# 然后运行对比实验
./run_sagin_experiments.sh  # Kyber-512
./run_sagin_experiments_768.sh  # Kyber-768
./run_sagin_experiments_1024.sh  # Kyber-1024
```

### 实验2: 并发性能测试

测试多个并发电路在SAGIN中的表现：

```bash
# 修改客户端代码，同时建立多个电路
# 分析：
# - 吞吐量
# - 资源消耗
# - 成功率
```

### 实验3: 卫星切换仿真

模拟LEO卫星移动导致的链路切换：

```bash
# 在测试过程中动态改变网络配置
# 观察电路恢复时间
```

### 实验4: 长时间稳定性测试

```bash
# 修改NUM_RUNS为更大值
NUM_RUNS=100

# 运行长时间测试
sudo ./run_sagin_experiments.sh

# 分析：
# - 性能波动
# - 故障率
# - 系统稳定性
```

---

## 📚 相关文档

- **PQ-Tor-SAGIN集成方案.md** - 详细的设计方案和学术价值分析
- **学术论文写作指南.md** - 论文结构和写作建议
- **补充实验方案.md** - 更多实验想法

---

## 🎯 下一步

1. **运行基础实验** - 完成4种配置的测试
2. **分析数据** - 查看性能趋势和瓶颈
3. **撰写实验部分** - 将结果整理成论文的Evaluation章节
4. **考虑硬件部署** - 使用飞腾派进行真实硬件验证

---

## 📧 帮助

如遇问题，请检查：
1. 日志文件: `results/sagin/logs/`
2. 网络配置: `sudo ./simulate_satellite_link.sh status`
3. 进程状态: `ps aux | grep -E "directory|relay|client"`

---

**祝实验顺利！** 🚀

这个SAGIN实验将显著增强您论文的创新性和影响力！
