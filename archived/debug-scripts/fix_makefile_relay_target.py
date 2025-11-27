#!/usr/bin/env python3
"""
Fix Makefile relay target to include -Iinclude
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

    fix_cmd = """
cd /home/user/pq-ntor-experiment/c

echo "=== 检查 relay 编译规则 ==="
grep -A 2 "^relay:" Makefile

echo ""
echo "=== 修复 Makefile ==="

# Find and replace the relay target
sed -i '/^relay:/,/^$/ {
    s|-Isrc|-Iinclude -Isrc|
}' Makefile

echo "✅ 已修复"

echo ""
echo "=== 新的 relay 编译规则 ==="
grep -A 2 "^relay:" Makefile

echo ""
echo "=== 重新编译 ==="
make relay

echo ""
ls -lh relay
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=60)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

    ssh.close()

if __name__ == "__main__":
    main()
