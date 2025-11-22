#!/bin/bash
#========================================
# 本地测试脚本
# 在开发机上启动所有服务进行测试
#========================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v python3 &> /dev/null; then
        echo "错误: 未找到 python3"
        exit 1
    fi

    # 检查Python包
    python3 -c "import websockets" 2>/dev/null || {
        log_info "安装 Python 依赖..."
        cd ../backend
        pip3 install -r requirements.txt
        cd ../scripts
    }
}

# 启动WebSocket Hub
start_hub() {
    log_info "启动 WebSocket Hub..."

    cd ../backend
    python3 websocket_hub.py > /tmp/sagin_hub.log 2>&1 &
    HUB_PID=$!
    echo $HUB_PID > /tmp/sagin_hub.pid

    log_info "WebSocket Hub 已启动 (PID: $HUB_PID)"
    log_info "日志: /tmp/sagin_hub.log"
}

# 启动模拟节点Agent
start_node_agent() {
    local node_id=$1
    local node_role=$2

    log_info "启动节点 Agent: $node_id ($node_role)"

    cd ../backend
    NODE_ID=$node_id NODE_ROLE=$node_role HUB_URL="ws://localhost:9000" \
        python3 node_agent.py > /tmp/sagin_node_${node_id}.log 2>&1 &
    NODE_PID=$!
    echo $NODE_PID >> /tmp/sagin_nodes.pid

    log_info "节点 $node_id 已启动 (PID: $NODE_PID)"
}

# 启动HTTP服务器
start_http_server() {
    log_info "启动 HTTP 服务器..."

    cd ../frontend
    python3 -m http.server 8080 > /tmp/sagin_http.log 2>&1 &
    HTTP_PID=$!
    echo $HTTP_PID > /tmp/sagin_http.pid

    log_info "HTTP 服务器已启动 (PID: $HTTP_PID)"
    log_info "控制台: http://localhost:8080/control-panel/"
    log_info "节点视图: http://localhost:8080/node-view/?node_id=SAT"
}

# 停止所有服务
stop_all() {
    log_info "停止所有服务..."

    # 停止Hub
    if [[ -f /tmp/sagin_hub.pid ]]; then
        kill $(cat /tmp/sagin_hub.pid) 2>/dev/null || true
        rm /tmp/sagin_hub.pid
    fi

    # 停止所有节点
    if [[ -f /tmp/sagin_nodes.pid ]]; then
        while read pid; do
            kill $pid 2>/dev/null || true
        done < /tmp/sagin_nodes.pid
        rm /tmp/sagin_nodes.pid
    fi

    # 停止HTTP服务器
    if [[ -f /tmp/sagin_http.pid ]]; then
        kill $(cat /tmp/sagin_http.pid) 2>/dev/null || true
        rm /tmp/sagin_http.pid
    fi

    log_info "所有服务已停止"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            log_info "========================================"
            log_info "启动本地测试环境"
            log_info "========================================"

            check_dependencies

            # 清理之前的进程
            stop_all
            sleep 1

            # 启动服务
            start_hub
            sleep 2

            # 启动6个模拟节点
            start_node_agent "SAT" "satellite"
            start_node_agent "SR" "aircraft"
            start_node_agent "S1R2" "aircraft"
            start_node_agent "S1" "ground"
            start_node_agent "S2" "ground"
            start_node_agent "T" "ground"
            sleep 2

            # 启动HTTP服务器
            start_http_server

            echo ""
            log_info "========================================"
            log_info "测试环境已启动！"
            log_info "========================================"
            echo ""
            log_info "访问地址:"
            log_info "  控制台: http://localhost:8080/control-panel/"
            log_info "  节点视图示例:"
            log_info "    卫星: http://localhost:8080/node-view/?node_id=SAT"
            log_info "    无人机1: http://localhost:8080/node-view/?node_id=SR"
            log_info "    终端1: http://localhost:8080/node-view/?node_id=S1"
            echo ""
            log_info "查看日志:"
            log_info "  Hub: tail -f /tmp/sagin_hub.log"
            log_info "  节点SAT: tail -f /tmp/sagin_node_SAT.log"
            echo ""
            log_info "停止服务: $0 stop"
            ;;

        stop)
            stop_all
            ;;

        restart)
            stop_all
            sleep 1
            $0 start
            ;;

        logs)
            log_info "Hub日志:"
            tail -20 /tmp/sagin_hub.log
            echo ""
            log_info "节点SAT日志:"
            tail -20 /tmp/sagin_node_SAT.log
            ;;

        *)
            echo "用法: $0 {start|stop|restart|logs}"
            exit 1
            ;;
    esac
}

# 捕获Ctrl+C (不包括EXIT，否则start命令会自动停止服务)
# trap stop_all INT TERM

main "$@"
