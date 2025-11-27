#!/bin/bash
# 启动 distributed-demo 版本（带地球显示）

echo "========================================"
echo "启动 PQ-NTOR SAGIN 演示系统"
echo "distributed-demo 版本（3D地球视图）"
echo "========================================"
echo ""

cd /home/ccc/pq-ntor-experiment/sagin-experiments/distributed-demo

# 停止现有服务
echo "清理现有服务..."
pkill -9 -f websocket_hub.py 2>/dev/null || true
pkill -9 -f node_agent.py 2>/dev/null || true
pkill -9 -f "http.server.*8080" 2>/dev/null || true
pkill -9 -f "http.server.*8081" 2>/dev/null || true
sleep 3

# 启动 WebSocket Hub
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

# 启动前端 - 绑定到 0.0.0.0
echo "启动前端（绑定所有接口）..."
cd ../frontend
nohup python3 -m http.server 8080 --bind 0.0.0.0 > /tmp/frontend.log 2>&1 &

sleep 2

# 显示状态
echo ""
echo "========================================"
echo "✅ 系统已启动！"
echo "========================================"
echo ""
echo "Hub: $(ps aux | grep websocket_hub.py | grep -v grep | wc -l) 个"
echo "节点: $(ps aux | grep node_agent.py | grep -v grep | wc -l) 个"
echo "Web: $(ps aux | grep 'http.server.*8080' | grep -v grep | wc -l) 个"
echo ""

echo "========================================"
echo "飞腾派访问地址："
echo "========================================"
echo "  控制面板: http://192.168.5.83:8080/control-panel/"
echo ""
echo "  节点视图（3D地球）:"
echo "    SAT:     http://192.168.5.83:8080/node-view/index.html?node_id=SAT"
echo "    UAV1:    http://192.168.5.83:8080/node-view/index.html?node_id=UAV1"
echo "    UAV2:    http://192.168.5.83:8080/node-view/index.html?node_id=UAV2"
echo "    Ground1: http://192.168.5.83:8080/node-view/index.html?node_id=Ground1"
echo "    Ground2: http://192.168.5.83:8080/node-view/index.html?node_id=Ground2"
echo "    Ground3: http://192.168.5.83:8080/node-view/index.html?node_id=Ground3"
echo ""

echo "本地访问："
for ip in $(hostname -I); do
    echo "  http://$ip:8080/node-view/index.html?node_id=UAV1"
done
echo ""

echo "日志查看:"
echo "  Hub:  tail -f /tmp/hub.log"
echo "  节点: tail -f /tmp/SAT.log"
echo "  前端: tail -f /tmp/frontend.log"
echo ""
echo "停止服务:"
echo "  pkill -f websocket_hub.py"
echo "  pkill -f node_agent.py"
echo "  pkill -f http.server"
echo ""
