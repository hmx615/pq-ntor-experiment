#!/bin/bash
# deploy_all.sh - 一键部署到所有7台飞腾派
# 使用方法: ./deploy_all.sh [GitHub仓库URL]

set -e

# 配置
REPO_URL="${1:-https://github.com/your-username/pq-ntor-experiment.git}"
USER="user"

# 节点IP配置
declare -A NODES
NODES[client]="192.168.5.110"
NODES[directory]="192.168.5.111"
NODES[guard]="192.168.5.112"
NODES[middle]="192.168.5.113"
NODES[exit]="192.168.5.114"
NODES[target]="192.168.5.115"
NODES[monitor]="192.168.5.116"

echo "======================================================================"
echo "  PQ-NTOR 7飞腾派分布式部署"
echo "======================================================================"
echo "仓库: $REPO_URL"
echo "用户: $USER"
echo "节点数: ${#NODES[@]}"
echo ""

# 检查SSH连接
echo "[0/7] 检查SSH连接..."
for node in "${!NODES[@]}"; do
    ip=${NODES[$node]}
    printf "  %-12s %-15s ... " "$node" "$ip"

    if ssh -o ConnectTimeout=5 -o BatchMode=yes $USER@$ip "exit" 2>/dev/null; then
        echo "✓"
    else
        echo "✗ 无法连接"
        exit 1
    fi
done

echo ""
echo "[1/7] 开始部署代码到所有节点..."
echo ""

# 部署函数
deploy_to_node() {
    local node=$1
    local ip=$2

    echo "[$node] 部署到 $ip ..."

    ssh $USER@$ip bash << ENDSSH
        set -e

        # 删除旧代码
        if [ -d ~/pq-ntor-experiment ]; then
            echo "  删除旧代码..."
            rm -rf ~/pq-ntor-experiment
        fi

        # 克隆最新代码
        echo "  克隆代码..."
        git clone $REPO_URL ~/pq-ntor-experiment 2>&1 | head -5

        # 进入目录
        cd ~/pq-ntor-experiment/c

        # 编译
        echo "  开始编译..."
        make clean > /dev/null 2>&1 || true
        make all 2>&1 | grep -E "(CC|LD|✓|error)" || true

        # 检查编译结果
        if [ -f ./directory ] && [ -f ./relay ] && [ -f ./benchmark_3hop_circuit ]; then
            echo "  ✓ 编译成功"
            ls -lh directory relay benchmark_3hop_circuit | awk '{print "    " \$9 " (" \$5 ")"}'
        else
            echo "  ✗ 编译失败"
            exit 1
        fi
ENDSSH

    if [ $? -eq 0 ]; then
        echo "  ✓ $node 部署完成"
    else
        echo "  ✗ $node 部署失败"
        return 1
    fi

    echo ""
}

# 部署到所有节点
failed_nodes=()
for node in "${!NODES[@]}"; do
    ip=${NODES[$node]}

    if ! deploy_to_node "$node" "$ip"; then
        failed_nodes+=("$node($ip)")
    fi
done

echo ""
echo "======================================================================"
echo "  部署总结"
echo "======================================================================"
echo "总节点: ${#NODES[@]}"
echo "成功: $((${#NODES[@]} - ${#failed_nodes[@]}))"
echo "失败: ${#failed_nodes[@]}"

if [ ${#failed_nodes[@]} -gt 0 ]; then
    echo ""
    echo "失败节点:"
    for node in "${failed_nodes[@]}"; do
        echo "  - $node"
    done
    exit 1
fi

echo ""
echo "✓ 所有节点部署成功！"
echo ""
echo "下一步："
echo "  1. 启动系统: ./start_all.sh"
echo "  2. 运行测试: ssh $USER@${NODES[client]} 'cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 10 ${NODES[directory]} 5000'"
echo "  3. 停止系统: ./stop_all.sh"
