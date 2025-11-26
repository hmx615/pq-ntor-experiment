#!/bin/bash

# ========================================
# 飞腾派部署脚本 - Classic+PQ双模式
# ========================================

set -e

# 配置
PHYTIUM_IP="192.168.5.110"
PHYTIUM_USER="user"
PROJECT_ROOT="/home/ccc/pq-ntor-experiment"
REMOTE_DIR="/home/${PHYTIUM_USER}/pq-ntor-experiment"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          飞腾派Classic+PQ双模式部署脚本                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "目标设备: ${PHYTIUM_IP}"
echo "用户名: ${PHYTIUM_USER}"
echo "项目路径: ${REMOTE_DIR}"
echo ""

# 步骤1: 检查飞腾派连接
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤1: 检查飞腾派连接"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ssh -o ConnectTimeout=5 ${PHYTIUM_USER}@${PHYTIUM_IP} "echo '连接成功'" 2>/dev/null; then
    echo "✅ 飞腾派连接正常"
else
    echo "❌ 无法连接到飞腾派 ${PHYTIUM_IP}"
    echo "请检查:"
    echo "  1. 飞腾派是否开机"
    echo "  2. 网络是否连通 (ping ${PHYTIUM_IP})"
    echo "  3. SSH服务是否运行"
    exit 1
fi
echo ""

# 步骤2: 检查飞腾派环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤2: 检查飞腾派环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} << 'ENDSSH'
echo "检查系统架构..."
uname -m
echo ""

echo "检查GCC版本..."
gcc --version | head -1
echo ""

echo "检查liboqs安装..."
if [ -d "$HOME/_oqs" ]; then
    echo "✅ liboqs 已安装: $HOME/_oqs"
    ls -lh $HOME/_oqs/lib/liboqs.so* 2>/dev/null || echo "⚠️ liboqs库文件未找到"
else
    echo "❌ liboqs 未安装"
    echo "请先运行: ./install_liboqs_arm.sh"
    exit 1
fi
echo ""

echo "检查OpenSSL..."
openssl version
echo ""
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 飞腾派环境检查失败"
    exit 1
fi
echo "✅ 飞腾派环境检查通过"
echo ""

# 步骤3: 创建远程目录结构
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤3: 创建远程目录结构"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} << ENDSSH
mkdir -p ${REMOTE_DIR}/c/src
mkdir -p ${REMOTE_DIR}/c/programs
mkdir -p ${REMOTE_DIR}/c/tests
mkdir -p ${REMOTE_DIR}/c/benchmark
mkdir -p ${REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/scripts
mkdir -p ${REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi
mkdir -p ${REMOTE_DIR}/sagin-experiments/noma-topologies/configs
ENDSSH
echo "✅ 目录结构创建完成"
echo ""

# 步骤4: 复制C源代码
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤4: 复制C源代码（包含Classic模式）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "复制核心源文件..."
scp ${PROJECT_ROOT}/c/src/*.c ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/src/
scp ${PROJECT_ROOT}/c/src/*.h ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/src/

echo "复制程序主文件..."
scp ${PROJECT_ROOT}/c/programs/*.c ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/programs/

echo "复制测试文件..."
scp ${PROJECT_ROOT}/c/tests/*.c ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/tests/

echo "复制benchmark文件..."
scp ${PROJECT_ROOT}/c/benchmark/*.c ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/benchmark/

echo "复制Makefile..."
scp ${PROJECT_ROOT}/c/Makefile ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/c/

echo "✅ C源代码复制完成"
echo ""

# 步骤5: 复制测试脚本和配置
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤5: 复制测试脚本和拓扑配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "复制测试脚本..."
scp ${PROJECT_ROOT}/sagin-experiments/pq-ntor-12topo-experiment/scripts/run_pq_ntor_12topologies.py \
    ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/scripts/

echo "复制拓扑配置..."
scp ${PROJECT_ROOT}/sagin-experiments/noma-topologies/configs/topology_*.json \
    ${PHYTIUM_USER}@${PHYTIUM_IP}:${REMOTE_DIR}/sagin-experiments/noma-topologies/configs/

echo "✅ 脚本和配置复制完成"
echo ""

# 步骤6: 在飞腾派上编译
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤6: 在飞腾派上编译Classic+PQ双模式"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} << ENDSSH
cd ${REMOTE_DIR}/c

echo "清理旧编译文件..."
make clean

echo ""
echo "开始编译（ARM架构）..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
make all

echo ""
echo "检查编译结果..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f directory ] && [ -f relay ] && [ -f client ]; then
    echo "✅ 核心程序编译成功:"
    ls -lh directory relay client
    echo ""
    echo "✅ 测试程序:"
    ls -lh test_* 2>/dev/null || echo "⚠️ 部分测试程序未编译"
    echo ""
    echo "✅ Benchmark程序:"
    ls -lh benchmark_* 2>/dev/null || echo "⚠️ Benchmark程序未编译"
else
    echo "❌ 编译失败，缺少核心程序"
    exit 1
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 编译失败"
    exit 1
fi
echo "✅ 编译完成"
echo ""

# 步骤7: 运行基础测试
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤7: 运行基础功能测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} << 'ENDSSH'
cd /home/user/pq-ntor-experiment/c

echo "测试1: Classic NTOR算法..."
if ./test_classic_ntor 2>&1 | grep -q "SUCCESS"; then
    echo "✅ Classic NTOR测试通过"
else
    echo "⚠️ Classic NTOR测试失败"
fi
echo ""

echo "测试2: PQ-NTOR算法..."
if ./test_pq_ntor 2>&1 | grep -q "SUCCESS"; then
    echo "✅ PQ-NTOR测试通过"
else
    echo "⚠️ PQ-NTOR测试失败"
fi
echo ""

echo "测试3: 客户端程序..."
if ./client --help 2>&1 | grep -q "mode"; then
    echo "✅ 客户端支持--mode参数"
else
    echo "⚠️ 客户端可能不支持--mode参数"
fi
ENDSSH
echo ""

# 步骤8: 运行性能基准测试
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤8: 运行ARM性能基准测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} << 'ENDSSH'
cd /home/user/pq-ntor-experiment/c

echo "运行benchmark_pq_ntor..."
if [ -f benchmark_pq_ntor ]; then
    ./benchmark_pq_ntor | tee benchmark_arm_results.txt
    echo ""
    echo "✅ Benchmark结果已保存到: benchmark_arm_results.txt"
else
    echo "⚠️ benchmark_pq_ntor未编译"
fi
ENDSSH
echo ""

# 完成
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          ✅ 飞腾派部署完成！                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "已部署内容:"
echo "  ✓ C源代码（包含Classic NTOR）"
echo "  ✓ 编译后的程序（directory, relay, client）"
echo "  ✓ 测试程序（test_classic_ntor, test_pq_ntor）"
echo "  ✓ Benchmark程序"
echo "  ✓ 12拓扑测试脚本"
echo ""
echo "下一步操作:"
echo "  1. SSH登录飞腾派:"
echo "     ssh ${PHYTIUM_USER}@${PHYTIUM_IP}"
echo ""
echo "  2. 运行12拓扑Classic测试:"
echo "     cd ${REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/scripts"
echo "     python3 run_pq_ntor_12topologies.py --mode classic --runs 10"
echo ""
echo "  3. 运行12拓扑PQ测试:"
echo "     python3 run_pq_ntor_12topologies.py --mode pq --runs 10"
echo ""
echo "  4. 查看benchmark结果:"
echo "     cat ${REMOTE_DIR}/c/benchmark_arm_results.txt"
echo ""
