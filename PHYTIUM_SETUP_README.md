# 🚀 飞腾派一键部署指南

**脚本**: `setup_phytium.sh`
**创建时间**: 2025-11-27
**适用平台**: ARM64 (飞腾派、树莓派等)
**预计时间**: 15-25 分钟

---

## 📋 功能概览

这个脚本会自动完成：

1. ✅ **检查系统环境** - 验证架构、操作系统、编译工具
2. ✅ **安装系统依赖** - GCC、CMake、OpenSSL 等
3. ✅ **编译 liboqs** - Kyber KEM 后量子密码库
4. ✅ **验证 Kyber** - 运行测试确保库正常工作
5. ✅ **编译 PQ-Tor** - 完整的 Tor 后量子实现
6. ✅ **运行测试** - 6 个单元测试验证
7. ✅ **环境配置** - 设置必要的环境变量
8. ✅ **生成报告** - 显示安装位置和使用说明

---

## 🎯 使用方法

### 方式 1: 一键运行（推荐）

```bash
# 在飞腾派上执行
cd ~/pq-ntor-experiment
./setup_phytium.sh
```

### 方式 2: 从零开始（全新设备）

```bash
# 1. 传输项目到飞腾派
# 在开发机上：
cd /home/ccc/pq-ntor-experiment
tar czf pq-tor-phytium.tar.gz \
    c/ \
    setup_phytium.sh \
    PHYTIUM_SETUP_README.md \
    readme/

# 传输到飞腾派
scp pq-tor-phytium.tar.gz user@飞腾派IP:~/

# 2. 在飞腾派上解压
ssh user@飞腾派IP
cd ~
tar xzf pq-tor-phytium.tar.gz

# 3. 运行部署脚本
cd pq-ntor-experiment
chmod +x setup_phytium.sh
./setup_phytium.sh
```

### 方式 3: 使用 Git（如果飞腾派可联网）

```bash
# 在飞腾派上
cd ~
git clone https://github.com/hmx615/pq-ntor-experiment.git
cd pq-ntor-experiment
./setup_phytium.sh
```

---

## 📊 脚本执行流程

```
╔════════════════════════════════════════════════════════════╗
║         PQ-Tor 飞腾派自动化部署脚本                        ║
╚════════════════════════════════════════════════════════════╝

[1/8] 检查系统架构
      ✅ ARM64 架构确认
      ✅ Linux 系统确认

[2/8] 检查必备工具
      ✅ GCC 已安装
      ✅ Make 已安装
      ✅ CMake 已安装
      ✅ Git 已安装
      ✅ OpenSSL 开发库已安装

[3/8] 安装系统依赖 (如需要)
      ✅ 软件源更新完成
      ✅ 所有依赖安装完成

[4/8] 编译安装 liboqs (Kyber KEM 库)
      ℹ️  源码准备完成 (版本: 0.11.0)
      ℹ️  CMake 配置完成
      ⚠️  ARM 设备编译时间较长，预计 3-8 分钟...
      ✅ 编译完成
      ✅ 安装完成
      ✅ 库文件存在
      ✅ 头文件目录存在

[5/8] 创建 Kyber KEM 验证程序
      ✅ 测试代码生成完成
      ✅ 编译完成

[6/8] 运行 Kyber KEM 验证
      ✅ Kyber512 可用
      ✅ KEM 对象创建成功
      ✅ 密钥对生成成功
      ✅ 封装成功
      ✅ 解封装成功
      ✅ 共享密钥匹配
      ✅ Kyber KEM 验证通过！

[7/8] 编译 PQ-Tor 项目
      ✅ PQ-Tor 编译完成
      ✅ directory
      ✅ relay
      ✅ client
      ✅ test_pq_ntor
      ✅ test_classic_ntor
      ✅ benchmark_pq_ntor

[8/8] 运行 PQ-Tor 单元测试
      ✅ test_kyber 通过
      ✅ test_crypto 通过
      ✅ test_pq_ntor 通过
      ✅ test_classic_ntor 通过
      ✅ test_cell 通过
      ✅ test_onion 通过
      ✅ 所有测试通过！

╔════════════════════════════════════════════════════════════╗
║                 🎉 部署完成！                              ║
╚════════════════════════════════════════════════════════════╝
```

---

## ⏱️ 时间预估

| 步骤 | 预计时间 | 说明 |
|------|---------|------|
| 系统检查 | 10 秒 | 验证环境 |
| 依赖安装 | 2-5 分钟 | 如需安装 |
| 编译 liboqs | 3-8 分钟 | ARM 设备较慢 |
| Kyber 验证 | 30 秒 | 测试编译运行 |
| 编译 PQ-Tor | 1-3 分钟 | 主项目编译 |
| 运行测试 | 1 分钟 | 6 个单元测试 |
| **总计** | **15-25 分钟** | 取决于设备性能 |

---

## 📁 安装位置

部署完成后，文件位置：

```
~/
├── oqs/                          # liboqs 安装目录
│   ├── lib/liboqs.so            # 动态链接库
│   └── include/oqs/             # 头文件
│
├── pq-tor-deps/                 # 编译工作目录
│   ├── liboqs/                  # liboqs 源码
│   └── kyber-test/              # Kyber 测试程序
│
└── pq-ntor-experiment/          # PQ-Tor 项目
    └── c/                       # 编译产物
        ├── directory            # 目录服务器
        ├── relay                # 中继节点
        ├── client               # 客户端
        ├── test_*               # 测试程序
        └── benchmark_pq_ntor    # 性能基准
```

---

## 🎯 验证安装

### 验证 liboqs

```bash
# 检查库文件
ls -lh ~/oqs/lib/liboqs.so*

# 运行 Kyber 测试
cd ~/pq-tor-deps/kyber-test
./test_kyber_simple
```

### 验证 PQ-Tor

```bash
cd ~/pq-ntor-experiment/c

# 运行单元测试
./test_pq_ntor
./test_classic_ntor

# 运行性能基准
./benchmark_pq_ntor

# 运行完整网络测试
./test_network.sh
```

---

## 🚀 快速开始

### 1. 运行本地测试网络

```bash
cd ~/pq-ntor-experiment/c

# 启动目录服务器（终端1）
./directory

# 启动中继节点（终端2）
./relay -r guard -p 6001

# 启动客户端（终端3）
./client -u http://127.0.0.1:8000/
```

### 2. 性能基准测试

```bash
cd ~/pq-ntor-experiment/c

# PQ-NTOR 基准测试
./benchmark_pq_ntor

# Classic vs PQ 对比
./client --mode classic -u http://127.0.0.1:8000/
./client --mode pq -u http://127.0.0.1:8000/
```

### 3. SAGIN 网络模拟

```bash
cd ~/pq-ntor-experiment/sagin-experiments

# 需要 sudo 权限（tc 网络模拟）
sudo ./run_sagin_experiments.sh
```

---

## 🐛 常见问题

### Q1: liboqs 编译失败

**可能原因**：CMake 版本太老或缺少依赖

**解决方案**：
```bash
# 重新安装依赖
sudo apt-get update
sudo apt-get install -y build-essential cmake libssl-dev

# 重新运行脚本
./setup_phytium.sh
```

### Q2: 找不到 liboqs.so

**可能原因**：环境变量未设置

**解决方案**：
```bash
# 临时设置
export LD_LIBRARY_PATH=~/oqs/lib:$LD_LIBRARY_PATH

# 永久设置
echo 'export LD_LIBRARY_PATH=~/oqs/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Q3: PQ-Tor 编译失败

**可能原因**：Makefile 找不到 liboqs

**解决方案**：
```bash
cd ~/pq-ntor-experiment/c

# 指定 liboqs 路径
make clean
make all LIBOQS_DIR=~/oqs
```

### Q4: 脚本中途失败

**解决方案**：
```bash
# 脚本支持重新运行，会跳过已完成的步骤
./setup_phytium.sh

# 或手动从失败步骤继续（见文档）
```

### Q5: ARM 设备编译太慢

**解决方案**：
```bash
# 减少并行编译数
cd ~/pq-tor-deps/liboqs/build
make -j2  # 只用 2 个核心

# 或者关闭优化（编译快但运行慢）
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

---

## 🔍 检查清单

部署完成后确认：

- [ ] liboqs 库文件存在：`~/oqs/lib/liboqs.so`
- [ ] Kyber 测试通过：运行 `~/pq-tor-deps/kyber-test/test_kyber_simple`
- [ ] PQ-Tor 可执行文件存在：`~/pq-ntor-experiment/c/client`
- [ ] 所有单元测试通过：6/6
- [ ] 环境变量已设置：`echo $LD_LIBRARY_PATH` 包含 `~/oqs/lib`
- [ ] 网络测试通过：`./test_network.sh` 成功

---

## 📝 脚本特性

### 智能检测
- ✅ 自动检测已安装的依赖，避免重复安装
- ✅ 检测到已编译的 liboqs，询问是否重新编译
- ✅ 支持 x86_64 和 ARM64 架构

### 彩色输出
- 🟦 蓝色：步骤标题和信息
- 🟩 绿色：成功消息
- 🟨 黄色：警告和提示
- 🟥 红色：错误消息

### 错误处理
- ✅ 遇到错误立即停止（`set -e`）
- ✅ 每个步骤都有验证
- ✅ 失败时给出明确提示

### 幂等性
- ✅ 可以多次运行
- ✅ 已完成的步骤会被跳过
- ✅ 不会破坏现有安装

---

## 🎓 学术使用

此部署脚本适用于：

- **实验环境搭建** - 快速在多个设备上部署
- **可重复性研究** - 确保环境一致性
- **教学演示** - 一键部署用于课堂演示
- **论文验证** - 审稿人可轻松复现实验

---

## 📞 获取帮助

### 查看详细日志

```bash
# 运行并保存日志
./setup_phytium.sh 2>&1 | tee setup.log

# 查看日志
cat setup.log
```

### 手动步骤（调试用）

如果自动脚本失败，可参考：

- `readme/飞腾派部署指南.md` - 完整手动步骤
- `readme/环境检测使用指南.md` - 环境检查方法
- `deployment/install_deps.sh` - liboqs 安装脚本

---

## 🆚 与其他脚本对比

| 脚本 | 位置 | 功能 | 适用场景 |
|------|------|------|---------|
| `setup_phytium.sh` | 项目根目录 | **完整自动化部署** | ✅ 推荐使用 |
| `check_full_environment.sh` | 项目根目录 | 环境检测（20项） | 部署前/后检查 |
| `deployment/install_deps.sh` | deployment/ | 仅安装 liboqs | 单独安装 liboqs |
| `deployment/check_env.sh` | deployment/ | 基础检查（8项） | 飞腾派初检 |

---

## ✅ 成功标志

当你看到以下输出时，说明部署完全成功：

```
╔════════════════════════════════════════════════════════════╗
║                 🎉 部署完成！                              ║
╚════════════════════════════════════════════════════════════╝

📦 安装位置：
   liboqs:        /home/user/oqs
   PQ-Tor:        /home/user/pq-ntor-experiment/c

🧪 验证测试：
   Kyber KEM:     ✅ 通过
   PQ-Tor 编译:   ✅ 完成

🚀 下一步操作：
   ...
```

---

**创建时间**: 2025-11-27
**版本**: 1.0
**状态**: ✅ 生产就绪
**支持平台**: ARM64 (飞腾派、树莓派、ARM 服务器)

祝部署顺利！🚀
