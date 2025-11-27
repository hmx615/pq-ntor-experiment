#!/usr/bin/env python3
"""
Fix relay_node.c to properly call registration
"""

import paramiko

HOST = "192.168.5.110"
PORT = 22
USER = "user"
PASSWORD = "user"

def main():
    print("🔌 连接到飞腾派...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
               allow_agent=False, look_for_keys=False)
    print("✅ 已连接\n")

    # First, let's check the current relay_main.c
    print("检查 programs/relay_main.c...")
    stdin, stdout, stderr = ssh.exec_command("cat /home/user/pq-ntor-experiment/c/programs/relay_main.c")
    relay_main = stdout.read().decode('utf-8')
    print(f"文件大小: {len(relay_main)} 字节\n")

    # Create a fixed version that adds registration in relay_main.c instead
    fix_cmd = """
cd /home/user/pq-ntor-experiment/c/programs

# Backup
cp relay_main.c relay_main.c.backup 2>/dev/null || true

# Create new version with registration
cat > relay_main.c << 'RELAY_MAIN_EOF'
/**
 * relay_main.c - Main program for PQ-Tor relay node
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include "../src/relay_node.h"

#ifdef USE_LOCAL_MODE
#include "../src/relay_registration.h"
#endif

static volatile int running = 1;

void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <port> <node_type>\\n", argv[0]);
        fprintf(stderr, "  node_type: 1=guard, 2=middle, 3=exit\\n");
        return 1;
    }

    uint16_t port = (uint16_t)atoi(argv[1]);
    node_type_t type = (node_type_t)atoi(argv[2]);

    printf("============================================\\n");
    switch (type) {
        case NODE_TYPE_GUARD:
            printf("  PQ-Tor Relay Node - Guard\\n");
            break;
        case NODE_TYPE_MIDDLE:
            printf("  PQ-Tor Relay Node - Middle\\n");
            break;
        case NODE_TYPE_EXIT:
            printf("  PQ-Tor Relay Node - Exit\\n");
            break;
        default:
            fprintf(stderr, "Invalid node type: %d\\n", type);
            return 1;
    }
    printf("============================================\\n\\n");

    // Setup signal handlers
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    // Initialize relay
    printf("[Main] Starting relay on port %u, type %d\\n", port, type);

    if (relay_node_init(port, type) != 0) {
        fprintf(stderr, "[Main] Failed to initialize relay node\\n");
        return 1;
    }

#ifdef USE_LOCAL_MODE
    // Register with directory in local mode
    printf("[Main] Registering with directory (local mode)...\\n");
    sleep(2); // Wait for directory to be ready

    if (register_with_directory("127.0.0.1", 5000, port, type) == 0) {
        printf("[Main] Successfully registered with directory\\n");
    } else {
        fprintf(stderr, "[Main] Warning: Failed to register with directory\\n");
        fprintf(stderr, "[Main] Relay will continue but may not be discoverable\\n");
    }
#endif

    printf("[Main] Relay running, press Ctrl+C to stop\\n");

    // Keep running
    while (running) {
        sleep(1);
    }

    printf("\\n[Main] Shutting down...\\n");
    relay_node_cleanup();

    return 0;
}
RELAY_MAIN_EOF

echo "✅ relay_main.c 已更新"

# Recompile
cd /home/user/pq-ntor-experiment/c
source ~/.bashrc
make clean
make relay

echo ""
echo "✅ 编译完成"
ls -lh relay
"""

    print("执行修复...")
    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=60)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    print("\n✅ 修复完成")

    ssh.close()

if __name__ == "__main__":
    main()
