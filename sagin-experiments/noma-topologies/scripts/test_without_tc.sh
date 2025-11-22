#!/bin/bash
##############################################################################
# 简化版测试脚本 - 不使用tc/netem网络模拟
# 适用于无sudo权限的环境
##############################################################################

set -e

TOPO_ID=${1:-1}
NUM_RUNS=${2:-3}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIGS_DIR="$BASE_DIR/configs"
RESULTS_DIR="$BASE_DIR/results"
LOGS_DIR="$BASE_DIR/logs"
PQ_NTOR_DIR="/home/ccc/pq-ntor-experiment/c"

mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

# 查找配置文件
TOPO_ID_PADDED=$(printf "%02d" $TOPO_ID)
CONFIG_FILE=$(ls "$CONFIGS_DIR"/topology_${TOPO_ID_PADDED}_*.json 2>/dev/null | head -n1)

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file for topology $TOPO_ID not found"
    exit 1
fi

TOPO_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['name'])")

echo "=========================================="
echo "  Testing PQ-NTOR (No Network Simulation)"
echo "=========================================="
echo "Topology ID: $TOPO_ID"
echo "Topology Name: $TOPO_NAME"
echo "Number of runs: $NUM_RUNS"
echo "NOTE: Running without tc/netem network simulation"
echo ""

# 检查PQ-NTOR可执行文件
if [ ! -f "$PQ_NTOR_DIR/directory" ] || [ ! -f "$PQ_NTOR_DIR/relay" ] || [ ! -f "$PQ_NTOR_DIR/client" ]; then
    echo "❌ Error: PQ-NTOR executables not found in $PQ_NTOR_DIR"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RAW_RESULTS="$RESULTS_DIR/no_tc_test_topo${TOPO_ID}_${TIMESTAMP}.csv"

echo "topology_id,topology_name,run_id,protocol,start_time,end_time,duration_s,success,exit_code" > "$RAW_RESULTS"

echo "[Step 1/2] Running PQ-NTOR tests (without network simulation)..."
successful_tests=0
failed_tests=0

for run in $(seq 1 $NUM_RUNS); do
    echo -n "  Run $run/$NUM_RUNS: "

    cd "$PQ_NTOR_DIR"

    # 启动directory和relays
    ./directory > "$LOGS_DIR/directory_topo${TOPO_ID}_run${run}.log" 2>&1 &
    DIR_PID=$!
    sleep 1

    ./relay -r guard -p 6001 > "$LOGS_DIR/guard_topo${TOPO_ID}_run${run}.log" 2>&1 &
    GUARD_PID=$!

    ./relay -r middle -p 6002 > "$LOGS_DIR/middle_topo${TOPO_ID}_run${run}.log" 2>&1 &
    MIDDLE_PID=$!

    ./relay -r exit -p 6003 > "$LOGS_DIR/exit_topo${TOPO_ID}_run${run}.log" 2>&1 &
    EXIT_PID=$!

    sleep 2

    # 运行客户端测试
    start_time=$(date +%s.%N)

    if timeout 120 ./client http://127.0.0.1:8000/ > "$LOGS_DIR/client_topo${TOPO_ID}_run${run}.log" 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        success="true"
        exit_code=0
        echo "✅ Success (${duration}s)"
        ((successful_tests++))
    else
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        success="false"
        exit_code=$?
        echo "❌ Failed (exit code: $exit_code)"
        ((failed_tests++))
    fi

    echo "$TOPO_ID,\"$TOPO_NAME\",$run,PQ-NTOR,$start_time,$end_time,$duration,$success,$exit_code" >> "$RAW_RESULTS"

    # 清理进程
    kill $DIR_PID $GUARD_PID $MIDDLE_PID $EXIT_PID 2>/dev/null || true
    sleep 1

    cd - > /dev/null
done

echo ""
echo "[Step 2/2] Test completed"
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Topology: $TOPO_NAME"
echo "Successful: $successful_tests/$NUM_RUNS"
echo "Failed: $failed_tests/$NUM_RUNS"
if [ $NUM_RUNS -gt 0 ]; then
    echo "Success rate: $(echo "scale=2; $successful_tests * 100 / $NUM_RUNS" | bc)%"
fi
echo ""
echo "📊 Results saved to: $RAW_RESULTS"
echo ""
echo "NOTE: This test ran without network simulation (tc/netem)."
echo "For full network simulation, you need sudo permissions."
echo ""
