#!/bin/bash
##############################################################################
# 实时监控测试进度
##############################################################################

LOGS_DIR="../logs"
RESULTS_DIR="../results"

echo "========================================"
echo "  Test Progress Monitor"
echo "========================================"
echo ""

# 查找最新的结果文件
LATEST_RESULT=$(ls -t "$RESULTS_DIR"/raw_results_*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_RESULT" ]; then
    echo "No test results found yet."
    exit 0
fi

echo "Latest result file: $(basename "$LATEST_RESULT")"
echo ""

# 统计已完成的测试
TOTAL_TESTS=$(wc -l < "$LATEST_RESULT")
TOTAL_TESTS=$((TOTAL_TESTS - 1))  # 减去表头

if [ $TOTAL_TESTS -eq 0 ]; then
    echo "No tests completed yet."
    exit 0
fi

# 统计成功和失败
SUCCESSFUL=$(grep -c ",true," "$LATEST_RESULT" || echo "0")
FAILED=$(grep -c ",false," "$LATEST_RESULT" || echo "0")

echo "Tests completed: $TOTAL_TESTS / 120"
echo "Successful: $SUCCESSFUL"
echo "Failed: $FAILED"
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $SUCCESSFUL * 100 / $TOTAL_TESTS" | bc)
    echo "Success rate: ${SUCCESS_RATE}%"
fi
echo ""

# 显示平均时间
if [ $SUCCESSFUL -gt 0 ]; then
    AVG_TIME=$(awk -F',' 'NR>1 && $8=="true" {sum+=$7; count++} END {if(count>0) printf "%.2f", sum/count}' "$LATEST_RESULT")
    echo "Average circuit setup time: ${AVG_TIME}s"
fi

echo ""
echo "========================================"
echo "Progress: [$(printf '%*s' $((TOTAL_TESTS * 40 / 120)) '' | tr ' ' '=')$(printf '%*s' $((40 - TOTAL_TESTS * 40 / 120)) '' | tr ' ' '-')]"
echo "========================================"
echo ""
echo "Press Ctrl+C to exit monitor (test continues in background)"
