#!/usr/bin/env python3
"""
Fix include path in relay_main.c
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
cd /home/user/pq-ntor-experiment/c/programs

# Fix the include path
sed -i 's|#include "../src/relay_registration.h"|#include "relay_registration.h"|' relay_main.c

echo "✅ 修复include路径"

# Recompile
cd /home/user/pq-ntor-experiment/c
make relay

echo ""
ls -lh relay
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=60)

    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))

    ssh.close()

if __name__ == "__main__":
    main()
