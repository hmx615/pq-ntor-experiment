#!/usr/bin/env python3
"""重启110和185两个飞腾派"""

import paramiko
import time

TARGETS = [
    {"ip": "192.168.5.110", "name": "Pi-110"},
    {"ip": "192.168.5.185", "name": "Pi-185"},
]

USERNAME = "user"
PASSWORD = "user"

def reboot_pi(ip, name):
    """重启单个飞腾派"""
    print(f"🔄 正在重启 {name} ({ip})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)

        # 发送重启命令
        ssh.exec_command(f'echo {PASSWORD} | sudo -S reboot')
        print(f"   ✅ 重启命令已发送")

        ssh.close()
        return True

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🔄 重启飞腾派 (使屏幕旋转生效)")
    print("=" * 80)
    print()

    for target in TARGETS:
        reboot_pi(target["ip"], target["name"])

    print()
    print("⏱️  等待设备重启...")
    print("   提示: 大约需要30-60秒")
    print()

    # 等待30秒
    for i in range(30, 0, -5):
        print(f"   {i}秒后检查连接...", end='\r')
        time.sleep(5)

    print()
    print("🔍 检查设备是否已恢复...")
    print()

    # 检查设备是否重启完成
    for target in TARGETS:
        ip = target["ip"]
        name = target["name"]
        print(f"检查 {name} ({ip})...", end='')

        for attempt in range(6):  # 再等30秒
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=3)

                # 检查旋转值
                stdin, stdout, stderr = ssh.exec_command('cat /sys/class/graphics/fbcon/rotate 2>/dev/null')
                rotate_value = stdout.read().decode().strip()

                ssh.close()

                if rotate_value == "2":
                    print(f" ✅ 在线 (屏幕旋转: 180度)")
                else:
                    print(f" ✅ 在线 (屏幕旋转: {rotate_value})")
                break

            except:
                if attempt < 5:
                    time.sleep(5)
                else:
                    print(f" ⏳ 设备可能还在重启中")

    print()
    print("=" * 80)
    print("✅ 重启完成!")
    print("=" * 80)

if __name__ == "__main__":
    main()
