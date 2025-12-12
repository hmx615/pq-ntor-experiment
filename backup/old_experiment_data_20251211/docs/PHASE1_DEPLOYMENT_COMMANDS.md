# Phase 1 快速部署命令参考

**部署时间**: 2025-12-03
**目标硬件**: Phytium Pi (ARM64 @ 2.3GHz)

---

## 🚀 一键部署流程 (三步完成)

### 准备工作: 设置你的飞腾派IP

```bash
# 替换为你的实际飞腾派IP地址
export PI_IP="192.168.5.XXX"  # 例如: 192.168.5.185
export PI_USER="pi"            # 飞腾派用户名
```

---

### Step 1: 传输文件到飞腾派 (2分钟)

**选项A: 使用rsync (推荐)**
```bash
cd /home/ccc/pq-ntor-experiment

rsync -avz --progress \
  sagin-experiments/docker/build_context/c/ \
  $PI_USER@$PI_IP:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/
```

**选项B: 使用scp**
```bash
cd /home/ccc/pq-ntor-experiment

scp -r sagin-experiments/docker/build_context/c/ \
  $PI_USER@$PI_IP:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/
```

**验证传输成功**:
```bash
ssh $PI_USER@$PI_IP "ls -lh ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/run_phase1_on_pi.sh"
```

---

### Step 2: 在飞腾派上运行测试 (1-2分钟)

**一键运行**:
```bash
ssh $PI_USER@$PI_IP "cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c && ./run_phase1_on_pi.sh"
```

**或者分步运行** (如果想查看详细过程):
```bash
# 2.1 登录飞腾派
ssh $PI_USER@$PI_IP

# 2.2 进入测试目录
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 2.3 执行测试脚本
./run_phase1_on_pi.sh

# 脚本会自动完成:
# - 检查系统环境 (CPU, 内存, 依赖)
# - 设置CPU性能模式
# - 编译Phase 1测试程序
# - 运行1000次性能测试
# - 保存结果到 ~/phase1_results_YYYYMMDD_HHMMSS/
```

---

### Step 3: 回传结果到开发机 (1分钟)

**查看飞腾派上的结果**:
```bash
ssh $PI_USER@$PI_IP "ls -lh ~/phase1_results_*/"
ssh $PI_USER@$PI_IP "cat ~/phase1_results_*/phase1_crypto_benchmarks.csv | column -t -s,"
```

**回传结果到本地**:
```bash
# 在开发机上执行
cd /home/ccc/pq-ntor-experiment/essay

# 回传所有结果文件
scp -r $PI_USER@$PI_IP:~/phase1_results_*/ ./phase1_results_phytium/

# 验证回传成功
ls -lh phase1_results_phytium/
cat phase1_results_phytium/phase1_results_*/phase1_crypto_benchmarks.csv
```

---

## 📊 预期结果验证

### 正常性能范围

运行完成后,检查CSV文件中的Mean值是否在以下范围:

| 操作 | 预期范围 (μs) | Berger x86 (μs) | 预期比率 |
|------|--------------|----------------|---------|
| Kyber-512 Keygen | **45-55** | 25.8 | 1.7-2.1× |
| Kyber-512 Encaps | **52-65** | 30.1 | 1.7-2.2× |
| Kyber-512 Decaps | **42-58** | 27.6 | 1.5-2.1× |
| HKDF-SHA256 | **8-15** | - | - |
| HMAC-SHA256 | **4-10** | - | - |

### 结果判断标准

✅ **正常**: ARM64比x86慢1.5-2.5倍
⚠️ **可疑**: ARM64比x86快,或慢超过3倍
❌ **错误**: 任何操作<5μs或>200μs

---

## 🔧 故障排查

### 问题1: SSH连接失败
```bash
# 测试连通性
ping $PI_IP

# 测试SSH
ssh $PI_USER@$PI_IP "echo 'Connection OK'"
```

### 问题2: 传输失败 - 目录不存在
```bash
# 在飞腾派上创建目录
ssh $PI_USER@$PI_IP "mkdir -p ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
```

### 问题3: 编译失败 - liboqs未找到
```bash
# 检查liboqs
ssh $PI_USER@$PI_IP "ls -lh ~/pq-ntor-experiment/_oqs/lib/liboqs.so"

# 如果不存在,需要先安装liboqs (参考主项目README)
```

### 问题4: 脚本没有执行权限
```bash
ssh $PI_USER@$PI_IP "chmod +x ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/run_phase1_on_pi.sh"
```

---

## 📁 结果文件说明

部署成功后,飞腾派上会生成以下文件:

```
~/phase1_results_20251203_HHMMSS/
├── phase1_crypto_benchmarks.csv    # CSV数据 (可用Excel打开)
├── phase1_output.txt               # 完整运行日志
└── system_info.txt                 # 系统硬件信息
```

**CSV文件格式**:
```csv
Operation,Min_us,Max_us,Mean_us,Median_us,StdDev_us,P95_us,P99_us,CI_Lower,CI_Upper
Kyber-512 Keygen,XX.XX,XX.XX,XX.XX,XX.XX,XX.XX,XX.XX,XX.XX,XX.XX,XX.XX
...
```

---

## 🎯 完成确认清单

运行完成后,确认以下项目:

- [ ] 程序正常运行,无崩溃
- [ ] 生成`phase1_crypto_benchmarks.csv`文件
- [ ] 生成`phase1_output.txt`日志
- [ ] 所有操作Mean时间 > 5μs
- [ ] ARM64/x86性能比在1.5-2.5×范围内
- [ ] 标准差(StdDev) < Mean的50%
- [ ] 结果文件已回传到开发机
- [ ] CSV数据可以正常打开查看

---

## 📞 需要帮助?

**详细文档**:
- 完整部署指南: `sagin-experiments/飞腾派部署指南_Phase1.md`
- 一键部署README: `sagin-experiments/飞腾派一键部署_README.md`
- 总结报告: `essay/Phase1_部署准备完成_总结.md`

**常用命令**:
```bash
# 查看飞腾派CPU信息
ssh $PI_USER@$PI_IP "lscpu | grep -E '(Architecture|Model|MHz)'"

# 查看飞腾派内存
ssh $PI_USER@$PI_IP "free -h"

# 手动编译 (如果脚本失败)
ssh $PI_USER@$PI_IP "cd ~/pq-ntor-experiment/.../c && make clean && make phase1_crypto_primitives"

# 手动运行测试
ssh $PI_USER@$PI_IP "cd ~/pq-ntor-experiment/.../c && ./phase1_crypto_primitives"
```

---

**创建日期**: 2025-12-03
**状态**: ✅ 代码就绪,等待部署
**下一步**: 执行上述三步部署流程
