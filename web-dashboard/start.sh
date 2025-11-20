#!/bin/bash
# PQ-Tor SAGIN Monitor 启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     PQ-Tor SAGIN Monitor - Web Dashboard                  ║"
echo "║     后量子Tor空天地网络监控系统                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查Python依赖
echo -e "${YELLOW}检查依赖...${NC}"
python3 -c "import flask" 2>/dev/null || {
    echo -e "${YELLOW}安装Flask...${NC}"
    pip3 install flask flask-cors pandas
}

# 启动API服务
echo -e "${GREEN}启动API服务...${NC}"
cd "$(dirname "$0")/api"
python3 server.py &
API_PID=$!

echo -e "${GREEN}✓ API服务已启动 (PID: $API_PID)${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo "  🌐 Web UI:  http://localhost:8080"
echo "  📡 API:     http://localhost:8080/api/status"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo "  - 按 Ctrl+C 停止服务"
echo "  - 在浏览器中打开 http://localhost:8080 查看界面"
echo "  - 使用 F11 进入全屏模式"
echo "  - 使用 Ctrl+D 启动演示模式"
echo ""

# 等待用户中断
wait $API_PID
