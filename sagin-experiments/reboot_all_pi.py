#!/usr/bin/env python3
"""
批量重启所有飞腾派
"""

import paramiko
import sys
import time

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
        print(f"  ⚠️  {e}")
        return False
    finally:
        ssh.close()


def main():
    print("\n" + "="*60)
    print("批量重启所有飞腾派")
    print("="*60 + "\n")

    print(f"⚠️  即将重启 {len(PI_HOSTS)} 个飞腾派")
    print("   IP列表: " + ", ".join([f"192.168.5.{h}" for h in PI_HOSTS]))
    print()

    response = input("确认重启？(yes/no): ").strip().lower()
    if response != "yes":
        print("❌ 取消重启")
        sys.exit(0)

    print("\n开始重启...\n")

    for host in PI_HOSTS:
        print(f"重启 192.168.5.{host}...")
        cmd = f"echo '{SSH_PASS}' | sudo -S reboot"
        execute_ssh_command(host, cmd)
        print(f"  ✅ 重启命令已发送")
        time.sleep(0.5)

    print("\n" + "="*60)
    print("✅ 所有重启命令已发送")
    print("="*60)
    print("\n预计等待时间: 约2-3分钟")
    print("重启完成后，所有飞腾派将自动登录到桌面\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
