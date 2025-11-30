#!/bin/bash
# 快速兼容性测试脚本 - 验证飞腾派环境
# 使用方法: ./quick_compatibility_test.sh

set -e  # 遇到错误立即退出

echo "======================================================================"
echo "           PQ-NTOR 飞腾派兼容性测试"
echo "======================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function check_pass() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

function check_fail() {
    echo -e "${RED}  ✗ $1${NC}"
}

# ==================== 1. 系统信息 ====================
echo "【1/7】系统信息检测"
echo "----------------------------------------"

log_info "操作系统:"
cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2
check_pass "操作系统检测完成"

log_info "内核版本:"
uname -r
check_pass "内核版本检测完成"

log_info "架构:"
ARCH=$(uname -m)
echo "  $ARCH"
if [[ "$ARCH" == "aarch64" ]]; then
    check_pass "ARM64架构 (飞腾派)"
elif [[ "$ARCH" == "x86_64" ]]; then
    check_warn "x86_64架构 (WSL/PC)"
else
    check_warn "其他架构: $ARCH"
fi

echo ""

# ==================== 2. Python环境 ====================
echo "【2/7】Python环境检测"
echo "----------------------------------------"

if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version | awk '{print $2}')
    log_info "Python版本: $PYTHON_VER"
    check_pass "Python3已安装"
else
    log_error "Python3未安装"
    check_fail "Python3未安装"
    echo "  安装方法: sudo apt-get install python3"
    exit 1
fi

echo ""

# ==================== 3. 依赖库检测 ====================
echo "【3/7】依赖库检测"
echo "----------------------------------------"

# 检查OpenSSL
if command -v openssl &> /dev/null; then
    OPENSSL_VER=$(openssl version | awk '{print $2}')
    log_info "OpenSSL版本: $OPENSSL_VER"
    check_pass "OpenSSL已安装"
else
    log_error "OpenSSL未安装"
    check_fail "OpenSSL未安装"
fi

# 检查liboqs（可选）
if ldconfig -p | grep -q liboqs; then
    log_info "liboqs: 已安装"
    check_pass "liboqs已安装"
else
    log_warn "liboqs未安装（可选依赖）"
fi

echo ""

# ==================== 4. 编译工具链 ====================
echo "【4/7】编译工具链检测"
echo "----------------------------------------"

if command -v gcc &> /dev/null; then
    GCC_VER=$(gcc --version | head -n1 | awk '{print $NF}')
    log_info "GCC版本: $GCC_VER"
    check_pass "GCC已安装"
else
    log_error "GCC未安装"
    check_fail "GCC未安装"
    echo "  安装方法: sudo apt-get install build-essential"
fi

if command -v make &> /dev/null; then
    MAKE_VER=$(make --version | head -n1 | awk '{print $NF}')
    log_info "Make版本: $MAKE_VER"
    check_pass "Make已安装"
else
    log_error "Make未安装"
    check_fail "Make未安装"
fi

echo ""

# ==================== 5. PQ-NTOR程序检测 ====================
echo "【5/7】PQ-NTOR程序检测"
echo "----------------------------------------"

PQ_NTOR_DIR="../c"
BENCHMARK_EXEC="$PQ_NTOR_DIR/benchmark_pq_ntor"

if [ -f "$BENCHMARK_EXEC" ]; then
    log_info "PQ-NTOR程序: 已编译"
    check_pass "找到 benchmark_pq_ntor"

    # 测试执行
    log_info "测试执行..."
    if timeout 5 "$BENCHMARK_EXEC" 10 &> /dev/null; then
        check_pass "程序可正常执行"
    else
        log_warn "程序执行失败或超时"
        check_warn "可能需要重新编译"
    fi
else
    log_warn "PQ-NTOR程序未编译"
    check_warn "benchmark_pq_ntor 未找到"
    echo "  编译方法:"
    echo "    cd $PQ_NTOR_DIR"
    echo "    make benchmark_pq_ntor"
fi

echo ""

# ==================== 6. 拓扑参数文件 ====================
echo "【6/7】拓扑参数文件检测"
echo "----------------------------------------"

PARAMS_FILE="topology_tc_params.json"

if [ -f "$PARAMS_FILE" ]; then
    log_info "拓扑参数文件: 已存在"
    check_pass "找到 $PARAMS_FILE"

    # 验证JSON格式
    if python3 -c "import json; json.load(open('$PARAMS_FILE'))" 2> /dev/null; then
        check_pass "JSON格式正确"

        # 统计拓扑数量
        TOPO_COUNT=$(python3 -c "import json; print(len(json.load(open('$PARAMS_FILE'))))")
        log_info "拓扑数量: $TOPO_COUNT"
    else
        log_error "JSON格式错误"
        check_fail "JSON解析失败"
    fi
else
    log_error "拓扑参数文件不存在"
    check_fail "$PARAMS_FILE 未找到"
    echo "  生成方法: python3 calculate_topology_params.py"
fi

echo ""

# ==================== 7. 网络工具检测（可选）====================
echo "【7/7】网络工具检测（可选）"
echo "----------------------------------------"

# 检查tc工具
if command -v tc &> /dev/null; then
    log_info "tc (traffic control): 已安装"
    check_pass "tc已安装（用于真实网络模拟）"
else
    log_warn "tc未安装（单机测试不需要）"
    echo "  安装方法: sudo apt-get install iproute2"
fi

# 检查iperf3（性能测试工具）
if command -v iperf3 &> /dev/null; then
    log_info "iperf3: 已安装"
    check_pass "iperf3已安装（用于网络带宽测试）"
else
    log_warn "iperf3未安装（可选）"
fi

echo ""

# ==================== 总结 ====================
echo "======================================================================"
echo "                         兼容性测试总结"
echo "======================================================================"
echo ""

ERRORS=0
WARNINGS=0

# 必需项检查
if ! command -v python3 &> /dev/null; then
    ((ERRORS++))
fi
if ! command -v gcc &> /dev/null; then
    ((ERRORS++))
fi
if ! command -v make &> /dev/null; then
    ((ERRORS++))
fi
if [ ! -f "$PARAMS_FILE" ]; then
    ((ERRORS++))
fi

# 警告项检查
if [ ! -f "$BENCHMARK_EXEC" ]; then
    ((WARNINGS++))
fi
if ! command -v tc &> /dev/null; then
    ((WARNINGS++))
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ 兼容性测试通过！${NC}"
    echo ""
    echo "系统已就绪，可以运行PQ-NTOR测试。"
    echo ""

    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}注意: 有 $WARNINGS 个警告项${NC}"
        echo "这些不影响单机测试，但可能影响真实网络实验。"
        echo ""
    fi

    echo "下一步:"
    if [ ! -f "$BENCHMARK_EXEC" ]; then
        echo "  1. 编译PQ-NTOR程序:"
        echo "       cd $PQ_NTOR_DIR"
        echo "       make benchmark_pq_ntor"
        echo ""
    fi
    echo "  2. 运行单机测试:"
    echo "       python3 test_pq_ntor_single_machine.py"
    echo ""

    exit 0
else
    echo -e "${RED}✗ 兼容性测试失败！${NC}"
    echo ""
    echo -e "${RED}有 $ERRORS 个必需项缺失${NC}"
    echo "请根据上述提示安装缺失的依赖。"
    echo ""
    exit 1
fi
