#!/bin/bash
# 飞腾派 192.168.5.185 屏幕旋转180度脚本
# 使用方法: ./rotate_screen_185.sh

PI_IP="192.168.5.185"
PI_USER="user"
PI_PASS="user"

echo "========================================"
echo "飞腾派屏幕旋转脚本"
echo "目标设备: $PI_IP"
echo "========================================"
echo ""

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo "⚠️  sshpass未安装，正在安装..."
    sudo apt-get update -qq
    sudo apt-get install -y sshpass
fi

echo "📡 连接到飞腾派..."
echo ""

# 1. 检查当前旋转状态
echo "1️⃣  检查当前旋转状态..."
CURRENT_ROTATE=$(sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP 'cat /sys/class/graphics/fbcon/rotate' 2>/dev/null)
echo "   当前旋转值: $CURRENT_ROTATE"
echo "   (0=正常, 1=90度, 2=180度, 3=270度)"
echo ""

# 2. 设置旋转为180度
echo "2️⃣  设置屏幕旋转为180度..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'ENDSSH'
    echo 2 | sudo -S tee /sys/class/graphics/fbcon/rotate > /dev/null
    echo "   ✅ 已设置旋转值为 2 (180度)"
ENDSSH
echo ""

# 3. 验证设置
echo "3️⃣  验证设置..."
NEW_ROTATE=$(sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP 'cat /sys/class/graphics/fbcon/rotate' 2>/dev/null)
echo "   新的旋转值: $NEW_ROTATE"
echo ""

# 4. 创建永久生效的systemd服务
echo "4️⃣  创建开机自动旋转服务..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'ENDSSH'
    # 创建systemd服务文件
    echo "user" | sudo -S bash -c 'cat > /etc/systemd/system/rotate-screen.service << EOF
[Unit]
Description=Rotate Screen 180 degrees
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 2 > /sys/class/graphics/fbcon/rotate"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF'

    # 启用服务
    echo "user" | sudo -S systemctl daemon-reload
    echo "user" | sudo -S systemctl enable rotate-screen.service
    echo "user" | sudo -S systemctl start rotate-screen.service

    echo "   ✅ 服务已创建并启用"
ENDSSH
echo ""

# 5. 检查是否有图形界面，配置xrandr
echo "5️⃣  检查图形界面配置..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'ENDSSH'
    if command -v xrandr &> /dev/null; then
        export DISPLAY=:0
        echo "   检测到X11环境"

        # 获取输出设备名称
        OUTPUT=$(DISPLAY=:0 xrandr | grep " connected" | awk '{print $1}' | head -n1)

        if [ -n "$OUTPUT" ]; then
            echo "   显示输出: $OUTPUT"

            # 旋转屏幕
            DISPLAY=:0 xrandr --output "$OUTPUT" --rotate inverted 2>/dev/null

            # 创建自动启动脚本
            mkdir -p ~/.config/autostart
            cat > ~/.config/autostart/rotate-screen.desktop << EOF
[Desktop Entry]
Type=Application
Name=Rotate Screen
Exec=sh -c 'export DISPLAY=:0; xrandr --output $OUTPUT --rotate inverted'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
            echo "   ✅ X11旋转已配置"
        else
            echo "   ℹ️  未检测到图形输出"
        fi
    else
        echo "   ℹ️  系统无图形界面，仅framebuffer旋转生效"
    fi
ENDSSH
echo ""

# 6. 刷新显示
echo "6️⃣  刷新显示..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'ENDSSH'
    # 尝试刷新framebuffer
    if [ -w /sys/class/vtconsole/vtcon1/bind ]; then
        echo "user" | sudo -S sh -c 'echo 0 > /sys/class/vtconsole/vtcon1/bind'
        echo "user" | sudo -S sh -c 'echo 1 > /sys/class/vtconsole/vtcon1/bind'
        echo "   ✅ Framebuffer已刷新"
    fi
ENDSSH
echo ""

echo "========================================"
echo "✅ 配置完成！"
echo "========================================"
echo ""
echo "📋 配置摘要:"
echo "  • Framebuffer旋转: 180度 (值=2)"
echo "  • 开机自动旋转: 已启用"
echo "  • X11图形界面: 已配置（如果存在）"
echo ""
echo "🔄 如果屏幕还未旋转，请执行以下命令重启飞腾派:"
echo "   sshpass -p 'user' ssh user@192.168.5.185 'sudo reboot'"
echo ""
echo "↩️  如需恢复正常显示，执行:"
echo "   echo 0 | sudo tee /sys/class/graphics/fbcon/rotate"
echo ""
