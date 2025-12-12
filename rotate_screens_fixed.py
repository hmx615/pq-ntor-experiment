#!/usr/bin/env python3
"""旋转110和185两个飞腾派的屏幕180度 - 模拟bash脚本逻辑"""

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
    print(f"=" * 80)
    print(f"🔄 {name} ({ip})")
    print(f"=" * 80)

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)

        # 1. 检查当前旋转状态
        print("1️⃣  检查当前旋转状态...")
        stdin, stdout, stderr = ssh.exec_command('cat /sys/class/graphics/fbcon/rotate 2>/dev/null || echo "0"')
        current = stdout.read().decode().strip()
        print(f"   当前旋转值: {current} (0=正常, 2=180度)")
        print()

        if current == "2":
            print(f"   ✅ 屏幕已经是180度旋转")
            ssh.close()
            return True

        # 2. 设置旋转为180度（直接执行sudo命令，密码通过stdin）
        print("2️⃣  设置屏幕旋转为180度...")
        # 使用bash heredoc方式，就像原始脚本一样
        cmd = f'''bash -c "echo {PASSWORD} | sudo -S tee /sys/class/graphics/fbcon/rotate > /dev/null" <<< "2"'''
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=False)
        time.sleep(1)
        print("   ✅ 已设置旋转值为 2")
        print()

        # 3. 验证设置
        print("3️⃣  验证设置...")
        stdin, stdout, stderr = ssh.exec_command('cat /sys/class/graphics/fbcon/rotate 2>/dev/null')
        new_value = stdout.read().decode().strip()
        print(f"   新的旋转值: {new_value}")
        print()

        # 4. 创建systemd服务（永久生效）
        print("4️⃣  创建开机自动旋转服务...")
        service_content = '''[Unit]
Description=Rotate Screen 180 degrees
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 2 > /sys/class/graphics/fbcon/rotate"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target'''

        # 使用sudo创建服务文件
        cmd = f'''bash -c "echo {PASSWORD} | sudo -S tee /etc/systemd/system/rotate-screen.service > /dev/null" <<< '{service_content}' '''
        ssh.exec_command(cmd)
        time.sleep(0.5)

        # 启用服务
        ssh.exec_command(f'echo {PASSWORD} | sudo -S systemctl daemon-reload')
        time.sleep(0.5)
        ssh.exec_command(f'echo {PASSWORD} | sudo -S systemctl enable rotate-screen.service')
        time.sleep(0.5)
        ssh.exec_command(f'echo {PASSWORD} | sudo -S systemctl start rotate-screen.service')
        time.sleep(0.5)
        print("   ✅ 服务已创建并启用")
        print()

        # 5. 刷新framebuffer（如果可能）
        print("5️⃣  刷新显示...")
        cmd1 = f'echo {PASSWORD} | sudo -S sh -c "echo 0 > /sys/class/vtconsole/vtcon1/bind" 2>/dev/null || true'
        cmd2 = f'echo {PASSWORD} | sudo -S sh -c "echo 1 > /sys/class/vtconsole/vtcon1/bind" 2>/dev/null || true'
        ssh.exec_command(cmd1)
        time.sleep(0.3)
        ssh.exec_command(cmd2)
        print("   ✅ 已尝试刷新framebuffer")
        print()

        ssh.close()

        print("✅ 配置完成！")
        print()
        print("📋 配置摘要:")
        print("  • Framebuffer旋转: 180度 (值=2)")
        print("  • 开机自动旋转: 已启用")
        print()

        return new_value == "2"

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
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

    print("=" * 80)
    print(f"📊 完成: {success_count}/{len(TARGETS)} 个设备旋转成功")
    print("=" * 80)

if __name__ == "__main__":
    main()
