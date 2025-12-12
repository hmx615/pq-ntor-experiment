#!/usr/bin/env python3
"""旋转110和185两个飞腾派的屏幕180度"""

import paramiko
import time

TARGETS = [
    {"ip": "192.168.5.110", "name": "Pi-110"},
    {"ip": "192.168.5.185", "name": "Pi-185"},
]

USERNAME = "user"
PASSWORD = "user"

def rotate_screen(ip, name):
    """旋转单个飞腾派的屏幕"""
    print(f"🔄 正在旋转 {name} ({ip}) 的屏幕...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)

        # 检查当前旋转状态
        stdin, stdout, stderr = ssh.exec_command('cat /sys/class/graphics/fbcon/rotate 2>/dev/null || echo "0"')
        current = stdout.read().decode().strip()
        print(f"   当前旋转值: {current} (0=正常, 2=180度)")

        if current == "2":
            print(f"   ✅ 屏幕已经是180度，无需旋转")
            ssh.close()
            return True

        # 旋转屏幕到180度 (使用sudo -S从stdin读取密码)
        print(f"   正在设置旋转值为2 (180度)...")
        command = f'echo {PASSWORD} | sudo -S bash -c "echo 2 > /sys/class/graphics/fbcon/rotate"'
        stdin, stdout, stderr = ssh.exec_command(command)
        time.sleep(2)

        error = stderr.read().decode().strip()
        if error and 'password' not in error.lower():
            print(f"   警告: {error}")

        # 验证设置
        stdin, stdout, stderr = ssh.exec_command('cat /sys/class/graphics/fbcon/rotate 2>/dev/null')
        new_value = stdout.read().decode().strip()

        if new_value == "2":
            print(f"   ✅ 屏幕旋转成功！")
            ssh.close()
            return True
        else:
            print(f"   ⚠️  旋转可能未生效，当前值: {new_value}")
            ssh.close()
            return False

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🔄 飞腾派屏幕旋转工具")
    print("=" * 80)
    print()

    success_count = 0
    for target in TARGETS:
        result = rotate_screen(target["ip"], target["name"])
        if result:
            success_count += 1
        print()

    print("=" * 80)
    print(f"📊 完成: {success_count}/{len(TARGETS)} 个设备旋转成功")
    print("=" * 80)

if __name__ == "__main__":
    main()
