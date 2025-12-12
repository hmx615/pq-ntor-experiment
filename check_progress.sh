#!/bin/bash
# 快速查看SAGIN实验进度

LOG_FILE="sagin_10iter_test_v2.log"

echo "=============================================="
echo "SAGIN实验进度 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# 检查进程
PID=$(pgrep -f "deploy_sagin_tc_and_test.py 10")
if [ -n "$PID" ]; then
    echo "✅ 测试进程运行中 (PID: $PID)"

    # 计算运行时间
    START_TIME=$(ps -p $PID -o lstart=)
    echo "   开始时间: $START_TIME"
else
    echo "❌ 测试进程未运行"
fi

echo ""
echo "已完成的拓扑:"
echo "----------------------------------------------"
grep -E "成功率: [0-9]+\.[0-9]+%" $LOG_FILE | nl -w2 -s'. '

echo ""
echo "当前正在测试:"
echo "----------------------------------------------"
tail -10 $LOG_FILE | grep -E "\[拓扑|应用TC|运行PQ-NTOR|进度:" | tail -3

echo ""
echo "预计完成时间:"
echo "----------------------------------------------"
COMPLETED=$(grep -c "成功率: [0-9]" $LOG_FILE)
if [ $COMPLETED -gt 0 ]; then
    echo "   已完成: $COMPLETED/12 拓扑 ($(echo "scale=1; $COMPLETED * 100 / 12" | bc)%)"

    # 估算剩余时间 (每个拓扑约9.5分钟)
    REMAINING=$((12 - COMPLETED))
    MINUTES=$((REMAINING * 10))
    echo "   预计剩余: ~$MINUTES 分钟"
else
    echo "   计算中..."
fi

echo ""
echo "=============================================="
