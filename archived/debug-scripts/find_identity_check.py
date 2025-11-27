#!/usr/bin/env python3
"""
Find identity verification code in pq_ntor.c
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

    find_cmd = """
cd /home/user/pq-ntor-experiment/c/src

echo "=== 查找 identity 检查代码 ==="
grep -n "relay_identity" pq_ntor.c | head -10

echo ""
echo "=== 查找 mismatch 错误 ==="
grep -n "mismatch" pq_ntor.c

echo ""
echo "=== 显示上下文 ==="
grep -B 3 -A 3 "relay_identity mismatch" pq_ntor.c
"""

    stdin, stdout, stderr = ssh.exec_command(find_cmd, timeout=30)

    print(stdout.read().decode('utf-8'))

    ssh.close()

if __name__ == "__main__":
    main()
