#!/bin/bash
# auto_deploy_single_pi.sh - 自动部署到单飞腾派
# 使用方法: ./auto_deploy_single_pi.sh

set -e

PI_IP="192.168.5.110"
PI_USER="user"
PI_PASS="user"

echo "======================================================================"
echo "  自动部署到飞腾派 (${PI_IP})"
echo "======================================================================"
echo ""

# 检查sshpass
if ! command -v sshpass &> /dev/null; then
    echo "正在安装sshpass..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y sshpass
    elif command -v yum &> /dev/null; then
        sudo yum install -y sshpass
    else
        echo "错误: 无法安装sshpass，请手动安装"
        exit 1
    fi
fi

# SSH命令封装
run_ssh() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP "$@"
}

run_ssh_bg() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP "$@" &
}

# 第1步：测试连接
echo "[1/8] 测试SSH连接..."
if run_ssh "echo '连接成功'" > /dev/null 2>&1; then
    echo "  ✓ SSH连接正常"
else
    echo "  ✗ SSH连接失败"
    exit 1
fi

# 第2步：检查代码是否已存在
echo ""
echo "[2/8] 检查现有代码..."
if run_ssh "test -d ~/pq-ntor-experiment"; then
    echo "  发现现有代码，正在更新..."
    run_ssh "cd ~/pq-ntor-experiment && git pull"
else
    echo "  代码不存在，正在克隆..."
    # 注意：这里需要你的GitHub仓库地址，或者从本地复制
    echo "  提示：由于无GitHub仓库地址，将从本地复制代码"
fi

# 第3步：从本地复制代码（替代git clone）
echo ""
echo "[3/8] 复制代码到飞腾派..."

# 先清理旧代码
run_ssh "rm -rf ~/pq-ntor-experiment"

# 创建目录
run_ssh "mkdir -p ~/pq-ntor-experiment"

# 使用scp复制代码
sshpass -p "$PI_PASS" scp -r -o StrictHostKeyChecking=no \
    /home/ccc/pq-ntor-experiment/* \
    $PI_USER@$PI_IP:~/pq-ntor-experiment/

echo "  ✓ 代码复制完成"

# 第4步：安装依赖
echo ""
echo "[4/8] 检查并安装依赖..."

run_ssh << 'ENDSSH'
    # 检查依赖
    missing_deps=""

    if ! command -v gcc &> /dev/null; then
        missing_deps="$missing_deps gcc"
    fi

    if ! command -v make &> /dev/null; then
        missing_deps="$missing_deps make"
    fi

    if ! pkg-config --exists liboqs 2>/dev/null; then
        missing_deps="$missing_deps liboqs-dev"
    fi

    if [ -n "$missing_deps" ]; then
        echo "  需要安装依赖: $missing_deps"
        echo "  请手动执行: ssh user@192.168.5.110"
        echo "             sudo apt update && sudo apt install -y $missing_deps"
    else
        echo "  ✓ 所有依赖已安装"
    fi
ENDSSH

# 第5步：编译代码
echo ""
echo "[5/8] 编译代码..."

run_ssh << 'ENDSSH'
    cd ~/pq-ntor-experiment/c

    # 清理旧编译
    make clean 2>/dev/null || true

    # 编译
    if make all 2>&1 | tee /tmp/make.log; then
        echo "  ✓ 编译成功"
        ls -lh directory relay benchmark_pq_ntor 2>/dev/null || echo "  警告：部分文件未生成"
    else
        echo "  ✗ 编译失败，查看日志:"
        cat /tmp/make.log
        exit 1
    fi
ENDSSH

# 第6步：编译三跳测试程序
echo ""
echo "[6/8] 编译三跳测试程序..."

run_ssh << 'ENDSSH'
    cd ~/pq-ntor-experiment/last_experiment/phytium_deployment

    if gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread 2>&1; then
        echo "  ✓ 三跳测试程序编译成功"
        ls -lh benchmark_3hop_circuit
    else
        echo "  ✗ 编译失败"
        exit 1
    fi
ENDSSH

# 第7步：运行握手测试
echo ""
echo "[7/8] 运行握手测试..."

run_ssh << 'ENDSSH'
    cd ~/pq-ntor-experiment/c

    if [ -f ./benchmark_pq_ntor ]; then
        echo "  运行10次握手测试..."
        ./benchmark_pq_ntor 10 | tee /tmp/handshake_test.log
    else
        echo "  ✗ benchmark_pq_ntor 不存在"
        exit 1
    fi
ENDSSH

# 第8步：运行完整系统测试
echo ""
echo "[8/8] 运行完整系统测试..."

run_ssh << 'ENDSSH'
    # 清理旧进程
    pkill -f directory 2>/dev/null || true
    pkill -f relay 2>/dev/null || true
    sleep 1

    cd ~/pq-ntor-experiment/c

    # 启动目录服务器
    echo "  启动目录服务器..."
    nohup ./directory 5000 > ~/directory.log 2>&1 &
    sleep 2

    # 启动3个中继
    echo "  启动中继节点..."
    nohup ./relay 6000 guard localhost:5000 > ~/guard.log 2>&1 &
    nohup ./relay 6001 middle localhost:5000 > ~/middle.log 2>&1 &
    nohup ./relay 6002 exit localhost:5000 > ~/exit.log 2>&1 &
    sleep 2

    # 检查进程
    if pgrep -f directory > /dev/null && pgrep -f relay > /dev/null; then
        echo "  ✓ 所有服务已启动"
        echo ""
        echo "  进程列表:"
        pgrep -a directory
        pgrep -a relay
    else
        echo "  ✗ 服务启动失败"
        exit 1
    fi

    echo ""
    echo "  等待5秒后运行三跳测试..."
    sleep 5

    # 运行三跳测试
    cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
    echo "  运行三跳电路测试（5次迭代）..."
    ./benchmark_3hop_circuit 5 localhost 5000 | tee /tmp/3hop_test.log

    # 保存结果
    echo ""
    echo "  测试完成，结果已保存到 /tmp/3hop_test.log"

    # 清理进程
    echo ""
    echo "  清理测试进程..."
    pkill -f directory
    pkill -f relay

    echo "  ✓ 测试进程已清理"
ENDSSH

# 第9步：创建配置脚本
echo ""
echo "[9/9] 创建节点配置脚本..."

run_ssh << 'ENDSSH'
    cat > ~/pq-ntor-experiment/setup_node.sh << 'SETUPEOF'
#!/bin/bash
NODE_ID=$1

if [ -z "$NODE_ID" ] || [ "$NODE_ID" -lt 1 ] || [ "$NODE_ID" -gt 7 ]; then
    echo "用法: sudo $0 <node_id>"
    echo "node_id: 1-7"
    exit 1
fi

BASE_IP="192.168.5"
IP="${BASE_IP}.$((109 + NODE_ID))"

declare -A ROLES
ROLES[1]="client"
ROLES[2]="directory"
ROLES[3]="guard"
ROLES[4]="middle"
ROLES[5]="exit"
ROLES[6]="target"
ROLES[7]="monitor"

ROLE=${ROLES[$NODE_ID]}
HOSTNAME="phytium-pi${NODE_ID}-${ROLE}"

echo "配置飞腾派 #${NODE_ID}"
echo "角色: $ROLE"
echo "IP: $IP"
echo "主机名: $HOSTNAME"

echo "$ROLE" > /home/user/pq-ntor-experiment/.node_role
echo "$NODE_ID" > /home/user/pq-ntor-experiment/.node_id
chown user:user /home/user/pq-ntor-experiment/.node_*

echo "✓ 配置完成"
SETUPEOF

    chmod +x ~/pq-ntor-experiment/setup_node.sh
    echo "  ✓ setup_node.sh 创建成功"
ENDSSH

# 完成
echo ""
echo "======================================================================"
echo "  ✓ 部署完成"
echo "======================================================================"
echo ""
echo "测试结果:"
echo "  - 握手测试: 已运行"
echo "  - 三跳测试: 已运行"
echo "  - 配置脚本: 已创建"
echo ""
echo "查看详细结果:"
echo "  ssh user@${PI_IP} 'cat /tmp/handshake_test.log'"
echo "  ssh user@${PI_IP} 'cat /tmp/3hop_test.log'"
echo ""
echo "下一步:"
echo "  1. 查看测试结果"
echo "  2. 如果成功，准备制作SD卡镜像"
echo "  3. 阅读 SINGLE_PI_TO_7PI_GUIDE.md 了解镜像制作步骤"
