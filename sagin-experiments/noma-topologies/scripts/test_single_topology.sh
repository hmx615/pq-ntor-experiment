#!/bin/bash
##############################################################################
# 测试单个NOMA拓扑
# 用于快速验证或单独测试某个特定拓扑
##############################################################################

set -e

# 配置参数
TOPO_ID=${1:-1}  # 默认测试拓扑1
NUM_RUNS=${2:-3}  # 默认3次测试（快速验证）
CONFIGS_DIR="../configs"
RESULTS_DIR="../results"
LOGS_DIR="../logs"
PQ_NTOR_DIR="/home/ccc/pq-ntor-experiment/c"

# 创建目录
mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

# 查找配置文件 (使用两位数格式 01, 02, ...)
TOPO_ID_PADDED=$(printf "%02d" $TOPO_ID)
CONFIG_FILE=$(ls "$CONFIGS_DIR"/topology_${TOPO_ID_PADDED}_*.json 2>/dev/null | head -n1)

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file for topology $TOPO_ID not found"
    exit 1
fi

# 提取拓扑名称（使用Python，不依赖jq）
TOPO_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['name'])")

echo "=========================================="
echo "  Testing Single Topology"
echo "=========================================="
echo "Topology ID: $TOPO_ID"
echo "Topology Name: $TOPO_NAME"
echo "Number of runs: $NUM_RUNS"
echo "Config file: $CONFIG_FILE"
echo ""

# 检查PQ-NTOR可执行文件
if [ ! -f "$PQ_NTOR_DIR/directory" ] || [ ! -f "$PQ_NTOR_DIR/relay" ] || [ ! -f "$PQ_NTOR_DIR/client" ]; then
    echo "❌ Error: PQ-NTOR executables not found in $PQ_NTOR_DIR"
    echo "   Please compile first: cd $PQ_NTOR_DIR && make all"
    exit 1
fi

# 结果文件
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RAW_RESULTS="$RESULTS_DIR/single_test_topo${TOPO_ID}_${TIMESTAMP}.csv"

# CSV表头
echo "topology_id,topology_name,run_id,protocol,start_time,end_time,duration_s,success,exit_code" > "$RAW_RESULTS"

# 配置网络参数
echo "[Step 1/3] Configuring network parameters..."
if command -v jq &> /dev/null; then
    # 如果有jq，使用bash版本
    ./configure_topology.sh "$CONFIG_FILE" > "$LOGS_DIR/config_topo${TOPO_ID}.log" 2>&1
else
    # 否则使用Python版本
    python3 ./configure_topology.py "$CONFIG_FILE" > "$LOGS_DIR/config_topo${TOPO_ID}.log" 2>&1
fi

# 运行测试
echo "[Step 2/3] Running tests..."
successful_tests=0
failed_tests=0

for run in $(seq 1 $NUM_RUNS); do
    echo -n "  Run $run/$NUM_RUNS: "

    # 启动Tor网络
    echo -n "Starting Tor... "
    cd "$PQ_NTOR_DIR"

    # 启动directory和relays (后台运行)
    ./directory > "$LOGS_DIR/directory_topo${TOPO_ID}_run${run}.log" 2>&1 &
    DIR_PID=$!
    sleep 1

    ./relay -r guard -p 6001 > "$LOGS_DIR/guard_topo${TOPO_ID}_run${run}.log" 2>&1 &
    GUARD_PID=$!

    ./relay -r middle -p 6002 > "$LOGS_DIR/middle_topo${TOPO_ID}_run${run}.log" 2>&1 &
    MIDDLE_PID=$!

    ./relay -r exit -p 6003 > "$LOGS_DIR/exit_topo${TOPO_ID}_run${run}.log" 2>&1 &
    EXIT_PID=$!

    sleep 2  # 等待节点启动

    # 运行客户端测试
    echo -n "Testing... "
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

    # 记录结果
    echo "$TOPO_ID,\"$TOPO_NAME\",$run,PQ-NTOR,$start_time,$end_time,$duration,$success,$exit_code" >> "$RAW_RESULTS"

    # 清理进程
    kill $DIR_PID $GUARD_PID $MIDDLE_PID $EXIT_PID 2>/dev/null || true
    sleep 1

    # 切换回脚本目录
    cd - > /dev/null
done

# 清理网络配置
echo "[Step 3/3] Cleaning up network configuration..."
sudo tc qdisc del dev lo root 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Topology: $TOPO_NAME"
echo "Successful: $successful_tests/$NUM_RUNS"
echo "Failed: $failed_tests/$NUM_RUNS"
echo "Success rate: $(echo "scale=2; $successful_tests * 100 / $NUM_RUNS" | bc)%"
echo ""
echo "📊 Results saved to: $RAW_RESULTS"
echo ""

if [ $successful_tests -gt 0 ]; then
    echo "Next step: Analyze results"
    echo "  python3 analyze_noma_results.py $RAW_RESULTS"
    echo ""
fi
