#!/usr/bin/env python3
"""检查飞腾派上的benchmark程序"""

import paramiko

PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PHYTIUM_IP, username=PHYTIUM_USER, password=PHYTIUM_PASS)

print("检查飞腾派上的benchmark程序...")

commands = [
    ("ls -lh benchmark_pq_ntor", "查看文件信息"),
    ("file benchmark_pq_ntor", "查看文件类型"),
    ("./benchmark_pq_ntor 10", "尝试运行"),
]

for cmd, desc in commands:
    print(f"\n{desc}: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR} && {cmd}")
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out:
        print(out)
    if err:
        print(f"错误: {err}")

ssh.close()
