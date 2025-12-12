# 飞腾派一键部署 - Phase 1性能测试

## 🚀 三步快速部署

### Step 1: 传输文件到飞腾派

**选项A: 使用rsync (推荐,支持断点续传)**

```bash
# 在开发机上执行 (替换IP地址)
PI_IP="192.168.5.XXX"  # 你的飞腾派IP
PI_USER="pi"           # 飞腾派用户名

cd /home/ccc/pq-ntor-experiment

# 同步整个C代码目录
rsync -avz --progress \
  sagin-experiments/docker/build_context/c/ \
  $PI_USER@$PI_IP:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/
```

**选项B: 使用scp (简单直接)**

```bash
PI_IP="192.168.5.XXX"
PI_USER="pi"

cd /home/ccc/pq-ntor-experiment

# 传输C代码目录
scp -r sagin-experiments/docker/build_context/c/ \
  $PI_USER@$PI_IP:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/
```

**选项C: 使用Git (如果飞腾派有网络)**

```bash
# 在飞腾派上执行
cd ~/pq-ntor-experiment
git pull origin main  # 或你的分支名
```

---

### Step 2: 登录飞腾派并运行测试

```bash
# SSH登录飞腾派
ssh pi@192.168.5.XXX

# 进入测试目录
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 一键运行测试脚本
./run_phase1_on_pi.sh
```

**脚本会自动**:
1. ✅ 检查系统环境 (CPU, 内存, 依赖)
2. ✅ 设置CPU性能模式
3. ✅ 编译Phase 1测试程序
4. ✅ 运行1000次性能测试
5. ✅ 保存结果到时间戳目录
6. ✅ 生成CSV和完整日志

**预计耗时**: 1-2分钟

---

### Step 3: 查看并回传结果

**在飞腾派上查看结果**:

```bash
# 脚本会显示结果目录路径,类似:
# 结果将保存到: /home/pi/phase1_results_20251203_151234

# 查看CSV数据
cat ~/phase1_results_*/phase1_crypto_benchmarks.csv | column -t -s,

# 查看性能摘要
grep "Summary Table" -A 10 ~/phase1_results_*/phase1_output.txt
```

**回传结果到开发机**:

```bash
# 在开发机上执行
PI_IP="192.168.5.XXX"
RESULT_DIR="phase1_results_20251203_151234"  # 替换为实际目录名

scp -r pi@$PI_IP:~/phase1_results_*/ \
  /home/ccc/pq-ntor-experiment/essay/phase1_results_phytium/
```

---

## 📊 预期结果

### 正常性能范围 (ARM64 Phytium FTC664 @ 2.3GHz)

| 操作 | 预期范围 (μs) | Berger x86 (μs) | ARM/x86比率 |
|------|--------------|----------------|------------|
| Kyber-512 Keygen | 40-60 | 25.8 | 1.5-2.3× |
| Kyber-512 Encaps | 50-70 | 30.1 | 1.7-2.3× |
| Kyber-512 Decaps | 40-60 | 27.6 | 1.4-2.2× |
| HKDF-SHA256 | 5-15 | - | - |
| HMAC-SHA256 | 3-10 | - | - |

**判断标准**:
- ✅ **正常**: ARM64比x86慢1.5-2.5倍
- ⚠️ **异常**: ARM64比x86快,或慢超过3倍
- ❌ **错误**: 任何操作<5μs或>200μs

---

## 🔧 故障排查

### 问题1: 传输失败 - Permission denied

```bash
# 确认可以SSH登录
ssh pi@192.168.5.XXX "echo 连接成功"

# 检查目标目录是否存在
ssh pi@192.168.5.XXX "mkdir -p ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
```

### 问题2: 脚本执行失败 - liboqs未找到

```bash
# 在飞腾派上检查liboqs
ls ~/pq-ntor-experiment/_oqs/lib/liboqs.so

# 如果不存在,需要安装liboqs
cd ~/pq-ntor-experiment
# 参考主项目README安装liboqs
```

### 问题3: 编译错误

```bash
# 手动编译查看详细错误
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make clean
make phase1_crypto_primitives V=1  # 显示详细编译过程
```

### 问题4: 性能异常

**如果结果过快 (<10μs)**:
```bash
# 检查CPU频率
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

# 设置performance模式
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**如果结果过慢 (>100μs)**:
```bash
# 检查系统负载
top
htop

# 关闭不必要的进程后重新测试
```

---

## 📝 手动运行 (如果脚本失败)

如果自动脚本出问题,可以手动执行:

```bash
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 1. 编译
make clean
make phase1_crypto_primitives

# 2. 运行
./phase1_crypto_primitives | tee phase1_output.txt

# 3. 查看结果
cat phase1_crypto_benchmarks.csv
```

---

## 🎯 成功检查清单

运行完成后,确认以下项目:

- [ ] 程序正常运行,无崩溃
- [ ] 生成`phase1_crypto_benchmarks.csv`文件
- [ ] 生成`phase1_output.txt`日志
- [ ] 所有操作Mean时间 > 5μs
- [ ] ARM64/x86性能比在1.5-2.5×范围内
- [ ] 标准差(StdDev) < Mean的50%
- [ ] 结果已保存到时间戳目录

---

## 📞 需要帮助?

如果遇到问题,检查:

1. **网络连接**: `ping 192.168.5.XXX`
2. **SSH密钥**: 使用密码或配置SSH密钥
3. **文件权限**: `chmod +x run_phase1_on_pi.sh`
4. **依赖环境**: liboqs, gcc, openssl是否都已安装

**查看完整部署指南**: `飞腾派部署指南_Phase1.md`

---

## 🎉 完成后的下一步

Phase 1成功后:

1. **分析数据**: 对比Berger论文,验证合理性
2. **生成图表**: 使用Python可视化性能分布
3. **准备Phase 2**: 协议握手性能测试(PQ-NTOR vs Classic)

---

**快速命令参考**:

```bash
# 传输文件
rsync -avz c/ pi@IP:~/pq-ntor-experiment/.../c/

# 运行测试
ssh pi@IP "cd ~/pq-ntor-experiment/.../c && ./run_phase1_on_pi.sh"

# 回传结果
scp -r pi@IP:~/phase1_results_*/ ./local_results/
```

---

**文档版本**: v1.0
**创建日期**: 2025-12-03
**适用平台**: Phytium Pi ARM64
