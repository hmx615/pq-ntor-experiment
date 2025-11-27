#!/usr/bin/env python3
"""
Manually compile relay with correct include path
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

echo "=== 手动编译 relay ==="
gcc -DUSE_LOCAL_MODE=1 -Wall -Wextra -O2 -g -std=c99 \\
    -I/home/user/_oqs/include \\
    -Iinclude \\
    -Isrc \\
    -o relay programs/relay_main.c \\
    src/relay_registration.o \\
    src/relay_node.o \\
    src/kyber_kem.o \\
    src/crypto_utils.o \\
    src/pq_ntor.o \\
    src/classic_ntor.o \\
    src/cell.o \\
    src/onion_crypto.o \\
    -L/home/user/_oqs/lib \\
    -loqs -lssl -lcrypto -lpthread \\
    -Wl,-rpath,/home/user/_oqs/lib

echo ""
echo "✅ 编译完成"
ls -lh relay

echo ""
echo "=== 测试 relay 帮助信息 ==="
./relay 2>&1 | head -3
"""

    stdin, stdout, stderr = ssh.exec_command(compile_cmd, timeout=60)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译警告:", err)

    ssh.close()

if __name__ == "__main__":
    main()
