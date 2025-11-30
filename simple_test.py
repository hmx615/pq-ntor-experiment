#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.5.110", username="user", password="user")

print("=== 检查程序 ===")
stdin, stdout, stderr = ssh.exec_command("ls -lh ~/pq-ntor-experiment/c/{directory,relay,benchmark_pq_ntor}")
print(stdout.read().decode())

print("\n=== 清理旧进程 ===")
ssh.exec_command("pkill -f directory; pkill -f relay")

print("\n=== 启动directory（后台） ===")
stdin, stdout, stderr = ssh.exec_command("cd ~/pq-ntor-experiment/c && nohup ./directory 5000 > ~/dir.log 2>&1 &")
import time
time.sleep(2)

print("\n=== 检查进程 ===")
stdin, stdout, stderr = ssh.exec_command("pgrep -a directory")
print(stdout.read().decode())

print("\n=== 检查日志 ===")
stdin, stdout, stderr = ssh.exec_command("cat ~/dir.log")
print(stdout.read().decode())

print("\n=== 测试连接 ===")
stdin, stdout, stderr = ssh.exec_command("cd ~/pq-ntor-experiment/c && curl http://localhost:5000/nodes 2>&1")
print(stdout.read().decode())

ssh.close()
