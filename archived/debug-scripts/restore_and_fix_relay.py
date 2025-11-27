#!/usr/bin/env python3
"""
Restore original relay_main.c and add registration
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

# Restore original
cp relay_main.c.backup relay_main.c

# Add registration include at the top
sed -i '/#include "..\/src\/relay_node.h"/a\\
#ifdef USE_LOCAL_MODE\\
#include "relay_registration.h"\\
#endif' relay_main.c

# Add registration call after relay_node_init, before printing Node Configuration
# We need to insert after the "global_node = &node;" line
sed -i '/global_node = &node;/a\\
\\
#ifdef USE_LOCAL_MODE\\
    /* Register with directory in local mode */\\
    printf("[Main] Registering with directory (local mode)...\\\\n");\\
    sleep(2); /* Wait for directory to be ready */\\
\\
    /* Determine node type from role */\\
    int node_type = (config.role == RELAY_ROLE_GUARD) ? 1 : \\
                   (config.role == RELAY_ROLE_MIDDLE) ? 2 : 3;\\
\\
    if (register_with_directory("127.0.0.1", 5000, config.port, node_type) == 0) {\\
        printf("[Main] Successfully registered with directory\\\\n");\\
    } else {\\
        fprintf(stderr, "[Main] Warning: Failed to register with directory\\\\n");\\
        fprintf(stderr, "[Main] Relay will continue but may not be discoverable\\\\n");\\
    }\\
#endif' relay_main.c

echo "✅ relay_main.c 已修复"

# Compile
cd /home/user/pq-ntor-experiment/c

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
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=90)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    ssh.close()

if __name__ == "__main__":
    main()
