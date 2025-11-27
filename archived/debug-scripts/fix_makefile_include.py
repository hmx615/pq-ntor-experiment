#!/usr/bin/env python3
"""
Fix Makefile to include the include directory
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

# Check current CFLAGS
echo "=== 当前 CFLAGS ==="
grep "^CFLAGS" Makefile | head -1

# Add -Iinclude if not present
if ! grep "^CFLAGS" Makefile | grep -q "\-Iinclude"; then
    sed -i 's|^CFLAGS = \(.*\)-Isrc|\1-Iinclude -Isrc|' Makefile
    echo "✅ 已添加 -Iinclude"
fi

echo ""
echo "=== 新 CFLAGS ==="
grep "^CFLAGS" Makefile | head -1

# Recompile
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
        print(err)

    ssh.close()

if __name__ == "__main__":
    main()
