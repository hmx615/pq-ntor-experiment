#!/usr/bin/env python3
"""
批量关闭所有飞腾派上的浏览器
"""

import paramiko
import sys

# 所有飞腾派IP
PI_HOSTS = ["187", "188", "190", "186", "110", "189", "185"]
SSH_USER = "user"
SSH_PASS = "user"


def execute_ssh_command(host, command):
    """执行SSH命令"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(f"192.168.5.{host}", username=SSH_USER, password=SSH_PASS, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.read()
        return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False
    finally:
        ssh.close()


def main():
    print("\n" + "="*60)
    print("关闭所有飞腾派浏览器")
    print("="*60 + "\n")

    for host in PI_HOSTS:
        print(f"关闭 192.168.5.{host} 的浏览器...")
        execute_ssh_command(host, "pkill -9 chromium")
        execute_ssh_command(host, "pkill -9 firefox")
        print(f"  ✅ 完成")

    print("\n✅ 所有浏览器已关闭\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
