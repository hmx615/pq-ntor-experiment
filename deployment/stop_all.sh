#!/bin/bash
# stop_all.sh - 停止所有节点服务

USER="user"

# 所有节点IP
ALL_IPS=(
    "192.168.5.111"  # 目录
    "192.168.5.112"  # Guard
    "192.168.5.113"  # Middle
    "192.168.5.114"  # Exit
    "192.168.5.115"  # 目标
    "192.168.5.116"  # 监控
)

echo "======================================================================"
echo "  停止PQ-NTOR分布式系统"
echo "======================================================================"
echo ""

for ip in "${ALL_IPS[@]}"; do
    echo "停止 $ip ..."

    ssh $USER@$ip << 'ENDSSH'
        # 杀死所有相关进程
        pkill -f 'directory' 2>/dev/null && echo "  ✓ 已停止directory"
        pkill -f 'relay' 2>/dev/null && echo "  ✓ 已停止relay"
        pkill -f 'http.server' 2>/dev/null && echo "  ✓ 已停止http.server"
        pkill -f 'monitor' 2>/dev/null && echo "  ✓ 已停止monitor"

        # 删除PID文件
        rm -f ~/*.pid 2>/dev/null

        # 清除TC规则
        sudo tc qdisc del dev eth0 root 2>/dev/null && echo "  ✓ 已清除TC规则" || true
ENDSSH

    echo ""
done

echo "======================================================================"
echo "  ✓ 所有节点已停止"
echo "======================================================================"
