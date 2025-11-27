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
    print("  🔍 搜索liboqs安装位置")
    print("="*70)

    # 搜索liboqs
    commands = [
        ("检查 ~/oqs", "ls -la ~/oqs 2>/dev/null || echo '不存在'"),
        ("检查 ~/_oqs", "ls -la ~/_oqs 2>/dev/null || echo '不存在'"),
        ("检查 /usr/local", "ls -la /usr/local/lib/liboqs* 2>/dev/null || echo '不存在'"),
        ("搜索整个home目录", "find ~ -name 'liboqs.so*' 2>/dev/null | head -10"),
        ("检查最近编译", "find ~ -name 'liboqs' -type d 2>/dev/null | head -10"),
        ("检查环境变量", "echo $LIBOQS_DIR"),
        ("检查bashrc配置", "grep -i liboqs ~/.bashrc 2>/dev/null || echo '未配置'"),
    ]

    for desc, cmd in commands:
        print(f"\n{desc}:")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        if output.strip():
            print(output)
        else:
            print("  (无输出)")

finally:
    ssh.close()
