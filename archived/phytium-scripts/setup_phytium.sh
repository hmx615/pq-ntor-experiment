#!/bin/bash
################################################################################
# PQ-Tor 飞腾派自动化部署脚本
#
# 功能：一键完成飞腾派环境配置
#   1. 检查系统环境
#   2. 安装基础依赖
#   3. 编译安装 liboqs
#   4. 验证 Kyber KEM
#   5. 编译 PQ-Tor
#   6. 运行测试验证
#
# 适用平台：ARM64 (飞腾派/树莓派等)
# 作者：PQ-Tor Project
# 创建时间：2025-11-27
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
WORK_DIR=~/pq-tor-deps
LIBOQS_INSTALL_DIR=~/oqs
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LIBOQS_VERSION="0.11.0"

# 计数器
STEP=0
TOTAL_STEPS=8

################################################################################
# 辅助函数
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         PQ-Tor 飞腾派自动化部署脚本                        ║"
    echo "║         Phytium Pi Auto-Deployment Script                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_step() {
    ((STEP++))
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[$STEP/$TOTAL_STEPS] $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "      ${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "      ${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "      ${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "      ${BLUE}ℹ️  $1${NC}"
}

################################################################################
# 检查函数
################################################################################

check_architecture() {
    print_step "检查系统架构"

    ARCH=$(uname -m)
    echo "      当前架构: $ARCH"

    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        print_success "ARM64 架构确认"
    elif [[ "$ARCH" == "x86_64" ]]; then
        print_warning "检测到 x86_64 架构（WSL/虚拟机）"
        print_info "脚本仍可运行，但主要针对 ARM64 优化"
    else
        print_error "不支持的架构: $ARCH"
        exit 1
    fi

    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "      操作系统: $NAME $VERSION"
        print_success "Linux 系统确认"
    else
        print_error "无法识别操作系统"
        exit 1
    fi

    echo ""
}

check_prerequisites() {
    print_step "检查必备工具"

    local missing_tools=()

    # 检查 GCC
    if command -v gcc &> /dev/null; then
        GCC_VERSION=$(gcc --version | head -n1)
        echo "      $GCC_VERSION"
        print_success "GCC 已安装"
    else
        missing_tools+=("gcc")
        print_error "GCC 未安装"
    fi

    # 检查 Make
    if command -v make &> /dev/null; then
        print_success "Make 已安装"
    else
        missing_tools+=("make")
        print_error "Make 未安装"
    fi

    # 检查 CMake
    if command -v cmake &> /dev/null; then
        CMAKE_VERSION=$(cmake --version | head -n1)
        echo "      $CMAKE_VERSION"
        print_success "CMake 已安装"
    else
        missing_tools+=("cmake")
        print_error "CMake 未安装"
    fi

    # 检查 Git
    if command -v git &> /dev/null; then
        print_success "Git 已安装"
    else
        missing_tools+=("git")
        print_error "Git 未安装"
    fi

    # 检查 OpenSSL
    if command -v openssl &> /dev/null && pkg-config --exists openssl 2>/dev/null; then
        OPENSSL_VERSION=$(openssl version)
        echo "      $OPENSSL_VERSION"
        print_success "OpenSSL 开发库已安装"
    else
        missing_tools+=("openssl-dev")
        print_error "OpenSSL 开发库未安装"
    fi

    echo ""

    # 如果有缺失工具，提示安装
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_warning "发现缺失工具，准备安装..."
        echo ""
        return 1
    fi

    return 0
}

install_dependencies() {
    print_step "安装系统依赖"

    print_info "更新软件源..."
    sudo apt-get update -qq
    print_success "软件源更新完成"

    print_info "安装编译工具和依赖库..."
    sudo apt-get install -y -qq \
        build-essential \
        cmake \
        git \
        libssl-dev \
        wget \
        curl \
        vim \
        pkg-config

    print_success "所有依赖安装完成"
    echo ""
}

check_liboqs_installed() {
    if [ -f "$LIBOQS_INSTALL_DIR/lib/liboqs.so" ] && \
       [ -d "$LIBOQS_INSTALL_DIR/include/oqs" ]; then
        return 0
    fi
    return 1
}

install_liboqs() {
    print_step "编译安装 liboqs (Kyber KEM 库)"

    # 检查是否已安装
    if check_liboqs_installed; then
        print_warning "liboqs 已安装在 $LIBOQS_INSTALL_DIR"
        read -p "      是否重新编译安装？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "跳过 liboqs 安装"
            echo ""
            return 0
        fi
    fi

    # 创建工作目录
    print_info "创建工作目录: $WORK_DIR"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"

    # 克隆或更新 liboqs
    if [ -d "liboqs" ]; then
        print_info "liboqs 目录已存在，更新代码..."
        cd liboqs
        git fetch --tags
    else
        print_info "克隆 liboqs 仓库..."
        git clone --depth 1 --branch "$LIBOQS_VERSION" \
            https://github.com/open-quantum-safe/liboqs.git
        cd liboqs
    fi

    print_success "源码准备完成 (版本: $LIBOQS_VERSION)"

    # 配置 CMake
    print_info "配置 CMake..."
    rm -rf build
    mkdir build && cd build

    cmake -DCMAKE_INSTALL_PREFIX="$LIBOQS_INSTALL_DIR" \
          -DCMAKE_BUILD_TYPE=Release \
          -DBUILD_SHARED_LIBS=ON \
          -DOQS_USE_OPENSSL=ON \
          .. > /dev/null

    print_success "CMake 配置完成"

    # 编译
    NPROC=$(nproc)
    print_info "开始编译 (使用 $NPROC 个 CPU 核心)..."
    print_warning "ARM 设备编译时间较长，预计 3-8 分钟，请耐心等待..."
    echo ""

    if make -j$NPROC; then
        print_success "编译完成"
    else
        print_error "编译失败"
        exit 1
    fi

    # 安装
    print_info "安装到 $LIBOQS_INSTALL_DIR ..."
    make install > /dev/null
    print_success "安装完成"

    # 验证安装
    echo ""
    print_info "验证安装..."
    if [ -f "$LIBOQS_INSTALL_DIR/lib/liboqs.so" ]; then
        print_success "库文件存在"
        ls -lh "$LIBOQS_INSTALL_DIR/lib/liboqs.so"* | sed 's/^/      /'
    else
        print_error "库文件未找到"
        exit 1
    fi

    if [ -d "$LIBOQS_INSTALL_DIR/include/oqs" ]; then
        print_success "头文件目录存在"
    else
        print_error "头文件目录未找到"
        exit 1
    fi

    echo ""
}

create_kyber_test() {
    print_step "创建 Kyber KEM 验证程序"

    TEST_DIR="$WORK_DIR/kyber-test"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"

    print_info "生成测试代码..."

    cat > test_kyber_simple.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <oqs/oqs.h>

int main(void) {
    printf("╔════════════════════════════════════════════════════════╗\n");
    printf("║     飞腾派 Kyber KEM 验证程序                          ║\n");
    printf("╚════════════════════════════════════════════════════════╝\n\n");

    // 1. 检查 Kyber512 算法
    printf("[1/5] 检查 Kyber512 算法可用性...\n");
    if (!OQS_KEM_alg_is_enabled("Kyber512")) {
        fprintf(stderr, "      ❌ Kyber512 不可用\n");
        return 1;
    }
    printf("      ✅ Kyber512 可用\n\n");

    // 2. 创建 KEM 对象
    printf("[2/5] 创建 KEM 对象...\n");
    OQS_KEM *kem = OQS_KEM_new("Kyber512");
    if (kem == NULL) {
        fprintf(stderr, "      ❌ 创建 KEM 失败\n");
        return 1;
    }
    printf("      ✅ KEM 对象创建成功\n");
    printf("      公钥大小: %zu bytes\n", kem->length_public_key);
    printf("      密钥大小: %zu bytes\n", kem->length_secret_key);
    printf("      密文大小: %zu bytes\n", kem->length_ciphertext);
    printf("      共享密钥: %zu bytes\n\n", kem->length_shared_secret);

    // 3. 生成密钥对
    printf("[3/5] 生成密钥对...\n");
    uint8_t *public_key = malloc(kem->length_public_key);
    uint8_t *secret_key = malloc(kem->length_secret_key);

    if (OQS_KEM_keypair(kem, public_key, secret_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 密钥生成失败\n");
        goto cleanup;
    }
    printf("      ✅ 密钥对生成成功\n\n");

    // 4. 封装测试
    printf("[4/5] 测试封装操作...\n");
    uint8_t *ciphertext = malloc(kem->length_ciphertext);
    uint8_t *shared_secret_enc = malloc(kem->length_shared_secret);

    if (OQS_KEM_encaps(kem, ciphertext, shared_secret_enc, public_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 封装失败\n");
        goto cleanup;
    }
    printf("      ✅ 封装成功\n\n");

    // 5. 解封装测试
    printf("[5/5] 测试解封装操作...\n");
    uint8_t *shared_secret_dec = malloc(kem->length_shared_secret);

    if (OQS_KEM_decaps(kem, shared_secret_dec, ciphertext, secret_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 解封装失败\n");
        goto cleanup;
    }
    printf("      ✅ 解封装成功\n");

    // 验证共享密钥
    if (memcmp(shared_secret_enc, shared_secret_dec, kem->length_shared_secret) != 0) {
        fprintf(stderr, "      ❌ 共享密钥不匹配\n");
        goto cleanup;
    }
    printf("      ✅ 共享密钥匹配\n\n");

    printf("╔════════════════════════════════════════════════════════╗\n");
    printf("║  ✅ 所有测试通过！                                     ║\n");
    printf("║  ✅ 飞腾派环境配置成功！                               ║\n");
    printf("║  ✅ liboqs 库工作正常！                                ║\n");
    printf("╚════════════════════════════════════════════════════════╝\n");

    free(shared_secret_dec);
    free(ciphertext);
    free(shared_secret_enc);

cleanup:
    free(public_key);
    free(secret_key);
    OQS_KEM_free(kem);

    return 0;
}
EOF

    print_success "测试代码生成完成"

    # 编译测试程序
    print_info "编译测试程序..."
    gcc -Wall -O2 \
        -I"$LIBOQS_INSTALL_DIR/include" \
        -L"$LIBOQS_INSTALL_DIR/lib" \
        -o test_kyber_simple \
        test_kyber_simple.c \
        -loqs \
        -Wl,-rpath,"$LIBOQS_INSTALL_DIR/lib"

    print_success "编译完成"
    echo ""
}

run_kyber_test() {
    print_step "运行 Kyber KEM 验证"

    TEST_DIR="$WORK_DIR/kyber-test"
    cd "$TEST_DIR"

    echo ""
    if ./test_kyber_simple; then
        echo ""
        print_success "Kyber KEM 验证通过！"
    else
        echo ""
        print_error "Kyber KEM 验证失败"
        exit 1
    fi

    echo ""
}

compile_pq_tor() {
    print_step "编译 PQ-Tor 项目"

    cd "$PROJECT_DIR/c"

    # 检查 Makefile 是否存在
    if [ ! -f "Makefile" ]; then
        print_error "Makefile 不存在"
        exit 1
    fi

    # 设置 liboqs 路径
    print_info "配置 liboqs 路径..."
    export LIBOQS_DIR="$LIBOQS_INSTALL_DIR"

    # 清理旧编译文件
    print_info "清理旧编译文件..."
    make clean > /dev/null 2>&1 || true

    # 编译所有程序
    print_info "编译所有程序（预计 1-3 分钟）..."
    echo ""

    if make all LIBOQS_DIR="$LIBOQS_INSTALL_DIR"; then
        echo ""
        print_success "PQ-Tor 编译完成"
    else
        echo ""
        print_error "PQ-Tor 编译失败"
        exit 1
    fi

    echo ""
    print_info "编译产物："
    for prog in directory relay client test_pq_ntor test_classic_ntor benchmark_pq_ntor; do
        if [ -f "$prog" ]; then
            echo "      ✅ $prog"
        fi
    done

    echo ""
}

run_pq_tor_tests() {
    print_step "运行 PQ-Tor 单元测试"

    cd "$PROJECT_DIR/c"

    local tests=("test_kyber" "test_crypto" "test_pq_ntor" "test_classic_ntor" "test_cell" "test_onion")
    local passed=0
    local failed=0

    echo ""
    for test in "${tests[@]}"; do
        if [ -f "$test" ]; then
            echo "      测试: $test"
            if ./"$test" > /dev/null 2>&1; then
                print_success "$test 通过"
                ((passed++))
            else
                print_error "$test 失败"
                ((failed++))
            fi
        fi
    done

    echo ""
    print_info "测试统计: 通过 $passed/$((passed + failed))"

    if [ $failed -eq 0 ]; then
        print_success "所有测试通过！"
    else
        print_warning "有 $failed 个测试失败"
    fi

    echo ""
}

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 🎉 部署完成！                              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    echo -e "${BLUE}📦 安装位置：${NC}"
    echo "   liboqs:        $LIBOQS_INSTALL_DIR"
    echo "   PQ-Tor:        $PROJECT_DIR/c"
    echo ""

    echo -e "${BLUE}🧪 验证测试：${NC}"
    echo "   Kyber KEM:     ✅ 通过"
    echo "   PQ-Tor 编译:   ✅ 完成"
    echo ""

    echo -e "${BLUE}🚀 下一步操作：${NC}"
    echo ""
    echo "   1. 运行网络测试："
    echo "      cd $PROJECT_DIR/c"
    echo "      ./test_network.sh"
    echo ""
    echo "   2. 运行基准测试："
    echo "      cd $PROJECT_DIR/c"
    echo "      ./benchmark_pq_ntor"
    echo ""
    echo "   3. 启动单节点测试："
    echo "      cd $PROJECT_DIR/c"
    echo "      ./directory &"
    echo "      ./relay -r guard -p 6001 &"
    echo "      ./client -u http://127.0.0.1:8000/"
    echo ""
    echo "   4. 查看文档："
    echo "      cat $PROJECT_DIR/readme/飞腾派部署指南.md"
    echo ""

    echo -e "${YELLOW}💡 提示：${NC}"
    echo "   - 如需在多个飞腾派上部署，请参考分布式部署文档"
    echo "   - 运行 SAGIN 实验需要 sudo 权限（用于 tc 网络模拟）"
    echo "   - 环境变量已设置，重启后需要重新执行："
    echo "     export LD_LIBRARY_PATH=$LIBOQS_INSTALL_DIR/lib:\$LD_LIBRARY_PATH"
    echo ""

    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

################################################################################
# 主流程
################################################################################

main() {
    print_header

    # 检查架构
    check_architecture

    # 检查并安装依赖
    if ! check_prerequisites; then
        install_dependencies
    else
        print_info "所有必备工具已就绪，跳过依赖安装"
        echo ""
    fi

    # 安装 liboqs
    install_liboqs

    # 创建并运行 Kyber 测试
    create_kyber_test
    run_kyber_test

    # 编译 PQ-Tor
    compile_pq_tor

    # 运行单元测试
    run_pq_tor_tests

    # 打印总结
    print_summary

    # 设置环境变量（临时）
    export LD_LIBRARY_PATH="$LIBOQS_INSTALL_DIR/lib:$LD_LIBRARY_PATH"
    export LIBOQS_DIR="$LIBOQS_INSTALL_DIR"

    # 提示用户添加到 bashrc
    echo -e "${YELLOW}📝 建议添加环境变量到 ~/.bashrc：${NC}"
    echo ""
    echo "   echo 'export LD_LIBRARY_PATH=$LIBOQS_INSTALL_DIR/lib:\$LD_LIBRARY_PATH' >> ~/.bashrc"
    echo "   echo 'export LIBOQS_DIR=$LIBOQS_INSTALL_DIR' >> ~/.bashrc"
    echo "   source ~/.bashrc"
    echo ""
}

# 执行主流程
main "$@"
