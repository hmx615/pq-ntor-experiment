#!/usr/bin/env python3
"""
Check original relay_main.c to understand the correct API
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

    check_cmd = """
cd /home/user/pq-ntor-experiment/c

echo "=== 检查备份的 relay_main.c ==="
if [ -f programs/relay_main.c.backup ]; then
    cat programs/relay_main.c.backup
else
    echo "没有备份文件"
fi
"""

    stdin, stdout, stderr = ssh.exec_command(check_cmd, timeout=30)

    print(stdout.read().decode('utf-8'))

    ssh.close()

if __name__ == "__main__":
    main()
