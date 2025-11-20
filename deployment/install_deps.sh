#!/bin/bash
# install_deps.sh - 自动安装liboqs到飞腾派
#
# 用途: 自动化安装PQ-Tor所需的liboqs库

set -e  # 遇到错误立即退出

echo "======================================"
echo "  liboqs 自动安装脚本"
echo "  目标平台: ARM64 (飞腾派)"
echo "======================================"
echo ""

# 检查架构
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo "❌ 错误: 此脚本仅适用于ARM64架构，当前架构: $ARCH"
    exit 1
fi

# 创建工作目录
WORK_DIR=~/pq-tor-deps
INSTALL_DIR=~/oqs

echo "[1/6] 创建工作目录..."
mkdir -p $WORK_DIR
cd $WORK_DIR
echo "      工作目录: $WORK_DIR"
echo "      安装目录: $INSTALL_DIR"
echo ""

# 克隆liboqs
echo "[2/6] 克隆liboqs仓库..."
if [ -d "liboqs" ]; then
    echo "      liboqs目录已存在，跳过克隆"
    cd liboqs
    git pull
else
    git clone https://github.com/open-quantum-safe/liboqs.git
    cd liboqs
fi
echo "      ✅ 源码就绪"
echo ""

# 创建构建目录
echo "[3/6] 配置CMake..."
rm -rf build
mkdir build && cd build

cmake -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR \
      -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_SHARED_LIBS=ON \
      -DOQS_USE_OPENSSL=ON \
      ..

echo "      ✅ 配置完成"
echo ""

# 编译
echo "[4/6] 编译liboqs..."
echo "      使用CPU核心数: $(nproc)"
echo "      预计时间: 3-8分钟"
echo ""
make -j$(nproc)
echo ""
echo "      ✅ 编译完成"
echo ""

# 安装
echo "[5/6] 安装到 $INSTALL_DIR ..."
make install
echo "      ✅ 安装完成"
echo ""

# 验证安装
echo "[6/6] 验证安装..."
if [ -f "$INSTALL_DIR/lib/liboqs.so" ]; then
    echo "      ✅ liboqs.so 存在"
    ls -lh $INSTALL_DIR/lib/liboqs.so*
else
    echo "      ❌ liboqs.so 未找到"
    exit 1
fi

if [ -d "$INSTALL_DIR/include/oqs" ]; then
    echo "      ✅ 头文件目录存在"
else
    echo "      ❌ 头文件目录未找到"
    exit 1
fi
echo ""

echo "======================================"
echo "  ✅ liboqs 安装成功！"
echo "======================================"
echo ""
echo "安装位置:"
echo "  库文件: $INSTALL_DIR/lib/liboqs.so"
echo "  头文件: $INSTALL_DIR/include/oqs/"
echo ""
echo "下一步:"
echo "  1. 编译测试程序: make"
echo "  2. 运行验证: ./test_kyber_simple"
echo ""
