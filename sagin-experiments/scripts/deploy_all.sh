#!/bin/bash
#========================================
# 6+1方案一键部署脚本
# 自动部署到7个飞腾派
#========================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 节点配置 (格式: IP:节点ID:节点角色)
NODES=(
    "192.168.100.11:SAT:satellite"
    "192.168.100.12:UAV1:aircraft"
    "192.168.100.13:UAV2:aircraft"
    "192.168.100.14:Ground1:ground"
    "192.168.100.15:Ground2:ground"
    "192.168.100.16:Ground3:ground"
)

# 控制台配置
CONTROL_IP="192.168.100.17"

# 部署目录
DEPLOY_DIR="/home/pi/sagin-demo"

# SSH用户名
SSH_USER="pi"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查飞腾派连接性
check_connectivity() {
    local ip=$1
    log_info "检查 $ip 的连接性..."

    if ping -c 1 -W 2 $ip > /dev/null 2>&1; then
        log_info "$ip 可访问 ✓"
        return 0
    else
        log_error "$ip 不可访问 ✗"
        return 1
    fi
}

# 部署节点 (Pi-1 到 Pi-6)
deploy_node() {
    local ip=$1
    local node_id=$2
    local node_role=$3

    log_info "========================================"
    log_info "部署节点: $node_id ($node_role) @ $ip"
    log_info "========================================"

    # 检查连接性
    if ! check_connectivity $ip; then
        log_error "跳过 $node_id 的部署"
        return 1
    fi

    # 创建部署目录
    log_info "创建远程目录..."
    ssh ${SSH_USER}@${ip} "mkdir -p ${DEPLOY_DIR}/{backend,frontend,docker}"

    # 传输文件
    log_info "传输后端文件..."
    scp -r backend/*.py backend/requirements.txt ${SSH_USER}@${ip}:${DEPLOY_DIR}/backend/

    log_info "传输前端文件..."
    scp -r frontend/node-view ${SSH_USER}@${ip}:${DEPLOY_DIR}/frontend/
    scp -r frontend/shared ${SSH_USER}@${ip}:${DEPLOY_DIR}/frontend/

    log_info "传输Docker配置..."
    scp docker/docker-compose-node.yml ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/docker-compose.yml
    scp docker/Dockerfile.agent ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/
    scp docker/nginx-node.conf ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/

    # 启动服务
    log_info "启动Docker服务..."
    ssh ${SSH_USER}@${ip} << EOF
        cd ${DEPLOY_DIR}/docker
        export NODE_ID=${node_id}
        export NODE_ROLE=${node_role}
        docker-compose down 2>/dev/null || true
        docker-compose up -d --build
        echo "✅ ${node_id} 部署完成"
EOF

    log_info "${GREEN}${node_id} 部署成功！${NC}"
    log_info "访问地址: http://${ip}?node_id=${node_id}"
    echo ""
}

# 部署控制台 (Pi-7)
deploy_control() {
    local ip=$1

    log_info "========================================"
    log_info "部署控制台 @ $ip"
    log_info "========================================"

    # 检查连接性
    if ! check_connectivity $ip; then
        log_error "控制台部署失败"
        return 1
    fi

    # 创建部署目录
    log_info "创建远程目录..."
    ssh ${SSH_USER}@${ip} "mkdir -p ${DEPLOY_DIR}/{backend,frontend,docker}"

    # 传输文件
    log_info "传输后端文件..."
    scp -r backend/*.py backend/requirements.txt ${SSH_USER}@${ip}:${DEPLOY_DIR}/backend/

    log_info "传输前端文件..."
    scp -r frontend/control-panel ${SSH_USER}@${ip}:${DEPLOY_DIR}/frontend/
    scp -r frontend/shared ${SSH_USER}@${ip}:${DEPLOY_DIR}/frontend/

    log_info "传输Docker配置..."
    scp docker/docker-compose-control.yml ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/docker-compose.yml
    scp docker/Dockerfile.hub ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/
    scp docker/nginx-control.conf ${SSH_USER}@${ip}:${DEPLOY_DIR}/docker/

    # 启动服务
    log_info "启动Docker服务..."
    ssh ${SSH_USER}@${ip} << 'EOF'
        cd ${DEPLOY_DIR}/docker
        docker-compose down 2>/dev/null || true
        docker-compose up -d --build
        echo "✅ 控制台部署完成"
EOF

    log_info "${GREEN}控制台部署成功！${NC}"
    log_info "访问地址: http://${ip}"
    echo ""
}

# 主函数
main() {
    log_info "========================================"
    log_info "SAGIN NOMA 6+1方案 - 一键部署"
    log_info "========================================"
    echo ""

    # 检查是否在正确的目录
    if [[ ! -f "backend/websocket_hub.py" ]]; then
        log_error "请在 distributed-demo 目录下运行此脚本"
        exit 1
    fi

    # 询问部署确认
    echo -e "${YELLOW}将部署到以下设备:${NC}"
    echo "  控制台: $CONTROL_IP"
    for node in "${NODES[@]}"; do
        IFS=':' read -r ip node_id role <<< "$node"
        echo "  节点 $node_id: $ip ($role)"
    done
    echo ""

    read -p "确认部署? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log_warn "部署已取消"
        exit 0
    fi

    echo ""

    # 部署控制台 (先部署，因为节点需要连接到它)
    deploy_control $CONTROL_IP

    # 等待控制台启动
    log_info "等待控制台启动（10秒）..."
    sleep 10

    # 部署所有节点
    for node in "${NODES[@]}"; do
        IFS=':' read -r ip node_id role <<< "$node"
        deploy_node $ip $node_id $role
        sleep 2  # 避免同时启动太多连接
    done

    # 部署完成
    log_info "========================================"
    log_info "🎉 部署完成！"
    log_info "========================================"
    echo ""
    log_info "访问地址:"
    log_info "  控制台 (Pi-7): http://${CONTROL_IP}"
    for node in "${NODES[@]}"; do
        IFS=':' read -r ip node_id role <<< "$node"
        log_info "  节点 ${node_id}: http://${ip}?node_id=${node_id}"
    done
    echo ""
    log_info "提示:"
    log_info "  - 在控制台切换拓扑，所有节点会同步更新"
    log_info "  - 检查日志: ssh pi@IP 'cd ${DEPLOY_DIR}/docker && docker-compose logs -f'"
    log_info "  - 重启服务: ssh pi@IP 'cd ${DEPLOY_DIR}/docker && docker-compose restart'"
}

# 运行主函数
main
