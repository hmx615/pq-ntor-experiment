#!/usr/bin/env python3
"""
Fix identity check in pq_ntor.c to skip in LOCAL_MODE
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

# Backup
cp pq_ntor.c pq_ntor.c.backup 2>/dev/null || true

# Use sed to wrap the identity check
sed -i '/\/\/ 验证 relay_identity/,/return PQ_NTOR_ERROR;/ {
    /\/\/ 验证 relay_identity/ i\\
#ifndef USE_LOCAL_MODE
    /return PQ_NTOR_ERROR;/ a\\
#else\\
    /* Skip identity verification in local mode */\\
    (void)received_relay_id; /* Suppress unused variable warning */\\
#endif
}' pq_ntor.c

echo "✅ 已修改 pq_ntor.c"

# Show the modified section
echo ""
echo "=== 修改后的代码 ==="
grep -B 2 -A 10 "验证 relay_identity" pq_ntor.c

# Recompile
cd /home/user/pq-ntor-experiment/c
source ~/.bashrc

echo ""
echo "=== 重新编译 ==="
make clean
make relay client

echo ""
ls -lh relay client
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=180)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    ssh.close()

if __name__ == "__main__":
    main()
