#!/usr/bin/env python3
import paramiko

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    # 查看日志
    print("查看日志:")
    stdin, stdout, stderr = ssh.exec_command("tail -100 /tmp/xxxtmp.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

finally:
    ssh.close()
