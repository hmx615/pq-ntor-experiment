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
    print("  🔍 诊断PQ-NTOR程序问题")
    print("="*70)

    # 1. 测试单独运行directory
    print("\n1️⃣ 测试directory程序:")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
timeout 3 ./directory 2>&1 || echo "Directory启动测试完成"
""", timeout=10)
    print(stdout.read().decode())

    # 2. 测试client直接运行
    print("\n2️⃣ 测试client程序（不带网络）:")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
./client --help 2>&1
""", timeout=10)
    print(stdout.read().decode())

    # 3. 检查程序依赖
    print("\n3️⃣ 检查程序库依赖:")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
ldd ./client | grep -i "not found\\|oqs\\|ssl"
echo "---"
ldd ./directory | grep -i "not found\\|oqs\\|ssl"
echo "---"
ldd ./relay | grep -i "not found\\|oqs\\|ssl"
""", timeout=10)
    output = stdout.read().decode()
    error = stderr.read().decode()
    print(output)
    if error:
        print("错误:", error)

    # 4. 手动测试完整流程
    print("\n4️⃣ 手动测试完整Tor流程:")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH

# 清理
pkill -9 directory relay client 2>/dev/null
sleep 1

# 启动directory（后台）
./directory > /tmp/dir.log 2>&1 &
DIR_PID=$!
sleep 2

# 启动guard relay（后台）
./relay -r guard -p 6001 > /tmp/guard.log 2>&1 &
GUARD_PID=$!
sleep 1

# 启动exit relay（后台）
./relay -r exit -p 6002 > /tmp/exit.log 2>&1 &
EXIT_PID=$!
sleep 2

# 运行client
echo "运行client测试..."
timeout 10 ./client -u http://example.com --mode pq 2>&1 || echo "Client完成"

# 查看日志
echo ""
echo "=== Directory日志 ==="
head -20 /tmp/dir.log

echo ""
echo "=== Guard Relay日志 ==="
head -20 /tmp/guard.log

echo ""
echo "=== Exit Relay日志 ==="
head -20 /tmp/exit.log

# 清理
kill $DIR_PID $GUARD_PID $EXIT_PID 2>/dev/null
pkill -9 directory relay client 2>/dev/null
""", timeout=30)

    # 读取输出
    import time
    while True:
        if stdout.channel.recv_ready():
            data = stdout.read(1024).decode()
            print(data, end='', flush=True)
        if stdout.channel.recv_stderr_ready():
            data = stderr.read(1024).decode()
            print(data, end='', flush=True)
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)

    print("\n" + "="*70)
    print("  诊断完成")
    print("="*70)

finally:
    ssh.close()
