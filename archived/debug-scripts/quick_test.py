#!/usr/bin/env python3
import paramiko

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("="*70)
    print("  快速测试")
    print("="*70)

    # 测试1: 查看client help
    print("\n1. Client help:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd ~/pq-ntor-experiment/c && export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH && ./client --help",
        timeout=5
    )
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("STDERR:", err)

    # 测试2: 运行test_pq_ntor
    print("\n2. 运行test_pq_ntor:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd ~/pq-ntor-experiment/c && export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH && ./test_pq_ntor",
        timeout=10
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    print(output[-500:] if len(output) > 500 else output)

    # 测试3: 检查端口占用
    print("\n3. 检查端口占用:")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep '5000\\|6001\\|6002\\|9050'")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode() or "无占用")

    # 测试4: 查看最近的日志
    print("\n4. 查看临时日志:")
    stdin, stdout, stderr = ssh.exec_command("ls -lt /tmp/*.log 2>/dev/null | head -5")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode() or "无日志")

finally:
    ssh.close()
