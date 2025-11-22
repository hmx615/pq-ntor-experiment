#!/bin/bash
##############################################################################
# 实时监控测试进度（每10秒刷新）
##############################################################################

while true; do
    clear
    ./monitor_test_progress.sh
    echo ""
    echo "Auto-refreshing every 10 seconds... (Ctrl+C to stop)"
    sleep 10
done
