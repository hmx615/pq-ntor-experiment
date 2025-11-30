#!/bin/bash
# start_all.sh - 启动所有节点服务
# 使用方法: ./start_all.sh

set -e

USER="user"

# 节点IP
DIR_IP="192.168.5.111"
GUARD_IP="192.168.5.112"
MIDDLE_IP="192.168.5.113"
EXIT_IP="192.168.5.114"
TARGET_IP="192.168.5.115"
MONITOR_IP="192.168.5.116"

echo "======================================================================"
echo "  启动PQ-NTOR分布式系统"
echo "======================================================================"
echo ""

# 清理旧进程
echo "[0/6] 清理旧进程..."
for ip in $DIR_IP $GUARD_IP $MIDDLE_IP $EXIT_IP $TARGET_IP $MONITOR_IP; do
    ssh $USER@$ip "pkill -f 'directory|relay|http.server|monitor' 2>/dev/null || true"
done
sleep 1

# 第1步：启动目录服务器
echo "[1/6] 启动目录服务器 ($DIR_IP:5000) ..."
ssh $USER@$DIR_IP << 'ENDSSH'
    cd ~/pq-ntor-experiment/c
    nohup ./directory 5000 > ~/directory.log 2>&1 &
    echo $! > ~/directory.pid
    sleep 1
    if pgrep -f "./directory 5000" > /dev/null; then
        echo "  ✓ 目录服务器已启动 (PID: $(cat ~/directory.pid))"
    else
        echo "  ✗ 目录服务器启动失败"
        exit 1
    fi
ENDSSH

sleep 2

# 第2步：启动Guard中继
echo "[2/6] 启动Guard中继 ($GUARD_IP:6000) ..."
ssh $USER@$GUARD_IP << ENDSSH
    cd ~/pq-ntor-experiment/c
    nohup ./relay 6000 guard $DIR_IP:5000 > ~/guard.log 2>&1 &
    echo \$! > ~/guard.pid
    sleep 1
    if pgrep -f "./relay 6000" > /dev/null; then
        echo "  ✓ Guard中继已启动 (PID: \$(cat ~/guard.pid))"
    else
        echo "  ✗ Guard启动失败"
        exit 1
    fi
ENDSSH

sleep 1

# 第3步：启动Middle中继
echo "[3/6] 启动Middle中继 ($MIDDLE_IP:6001) ..."
ssh $USER@$MIDDLE_IP << ENDSSH
    cd ~/pq-ntor-experiment/c
    nohup ./relay 6001 middle $DIR_IP:5000 > ~/middle.log 2>&1 &
    echo \$! > ~/middle.pid
    sleep 1
    if pgrep -f "./relay 6001" > /dev/null; then
        echo "  ✓ Middle中继已启动 (PID: \$(cat ~/middle.pid))"
    else
        echo "  ✗ Middle启动失败"
        exit 1
    fi
ENDSSH

sleep 1

# 第4步：启动Exit中继
echo "[4/6] 启动Exit中继 ($EXIT_IP:6002) ..."
ssh $USER@$EXIT_IP << ENDSSH
    cd ~/pq-ntor-experiment/c
    nohup ./relay 6002 exit $DIR_IP:5000 > ~/exit.log 2>&1 &
    echo \$! > ~/exit.pid
    sleep 1
    if pgrep -f "./relay 6002" > /dev/null; then
        echo "  ✓ Exit中继已启动 (PID: \$(cat ~/exit.pid))"
    else
        echo "  ✗ Exit启动失败"
        exit 1
    fi
ENDSSH

sleep 1

# 第5步：启动目标服务器
echo "[5/6] 启动目标HTTP服务器 ($TARGET_IP:8080) ..."
ssh $USER@$TARGET_IP << 'ENDSSH'
    cd ~
    nohup python3 -m http.server 8080 > ~/http.log 2>&1 &
    echo $! > ~/http.pid
    sleep 1
    if pgrep -f "http.server 8080" > /dev/null; then
        echo "  ✓ HTTP服务器已启动 (PID: $(cat ~/http.pid))"
    else
        echo "  ✗ HTTP服务器启动失败"
        exit 1
    fi
ENDSSH

sleep 1

# 第6步：启动监控节点
echo "[6/6] 启动监控系统 ($MONITOR_IP:9000) ..."
ssh $USER@$MONITOR_IP << 'ENDSSH'
    cd ~/pq-ntor-experiment/scripts
    if [ -f ./monitor_system.py ]; then
        nohup python3 ./monitor_system.py > ~/monitor.log 2>&1 &
        echo $! > ~/monitor.pid
        echo "  ✓ 监控系统已启动 (PID: $(cat ~/monitor.pid))"
    else
        echo "  ⚠ monitor_system.py不存在，跳过监控启动"
    fi
ENDSSH

sleep 2

echo ""
echo "======================================================================"
echo "  系统状态检查"
echo "======================================================================"
echo ""

# 检查所有服务状态
printf "%-15s %-15s %-10s %-10s\n" "节点" "IP地址" "端口" "状态"
echo "----------------------------------------------------------------------"

# 目录服务器
if ssh $USER@$DIR_IP "pgrep -f './directory 5000' > /dev/null"; then
    printf "%-15s %-15s %-10s %-10s\n" "目录服务器" "$DIR_IP" "5000" "✓ 运行中"
else
    printf "%-15s %-15s %-10s %-10s\n" "目录服务器" "$DIR_IP" "5000" "✗ 已停止"
fi

# Guard
if ssh $USER@$GUARD_IP "pgrep -f './relay 6000' > /dev/null"; then
    printf "%-15s %-15s %-10s %-10s\n" "Guard中继" "$GUARD_IP" "6000" "✓ 运行中"
else
    printf "%-15s %-15s %-10s %-10s\n" "Guard中继" "$GUARD_IP" "6000" "✗ 已停止"
fi

# Middle
if ssh $USER@$MIDDLE_IP "pgrep -f './relay 6001' > /dev/null"; then
    printf "%-15s %-15s %-10s %-10s\n" "Middle中继" "$MIDDLE_IP" "6001" "✓ 运行中"
else
    printf "%-15s %-15s %-10s %-10s\n" "Middle中继" "$MIDDLE_IP" "6001" "✗ 已停止"
fi

# Exit
if ssh $USER@$EXIT_IP "pgrep -f './relay 6002' > /dev/null"; then
    printf "%-15s %-15s %-10s %-10s\n" "Exit中继" "$EXIT_IP" "6002" "✓ 运行中"
else
    printf "%-15s %-15s %-10s %-10s\n" "Exit中继" "$EXIT_IP" "6002" "✗ 已停止"
fi

# HTTP服务器
if ssh $USER@$TARGET_IP "pgrep -f 'http.server 8080' > /dev/null"; then
    printf "%-15s %-15s %-10s %-10s\n" "目标服务器" "$TARGET_IP" "8080" "✓ 运行中"
else
    printf "%-15s %-15s %-10s %-10s\n" "目标服务器" "$TARGET_IP" "8080" "✗ 已停止"
fi

echo ""
echo "======================================================================"
echo "  ✓ 系统启动完成"
echo "======================================================================"
echo ""
echo "现在可以运行测试："
echo "  ssh $USER@192.168.5.110 'cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 10 $DIR_IP 5000'"
echo ""
echo "查看日志："
echo "  ssh $USER@$DIR_IP 'tail -f ~/directory.log'"
echo "  ssh $USER@$GUARD_IP 'tail -f ~/guard.log'"
echo ""
echo "停止系统："
echo "  ./stop_all.sh"
