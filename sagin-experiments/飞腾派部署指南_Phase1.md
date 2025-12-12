# 飞腾派部署指南 - Phase 1 密码学基元测试

**目标**: 在真实ARM64飞腾派硬件上运行Phase 1性能测试
**预期时间**: 15-20分钟

---

## 📋 部署前检查清单

### 1. 飞腾派硬件信息确认

登录飞腾派,确认硬件配置:

```bash
# 1. 检查CPU信息
lscpu | grep -E "(Architecture|Model name|CPU MHz|BogoMIPS)"

# 2. 确认是ARM64
uname -m  # 应输出: aarch64

# 3. 检查内存
free -h

# 4. 检查系统版本
cat /etc/os-release
```

**预期输出**:
- Architecture: aarch64
- Model: Phytium FTC664 或类似
- CPU MHz: 2300 左右

### 2. 检查依赖环境

```bash
# 检查liboqs是否已安装
ls -la ~/pq-ntor-experiment/_oqs/lib/liboqs.so* 2>/dev/null || echo "liboqs未安装"

# 检查OpenSSL
openssl version

# 检查GCC
gcc --version
```

**如果liboqs未安装**,参考之前的安装脚本(见主项目README)。

---

## 🚀 快速部署步骤

### 方法A: 使用Git同步 (推荐)

如果飞腾派可以访问你的Git仓库:

```bash
# 在飞腾派上
cd ~/pq-ntor-experiment
git pull origin main  # 拉取最新代码

cd sagin-experiments/docker/build_context/c
make clean
make phase1_crypto_primitives
```

### 方法B: SCP文件传输

如果飞腾派IP是`192.168.5.XXX`:

```bash
# 在开发机(WSL2)上执行
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 传输源代码
scp -r benchmark/ Makefile src/ pi@192.168.5.XXX:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/

# 或者使用rsync (更快)
rsync -avz --progress benchmark/ Makefile src/ \
  pi@192.168.5.XXX:~/pq-ntor-experiment/sagin-experiments/docker/build_context/c/
```

然后在飞腾派上编译:

```bash
# 在飞腾派上
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make clean
make phase1_crypto_primitives
```

---

## 🔧 编译验证

### 1. 编译Phase 1程序

```bash
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make phase1_crypto_primitives
```

**预期输出**:
```
Compiling src/kyber_kem.c...
Compiling src/crypto_utils.c...
Compiling src/pq_ntor.c...
...
Building Phase 1 Crypto Primitives Benchmark...
✓ Built: phase1_crypto_primitives
```

**如果编译失败**,检查:
- liboqs路径是否正确: `ls ~/pq-ntor-experiment/_oqs/lib/liboqs.so`
- Makefile中的`LIBOQS_DIR`是否正确

### 2. 测试运行

```bash
# 快速测试(10次迭代,验证程序可运行)
./phase1_crypto_primitives 2>&1 | head -30
```

如果看到类似输出,说明程序正常:
```
======================================================================
Phase 1: Cryptographic Primitives Performance Benchmarking
======================================================================
Platform:      ARM64 Phytium Pi (FTC664 @ 2.3GHz)
Algorithm:     Kyber512
...
```

---

## 📊 正式运行测试

### 1. 运行完整测试

```bash
cd ~/pq-ntor-experiment/sagin-experiments/docker/build_context/c

# 运行Phase 1测试 (约1-2分钟)
make phase1 | tee phase1_output.txt
```

### 2. 检查输出

```bash
# 查看CSV结果
cat phase1_crypto_benchmarks.csv

# 查看完整输出
less phase1_output.txt
```

### 3. 保存结果

```bash
# 创建结果目录
mkdir -p ~/phase1_results_$(date +%Y%m%d_%H%M%S)
RESULT_DIR=~/phase1_results_$(date +%Y%m%d_%H%M%S)

# 复制结果文件
cp phase1_crypto_benchmarks.csv $RESULT_DIR/
cp phase1_output.txt $RESULT_DIR/

# 保存系统信息
lscpu > $RESULT_DIR/system_info.txt
cat /proc/cpuinfo >> $RESULT_DIR/system_info.txt
free -h >> $RESULT_DIR/system_info.txt

echo "结果已保存到: $RESULT_DIR"
```

---

## 📈 结果分析

### 1. 关键指标检查

打开CSV文件,检查以下指标:

```bash
cat phase1_crypto_benchmarks.csv | column -t -s,
```

**预期范围** (基于文献和ARM64特性):

| 操作 | 预期范围 (μs) | 备注 |
|------|--------------|------|
| Kyber-512 Keygen | 40-60 | ARM64约为x86的1.5-2× |
| Kyber-512 Encaps | 50-70 | - |
| Kyber-512 Decaps | 40-60 | - |
| HKDF-SHA256 | 5-15 | 取决于数据量 |
| HMAC-SHA256 | 3-10 | - |

**如果结果显著偏离**:
- 太快(<10μs): 可能时间测量有问题或优化过度
- 太慢(>100μs): 可能CPU频率未达标或后台负载高

### 2. 与Berger论文对比

程序会自动输出对比表格:

```
Performance Comparison with Literature (Berger et al. 2025)
======================================================================
Operation              This Work      Berger (x86)    Ratio
                       (ARM64)        @3.0GHz         ARM/x86
----------------------------------------------------------------------
Kyber-512 Keygen       XX.XX μs      25.80 μs        X.XXx
```

**合理范围**:
- ARM64/x86比率应在: **1.5-2.5×** (ARM64较慢)
- 如果<1.0×(ARM64更快),数据异常,需重新测试

---

## 🔍 故障排查

### 问题1: 编译错误 - 找不到liboqs

```bash
# 检查liboqs路径
ls ~/pq-ntor-experiment/_oqs/lib/liboqs.so

# 如果不存在,需要重新安装liboqs
cd ~/pq-ntor-experiment
# 运行liboqs安装脚本
```

### 问题2: 运行时错误 - Segmentation fault

```bash
# 检查是否有权限问题
chmod +x phase1_crypto_primitives

# 使用gdb调试
gdb ./phase1_crypto_primitives
(gdb) run
(gdb) bt  # 如果crash,查看backtrace
```

### 问题3: 结果异常 - 性能过快或过慢

**可能原因与解决方案**:

1. **CPU频率未达标**:
   ```bash
   # 检查当前频率
   cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

   # 设置为performance模式
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

2. **后台负载高**:
   ```bash
   # 检查负载
   top

   # 关闭不必要的进程
   ```

3. **时间测量精度问题**:
   - 当前使用`gettimeofday`(微秒精度)
   - 如果结果异常,可能需要修改为`clock_gettime`(纳秒精度)

---

## 📤 结果回传

### 方法A: SCP回传到开发机

```bash
# 在飞腾派上
RESULT_DIR=~/phase1_results_20251203_XXXXXX  # 替换为实际目录
scp -r $RESULT_DIR user@your-dev-machine:/path/to/destination/
```

### 方法B: Git提交(如果有仓库)

```bash
cd ~/pq-ntor-experiment
git add phase1_crypto_benchmarks.csv phase1_output.txt
git commit -m "feat: Phase 1 benchmark results from Phytium Pi"
git push
```

### 方法C: 直接复制粘贴

```bash
# 在飞腾派上显示结果
cat phase1_crypto_benchmarks.csv
cat phase1_output.txt | grep -A 50 "Summary Table"
```

然后手动复制到开发机。

---

## ✅ 成功标准

Phase 1测试成功的标志:

1. ✅ 程序正常编译,无错误
2. ✅ 运行完整,生成CSV文件
3. ✅ 所有操作Mean时间 > 0
4. ✅ ARM64/x86性能比在1.5-2.5×范围内
5. ✅ 标准差 < Mean的30%
6. ✅ P99 < Mean的3倍

---

## 📞 需要帮助?

如果遇到问题:

1. **编译问题**: 检查依赖安装,查看错误日志
2. **运行问题**: 使用`gdb`调试,检查系统资源
3. **结果异常**: 重新运行3次,取平均值

**常用调试命令**:
```bash
# 查看详细编译过程
make phase1_crypto_primitives V=1

# 检查链接的库
ldd ./phase1_crypto_primitives

# 运行并保存所有输出
./phase1_crypto_primitives 2>&1 | tee full_output.log
```

---

## 🎯 下一步

Phase 1完成后:

1. **分析结果**: 对比文献数据,验证合理性
2. **准备Phase 2**: 协议握手性能测试
3. **准备Phase 3**: 12拓扑SAGIN网络测试

---

**文档版本**: v1.0
**更新日期**: 2025-12-03
**适用平台**: Phytium Pi (ARM64)
