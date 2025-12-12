#!/usr/bin/env python3
"""查找飞腾派上可能存在的部署位置"""

import paramiko

PI_IP = "192.168.5.186"
USERNAME = "user"
PASSWORD = "user"

def find_deployment():
    """查找Pi上的部署"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        # 搜索可能的位置
        commands = [
            ("主目录结构", "ls -la /home/user/ | head -30"),
            ("查找directory二进制", "find /home/user -name 'directory' -type f 2>/dev/null | head -5"),
            ("查找relay二进制", "find /home/user -name 'relay' -type f 2>/dev/null | head -5"),
            ("查找client二进制", "find /home/user -name 'client' -type f 2>/dev/null | head -5"),
            ("查找配置文件", "find /home/user -name '*topo*mapping*.json' 2>/dev/null | head -10"),
        ]

        for title, cmd in commands:
            print(f"\n{'='*70}")
            print(f"📋 {title}")
            print(f"{'='*70}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode().strip()
            if output:
                print(output)
            else:
                print("(未找到)")

        ssh.close()

    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("  查找飞腾派 Pi-186 部署位置")
    print("=" * 70)
    find_deployment()
