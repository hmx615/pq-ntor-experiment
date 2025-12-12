#!/bin/bash
# 12拓扑实验实时监控脚本

echo "========================================"
echo "  12拓扑实验监控"
echo "========================================"
echo ""

# 检查进程
PID=$(cat /tmp/12topo_experiment.pid 2>/dev/null)
if [ -n "$PID" ] && ps -p $PID > /dev/null 2>&1; then
    echo "✅ 实验进程运行中 (PID: $PID)"
    echo ""
else
    echo "❌ 实验进程未运行"
    echo ""
    exit 1
fi

# 检查结果文件
RESULTS_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl"
echo "📊 已完成的拓扑:"
ls -1 "$RESULTS_DIR"/*.json 2>/dev/null | while read file; do
    topo=$(basename "$file" | grep -oP 'topo\d+')
    success_count=$(jq -r '.summary.success_count' "$file" 2>/dev/null || echo "0")
    total=$(jq -r '.summary.total_runs' "$file" 2>/dev/null || echo "?")
    echo "  $topo: $success_count/$total 成功"
done

echo ""
echo "📁 结果文件数: $(ls -1 "$RESULTS_DIR"/*.json 2>/dev/null | wc -l)/24 (12拓扑 × 2算法)"
echo ""

# 显示最新日志
if [ -f /tmp/12topo_full_experiment.log ]; then
    LINES=$(wc -l < /tmp/12topo_full_experiment.log)
    if [ $LINES -gt 0 ]; then
        echo "📝 最新日志 (最后20行):"
        echo "----------------------------------------"
        tail -20 /tmp/12topo_full_experiment.log
    else
        echo "⏳ 日志文件为空 (输出可能被缓冲)"
    fi
else
    echo "⚠️  日志文件不存在"
fi

echo ""
echo "========================================"
echo "监控命令:"
echo "  watch -n 5 ./monitor_experiment.sh"
echo "  tail -f /tmp/12topo_full_experiment.log"
echo "========================================"
