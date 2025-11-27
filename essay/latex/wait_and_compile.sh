#!/bin/bash
# 智能等待 apt 完成，然后自动编译

cd "$(dirname "$0")"

echo "========================================="
echo "智能等待和编译脚本"
echo "========================================="
echo ""

# 检查是否有 apt 进程
if ps aux | grep -v grep | grep -E "apt-get|apt.systemd" > /dev/null; then
    echo "⏳ 检测到系统正在自动更新..."
    echo "   这通常需要 1-3 分钟"
    echo ""
    echo "正在等待更新完成..."

    COUNT=0
    while ps aux | grep -v grep | grep -E "apt-get|apt.systemd" > /dev/null; do
        echo -n "."
        sleep 5
        COUNT=$((COUNT + 1))

        # 每30秒显示一次状态
        if [ $((COUNT % 6)) -eq 0 ]; then
            ELAPSED=$((COUNT * 5))
            echo ""
            echo "   已等待 ${ELAPSED} 秒..."
        fi

        # 如果超过5分钟，提示用户
        if [ $COUNT -gt 60 ]; then
            echo ""
            echo "⚠️  已等待超过 5 分钟"
            echo "   您可以："
            echo "   1. 继续等待（按 Enter）"
            echo "   2. 强制终止并继续（输入 'kill' 然后按 Enter）"
            echo "   3. 退出（按 Ctrl+C）"
            read -t 10 -p "   您的选择: " USER_CHOICE || USER_CHOICE=""

            if [ "$USER_CHOICE" = "kill" ]; then
                echo "   强制终止 apt 进程..."
                sudo killall apt-get 2>/dev/null || true
                sleep 3
                break
            fi
            COUNT=0  # 重置计数器
        fi
    done

    echo ""
    echo "✅ apt 进程已完成！"
else
    echo "✅ 没有检测到 apt 进程"
fi

echo ""
echo "========================================="
echo "开始安装 LaTeX 和编译论文"
echo "========================================="
echo ""

# 运行主安装脚本
if [ -f "./install_and_compile.sh" ]; then
    ./install_and_compile.sh
else
    echo "❌ 找不到 install_and_compile.sh"
    exit 1
fi
