#!/bin/bash
#
# 性能测试脚本 - 对比原版Agent vs Lite Agent
#

set -e

NODE_ID=${1:-"pi-1"}
NODE_ROLE=${2:-"ground"}

echo "==================================="
echo "  Agent Performance Test"
echo "==================================="
echo "Node ID: $NODE_ID"
echo "Node Role: $NODE_ROLE"
echo ""

# 测试精简版Agent
test_lite_agent() {
    echo "### Testing Lite Agent ###"

    cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker

    # 启动精简版
    export NODE_ID=$NODE_ID
    export NODE_ROLE=$NODE_ROLE
    docker-compose -f docker-compose-node-optimized.yml up -d

    echo "Waiting for agent to start (10s)..."
    sleep 10

    # 性能测试
    echo ""
    echo "=== Resource Usage (Lite) ==="
    docker stats --no-stream sagin_node_lite_${NODE_ID} --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    # 停止
    echo ""
    echo "Stopping lite agent..."
    docker-compose -f docker-compose-node-optimized.yml down
}

# 对比原版Agent (如果存在)
test_original_agent() {
    echo ""
    echo "### Testing Original Agent (for comparison) ###"

    if [ ! -f docker-compose-node.yml ]; then
        echo "Original docker-compose not found, skipping comparison"
        return
    fi

    # 启动原版
    export NODE_ID=$NODE_ID
    export NODE_ROLE=$NODE_ROLE
    docker-compose -f docker-compose-node.yml up -d

    echo "Waiting for agent to start (10s)..."
    sleep 10

    # 性能测试
    echo ""
    echo "=== Resource Usage (Original) ==="
    docker stats --no-stream sagin_node_${NODE_ID} sagin_node_nginx_${NODE_ID} --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    # 停止
    echo ""
    echo "Stopping original agent..."
    docker-compose -f docker-compose-node.yml down
}

# 运行测试
test_lite_agent
test_original_agent

echo ""
echo "==================================="
echo "  Test Complete"
echo "==================================="
echo ""
echo "Expected improvements:"
echo "  - CPU: 60-70% reduction"
echo "  - Memory: ~75MB reduction"
echo "  - Lite agent should use < 5% CPU, < 30MB RAM"
