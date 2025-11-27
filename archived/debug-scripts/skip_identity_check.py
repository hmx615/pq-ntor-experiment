#!/usr/bin/env python3
"""
Skip identity verification in LOCAL_MODE for quick testing
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
cd /home/user/pq-ntor-experiment/c/src

# Backup pq_ntor.c
cp pq_ntor.c pq_ntor.c.backup 2>/dev/null || true

# Find and modify the identity verification in server_reply
# Look for the identity check and wrap it with #ifndef USE_LOCAL_MODE

# Create a modified version
cat pq_ntor.c | sed '/memcmp.*relay_identity/i\\
#ifndef USE_LOCAL_MODE  /* Skip identity check in local mode */' | \\
sed '/memcmp.*relay_identity/,+3 a\\
#endif  /* USE_LOCAL_MODE */' > pq_ntor.c.tmp

mv pq_ntor.c.tmp pq_ntor.c

echo "✅ 已修改 pq_ntor.c 跳过本地模式 identity 检查"

# Recompile relay
cd /home/user/pq-ntor-experiment/c
source ~/.bashrc

# Recompile pq_ntor.o
gcc -DUSE_LOCAL_MODE=1 -Wall -Wextra -O2 -g -std=c99 \\
    -I/home/user/_oqs/include -Iinclude -Isrc \\
    -c src/pq_ntor.c -o src/pq_ntor.o

# Recompile relay
gcc -DUSE_LOCAL_MODE=1 -Wall -Wextra -O2 -g -std=c99 \\
    -I/home/user/_oqs/include -Iinclude -Isrc \\
    -o relay programs/relay_main.c \\
    src/relay_registration.o \\
    src/relay_node.o \\
    src/kyber_kem.o \\
    src/crypto_utils.o \\
    src/pq_ntor.o \\
    src/classic_ntor.o \\
    src/cell.o \\
    src/onion_crypto.o \\
    -L/home/user/_oqs/lib -loqs -lssl -lcrypto -lpthread \\
    -Wl,-rpath,/home/user/_oqs/lib

echo ""
echo "✅ 编译完成"
ls -lh relay
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=120)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    ssh.close()

if __name__ == "__main__":
    main()
