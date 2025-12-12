#!/bin/bash
# Phase 3 本地WSL2运行脚本 - 真实网络模拟

set -e

WORK_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
RESULT_DIR="/home/ccc/pq-ntor-experiment/essay/phase3_results_wsl2_$(date +%Y%m%d_%H%M%S)"

echo "========================================================================"
echo "🚀 Phase 3 SAGIN网络集成测试 - WSL2本地运行"
echo "========================================================================"
echo "✅ WSL2内核支持: netem + tbf"
echo "📍 工作目录: $WORK_DIR"
echo "📊 结果保存: $RESULT_DIR"
echo "========================================================================"
echo ""

# 1. 编译Phase 3
echo "🔨 编译Phase 3..."
cd "$WORK_DIR"
make clean 2>/dev/null || true
make phase3_sagin_network

if [ ! -f "./phase3_sagin_network" ]; then
    echo "❌ 编译失败!"
    exit 1
fi

echo "✅ 编译成功!"
ls -lh ./phase3_sagin_network
echo ""

# 2. 检查tc/netem支持
echo "🔍 检查tc/netem支持..."
if ! tc -Version > /dev/null 2>&1; then
    echo "❌ tc工具不可用"
    exit 1
fi

echo "✅ tc工具可用: $(tc -Version 2>&1 | head -1)"
echo ""

# 3. 检查sudo权限
echo "🔑 检查sudo权限..."
if sudo -n tc qdisc show dev lo > /dev/null 2>&1; then
    echo "✅ sudo权限可用（无密码）"
elif sudo tc qdisc show dev lo > /dev/null 2>&1; then
    echo "✅ sudo权限可用（需要密码）"
else
    echo "❌ sudo权限不可用"
    echo "请配置sudo无密码: sudo visudo"
    exit 1
fi
echo ""

# 4. 清理现有tc配置
echo "🧹 清理现有tc配置..."
sudo tc qdisc del dev lo root 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 5. 设置CPU性能模式（如果可用）
echo "⚡ 尝试设置CPU性能模式..."
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo "   使用默认CPU模式"
echo ""

# 6. 运行测试
echo "========================================================================"
echo "🚀 开始Phase 3测试"
echo "========================================================================"
echo "📋 测试配置:"
echo "   - 12个SAGIN拓扑"
echo "   - 2种协议 (Classic NTOR + PQ-NTOR)"
echo "   - 每个20次迭代 + 3次预热"
echo "   - 总计: 480次电路构建测试"
echo ""
echo "⏱️  预计耗时: 10-15分钟"
echo ""
echo "开始测试..."
echo ""

START_TIME=$(date +%s)

sudo ./phase3_sagin_network 2>&1 | tee phase3_output.log

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "========================================================================"
echo "✅ 测试完成!"
echo "========================================================================"
echo "⏱️  实际耗时: $((ELAPSED / 60))分$((ELAPSED % 60))秒 (总计${ELAPSED}秒)"
echo ""

# 7. 清理tc配置
echo "🧹 恢复网络配置..."
sudo tc qdisc del dev lo root 2>/dev/null || true
echo "✅ 网络配置已恢复"
echo ""

# 8. 保存结果
echo "💾 保存结果..."
mkdir -p "$RESULT_DIR"

if [ -f "./phase3_sagin_cbt.csv" ]; then
    cp ./phase3_sagin_cbt.csv "$RESULT_DIR/"
    echo "✅ 已保存: phase3_sagin_cbt.csv"
else
    echo "⚠️  警告: phase3_sagin_cbt.csv 未生成"
fi

if [ -f "./phase3_output.log" ]; then
    cp ./phase3_output.log "$RESULT_DIR/"
    echo "✅ 已保存: phase3_output.log"
fi

# 保存系统信息
echo "📋 保存系统信息..."
{
    echo "=== 系统信息 ==="
    echo "日期: $(date)"
    echo "内核: $(uname -r)"
    echo "CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
    echo "内存: $(free -h | grep Mem | awk '{print $2}')"
    echo ""
    echo "=== tc工具版本 ==="
    tc -Version 2>&1
    echo ""
    echo "=== 内核网络模块支持 ==="
    zcat /proc/config.gz 2>/dev/null | grep -E "(CONFIG_NET_SCH_NETEM|CONFIG_NET_SCH_TBF)" || echo "配置不可访问"
} > "$RESULT_DIR/system_info.txt"

echo "✅ 已保存: system_info.txt"
echo ""

# 9. 快速预览结果
if [ -f "$RESULT_DIR/phase3_sagin_cbt.csv" ]; then
    echo "========================================================================"
    echo "📊 结果预览"
    echo "========================================================================"
    echo ""
    head -7 "$RESULT_DIR/phase3_sagin_cbt.csv"
    echo "... (更多数据请查看完整CSV文件)"
    echo ""

    # 快速统计
    echo "========================================================================"
    echo "📈 快速统计"
    echo "========================================================================"

    CLASSIC_AVG=$(awk -F',' 'NR>1 && $2~/Classic/ {sum+=$3; count++} END {if(count>0) print sum/count; else print "N/A"}' "$RESULT_DIR/phase3_sagin_cbt.csv")
    PQ_AVG=$(awk -F',' 'NR>1 && $2~/PQ/ {sum+=$3; count++} END {if(count>0) print sum/count; else print "N/A"}' "$RESULT_DIR/phase3_sagin_cbt.csv")

    if [ "$CLASSIC_AVG" != "N/A" ] && [ "$PQ_AVG" != "N/A" ]; then
        OVERHEAD=$(echo "scale=2; $PQ_AVG / $CLASSIC_AVG" | bc)
        echo "  平均Classic NTOR CBT: $(printf '%8.2f' $CLASSIC_AVG) ms"
        echo "  平均PQ-NTOR CBT:      $(printf '%8.2f' $PQ_AVG) ms"
        echo "  PQ开销倍数:            $(printf '%8.2f' $OVERHEAD)×"
        echo ""

        # 评估
        if (( $(echo "$OVERHEAD < 1.0" | bc -l) )); then
            echo "  状态: ⚠️  PQ反而更快 (${OVERHEAD}×) - 可能需要检查"
        elif (( $(echo "$OVERHEAD <= 1.5" | bc -l) )); then
            echo "  状态: ✅ PQ开销很小 (${OVERHEAD}×) - 优秀!"
        elif (( $(echo "$OVERHEAD <= 2.5" | bc -l) )); then
            echo "  状态: ✅ PQ开销合理 (${OVERHEAD}×)"
        else
            echo "  状态: ⚠️  PQ开销较大 (${OVERHEAD}×)"
        fi
    fi
    echo ""
fi

echo "========================================================================"
echo "✅ Phase 3 测试完成!"
echo "========================================================================"
echo ""
echo "📁 结果保存在: $RESULT_DIR"
echo ""
echo "🎯 下一步:"
echo "  1. 查看完整结果: cat $RESULT_DIR/phase3_sagin_cbt.csv"
echo "  2. 生成可视化图表: python3 visualize_phase3.py"
echo "  3. 综合分析Phase 1+2+3: python3 comprehensive_analysis.py"
echo "  4. 撰写论文实验章节"
echo ""
echo "========================================================================"
