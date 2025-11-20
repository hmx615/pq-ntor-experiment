#!/bin/bash
# check_env.sh - 飞腾派环境检查脚本

echo "======================================"
echo "  飞腾派环境检查"
echo "======================================"
echo ""

# 检查架构
ARCH=$(uname -m)
echo "[1/8] 检查CPU架构..."
echo "      架构: $ARCH"
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    echo "      ✅ ARM64架构正确"
else
    echo "      ❌ 错误: 需要ARM64架构，当前是 $ARCH"
    exit 1
fi
echo ""

# 检查操作系统
echo "[2/8] 检查操作系统..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "      OS: $NAME $VERSION"
    echo "      ✅ Linux系统"
else
    echo "      ❌ 无法识别操作系统"
    exit 1
fi
echo ""

# 检查GCC
echo "[3/8] 检查GCC编译器..."
if command -v gcc &> /dev/null; then
    GCC_VERSION=$(gcc --version | head -n1)
    echo "      $GCC_VERSION"
    echo "      ✅ GCC已安装"
else
    echo "      ❌ GCC未安装"
    echo "      安装: sudo apt-get install build-essential"
    exit 1
fi
echo ""

# 检查Make
echo "[4/8] 检查Make..."
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n1)
    echo "      $MAKE_VERSION"
    echo "      ✅ Make已安装"
else
    echo "      ❌ Make未安装"
    exit 1
fi
echo ""

# 检查CMake
echo "[5/8] 检查CMake..."
if command -v cmake &> /dev/null; then
    CMAKE_VERSION=$(cmake --version | head -n1)
    echo "      $CMAKE_VERSION"
    echo "      ✅ CMake已安装"
else
    echo "      ❌ CMake未安装"
    echo "      安装: sudo apt-get install cmake"
    exit 1
fi
echo ""

# 检查OpenSSL
echo "[6/8] 检查OpenSSL..."
if command -v openssl &> /dev/null; then
    OPENSSL_VERSION=$(openssl version)
    echo "      $OPENSSL_VERSION"
    if pkg-config --exists openssl; then
        echo "      ✅ OpenSSL开发库已安装"
    else
        echo "      ❌ OpenSSL开发库未安装"
        echo "      安装: sudo apt-get install libssl-dev"
        exit 1
    fi
else
    echo "      ❌ OpenSSL未安装"
    exit 1
fi
echo ""

# 检查Git
echo "[7/8] 检查Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "      $GIT_VERSION"
    echo "      ✅ Git已安装"
else
    echo "      ❌ Git未安装"
    echo "      安装: sudo apt-get install git"
    exit 1
fi
echo ""

# 检查磁盘空间
echo "[8/8] 检查磁盘空间..."
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
echo "      可用空间: $AVAILABLE"
echo "      需要空间: ~500MB"
echo "      ✅ 磁盘空间检查完成"
echo ""

echo "======================================"
echo "  ✅ 环境检查通过！"
echo "======================================"
echo ""
echo "下一步: 安装依赖项"
echo "运行: sudo apt-get install build-essential cmake libssl-dev git"
