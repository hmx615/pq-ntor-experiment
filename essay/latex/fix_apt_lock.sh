#!/bin/bash
# 解决 apt 锁定问题

echo "========================================="
echo "解决 apt 锁定问题"
echo "========================================="
echo ""

echo "正在检查 apt 进程..."
if ps aux | grep -v grep | grep apt-get > /dev/null; then
    echo "发现正在运行的 apt-get 进程："
    ps aux | grep -v grep | grep apt-get
    echo ""
    echo "选项："
    echo "  1) 等待自动更新完成（推荐，1-2分钟）"
    echo "  2) 强制终止 apt 进程（可能不安全）"
    echo ""
    read -p "请选择 [1/2]: " choice

    case $choice in
        1)
            echo "等待 apt 进程完成..."
            while ps aux | grep -v grep | grep apt-get > /dev/null; do
                echo -n "."
                sleep 5
            done
            echo ""
            echo "✅ apt 进程已完成！"
            ;;
        2)
            echo "强制终止 apt 进程..."
            sudo killall apt-get 2>/dev/null || true
            sudo killall apt 2>/dev/null || true
            echo "等待 3 秒..."
            sleep 3
            echo "✅ 已终止"
            ;;
        *)
            echo "无效选择"
            exit 1
            ;;
    esac
else
    echo "✅ 没有发现 apt 进程，可以继续"
fi

echo ""
echo "清理 apt 缓存..."
sudo rm -f /var/lib/apt/lists/lock
sudo rm -f /var/cache/apt/archives/lock
sudo rm -f /var/lib/dpkg/lock*

echo "重新配置 dpkg..."
sudo dpkg --configure -a

echo ""
echo "========================================="
echo "✅ 修复完成！"
echo "========================================="
echo ""
echo "现在可以重新运行："
echo "  ./install_and_compile.sh"
echo ""
