#!/bin/bash
# 监控SAGIN测试进度

echo "SAGIN实验进度监控"
echo "================="
echo ""

# 检查主进程
MAIN_PID=$(pgrep -f "deploy_sagin_tc_and_test.py 10")
if [ -n "$MAIN_PID" ]; then
    echo "✅ 主测试进程运行中 (PID: $MAIN_PID)"
else
    echo "❌ 主测试进程未运行"
fi

echo ""
echo "最新日志 (最后20行):"
echo "-------------------"
tail -20 sagin_10iter_test.log

echo ""
echo "-------------------"
echo "结果文件:"
if [ -f "sagin_pq_ntor_results.csv" ]; then
    echo "✅ sagin_pq_ntor_results.csv 已生成"
    wc -l sagin_pq_ntor_results.csv
else
    echo "⏳ sagin_pq_ntor_results.csv 尚未生成"
fi

echo ""
echo "持续监控命令:"
echo "  watch -n 5 ./monitor_test.sh"
echo "  tail -f sagin_10iter_test.log"
