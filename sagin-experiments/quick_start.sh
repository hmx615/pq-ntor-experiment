#!/bin/bash
# 快速启动6+1系统

echo "========================================"
echo "启动 PQ-NTOR SAGIN 6+1 系统"
echo "========================================"
echo ""

cd /home/ccc/pq-ntor-experiment/sagin-experiments

# 停止现有服务
echo "清理现有服务..."
pkill -f websocket_hub.py 2>/dev/null || true
pkill -f node_agent.py 2>/dev/null || true
pkill -f "http.server.*8080" 2>/dev/null || true
pkill -f "http.server.*8081" 2>/dev/null || true
sleep 2

# 启动 WebSocket Hub (端口 9000)
echo "启动 WebSocket Hub..."
cd backend
nohup python3 websocket_hub.py > /tmp/hub.log 2>&1 &
sleep 2

# 启动 6 个节点
echo "启动节点 Agent..."
HUB_URL="ws://localhost:9000"

HUB_URL=$HUB_URL NODE_ID=SAT NODE_ROLE=satellite python3 node_agent.py > /tmp/SAT.log 2>&1 &
HUB_URL=$HUB_URL NODE_ID=UAV1 NODE_ROLE=aircraft python3 node_agent.py > /tmp/UAV1.log 2>&1 &
HUB_URL=$HUB_URL NODE_ID=UAV2 NODE_ROLE=aircraft python3 node_agent.py > /tmp/UAV2.log 2>&1 &
HUB_URL=$HUB_URL NODE_ID=Ground1 NODE_ROLE=ground python3 node_agent.py > /tmp/Ground1.log 2>&1 &
HUB_URL=$HUB_URL NODE_ID=Ground2 NODE_ROLE=ground python3 node_agent.py > /tmp/Ground2.log 2>&1 &
HUB_URL=$HUB_URL NODE_ID=Ground3 NODE_ROLE=ground python3 node_agent.py > /tmp/Ground3.log 2>&1 &

sleep 3

# 启动前端
echo "启动前端..."
cd ../frontend/control-panel
python3 -m http.server 8080 > /tmp/frontend_control.log 2>&1 &

cd ../node-view
python3 -m http.server 8081 > /tmp/frontend_node.log 2>&1 &

sleep 2

# 显示状态
echo ""
echo "========================================"
echo "✅ 系统已启动！"
echo "========================================"
echo ""
echo "Hub: $(ps aux | grep websocket_hub.py | grep -v grep | wc -l) 个"
echo "节点: $(ps aux | grep node_agent.py | grep -v grep | wc -l) 个"
echo "Web: $(ps aux | grep 'http.server' | grep -v grep | wc -l) 个"
echo ""
echo "访问地址（WSL 本地）:"
echo "  控制面板: http://localhost:8080"
echo "  节点视图: http://localhost:8081"
echo ""
WSL_IP=$(hostname -I | awk '{print $1}')
echo "访问地址（飞腾派访问）:"
echo "  控制面板: http://$WSL_IP:8080"
echo "  节点视图: http://$WSL_IP:8081"
echo ""
echo "日志查看:"
echo "  Hub:  tail -f /tmp/hub.log"
echo "  节点: tail -f /tmp/SAT.log"
echo ""
echo "停止服务:"
echo "  pkill -f websocket_hub.py"
echo "  pkill -f node_agent.py"
echo "  pkill -f http.server"
echo ""
