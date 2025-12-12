#!/usr/bin/env python3
"""
飞腾派屏幕旋转180度脚本
使用paramiko库SSH连接并配置
"""

import paramiko
import time
import sys

# 飞腾派配置
PI_HOST = "192.168.5.185"
PI_USER = "user"
PI_PASS = "user"
PI_PORT = 22

def execute_command(ssh, command, use_sudo=False, sudo_password=None):
    """执行SSH命令"""
    if use_sudo and sudo_password:
        command = f'echo "{sudo_password}" | sudo -S {command}'

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    return output, error

def main():
    print("=" * 50)
    print("飞腾派屏幕旋转脚本 (Python版)")
    print(f"目标设备: {PI_HOST}")
    print("=" * 50)
    print()

    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接到飞腾派
        print(f"📡 连接到 {PI_HOST}...")
        ssh.connect(PI_HOST, port=PI_PORT, username=PI_USER, password=PI_PASS)
        print("✅ 连接成功！")
        print()

        # 1. 检查当前旋转状态
        print("1️⃣  检查当前旋转状态...")
        output, error = execute_command(ssh, "cat /sys/class/graphics/fbcon/rotate")
        print(f"   当前旋转值: {output}")
        print(f"   (0=正常, 1=90度, 2=180度, 3=270度)")
        print()

        # 2. 设置旋转为180度
        print("2️⃣  设置屏幕旋转为180度...")
        output, error = execute_command(
            ssh,
            "bash -c 'echo 2 | tee /sys/class/graphics/fbcon/rotate'",
            use_sudo=True,
            sudo_password=PI_PASS
        )
        print(f"   ✅ 已设置旋转值为 2 (180度)")
        print()

        # 3. 验证设置
        print("3️⃣  验证设置...")
        output, error = execute_command(ssh, "cat /sys/class/graphics/fbcon/rotate")
        print(f"   新的旋转值: {output}")
        print()

        # 4. 创建永久生效的systemd服务
        print("4️⃣  创建开机自动旋转服务...")

        service_content = """[Unit]
Description=Rotate Screen 180 degrees
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 2 > /sys/class/graphics/fbcon/rotate"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""

        # 创建服务文件
        commands = [
            f"echo '{service_content}' | sudo -S tee /etc/systemd/system/rotate-screen.service > /dev/null",
            "sudo systemctl daemon-reload",
            "sudo systemctl enable rotate-screen.service",
            "sudo systemctl start rotate-screen.service"
        ]

        for cmd in commands:
            execute_command(ssh, f"echo '{PI_PASS}' | {cmd}", use_sudo=False)

        print("   ✅ 服务已创建并启用")
        print()

        # 5. 检查图形界面
        print("5️⃣  检查图形界面配置...")
        output, error = execute_command(ssh, "command -v xrandr")

        if output:
            print("   检测到X11环境")

            # 获取显示输出设备
            output, error = execute_command(
                ssh,
                "DISPLAY=:0 xrandr | grep ' connected' | awk '{print $1}' | head -n1"
            )

            if output:
                display_output = output.strip()
                print(f"   显示输出: {display_output}")

                # 旋转屏幕
                execute_command(
                    ssh,
                    f"DISPLAY=:0 xrandr --output {display_output} --rotate inverted"
                )

                # 创建自动启动脚本
                autostart_content = f"""[Desktop Entry]
Type=Application
Name=Rotate Screen
Exec=sh -c 'export DISPLAY=:0; xrandr --output {display_output} --rotate inverted'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                execute_command(ssh, "mkdir -p ~/.config/autostart")
                execute_command(
                    ssh,
                    f"echo '{autostart_content}' > ~/.config/autostart/rotate-screen.desktop"
                )

                print("   ✅ X11旋转已配置")
            else:
                print("   ℹ️  未检测到图形输出")
        else:
            print("   ℹ️  系统无图形界面，仅framebuffer旋转生效")
        print()

        # 6. 刷新显示
        print("6️⃣  刷新显示...")
        commands = [
            "bash -c 'if [ -w /sys/class/vtconsole/vtcon1/bind ]; then echo 0 > /sys/class/vtconsole/vtcon1/bind; echo 1 > /sys/class/vtconsole/vtcon1/bind; fi'",
        ]

        for cmd in commands:
            execute_command(ssh, f"echo '{PI_PASS}' | sudo -S {cmd}")

        print("   ✅ Framebuffer已刷新")
        print()

        # 完成
        print("=" * 50)
        print("✅ 配置完成！")
        print("=" * 50)
        print()
        print("📋 配置摘要:")
        print("  • Framebuffer旋转: 180度 (值=2)")
        print("  • 开机自动旋转: 已启用")
        print("  • X11图形界面: 已配置（如果存在）")
        print()
        print("🔄 如果屏幕还未旋转，可能需要重启飞腾派")
        print()

        # 询问是否重启
        user_input = input("是否立即重启飞腾派? (y/N): ").strip().lower()
        if user_input == 'y':
            print("正在重启飞腾派...")
            execute_command(ssh, f"echo '{PI_PASS}' | sudo -S reboot")
            print("✅ 重启命令已发送")
        else:
            print("ℹ️  稍后可手动重启: ssh user@192.168.5.185 'sudo reboot'")

        print()
        print("↩️  如需恢复正常显示，执行:")
        print("   echo 0 | sudo tee /sys/class/graphics/fbcon/rotate")
        print()

    except paramiko.AuthenticationException:
        print("❌ 认证失败！请检查用户名和密码")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"❌ SSH连接错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)
    finally:
        ssh.close()
        print("🔌 SSH连接已关闭")

if __name__ == "__main__":
    main()
