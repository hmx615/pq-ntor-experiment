#!/usr/bin/env python3
import paramiko

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("="*70)
    print("  ✅ liboqs安装验证")
    print("="*70)

    commands = [
        ("liboqs库文件", "ls -lh ~/_oqs/lib/"),
        ("liboqs头文件", "ls ~/_oqs/include/oqs/"),
        ("测试程序是否能找到liboqs", "cd ~/pq-ntor-experiment/c && ldd ./test_kyber | grep -i oqs || echo '未链接到liboqs'"),
        ("运行test_kyber测试", "cd ~/pq-ntor-experiment/c && LD_LIBRARY_PATH=~/_oqs/lib:$LD_LIBRARY_PATH ./test_kyber 2>&1 | head -20"),
    ]

    for desc, cmd in commands:
        print(f"\n{desc}:")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if output.strip():
            print(output)
        if error.strip() and "SUCCESS" not in error:
            print(f"错误: {error}")

finally:
    ssh.close()
