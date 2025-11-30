#!/bin/bash
# 飞腾派部署脚本
# 使用方法: 在WSL上运行此脚本自动部署到飞腾派

set -e

# 配置
PHYTIUM_IP="192.168.5.110"
PHYTIUM_USER="user"
PHYTIUM_PASS="user"
REMOTE_DIR="/home/user/pq-ntor-test"

echo "======================================"
echo "  PQ-NTOR测试脚本 - 飞腾派部署工具"
echo "======================================"
echo ""

# 检查sshpass
if ! command -v sshpass &> /dev/null; then
    echo "警告: sshpass未安装，使用交互式SSH"
    echo "提示: 密码是 'user'"
    USE_SSHPASS=false
else
    USE_SSHPASS=true
fi

# SSH命令前缀
if [ "$USE_SSHPASS" = true ]; then
    SSH_CMD="sshpass -p $PHYTIUM_PASS ssh -o StrictHostKeyChecking=no"
    SCP_CMD="sshpass -p $PHYTIUM_PASS scp -o StrictHostKeyChecking=no"
else
    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    SCP_CMD="scp -o StrictHostKeyChecking=no"
fi

echo "步骤 1/5: 测试飞腾派连接..."
if $SSH_CMD $PHYTIUM_USER@$PHYTIUM_IP "echo '连接成功'"; then
    echo "✓ 飞腾派连接成功"
else
    echo "✗ 无法连接到飞腾派 $PHYTIUM_IP"
    exit 1
fi

echo ""
echo "步骤 2/5: 检查飞腾派环境..."
$SSH_CMD $PHYTIUM_USER@$PHYTIUM_IP "uname -m && python3 --version"

echo ""
echo "步骤 3/5: 创建远程目录..."
$SSH_CMD $PHYTIUM_USER@$PHYTIUM_IP "mkdir -p $REMOTE_DIR"

echo ""
echo "步骤 4/5: 复制测试文件..."
$SCP_CMD test_pq_ntor_single_machine.py $PHYTIUM_USER@$PHYTIUM_IP:$REMOTE_DIR/
$SCP_CMD topology_tc_params.json $PHYTIUM_USER@$PHYTIUM_IP:$REMOTE_DIR/

# 复制benchmark程序
if [ -f "../../c/benchmark_pq_ntor" ]; then
    echo "发现benchmark程序，复制中..."
    $SCP_CMD ../../c/benchmark_pq_ntor $PHYTIUM_USER@$PHYTIUM_IP:$REMOTE_DIR/
else
    echo "警告: benchmark_pq_ntor未找到，需要在飞腾派上编译"
fi

echo ""
echo "步骤 5/5: 验证部署..."
$SSH_CMD $PHYTIUM_USER@$PHYTIUM_IP "ls -lh $REMOTE_DIR"

echo ""
echo "======================================"
echo "✓ 部署完成！"
echo "======================================"
echo ""
echo "下一步操作:"
echo ""
echo "1. SSH登录到飞腾派:"
echo "   ssh user@192.168.5.110  (密码: user)"
echo ""
echo "2. 进入测试目录:"
echo "   cd $REMOTE_DIR"
echo ""
echo "3. 如果需要编译benchmark程序:"
echo "   # 复制整个c目录并编译"
echo "   # 或者从WSL复制已编译的程序"
echo ""
echo "4. 运行测试:"
echo "   python3 test_pq_ntor_single_machine.py"
echo ""
echo "5. 查看结果:"
echo "   cat results/performance_summary.csv"
echo ""
