# ProVerif 手动安装教程

本文档提供在 WSL2/Ubuntu 环境下手动安装 ProVerif 的详细步骤。

## 方法1：从源码编译安装（推荐）

### 步骤1：安装依赖

ProVerif 是用 OCaml 编写的，需要先安装 OCaml 编译器：

```bash
sudo apt-get update
sudo apt-get install -y ocaml ocaml-native-compilers make wget
```

### 步骤2：下载 ProVerif 源码

访问官网获取最新版本：https://bblanche.gitlabpages.inria.fr/proverif/

或直接下载 2.04 版本（当前最新稳定版）：

```bash
cd ~
wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.04.tar.gz
```

如果下载速度慢，可以使用代理：

```bash
export http_proxy=http://192.168.64.1:7890
export https_proxy=http://192.168.64.1:7890
wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.04.tar.gz
```

### 步骤3：解压源码

```bash
tar -xzf proverif2.04.tar.gz
cd proverif2.04
```

### 步骤4：编译

```bash
./build
```

编译过程需要几分钟，成功后会在当前目录生成 `proverif` 可执行文件。

### 步骤5：安装到系统路径（可选）

#### 方式A：安装到 /usr/local/bin（需要 sudo）

```bash
sudo cp proverif /usr/local/bin/
sudo chmod +x /usr/local/bin/proverif
```

#### 方式B：安装到用户目录（不需要 sudo）

```bash
mkdir -p ~/bin
cp proverif ~/bin/
chmod +x ~/bin/proverif
```

然后将 `~/bin` 添加到 PATH（如果还没有的话）：

```bash
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 步骤6：验证安装

```bash
proverif --version
```

应该输出：
```
ProVerif 2.04
```

## 方法2：使用预编译二进制文件

如果编译遇到问题，可以尝试使用预编译版本：

### Ubuntu/Debian 软件源安装

```bash
sudo apt-get update
sudo apt-get install proverif
```

注意：软件源中的版本可能较老。

## 验证 ProVerif 模型

安装完成后，进入 proverif 目录运行验证：

```bash
cd /home/ccc/pq-ntor-experiment/essay/security/proverif
proverif pq_ntor.pv
```

### 保存验证结果

```bash
proverif pq_ntor.pv > verification_results.txt
```

### 查看结果

```bash
cat verification_results.txt
```

## 常见问题解决

### 问题1：OCaml 版本过低

**错误提示**：
```
Error: This version of OCaml is too old
```

**解决方案**：安装更新版本的 OCaml

```bash
# 添加 OPAM（OCaml 包管理器）
sudo apt-get install opam
opam init
eval $(opam env)

# 安装最新 OCaml
opam switch create 4.14.0
eval $(opam env)

# 重新编译 ProVerif
cd ~/proverif2.04
./build
```

### 问题2：网络下载失败

**解决方案**：使用代理或手动下载

```bash
# 使用代理
export http_proxy=http://192.168.64.1:7890
export https_proxy=http://192.168.64.1:7890

# 或者从备用源下载
wget https://github.com/ProVerif/ProVerif/archive/refs/tags/2.04.tar.gz
```

### 问题3：编译失败

**解决方案**：检查依赖并清理重新编译

```bash
# 确保所有依赖已安装
sudo apt-get install -y ocaml ocaml-native-compilers make

# 清理并重新编译
cd ~/proverif2.04
make clean
./build
```

### 问题4：权限问题

**错误提示**：
```
Permission denied
```

**解决方案**：

```bash
# 给予执行权限
chmod +x proverif

# 或使用用户目录安装（不需要 sudo）
cp proverif ~/bin/
```

## 快速验证脚本

创建一个快速验证脚本：

```bash
cat > ~/verify_pq_ntor.sh << 'EOF'
#!/bin/bash
cd /home/ccc/pq-ntor-experiment/essay/security/proverif

echo "=========================================="
echo "PQ-NTOR ProVerif 验证"
echo "=========================================="
echo ""

if ! command -v proverif &> /dev/null; then
    echo "❌ ProVerif 未安装"
    echo "请先运行安装命令"
    exit 1
fi

echo "✅ ProVerif 已安装: $(proverif --version)"
echo ""
echo "开始验证 pq_ntor.pv ..."
echo ""

proverif pq_ntor.pv | tee verification_results.txt

echo ""
echo "=========================================="
echo "验证完成！结果已保存到："
echo "verification_results.txt"
echo "=========================================="
EOF

chmod +x ~/verify_pq_ntor.sh
```

运行验证：

```bash
~/verify_pq_ntor.sh
```

## 在线验证（备选方案）

如果本地安装困难，可以使用在线编译器：

1. 访问 https://try.ocamlpro.com/ （OCaml 在线环境）
2. 或在有 ProVerif 的机器上运行

## 验证结果解读

成功运行后，您应该看到类似输出：

```
--------------------------------------------------------------
Verification summary:

Query not attacker(session_key_secret[]) is true.

Query inj-event(RelayReceivesHandshake(...)) ==>
      inj-event(ClientSendsHandshake(...)) is true.

Query event(ClientAccepts(...)) ==> event(RelayResponds(...)) is true.

Query event(RelayAccepts(...)) ==> event(ClientSendsHandshake(...)) is true.

--------------------------------------------------------------

RESULT: All queries have been proved.
```

**结果说明**：
- `is true` = 安全属性得到验证 ✅
- `is false` = 安全属性被违反 ❌
- `cannot be proved` = 无法证明（可能需要调整模型）

## 完整安装命令（一键脚本）

将以下内容保存为 `install_proverif.sh`：

```bash
#!/bin/bash
set -e

echo "=== ProVerif 自动安装脚本 ==="

# 1. 安装依赖
echo "[1/5] 安装依赖..."
sudo apt-get update
sudo apt-get install -y ocaml ocaml-native-compilers make wget

# 2. 下载源码
echo "[2/5] 下载 ProVerif 2.04..."
cd ~
if [ ! -f proverif2.04.tar.gz ]; then
    wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.04.tar.gz
fi

# 3. 解压
echo "[3/5] 解压源码..."
tar -xzf proverif2.04.tar.gz
cd proverif2.04

# 4. 编译
echo "[4/5] 编译 ProVerif..."
./build

# 5. 安装
echo "[5/5] 安装到用户目录..."
mkdir -p ~/bin
cp proverif ~/bin/
chmod +x ~/bin/proverif

# 添加到 PATH
if ! grep -q 'export PATH=$HOME/bin:$PATH' ~/.bashrc; then
    echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
fi

echo ""
echo "✅ ProVerif 安装完成！"
echo ""
echo "请运行以下命令使 PATH 生效："
echo "  source ~/.bashrc"
echo ""
echo "然后验证安装："
echo "  proverif --version"
echo ""
echo "运行验证："
echo "  cd /home/ccc/pq-ntor-experiment/essay/security/proverif"
echo "  proverif pq_ntor.pv"
```

使用方法：

```bash
chmod +x install_proverif.sh
./install_proverif.sh
source ~/.bashrc
proverif --version
```

## 参考资源

- ProVerif 官网: https://bblanche.gitlabpages.inria.fr/proverif/
- ProVerif 手册: https://bblanche.gitlabpages.inria.fr/proverif/manual.pdf
- ProVerif 教程: https://prosecco.gforge.inria.fr/personal/bblanche/proverif/tutorial.pdf
- OCaml 官网: https://ocaml.org/

## 联系支持

如果遇到安装问题：
1. 检查 OCaml 版本：`ocaml --version`（需要 >= 4.08）
2. 查看编译日志：`./build 2>&1 | tee build.log`
3. 参考官方文档：https://bblanche.gitlabpages.inria.fr/proverif/
