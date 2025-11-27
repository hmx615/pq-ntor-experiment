#!/usr/bin/env python3
import paramiko
import time

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("="*70)
    print("  检查directory程序是否包含test_server")
    print("="*70)

    # 1. 检查directory二进制中是否有test_server符号
    print("\n1. 检查directory程序符号:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd ~/pq-ntor-experiment/c && nm ./directory | grep -i test_server | head -10"
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    if output:
        print("✅ 找到test_server符号:")
        print(output)
    else:
        print("❌ 未找到test_server符号")

    # 2. 测试启动directory并检查端口
    print("\n2. 测试启动directory并检查端口:")
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH

# 清理
pkill -9 directory 2>/dev/null
sleep 1

# 启动directory（后台）
./directory > /tmp/directory_test.log 2>&1 &
DIR_PID=$!
echo "Directory PID: $DIR_PID"

# 等待启动
sleep 3

# 检查进程
ps -p $DIR_PID && echo "✅ Directory进程运行中" || echo "❌ Directory进程已退出"

# 检查端口
echo ""
echo "检查端口:"
netstat -tuln | grep -E '5000|8000' || echo "未监听5000/8000端口"

# 检查日志
echo ""
echo "Directory日志:"
head -30 /tmp/directory_test.log

# 测试访问
echo ""
echo "测试HTTP访问:"
curl -s -m 2 http://localhost:8000/ | head -10 || echo "HTTP服务器无响应"

# 清理
kill $DIR_PID 2>/dev/null
pkill -9 directory 2>/dev/null
""", timeout=15)

    # 实时读取输出
    while True:
        if stdout.channel.recv_ready():
            print(stdout.read(1024).decode(), end='', flush=True)
        if stdout.channel.recv_stderr_ready():
            print(stderr.read(1024).decode(), end='', flush=True)
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)

    print("\n" + "="*70)

finally:
    ssh.close()
