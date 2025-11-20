#!/bin/bash
################################################################################
# 飞腾派SAGIN环境检测脚本
# Phytium Pi Environment Check for SAGIN Deployment
#
# 用途: 检测飞腾派上的Docker和Python环境，确保可以运行SAGIN实验
# 版本: v1.0
# 日期: 2025-11-13
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查结果计数
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

################################################################################
# 辅助函数
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
}

check_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASS_COUNT++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
    ((WARN_COUNT++))
}

check_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAIL_COUNT++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

################################################################################
# 检查项
################################################################################

check_system_info() {
    print_section "系统信息检查"

    # 操作系统
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        print_info "操作系统: $PRETTY_NAME"
        check_pass "操作系统信息: $ID $VERSION_ID"
    else
        check_fail "无法读取 /etc/os-release"
    fi

    # 内核版本
    KERNEL=$(uname -r)
    print_info "内核版本: $KERNEL"
    check_pass "内核: $KERNEL"

    # 架构
    ARCH=$(uname -m)
    print_info "系统架构: $ARCH"

    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        check_pass "ARM64架构: $ARCH（飞腾派兼容）"
    else
        check_warn "架构不是ARM64: $ARCH（飞腾派通常是aarch64）"
    fi

    # CPU信息
    if [ -f /proc/cpuinfo ]; then
        CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
        if [ -z "$CPU_MODEL" ]; then
            CPU_MODEL=$(grep "Hardware" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
        fi
        print_info "CPU: $CPU_MODEL"

        CPU_CORES=$(nproc)
        print_info "CPU核心数: $CPU_CORES"

        if [ "$CPU_CORES" -ge 4 ]; then
            check_pass "CPU核心数充足: $CPU_CORES 核"
        else
            check_warn "CPU核心数较少: $CPU_CORES 核（建议至少4核）"
        fi
    fi

    # 内存
    TOTAL_MEM=$(free -h | grep "Mem:" | awk '{print $2}')
    AVAIL_MEM=$(free -h | grep "Mem:" | awk '{print $7}')
    print_info "总内存: $TOTAL_MEM, 可用内存: $AVAIL_MEM"

    TOTAL_MEM_MB=$(free -m | grep "Mem:" | awk '{print $2}')
    if [ "$TOTAL_MEM_MB" -ge 4096 ]; then
        check_pass "内存充足: $TOTAL_MEM (≥4GB)"
    elif [ "$TOTAL_MEM_MB" -ge 2048 ]; then
        check_warn "内存偏少: $TOTAL_MEM (建议≥4GB，当前≥2GB)"
    else
        check_fail "内存不足: $TOTAL_MEM (<2GB，无法运行SAGIN)"
    fi

    # 磁盘空间
    DISK_AVAIL=$(df -h . | tail -1 | awk '{print $4}')
    DISK_AVAIL_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    print_info "可用磁盘空间: $DISK_AVAIL"

    if [ "$DISK_AVAIL_GB" -ge 10 ]; then
        check_pass "磁盘空间充足: $DISK_AVAIL (≥10GB)"
    elif [ "$DISK_AVAIL_GB" -ge 5 ]; then
        check_warn "磁盘空间偏少: $DISK_AVAIL (建议≥10GB)"
    else
        check_fail "磁盘空间不足: $DISK_AVAIL (<5GB，无法构建镜像)"
    fi
}

check_docker() {
    print_section "Docker环境检查"

    # Docker命令存在性
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_info "$DOCKER_VERSION"
        check_pass "Docker已安装"

        # Docker服务状态
        if systemctl is-active --quiet docker 2>/dev/null; then
            check_pass "Docker服务正在运行"
        elif service docker status &> /dev/null; then
            check_pass "Docker服务正在运行（通过service检测）"
        else
            check_fail "Docker服务未运行，请启动: sudo systemctl start docker"
        fi

        # Docker权限
        if docker ps &> /dev/null; then
            check_pass "Docker权限正常（无需sudo）"
        else
            check_warn "Docker需要sudo权限，建议将用户加入docker组: sudo usermod -aG docker \$USER"
        fi

        # Docker架构支持
        DOCKER_ARCH=$(docker version --format '{{.Server.Arch}}' 2>/dev/null || echo "unknown")
        print_info "Docker架构: $DOCKER_ARCH"

        if [[ "$DOCKER_ARCH" == "arm64" || "$DOCKER_ARCH" == "aarch64" ]]; then
            check_pass "Docker架构正确: $DOCKER_ARCH"
        else
            check_warn "Docker架构可能不匹配: $DOCKER_ARCH（期望arm64/aarch64）"
        fi

        # 检查buildx（多架构支持）
        if docker buildx version &> /dev/null; then
            check_pass "Docker Buildx已安装（支持多架构构建）"
        else
            check_warn "Docker Buildx未安装（可选，但推荐安装）"
        fi

    else
        check_fail "Docker未安装"
        print_info "安装命令:"
        print_info "  curl -fsSL https://get.docker.com -o get-docker.sh"
        print_info "  sudo sh get-docker.sh"
    fi

    # Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_info "$COMPOSE_VERSION"
        check_pass "Docker Compose已安装"
    else
        check_warn "Docker Compose未安装（可选，但推荐安装）"
        print_info "安装命令:"
        print_info "  sudo apt-get install docker-compose"
    fi
}

check_python() {
    print_section "Python环境检查"

    # Python 3
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_info "$PYTHON_VERSION"

        PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
        PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            check_pass "Python版本符合要求: $PYTHON_VERSION (≥3.8)"
        else
            check_fail "Python版本过低: $PYTHON_VERSION (<3.8)"
        fi
    else
        check_fail "Python 3未安装"
        print_info "安装命令: sudo apt-get install python3 python3-pip"
    fi

    # pip
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
        print_info "pip: $PIP_VERSION"
        check_pass "pip3已安装"
    else
        check_fail "pip3未安装"
        print_info "安装命令: sudo apt-get install python3-pip"
    fi

    # 必要的Python库
    print_info "检查Python依赖库..."

    REQUIRED_PACKAGES=("numpy" "requests" "skyfield")
    MISSING_PACKAGES=()

    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $pkg" &> /dev/null; then
            check_pass "Python库已安装: $pkg"
        else
            check_warn "Python库未安装: $pkg"
            MISSING_PACKAGES+=("$pkg")
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        print_info "安装缺失的库:"
        print_info "  pip3 install ${MISSING_PACKAGES[*]}"
    fi
}

check_network_tools() {
    print_section "网络工具检查"

    # 必要的网络工具
    REQUIRED_TOOLS=("tc" "iptables" "ip" "ping" "netstat" "curl")

    for tool in "${REQUIRED_TOOLS[@]}"; do
        if command -v $tool &> /dev/null; then
            check_pass "网络工具已安装: $tool"
        else
            check_fail "网络工具未安装: $tool"

            case $tool in
                tc)
                    print_info "安装命令: sudo apt-get install iproute2"
                    ;;
                iptables)
                    print_info "安装命令: sudo apt-get install iptables"
                    ;;
                ip)
                    print_info "安装命令: sudo apt-get install iproute2"
                    ;;
                ping)
                    print_info "安装命令: sudo apt-get install iputils-ping"
                    ;;
                netstat)
                    print_info "安装命令: sudo apt-get install net-tools"
                    ;;
                curl)
                    print_info "安装命令: sudo apt-get install curl"
                    ;;
            esac
        fi
    done
}

check_system_permissions() {
    print_section "系统权限检查"

    # 检查是否有sudo权限
    if sudo -n true 2>/dev/null; then
        check_pass "有sudo权限（无需密码）"
    else
        if sudo -v 2>/dev/null; then
            check_pass "有sudo权限（需要密码）"
        else
            check_warn "无sudo权限，某些功能可能受限"
        fi
    fi

    # 检查NET_ADMIN权限（运行tc和iptables需要）
    if [ -x /sbin/tc ] || [ -x /usr/sbin/tc ]; then
        check_pass "tc命令可访问"
    else
        check_warn "tc命令不可访问（可能需要sudo）"
    fi

    if [ -x /sbin/iptables ] || [ -x /usr/sbin/iptables ]; then
        check_pass "iptables命令可访问"
    else
        check_warn "iptables命令不可访问（可能需要sudo）"
    fi
}

check_sagin_files() {
    print_section "SAGIN文件检查"

    SAGIN_ROOT="/home/ccc/pq-ntor-experiment/sagin-experiments"

    # 检查目录是否存在
    if [ -d "$SAGIN_ROOT" ]; then
        check_pass "SAGIN目录存在: $SAGIN_ROOT"

        # 检查关键文件
        KEY_FILES=(
            "configs/sagin_topology_config.json"
            "docker/Dockerfile.pq-ntor"
            "scripts/simulate_pq_ntor_test.py"
            "scripts/network_topology_manager.py"
            "scripts/orbit_simulator.py"
        )

        for file in "${KEY_FILES[@]}"; do
            if [ -f "$SAGIN_ROOT/$file" ]; then
                check_pass "关键文件存在: $file"
            else
                check_warn "关键文件缺失: $file"
            fi
        done
    else
        check_fail "SAGIN目录不存在: $SAGIN_ROOT"
        print_info "请先克隆代码仓库或调整路径"
    fi
}

check_arm_specific() {
    print_section "飞腾派特定检查"

    # 检查是否真的是飞腾派
    if grep -q "Phytium" /proc/cpuinfo 2>/dev/null; then
        check_pass "检测到飞腾CPU"
    else
        check_warn "未检测到飞腾CPU（可能是其他ARM设备）"
    fi

    # 检查设备树（ARM特有）
    if [ -d /proc/device-tree ]; then
        check_pass "设备树存在（ARM设备）"

        if [ -f /proc/device-tree/model ]; then
            MODEL=$(cat /proc/device-tree/model | tr -d '\0')
            print_info "设备型号: $MODEL"
        fi
    else
        check_warn "未找到设备树（可能不是ARM设备）"
    fi

    # 检查散热情况（飞腾派重要）
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
        TEMP_C=$((TEMP / 1000))
        print_info "CPU温度: ${TEMP_C}°C"

        if [ "$TEMP_C" -lt 70 ]; then
            check_pass "CPU温度正常: ${TEMP_C}°C (<70°C)"
        elif [ "$TEMP_C" -lt 80 ]; then
            check_warn "CPU温度偏高: ${TEMP_C}°C (建议<70°C)"
        else
            check_fail "CPU温度过高: ${TEMP_C}°C (>80°C，可能影响性能)"
        fi
    fi

    # 检查存储类型（SD卡 vs eMMC）
    if mount | grep -q "mmcblk0p"; then
        STORAGE_TYPE="MMC/SD卡"
        check_warn "使用SD卡/eMMC存储（性能可能受限）"
        print_info "建议使用高速SD卡或外接SSD"
    else
        check_pass "使用非MMC存储（性能较好）"
    fi
}

generate_report() {
    print_header "环境检查报告"

    echo ""
    echo -e "${GREEN}通过检查项: $PASS_COUNT${NC}"
    echo -e "${YELLOW}警告项: $WARN_COUNT${NC}"
    echo -e "${RED}失败项: $FAIL_COUNT${NC}"
    echo ""

    if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ 环境完全满足要求，可以运行SAGIN实验！${NC}"
        return 0
    elif [ "$FAIL_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}⚠ 环境基本满足要求，但有 $WARN_COUNT 个警告项${NC}"
        echo -e "${YELLOW}建议修复警告项以获得最佳性能${NC}"
        return 1
    else
        echo -e "${RED}✗ 环境不满足要求，有 $FAIL_COUNT 个失败项${NC}"
        echo -e "${RED}请修复失败项后再运行SAGIN实验${NC}"
        return 2
    fi
}

print_next_steps() {
    print_header "下一步操作建议"

    if [ "$FAIL_COUNT" -gt 0 ]; then
        echo "1. 根据上述失败项，安装缺失的软件"
        echo "2. 重新运行本脚本验证: ./phytium_env_check.sh"
        echo "3. 修复所有失败项后，开始SAGIN部署"
    elif [ "$WARN_COUNT" -gt 0 ]; then
        echo "1. （可选）根据警告项优化环境"
        echo "2. 开始SAGIN环境部署："
        echo "   cd /home/ccc/pq-ntor-experiment/sagin-experiments"
        echo "   ./phytium_deploy.sh"
    else
        echo "环境已就绪！可以开始SAGIN部署："
        echo "  cd /home/ccc/pq-ntor-experiment/sagin-experiments"
        echo "  ./phytium_deploy.sh"
    fi

    echo ""
    echo "相关文档："
    echo "  - SAGIN环境复用指南.md"
    echo "  - SAGIN代码结构说明-技术版.md"
    echo "  - Phase2最终总结_学术版.md"
}

save_report() {
    REPORT_FILE="/tmp/phytium_env_check_$(date +%Y%m%d_%H%M%S).txt"

    {
        print_header "飞腾派SAGIN环境检测报告"
        echo "检测时间: $(date)"
        echo "主机名: $(hostname)"
        echo ""
        echo "检查结果统计："
        echo "  通过: $PASS_COUNT"
        echo "  警告: $WARN_COUNT"
        echo "  失败: $FAIL_COUNT"
        echo ""
        echo "详细信息请查看终端输出"
    } > "$REPORT_FILE"

    print_info "报告已保存到: $REPORT_FILE"
}

################################################################################
# 主函数
################################################################################

main() {
    print_header "飞腾派SAGIN环境检测"
    echo "检测时间: $(date)"
    echo "主机名: $(hostname)"
    echo ""

    # 执行所有检查
    check_system_info
    check_arm_specific
    check_docker
    check_python
    check_network_tools
    check_system_permissions
    check_sagin_files

    echo ""

    # 生成报告
    generate_report
    RESULT=$?

    echo ""

    # 保存报告
    save_report

    echo ""

    # 打印下一步建议
    print_next_steps

    return $RESULT
}

# 运行主函数
main

exit $?
