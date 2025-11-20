#!/bin/bash
# Build PQ-NTOR Docker Image for SAGIN Experiments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/ccc/pq-ntor-experiment"
IMAGE_NAME="pq-ntor-sagin"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

print_header "构建 PQ-NTOR Docker 镜像"
echo "镜像名称: ${FULL_IMAGE_NAME}"
echo "项目根目录: ${PROJECT_ROOT}"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装"
    exit 1
fi

# Check if running as root or in docker group
if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
    print_error "需要 root 权限或在 docker 组中"
    echo "请运行: sudo ./build_pq_ntor_image.sh"
    exit 1
fi

# Check if source code exists
if [ ! -d "${PROJECT_ROOT}/c" ]; then
    print_error "PQ-NTOR 源代码目录不存在: ${PROJECT_ROOT}/c"
    exit 1
fi

# Create .dockerignore if it doesn't exist
print_info "创建 .dockerignore 文件..."
cat > "${SCRIPT_DIR}/.dockerignore" << 'EOF'
# Compiled binaries
*.o
*.so
*.a
*.out

# Logs
*.log

# Build artifacts
.vscode/
__pycache__/
*.pyc

# Git
.git/
.gitignore

# Documentation
*.md
*.txt

# Test results
results/
benchmark_results.csv
EOF

print_success ".dockerignore 创建完成"

# Copy source code to docker build context
print_info "准备构建上下文..."
BUILD_CONTEXT="${SCRIPT_DIR}/build_context"
rm -rf "${BUILD_CONTEXT}"
mkdir -p "${BUILD_CONTEXT}"

# Copy C source code
cp -r "${PROJECT_ROOT}/c" "${BUILD_CONTEXT}/"
print_success "源代码复制完成"

# Build the image
print_header "开始构建 Docker 镜像"
print_info "这可能需要 5-10 分钟..."
echo ""

cd "${SCRIPT_DIR}"
if docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -t "${FULL_IMAGE_NAME}" \
    -f Dockerfile.pq-ntor \
    "${BUILD_CONTEXT}"; then

    print_success "镜像构建成功!"
    echo ""

    # Clean up build context
    print_info "清理构建上下文..."
    rm -rf "${BUILD_CONTEXT}"

    # Show image info
    print_header "镜像信息"
    docker images | grep -E "REPOSITORY|${IMAGE_NAME}"

    echo ""
    print_header "验证镜像"

    # Test the image
    print_info "启动测试容器..."
    TEST_CONTAINER="pq-ntor-test-$$"

    if docker run --rm --name "${TEST_CONTAINER}" "${FULL_IMAGE_NAME}" /bin/bash -c "\
        echo 'Testing PQ-NTOR executables...' && \
        ls -lh /root/pq-ntor/relay /root/pq-ntor/client /root/pq-ntor/directory && \
        echo 'Checking liboqs...' && \
        ldd /root/pq-ntor/relay | grep oqs && \
        echo 'All checks passed!'" 2>&1; then

        print_success "镜像验证通过!"
    else
        print_error "镜像验证失败"
        exit 1
    fi

    echo ""
    print_header "构建完成"
    echo "镜像: ${FULL_IMAGE_NAME}"
    echo ""
    echo "使用方法:"
    echo "  1. 运行容器: docker run -it ${FULL_IMAGE_NAME} /bin/bash"
    echo "  2. 运行中继: docker run ${FULL_IMAGE_NAME} /root/pq-ntor/relay [args]"
    echo "  3. 在 SAGIN 中使用: 修改 sagin_integration.py 中的 base_image"
    echo ""

else
    print_error "镜像构建失败"
    rm -rf "${BUILD_CONTEXT}"
    exit 1
fi
