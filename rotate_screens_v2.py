#!/usr/bin/env python3
"""旋转110和185两个飞腾派的屏幕180度 - 使用配置文件方式"""

import paramiko
import time

TARGETS = [
    {"ip": "192.168.5.110", "name": "Pi-110"},
    {"ip": "192.168.5.185", "name": "Pi-185"},
]

USERNAME = "user"
PASSWORD = "user"

def rotate_screen_config(ip, name):
    """通过创建配置文件方式旋转屏幕（开机生效）"""
    print(f"🔄 正在为 {name} ({ip}) 配置屏幕旋转...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)

        # 方法1: 创建rc.local服务来在启动时旋转屏幕
        print(f"   创建启动脚本...")
        commands = [
            # 创建旋转脚本
            'cat > /tmp/rotate_screen.sh << "EOF"\n#!/bin/bash\necho 2 > /sys/class/graphics/fbcon/rotate 2>/dev/null || true\nEOF',
            'chmod +x /tmp/rotate_screen.sh',
            # 使用sudo移动到系统目录
            f'echo {PASSWORD} | sudo -S mv /tmp/rotate_screen.sh /usr/local/bin/rotate_screen.sh',
            # 创建systemd服务
            'cat > /tmp/rotate-screen.service << "EOF"\n[Unit]\nDescription=Rotate Screen 180 degrees\nAfter=graphical.target\n\n[Service]\nType=oneshot\nExecStart=/usr/local/bin/rotate_screen.sh\n\n[Install]\nWantedBy=graphical.target\nEOF',
            f'echo {PASSWORD} | sudo -S mv /tmp/rotate-screen.service /etc/systemd/system/',
            f'echo {PASSWORD} | sudo -S systemctl daemon-reload',
            f'echo {PASSWORD} | sudo -S systemctl enable rotate-screen.service',
            f'echo {PASSWORD} | sudo -S systemctl start rotate-screen.service',
        ]

        for cmd in commands:
            ssh.exec_command(cmd)
            time.sleep(0.5)

        print(f"   ✅ 配置已创建，重启后生效")
        print(f"   提示: 运行 'sudo reboot' 重启设备使配置生效")

        ssh.close()
        return True

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🔄 飞腾派屏幕旋转配置工具 (开机自动旋转)")
    print("=" * 80)
    print()

    for target in TARGETS:
        rotate_screen_config(target["ip"], target["name"])
        print()

    print("=" * 80)
    print("📋 配置完成说明:")
    print("   • 已为Pi-110和Pi-185创建开机自动旋转服务")
    print("   • 需要重启设备才能看到效果")
    print("   • 或者手动登录到设备运行: sudo /usr/local/bin/rotate_screen.sh")
    print("=" * 80)

if __name__ == "__main__":
    main()
