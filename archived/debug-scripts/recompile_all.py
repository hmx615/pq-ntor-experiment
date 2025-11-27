#!/usr/bin/env python3
"""
Recompile all programs
"""

import paramiko

HOST = "192.168.5.110"
PORT = 22
USER = "user"
PASSWORD = "user"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
               allow_agent=False, look_for_keys=False)

    compile_cmd = """
cd /home/user/pq-ntor-experiment/c
source ~/.bashrc

echo "=== 编译 directory ==="
make directory

echo ""
echo "=== 编译 client ==="
make client

echo ""
echo "=== 检查编译结果 ==="
ls -lh directory relay client

echo ""
echo "✅ 完成"
"""

    stdin, stdout, stderr = ssh.exec_command(compile_cmd, timeout=120)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    ssh.close()

if __name__ == "__main__":
    main()
