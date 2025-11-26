#!/bin/bash
#
# 监控PQ-NTOR测试进度
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results/local_wsl"
LOGS_DIR="$SCRIPT_DIR/../logs"

clear
echo "=========================================="
echo "  📊 PQ-NTOR测试进度监控"
echo "=========================================="
echo ""

# 检查是否有测试在运行
if pgrep -f "run_pq_ntor_12topologies.py" > /dev/null; then
    echo "✅ 测试正在运行中..."
    echo ""
else
    echo "⚠️  未检测到运行中的测试"
    echo ""
fi

# 统计已完成的拓扑
echo "📂 已完成的拓扑结果:"
echo "----------------------------------------"
completed=0
for i in {01..12}; do
    result_file="$RESULTS_DIR/topo${i}_results.json"
    if [ -f "$result_file" ]; then
        # 提取成功率
        if command -v jq &> /dev/null; then
            success_rate=$(jq -r '.summary.success_rate' "$result_file" 2>/dev/null || echo "N/A")
            total_runs=$(jq -r '.summary.total_runs' "$result_file" 2>/dev/null || echo "?")
            echo "  ✅ 拓扑 $i: 成功率 ${success_rate}% ($total_runs 次运行)"
        else
            echo "  ✅ 拓扑 $i: 已完成"
        fi
        ((completed++))
    fi
done

if [ $completed -eq 0 ]; then
    echo "  (暂无完成的拓扑)"
fi

echo ""
echo "进度: $completed / 12 拓扑完成"
echo ""

# 显示最新日志（最后10行）
echo "📋 最新测试日志 (最后10行):"
echo "----------------------------------------"
if [ -f "$LOGS_DIR/full_test_run.log" ]; then
    tail -10 "$LOGS_DIR/full_test_run.log"
else
    echo "  (暂无日志文件)"
fi

echo ""
echo "=========================================="
echo "持续监控: watch -n 5 $0"
echo "查看完整日志: tail -f $LOGS_DIR/full_test_run.log"
echo "=========================================="
