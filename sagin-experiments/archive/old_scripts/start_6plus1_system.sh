#!/bin/bash
# 启动6+1系统（Hub + 6个节点 + 前端）

echo "========================================"
echo "启动 PQ-NTOR SAGIN 6+1 演示系统"
echo "========================================"
echo ""

cd /home/ccc/pq-ntor-experiment/sagin-experiments

# 1. 停止现有服务
echo "步骤 1/4: 停止现有服务..."
pkill -f hub_server.py 2>/dev/null || true
pkill -f node_agent.py 2>/dev/null || true
pkill -f "http.server.*8080" 2>/dev/null || true
pkill -f "http.server.*8081" 2>/dev/null || true
sleep 2

# 2. 启动 Hub Server
echo ""
echo "步骤 2/4: 启动 Hub Server (端口 9000)..."
cd backend
nohup python3 hub_server.py > /tmp/hub_server.log 2>&1 &
HUB_PID=$!
echo "✓ Hub Server 已启动 (PID: $HUB_PID)"
sleep 2

# 检查 Hub 是否启动成功
if ! ps -p $HUB_PID > /dev/null; then
    echo "❌ Hub Server 启动失败"
    echo "查看日志: cat /tmp/hub_server.log"
    exit 1
fi

# 3. 启动 6 个节点 Agent
echo ""
echo "步骤 3/4: 启动 6 个节点 Agent..."

HUB_URL="ws://localhost:9000"

# SAT (卫星)
HUB_URL=$HUB_URL NODE_ID=SAT NODE_ROLE=satellite nohup python3 node_agent.py > /tmp/agent_SAT.log 2>&1 &
echo "  ✓ SAT (卫星)"

# UAV1 (无人机1)
HUB_URL=$HUB_URL NODE_ID=UAV1 NODE_ROLE=aircraft nohup python3 node_agent.py > /tmp/agent_UAV1.log 2>&1 &
echo "  ✓ UAV1 (无人机1)"

# UAV2 (无人机2)
HUB_URL=$HUB_URL NODE_ID=UAV2 NODE_ROLE=aircraft nohup python3 node_agent.py > /tmp/agent_UAV2.log 2>&1 &
echo "  ✓ UAV2 (无人机2)"

# Ground1 (终端1)
HUB_URL=$HUB_URL NODE_ID=Ground1 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground1.log 2>&1 &
echo "  ✓ Ground1 (终端1)"

# Ground2 (终端2)
HUB_URL=$HUB_URL NODE_ID=Ground2 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground2.log 2>&1 &
echo "  ✓ Ground2 (终端2)"

# Ground3 (终端3)
HUB_URL=$HUB_URL NODE_ID=Ground3 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground3.log 2>&1 &
echo "  ✓ Ground3 (终端3)"

sleep 3

# 4. 启动前端Web服务器
echo ""
echo "步骤 4/4: 启动前端 Web 服务器..."

cd ../frontend

# 控制面板 (端口 8080)
cd control-panel
nohup python3 -m http.server 8080 > /tmp/frontend_control.log 2>&1 &
echo "  ✓ 控制面板: http://localhost:8080"

# 节点视图 (端口 8081)
cd ../node-view
nohup python3 -m http.server 8081 > /tmp/frontend_node.log 2>&1 &
echo "  ✓ 节点视图: http://localhost:8081"

sleep 2

# 5. 检查所有服务状态
echo ""
echo "========================================"
echo "服务状态检查"
echo "========================================"
echo ""

echo "Hub Server:"
ps aux | grep hub_server.py | grep -v grep | awk '{print "  PID:", $2, "运行中"}'

echo ""
echo "节点 Agent (共6个):"
ps aux | grep node_agent.py | grep -v grep | wc -l | awk '{print "  运行中:", $1, "个节点"}'

echo ""
echo "Web 服务器:"
ps aux | grep "http.server" | grep -v grep | awk '{print "  端口", $NF, "运行中"}'

echo ""
echo "========================================"
echo "访问地址"
echo "========================================"
echo ""
echo "📱 控制面板: http://localhost:8080"
echo "📱 节点视图: http://localhost:8081"
echo ""
echo "如果在飞腾派上访问，请使用 WSL 的 IP 地址："
echo "  控制面板: http://$(hostname -I | awk '{print $1}'):8080"
echo "  节点视图: http://$(hostname -I | awk '{print $1}'):8081"
echo ""
echo "========================================"
echo "日志文件"
echo "========================================"
echo ""
echo "Hub Server:  tail -f /tmp/hub_server.log"
echo "节点 Agent:  tail -f /tmp/agent_*.log"
echo "控制面板:    tail -f /tmp/frontend_control.log"
echo "节点视图:    tail -f /tmp/frontend_node.log"
echo ""
echo "========================================"
echo "停止服务"
echo "========================================"
echo ""
echo "pkill -f hub_server.py"
echo "pkill -f node_agent.py"
echo "pkill -f http.server"
echo ""
echo "✅ 系统启动完成！"
