#!/bin/bash
# PQ-Tor完整环境检查脚本
# 包含：基础环境 + PQ-Tor核心 + SAGIN实验 + Web前端

# 不要在出错时立即退出，完成所有检查
# set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# 检查结果函数
check_pass() {
    echo -e "      ${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
}

check_fail() {
    echo -e "      ${RED}❌ $1${NC}"
    if [ -n "$2" ]; then
        echo -e "      ${YELLOW}   → 安装方法: $2${NC}"
    fi
    ((FAILED_CHECKS++))
}

check_warning() {
    echo -e "      ${YELLOW}⚠️  $1${NC}"
    if [ -n "$2" ]; then
        echo -e "      ${YELLOW}   → 建议: $2${NC}"
    fi
    ((WARNING_CHECKS++))
}

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     PQ-Tor 完整环境检查                                    ║"
echo "║     Complete Environment Check                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# ==================== 第一部分：基础系统环境 ====================
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}第一部分：基础系统环境 (Basic System)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 1. CPU架构
((TOTAL_CHECKS++))
echo "[1/20] 检查CPU架构..."
ARCH=$(uname -m)
echo "      架构: $ARCH"
if [[ "$ARCH" == "x86_64" || "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    check_pass "支持的架构"
else
    check_warning "架构 $ARCH 可能不受支持" "建议使用 x86_64 或 ARM64"
fi
echo ""

# 2. 操作系统
((TOTAL_CHECKS++))
echo "[2/20] 检查操作系统..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "      OS: $NAME $VERSION"
    if [[ "$NAME" == *"Ubuntu"* ]] || [[ "$NAME" == *"Debian"* ]]; then
        check_pass "Linux系统 (Ubuntu/Debian)"
    else
        check_warning "非Ubuntu/Debian系统" "某些命令可能需要调整"
    fi
else
    check_fail "无法识别操作系统"
fi
echo ""

# 3. GCC编译器
((TOTAL_CHECKS++))
echo "[3/20] 检查GCC编译器..."
if command -v gcc &> /dev/null; then
    GCC_VERSION=$(gcc --version | head -n1)
    echo "      $GCC_VERSION"
    GCC_MAJOR=$(gcc -dumpversion | cut -d. -f1)
    if [ "$GCC_MAJOR" -ge 7 ]; then
        check_pass "GCC版本足够 (>= 7.x)"
    else
        check_warning "GCC版本较老" "建议升级到GCC 9+"
    fi
else
    check_fail "GCC未安装" "sudo apt-get install build-essential"
fi
echo ""

# 4. Make工具
((TOTAL_CHECKS++))
echo "[4/20] 检查Make..."
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n1)
    echo "      $MAKE_VERSION"
    check_pass "Make已安装"
else
    check_fail "Make未安装" "sudo apt-get install make"
fi
echo ""

# 5. CMake
((TOTAL_CHECKS++))
echo "[5/20] 检查CMake..."
if command -v cmake &> /dev/null; then
    CMAKE_VERSION=$(cmake --version | head -n1)
    echo "      $CMAKE_VERSION"
    check_pass "CMake已安装"
else
    check_warning "CMake未安装" "编译liboqs需要: sudo apt-get install cmake"
fi
echo ""

# ==================== 第二部分：PQ-Tor核心依赖 ====================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}第二部分：PQ-Tor核心依赖 (PQ-Tor Core)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 6. OpenSSL
((TOTAL_CHECKS++))
echo "[6/20] 检查OpenSSL..."
if command -v openssl &> /dev/null; then
    OPENSSL_VERSION=$(openssl version)
    echo "      $OPENSSL_VERSION"
    if pkg-config --exists openssl 2>/dev/null; then
        check_pass "OpenSSL开发库已安装"
    else
        check_fail "OpenSSL开发库未安装" "sudo apt-get install libssl-dev"
    fi
else
    check_fail "OpenSSL未安装" "sudo apt-get install openssl libssl-dev"
fi
echo ""

# 7. liboqs (Kyber KEM)
((TOTAL_CHECKS++))
echo "[7/20] 检查liboqs..."
LIBOQS_PATH="$HOME/_oqs/lib/liboqs.so"
if [ -f "$LIBOQS_PATH" ]; then
    echo "      路径: $LIBOQS_PATH"
    check_pass "liboqs已安装"
elif [ -f "/usr/local/lib/liboqs.so" ]; then
    echo "      路径: /usr/local/lib/liboqs.so"
    check_pass "liboqs已安装（系统路径）"
else
    check_warning "liboqs未找到" "需要编译安装 (见部署文档)"
fi
echo ""

# 8. pthread库
((TOTAL_CHECKS++))
echo "[8/20] 检查pthread库..."
if gcc -pthread -x c - -o /dev/null <<< "int main(){return 0;}" 2>/dev/null; then
    check_pass "pthread支持正常"
else
    check_fail "pthread不可用"
fi
echo ""

# 9. 编译PQ-Tor
((TOTAL_CHECKS++))
echo "[9/20] 检查PQ-Tor可执行文件..."
C_DIR="/home/ccc/pq-ntor-experiment/c"
if [ -f "$C_DIR/directory" ] && [ -f "$C_DIR/relay" ] && [ -f "$C_DIR/client" ]; then
    echo "      目录: $C_DIR"
    check_pass "PQ-Tor已编译 (directory, relay, client)"
else
    check_warning "PQ-Tor未编译" "运行: cd $C_DIR && make all"
fi
echo ""

# ==================== 第三部分：SAGIN实验环境 ====================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}第三部分：SAGIN实验环境 (SAGIN Experiments)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 10. tc工具 (流量控制)
((TOTAL_CHECKS++))
echo "[10/20] 检查tc工具 (traffic control)..."
if command -v tc &> /dev/null; then
    TC_VERSION=$(tc -Version 2>&1 | head -n1)
    echo "      $TC_VERSION"
    check_pass "tc工具已安装"
else
    check_fail "tc工具未安装" "sudo apt-get install iproute2"
fi
echo ""

# 11. sudo权限
((TOTAL_CHECKS++))
echo "[11/20] 检查sudo权限..."
if sudo -n true 2>/dev/null; then
    check_pass "sudo权限正常（免密码）"
else
    if sudo -v; then
        check_warning "sudo需要密码" "配置免密码: sudo visudo"
    else
        check_fail "sudo权限不可用"
    fi
fi
echo ""

# 12. SAGIN实验脚本
((TOTAL_CHECKS++))
echo "[12/20] 检查SAGIN实验脚本..."
SAGIN_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments"
if [ -f "$SAGIN_DIR/simulate_satellite_link.sh" ] && [ -f "$SAGIN_DIR/run_sagin_experiments.sh" ]; then
    check_pass "SAGIN实验脚本就绪"
else
    check_warning "SAGIN实验脚本缺失" "检查 sagin-experiments 目录"
fi
echo ""

# ==================== 第四部分：Web前端环境 ====================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}第四部分：Web前端环境 (Web Dashboard)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 13. Python3
((TOTAL_CHECKS++))
echo "[13/20] 检查Python3..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "      $PYTHON_VERSION"
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 7 ]; then
        check_pass "Python版本足够 (>= 3.7)"
    else
        check_warning "Python版本较老" "建议Python 3.8+"
    fi
else
    check_fail "Python3未安装" "sudo apt-get install python3"
fi
echo ""

# 14. pip3
((TOTAL_CHECKS++))
echo "[14/20] 检查pip3..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo "      $PIP_VERSION"
    check_pass "pip3已安装"
else
    check_fail "pip3未安装" "sudo apt-get install python3-pip"
fi
echo ""

# 15. Flask
((TOTAL_CHECKS++))
echo "[15/20] 检查Flask..."
if python3 -c "import flask" 2>/dev/null; then
    FLASK_VERSION=$(python3 -c "import flask; print(flask.__version__)")
    echo "      Flask版本: $FLASK_VERSION"
    check_pass "Flask已安装"
else
    check_fail "Flask未安装" "pip3 install flask"
fi
echo ""

# 16. pandas
((TOTAL_CHECKS++))
echo "[16/20] 检查pandas..."
if python3 -c "import pandas" 2>/dev/null; then
    PANDAS_VERSION=$(python3 -c "import pandas; print(pandas.__version__)")
    echo "      pandas版本: $PANDAS_VERSION"
    check_pass "pandas已安装"
else
    check_fail "pandas未安装" "pip3 install pandas"
fi
echo ""

# 17. flask-cors
((TOTAL_CHECKS++))
echo "[17/20] 检查flask-cors..."
if python3 -c "import flask_cors" 2>/dev/null; then
    check_pass "flask-cors已安装"
else
    check_warning "flask-cors未安装" "pip3 install flask-cors"
fi
echo ""

# 18. Web Dashboard文件
((TOTAL_CHECKS++))
echo "[18/20] 检查Web Dashboard文件..."
WEB_DIR="/home/ccc/pq-ntor-experiment/web-dashboard"
if [ -f "$WEB_DIR/index.html" ] && [ -f "$WEB_DIR/api/server.py" ]; then
    echo "      目录: $WEB_DIR"
    check_pass "Web Dashboard文件完整"
else
    check_fail "Web Dashboard文件缺失" "检查 web-dashboard 目录"
fi
echo ""

# 19. 浏览器
((TOTAL_CHECKS++))
echo "[19/20] 检查浏览器..."
if command -v chromium-browser &> /dev/null; then
    BROWSER_VERSION=$(chromium-browser --version 2>/dev/null || echo "Chromium")
    echo "      $BROWSER_VERSION"
    check_pass "Chromium已安装"
elif command -v firefox &> /dev/null; then
    BROWSER_VERSION=$(firefox --version 2>/dev/null || echo "Firefox")
    echo "      $BROWSER_VERSION"
    check_pass "Firefox已安装"
elif command -v google-chrome &> /dev/null; then
    BROWSER_VERSION=$(google-chrome --version 2>/dev/null || echo "Chrome")
    echo "      $BROWSER_VERSION"
    check_pass "Chrome已安装"
else
    check_warning "未找到浏览器" "安装: sudo apt-get install chromium-browser"
fi
echo ""

# 20. 端口可用性
((TOTAL_CHECKS++))
echo "[20/20] 检查端口8080可用性..."
if lsof -i :8080 &> /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    check_warning "端口8080已被占用" "停止占用进程或使用其他端口"
else
    check_pass "端口8080可用"
fi
echo ""

# ==================== 总结报告 ====================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    检查完成！                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}检查统计：${NC}"
echo -e "  总检查项数: ${TOTAL_CHECKS}"
echo -e "  ${GREEN}✅ 通过: ${PASSED_CHECKS}${NC}"
echo -e "  ${RED}❌ 失败: ${FAILED_CHECKS}${NC}"
echo -e "  ${YELLOW}⚠️  警告: ${WARNING_CHECKS}${NC}"
echo ""

# 计算通过率
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)
    echo -e "  通过率: ${PASS_RATE}%"
    echo ""
fi

# 根据结果给出建议
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 恭喜！所有检查项都通过！${NC}"
        echo ""
        echo "✅ PQ-Tor核心系统可用"
        echo "✅ SAGIN实验环境就绪"
        echo "✅ Web前端系统可用"
        echo ""
        echo -e "${BLUE}下一步操作：${NC}"
        echo "  1. 编译PQ-Tor: cd c && make all"
        echo "  2. 运行测试: cd c && ./test_network.sh"
        echo "  3. SAGIN实验: cd sagin-experiments && sudo ./run_sagin_experiments.sh"
        echo "  4. 启动Web界面: cd web-dashboard && ./start.sh"
    else
        echo -e "${YELLOW}⚠️  环境基本可用，但有一些警告项需要注意${NC}"
        echo ""
        echo "建议查看上述警告项并根据提示进行优化"
    fi
else
    echo -e "${RED}❌ 环境检查未完全通过，请先解决失败项${NC}"
    echo ""
    echo "请查看上述失败项的安装方法，完成安装后重新运行此脚本"
    echo ""
    echo -e "${BLUE}快速安装命令（Ubuntu/Debian）：${NC}"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install build-essential cmake libssl-dev git"
    echo "  sudo apt-get install iproute2 python3 python3-pip"
    echo "  sudo apt-get install chromium-browser"
    echo "  pip3 install flask flask-cors pandas"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

exit 0
