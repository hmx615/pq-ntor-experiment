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
    print("  🔍 深度诊断失败原因")
    print("="*70)

    # 手动测试完整流程
    print("\n📝 手动测试完整Tor流程...")
    print("-"*70)

    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH

# 清理
pkill -9 directory relay client 2>/dev/null
sleep 2

# 启动directory
echo "1. 启动directory..."
./directory > /tmp/dir_test.log 2>&1 &
DIR_PID=$!
echo "   Directory PID: $DIR_PID"
sleep 3

# 检查directory
if ps -p $DIR_PID > /dev/null; then
    echo "   ✅ Directory运行中"
else
    echo "   ❌ Directory已退出"
    cat /tmp/dir_test.log
    exit 1
fi

# 检查端口
echo "2. 检查端口:"
netstat -tuln | grep -E '5000|8000' && echo "   ✅ 端口正常" || echo "   ❌ 端口未监听"

# 测试HTTP服务器
echo "3. 测试HTTP服务器:"
curl -s -m 2 http://localhost:8000/ | head -5 && echo "   ✅ HTTP正常" || echo "   ❌ HTTP无响应"

# 启动guard
echo "4. 启动guard relay..."
./relay -r guard -p 6001 > /tmp/guard_test.log 2>&1 &
GUARD_PID=$!
sleep 2
ps -p $GUARD_PID > /dev/null && echo "   ✅ Guard运行中" || echo "   ❌ Guard已退出"

# 启动exit
echo "5. 启动exit relay..."
./relay -r exit -p 6002 > /tmp/exit_test.log 2>&1 &
EXIT_PID=$!
sleep 2
ps -p $EXIT_PID > /dev/null && echo "   ✅ Exit运行中" || echo "   ❌ Exit已退出"

# 等待relay注册
echo "6. 等待relays注册到directory..."
sleep 3

# 查询directory节点列表
echo "7. 查询directory节点列表:"
curl -s http://localhost:5000/nodes | python3 -m json.tool 2>/dev/null || echo "   ❌ 无法获取节点列表"

# 运行client
echo "8. 运行client测试:"
echo "   命令: ./client -u http://localhost:8000/ --mode pq"
timeout 15 ./client -u http://localhost:8000/ --mode pq 2>&1 | head -30

echo ""
echo "9. 查看日志前20行:"
echo "=== Directory ==="
head -20 /tmp/dir_test.log
echo ""
echo "=== Guard ==="
head -20 /tmp/guard_test.log
echo ""
echo "=== Exit ==="
head -20 /tmp/exit_test.log

# 清理
kill $DIR_PID $GUARD_PID $EXIT_PID 2>/dev/null
pkill -9 directory relay client 2>/dev/null
""", timeout=45)

    # 读取输出
    while True:
        if stdout.channel.recv_ready():
            print(stdout.read(1024).decode(), end='', flush=True)
        if stdout.channel.recv_stderr_ready():
            data = stderr.read(1024).decode()
            if data:
                print("STDERR:", data, end='', flush=True)
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)

    print("\n" + "="*70)
    print("  诊断完成")
    print("="*70)

finally:
    ssh.close()
