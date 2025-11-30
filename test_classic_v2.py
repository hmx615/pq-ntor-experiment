#!/usr/bin/env python3
"""测试优化版Classic NTOR"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.5.110", username="user", password="user")

print("上传v2版本...")
sftp = ssh.open_sftp()
sftp.put(
    "/home/ccc/pq-ntor-experiment/c/benchmark/benchmark_classic_ntor_v2.c",
    "/home/user/pq-ntor-experiment/c/benchmark/benchmark_classic_ntor_v2.c"
)
sftp.close()

print("\n编译...")
stdin, stdout, stderr = ssh.exec_command(
    "cd ~/pq-ntor-experiment/c && "
    "gcc -O3 -march=native -std=c99 "  # 使用O3和native优化
    "-o benchmark_classic_v2 "
    "benchmark/benchmark_classic_ntor_v2.c "
    "-lssl -lcrypto -lm -lpthread",
    get_pty=True
)
print(stdout.read().decode())

print("\n运行测试...")
stdin, stdout, stderr = ssh.exec_command(
    "cd ~/pq-ntor-experiment/c && ./benchmark_classic_v2 1000",
    timeout=120, get_pty=True
)
print(stdout.read().decode())

ssh.close()
