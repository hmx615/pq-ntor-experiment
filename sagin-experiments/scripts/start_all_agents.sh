#!/bin/bash
# 启动所有6个节点agent（使用统一命名规则）

cd /home/ccc/pq-ntor-experiment/sagin-experiments/backend

# Hub URL (WSL本地测试)
HUB_URL="ws://localhost:9000"

# 杀死现有进程
echo "正在停止现有node_agent进程..."
pkill -f node_agent.py
sleep 2

# 启动所有节点agent
echo "启动节点agent..."

# SAT (卫星)
HUB_URL=$HUB_URL NODE_ID=SAT NODE_ROLE=satellite nohup python3 node_agent.py > /tmp/agent_SAT.log 2>&1 &
echo "✓ 启动 SAT (卫星)"

# UAV1 (无人机1)
HUB_URL=$HUB_URL NODE_ID=UAV1 NODE_ROLE=aircraft nohup python3 node_agent.py > /tmp/agent_UAV1.log 2>&1 &
echo "✓ 启动 UAV1 (无人机1)"

# UAV2 (无人机2)
HUB_URL=$HUB_URL NODE_ID=UAV2 NODE_ROLE=aircraft nohup python3 node_agent.py > /tmp/agent_UAV2.log 2>&1 &
echo "✓ 启动 UAV2 (无人机2)"

# Ground1 (终端1)
HUB_URL=$HUB_URL NODE_ID=Ground1 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground1.log 2>&1 &
echo "✓ 启动 Ground1 (终端1)"

# Ground2 (终端2)
HUB_URL=$HUB_URL NODE_ID=Ground2 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground2.log 2>&1 &
echo "✓ 启动 Ground2 (终端2)"

# Ground3 (终端3)
HUB_URL=$HUB_URL NODE_ID=Ground3 NODE_ROLE=ground nohup python3 node_agent.py > /tmp/agent_Ground3.log 2>&1 &
echo "✓ 启动 Ground3 (终端3)"

sleep 2

echo ""
echo "=== 节点状态 ==="
ps aux | grep node_agent.py | grep -v grep | awk '{print $2, $NF}'

echo ""
echo "=== 日志文件 ==="
ls -lh /tmp/agent_*.log

echo ""
echo "✅ 所有节点agent已启动！"
echo "查看日志: tail -f /tmp/agent_<NODE_ID>.log"
