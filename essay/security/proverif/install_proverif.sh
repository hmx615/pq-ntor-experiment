#!/bin/bash
set -e

echo "==================================================================="
echo "ProVerif 自动安装脚本"
echo "==================================================================="
echo ""

# 1. 安装依赖
echo "[1/5] 安装依赖 (OCaml, ocamlfind, make, wget)..."
sudo apt-get update
sudo apt-get install -y ocaml ocaml-native-compilers ocaml-findlib make wget

# 2. 下载源码
echo ""
echo "[2/5] 下载 ProVerif 2.04..."
cd ~
if [ ! -f proverif2.04.tar.gz ]; then
    echo "下载中..."
    wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.04.tar.gz
else
    echo "✅ 源码包已存在，跳过下载"
fi

# 3. 解压
echo ""
echo "[3/5] 解压源码..."
if [ -d proverif2.04 ]; then
    echo "⚠️  目录已存在，删除旧版本..."
    rm -rf proverif2.04
fi
tar -xzf proverif2.04.tar.gz
cd proverif2.04

# 4. 编译
echo ""
echo "[4/5] 编译 ProVerif (需要几分钟)..."
./build

# 5. 安装
echo ""
echo "[5/5] 安装到用户目录 ~/bin ..."
mkdir -p ~/bin
cp proverif ~/bin/
chmod +x ~/bin/proverif

# 添加到 PATH
if ! grep -q 'export PATH=$HOME/bin:$PATH' ~/.bashrc; then
    echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
    echo "✅ 已添加 ~/bin 到 PATH"
else
    echo "✅ PATH 已配置"
fi

echo ""
echo "==================================================================="
echo "✅ ProVerif 安装完成！"
echo "==================================================================="
echo ""
echo "下一步："
echo ""
echo "1. 使 PATH 生效："
echo "   source ~/.bashrc"
echo ""
echo "2. 验证安装："
echo "   proverif --version"
echo ""
echo "3. 运行 PQ-NTOR 验证："
echo "   cd /home/ccc/pq-ntor-experiment/essay/security/proverif"
echo "   proverif pq_ntor.pv"
echo ""
echo "4. 保存验证结果："
echo "   proverif pq_ntor.pv > verification_results.txt"
echo ""
echo "==================================================================="
