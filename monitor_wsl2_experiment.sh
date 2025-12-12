#!/bin/bash
# WSL2实验监控脚本

echo "========================================================================"
echo "  WSL2 12拓扑实验监控"
echo "========================================================================"
echo ""

# 检查进程
PID=$(cat /tmp/wsl2_experiment.pid 2>/dev/null)
if [ -n "$PID" ]; then
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 实验进程运行中 (PID: $PID)"
        # 获取Python子进程
        PYTHON_PID=$(ps --ppid $PID -o pid= | tr -d ' ')
        if [ -n "$PYTHON_PID" ]; then
            echo "   Python PID: $PYTHON_PID"
            # CPU和内存使用
            ps -p $PYTHON_PID -o %cpu,%mem,etime,cmd | tail -1
        fi
    else
        echo "❌ 实验进程已结束"
    fi
else
    echo "❌ 未找到PID文件"
fi

echo ""
echo "========================================================================"
echo "📊 结果文件统计"
echo "========================================================================"

RESULTS_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl"

# 统计今天16:54之后的文件（新实验）
NEW_COUNT=$(find "$RESULTS_DIR" -name "topo*_results.json" -newermt "2025-12-11 16:54" | wc -l)
echo "新生成结果: $NEW_COUNT / 12"

if [ $NEW_COUNT -gt 0 ]; then
    echo ""
    echo "最新文件:"
    ls -lht "$RESULTS_DIR"/*.json | head -5
fi

echo ""
echo "========================================================================"
echo "📝 进程日志 (strace)"
echo "========================================================================"

if [ -n "$PYTHON_PID" ]; then
    echo "当前系统调用:"
    timeout 2 strace -p $PYTHON_PID 2>&1 | head -10 || echo "(无法获取strace，可能需要sudo)"
fi

echo ""
echo "========================================================================"
echo "💡 监控命令:"
echo "   watch -n 5 /home/ccc/pq-ntor-experiment/monitor_wsl2_experiment.sh"
echo "========================================================================"
