#!/bin/bash
#
# 快速测试脚本 - 验证PQ-NTOR 12拓扑实验框架
# 只测试拓扑1，运行3次，快速验证整体流程
#

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  🚀 PQ-NTOR快速测试"
echo "=========================================="
echo "测试范围: 拓扑1"
echo "运行次数: 3"
echo ""

# 检查依赖
echo "🔍 检查依赖..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到python3"
    exit 1
fi
echo "  ✅ Python3: $(python3 --version)"

# 检查sudo权限
if ! sudo -n tc qdisc show dev lo &> /dev/null; then
    echo "⚠️  需要sudo权限配置tc"
    echo "   请运行: sudo visudo"
    echo "   添加: $USER ALL=(ALL) NOPASSWD: /sbin/tc"
    exit 1
fi
echo "  ✅ Sudo权限: 已配置"

# 检查PQ-NTOR可执行文件
PQ_NTOR_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
for prog in directory relay client; do
    if [ ! -x "$PQ_NTOR_DIR/$prog" ]; then
        echo "❌ PQ-NTOR可执行文件不存在: $prog"
        echo "   请先编译: cd $PQ_NTOR_DIR && make"
        exit 1
    fi
done
echo "  ✅ PQ-NTOR可执行文件: 已就绪"

# 清理之前的进程
echo ""
echo "🧹 清理残留进程..."
pkill -9 directory 2>/dev/null || true
pkill -9 relay 2>/dev/null || true
pkill -9 client 2>/dev/null || true
sudo tc qdisc del dev lo root 2>/dev/null || true
sleep 1
echo "  ✅ 清理完成"

# 运行快速测试
echo ""
echo "▶️  开始快速测试..."
echo "=========================================="
echo ""

python3 ./run_pq_ntor_12topologies.py --topo 1 --runs 3

echo ""
echo "=========================================="
echo "✅ 快速测试完成!"
echo "=========================================="
echo ""
echo "📊 查看结果:"
echo "  日志: $SCRIPT_DIR/../logs/"
echo "  结果: $SCRIPT_DIR/../results/local_wsl/topo01_results.json"
echo ""
echo "🚀 运行完整测试:"
echo "  python3 ./run_pq_ntor_12topologies.py --quick"
echo "  python3 ./run_pq_ntor_12topologies.py  # 完整测试(每个拓扑10次)"
echo ""
