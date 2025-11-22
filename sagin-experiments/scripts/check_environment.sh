#!/bin/bash
#########################################################################
# 飞腾派环境检测脚本 - SAGIN 6+1 分布式展示系统
# 用途: 检查系统依赖、网络配置、资源是否满足部署要求
# 平台: 飞腾派 (ARM64)
#########################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查结果统计
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

#########################################################################
# 1. 系统基本信息
#########################################################################
echo "========================================"
echo "飞腾派环境检测 - SAGIN 6+1 系统"
echo "========================================"
echo ""

log_info "检测系统信息..."
echo "  主机名: $(hostname)"
echo "  内核版本: $(uname -r)"
echo "  CPU架构: $(uname -m)"
echo "  操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo ""

#########################################################################
# 2. CPU 架构检查
#########################################################################
log_info "检查 CPU 架构..."
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
    log_success "CPU 架构: $ARCH (ARM64，飞腾派兼容)"
    ((CHECKS_PASSED++))
else
    log_warning "CPU 架构: $ARCH (不是 ARM64，可能不是飞腾派)"
    ((CHECKS_WARNING++))
fi
echo ""

#########################################################################
# 3. Python 环境检查
#########################################################################
log_info "检查 Python 环境..."

# Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [[ $PYTHON_MAJOR -eq 3 ]] && [[ $PYTHON_MINOR -ge 7 ]]; then
        log_success "Python3: $PYTHON_VERSION (>= 3.7)"
        ((CHECKS_PASSED++))
    else
        log_error "Python3: $PYTHON_VERSION (需要 >= 3.7)"
        ((CHECKS_FAILED++))
    fi
else
    log_error "Python3 未安装"
    ((CHECKS_FAILED++))
fi

# pip3
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version | awk '{print $2}')
    log_success "pip3: $PIP_VERSION"
    ((CHECKS_PASSED++))
else
    log_error "pip3 未安装"
    ((CHECKS_FAILED++))
fi
echo ""

#########################################################################
# 4. Python 依赖包检查
#########################################################################
log_info "检查 Python 依赖包..."

check_python_package() {
    PACKAGE=$1
    if python3 -c "import $PACKAGE" 2>/dev/null; then
        VERSION=$(python3 -c "import $PACKAGE; print($PACKAGE.__version__)" 2>/dev/null || echo "未知版本")
        log_success "$PACKAGE: $VERSION"
        ((CHECKS_PASSED++))
        return 0
    else
        log_error "$PACKAGE: 未安装"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_python_package "websockets"
check_python_package "asyncio"
echo ""

#########################################################################
# 5. 网络配置检查
#########################################################################
log_info "检查网络配置..."

# 获取 IP 地址
IP_ADDR=$(hostname -I | awk '{print $1}')
if [[ -n "$IP_ADDR" ]]; then
    log_success "本机 IP: $IP_ADDR"
    ((CHECKS_PASSED++))
else
    log_error "无法获取 IP 地址"
    ((CHECKS_FAILED++))
fi

# 检查是否在 192.168.100.x 网段
if [[ "$IP_ADDR" =~ ^192\.168\.100\. ]]; then
    log_success "IP 网段: 192.168.100.x (符合预期)"
    ((CHECKS_PASSED++))
else
    log_warning "IP 网段: 非 192.168.100.x (请确认网络配置)"
    ((CHECKS_WARNING++))
fi
echo ""

#########################################################################
# 6. 端口占用检查
#########################################################################
log_info "检查端口占用情况..."

check_port() {
    PORT=$1
    DESC=$2
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        log_warning "端口 $PORT ($DESC) 已被占用"
        ((CHECKS_WARNING++))
        return 1
    else
        log_success "端口 $PORT ($DESC) 可用"
        ((CHECKS_PASSED++))
        return 0
    fi
}

check_port 9000 "WebSocket Hub"
check_port 8080 "HTTP 服务器"
echo ""

#########################################################################
# 7. 系统资源检查
#########################################################################
log_info "检查系统资源..."

# 内存
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
if [[ $TOTAL_MEM -ge 2048 ]]; then
    log_success "总内存: ${TOTAL_MEM}MB (>= 2GB)"
    ((CHECKS_PASSED++))
elif [[ $TOTAL_MEM -ge 1024 ]]; then
    log_warning "总内存: ${TOTAL_MEM}MB (建议 >= 2GB)"
    ((CHECKS_WARNING++))
else
    log_error "总内存: ${TOTAL_MEM}MB (不足 1GB)"
    ((CHECKS_FAILED++))
fi

# 磁盘空间
DISK_AVAIL=$(df -BM / | awk 'NR==2 {print $4}' | sed 's/M//')
if [[ $DISK_AVAIL -ge 1024 ]]; then
    log_success "可用磁盘: ${DISK_AVAIL}MB (>= 1GB)"
    ((CHECKS_PASSED++))
else
    log_warning "可用磁盘: ${DISK_AVAIL}MB (建议 >= 1GB)"
    ((CHECKS_WARNING++))
fi

# CPU 核心数
CPU_CORES=$(nproc)
log_success "CPU 核心数: $CPU_CORES"
((CHECKS_PASSED++))
echo ""

#########################################################################
# 8. C 语言程序环境检查
#########################################################################
log_info "检查 C 语言程序环境..."

# GCC
if command -v gcc &> /dev/null; then
    GCC_VERSION=$(gcc --version | head -n1 | awk '{print $NF}')
    log_success "GCC: $GCC_VERSION"
    ((CHECKS_PASSED++))
else
    log_warning "GCC 未安装 (如需编译 C 程序请安装)"
    ((CHECKS_WARNING++))
fi

# Make
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n1 | awk '{print $NF}')
    log_success "Make: $MAKE_VERSION"
    ((CHECKS_PASSED++))
else
    log_warning "Make 未安装"
    ((CHECKS_WARNING++))
fi
echo ""

#########################################################################
# 9. Docker 检查 (可选)
#########################################################################
log_info "检查 Docker 环境 (可选)..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log_success "Docker: $DOCKER_VERSION"
    ((CHECKS_PASSED++))

    # Docker 服务状态
    if systemctl is-active --quiet docker; then
        log_success "Docker 服务: 运行中"
        ((CHECKS_PASSED++))
    else
        log_warning "Docker 服务: 未运行"
        ((CHECKS_WARNING++))
    fi
else
    log_warning "Docker 未安装 (当前使用模拟 Agent，暂不需要)"
    ((CHECKS_WARNING++))
fi
echo ""

#########################################################################
# 10. 项目文件检查
#########################################################################
log_info "检查项目文件..."

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

check_file() {
    FILE=$1
    DESC=$2
    if [[ -f "$PROJECT_ROOT/$FILE" ]]; then
        log_success "$DESC: 存在"
        ((CHECKS_PASSED++))
        return 0
    else
        log_error "$DESC: 缺失 ($FILE)"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_file "backend/websocket_hub.py" "WebSocket Hub"
check_file "backend/node_agent.py" "Node Agent"
check_file "frontend/control-panel/index.html" "控制面板"
check_file "frontend/node-view/index.html" "节点视图"
check_file "scripts/test_local.sh" "本地测试脚本"
echo ""

#########################################################################
# 11. 总结
#########################################################################
echo "========================================"
echo "检测结果汇总"
echo "========================================"
log_success "通过: $CHECKS_PASSED 项"
if [[ $CHECKS_WARNING -gt 0 ]]; then
    log_warning "警告: $CHECKS_WARNING 项"
fi
if [[ $CHECKS_FAILED -gt 0 ]]; then
    log_error "失败: $CHECKS_FAILED 项"
fi
echo ""

#########################################################################
# 12. 建议
#########################################################################
if [[ $CHECKS_FAILED -gt 0 ]]; then
    echo "========================================"
    echo "修复建议"
    echo "========================================"
    echo "请安装缺失的依赖:"
    echo ""
    echo "  # 更新软件包列表"
    echo "  sudo apt update"
    echo ""
    echo "  # 安装 Python 和依赖"
    echo "  sudo apt install -y python3 python3-pip"
    echo ""
    echo "  # 安装 Python 包"
    echo "  pip3 install websockets asyncio"
    echo ""
    echo "  # 安装 C 编译环境 (可选)"
    echo "  sudo apt install -y gcc make"
    echo ""
    exit 1
elif [[ $CHECKS_WARNING -gt 0 ]]; then
    log_warning "存在警告项，建议检查后再部署"
    exit 0
else
    log_success "所有检查通过！环境满足部署要求"
    echo ""
    echo "下一步:"
    echo "  1. 配置节点 ID: 编辑 scripts/run_node.sh"
    echo "  2. 启动服务: ./scripts/test_local.sh start"
    echo ""
    exit 0
fi
