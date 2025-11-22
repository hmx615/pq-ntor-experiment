#!/bin/bash
##############################################################################
# 自动化测试所有12种NOMA拓扑
# 对每个拓扑运行多次测试，收集性能数据
##############################################################################

set -e

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIGS_DIR="$BASE_DIR/configs"
RESULTS_DIR="$BASE_DIR/results"
LOGS_DIR="$BASE_DIR/logs"
NUM_RUNS=10  # 每个拓扑测试10次 (可调整)
PQ_NTOR_DIR="/home/ccc/pq-ntor-experiment/c"

# 创建目录
mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

# 结果文件
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RAW_RESULTS="$RESULTS_DIR/raw_results_${TIMESTAMP}.csv"
SUMMARY_RESULTS="$RESULTS_DIR/summary_${TIMESTAMP}.csv"

# CSV表头
echo "topology_id,topology_name,run_id,protocol,start_time,end_time,duration_s,success,exit_code" > "$RAW_RESULTS"

echo "=========================================="
echo "  NOMA Topology Automated Testing"
echo "=========================================="
echo "Configs directory: $CONFIGS_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Number of runs per topology: $NUM_RUNS"
echo "Timestamp: $TIMESTAMP"
echo ""

# 检查PQ-NTOR可执行文件
if [ ! -f "$PQ_NTOR_DIR/directory" ] || [ ! -f "$PQ_NTOR_DIR/relay" ] || [ ! -f "$PQ_NTOR_DIR/client" ]; then
    echo "❌ Error: PQ-NTOR executables not found in $PQ_NTOR_DIR"
    echo "   Please compile first: cd $PQ_NTOR_DIR && make all"
    exit 1
fi

# 遍历所有拓扑配置
total_tests=0
successful_tests=0
failed_tests=0

for topo_id in {1..12}; do
    # 查找配置文件 (使用两位数格式 01, 02, ...)
    topo_id_padded=$(printf "%02d" $topo_id)
    config_file=$(ls "$CONFIGS_DIR"/topology_${topo_id_padded}_*.json 2>/dev/null | head -n1)

    if [ ! -f "$config_file" ]; then
        echo "⚠️  Warning: Config for topology $topo_id not found, skipping..."
        continue
    fi

    # 提取拓扑名称（使用Python，不依赖jq）
    topo_name=$(python3 -c "import json; print(json.load(open('$config_file'))['name'])")

    echo ""
    echo "=========================================="
    echo "Testing Topology $topo_id: $topo_name"
    echo "=========================================="

    # 配置网络参数 (优先使用Python版本，不依赖jq)
    echo "[Step 1/4] Configuring network parameters..."
    if command -v jq &> /dev/null; then
        ./configure_topology.sh "$config_file" > "$LOGS_DIR/config_topo${topo_id}.log" 2>&1
    else
        python3 ./configure_topology.py "$config_file" > "$LOGS_DIR/config_topo${topo_id}.log" 2>&1
    fi

    # 运行多次测试
    for run in $(seq 1 $NUM_RUNS); do
        echo -n "  Run $run/$NUM_RUNS: "

        # 启动Tor网络
        echo -n "Starting Tor network... "
        cd "$PQ_NTOR_DIR"

        # 启动directory和relays (后台运行)
        ./directory > "$LOGS_DIR/directory_topo${topo_id}_run${run}.log" 2>&1 &
        DIR_PID=$!
        sleep 1

        ./relay -r guard -p 6001 > "$LOGS_DIR/guard_topo${topo_id}_run${run}.log" 2>&1 &
        GUARD_PID=$!

        ./relay -r middle -p 6002 > "$LOGS_DIR/middle_topo${topo_id}_run${run}.log" 2>&1 &
        MIDDLE_PID=$!

        ./relay -r exit -p 6003 > "$LOGS_DIR/exit_topo${topo_id}_run${run}.log" 2>&1 &
        EXIT_PID=$!

        sleep 2  # 等待节点启动

        # 运行客户端测试
        echo -n "Testing... "
        start_time=$(date +%s.%N)

        if timeout 120 ./client http://127.0.0.1:8000/ > "$LOGS_DIR/client_topo${topo_id}_run${run}.log" 2>&1; then
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

        ((total_tests++))

        # 清理进程
        kill $DIR_PID $GUARD_PID $MIDDLE_PID $EXIT_PID 2>/dev/null || true
        sleep 1

        # 切换回脚本目录
        cd - > /dev/null

        # 记录结果（在切换回脚本目录后）
        echo "$topo_id,\"$topo_name\",$run,PQ-NTOR,$start_time,$end_time,$duration,$success,$exit_code" >> "$RAW_RESULTS"
    done

    # 清理网络配置
    echo "[Step 4/4] Cleaning up network configuration..."
    sudo tc qdisc del dev lo root 2>/dev/null || true

    echo "✅ Topology $topo_id completed: $successful_tests/$NUM_RUNS successful"
done

echo ""
echo "=========================================="
echo "  Testing Summary"
echo "=========================================="
echo "Total tests run: $total_tests"
echo "Successful: $successful_tests"
echo "Failed: $failed_tests"
echo "Success rate: $(echo "scale=2; $successful_tests * 100 / $total_tests" | bc)%"
echo ""
echo "📊 Raw results saved to: $RAW_RESULTS"
echo ""
echo "Next step: Run analysis script to generate summary and plots"
echo "  python3 analyze_noma_results.py $RAW_RESULTS"
echo ""
