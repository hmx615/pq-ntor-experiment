#!/usr/bin/env python3
"""检查飞腾派的依赖库"""

import paramiko

PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PHYTIUM_IP, username=PHYTIUM_USER, password=PHYTIUM_PASS)

print("检查飞腾派依赖...")
print("=" * 60)

commands = [
    ("pkg-config --modversion openssl", "OpenSSL版本"),
    ("ls -la /home/user/_oqs", "OQS库"),
    ("ls -la /usr/include/openssl | head -10", "OpenSSL头文件"),
]

for cmd, desc in commands:
    print(f"\n{desc}:")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out:
        print(out)
    if err:
        print(f"错误: {err}")

ssh.close()
