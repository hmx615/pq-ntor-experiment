#!/usr/bin/env python3
"""
Debug 12-topology test v2 with correct relay arguments
"""

import paramiko
import time

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

    # Run a single test with full output
    test_cmd = """
cd /home/user/pq-ntor-experiment/c

echo "=== 清理旧进程 ==="
killall -9 directory relay client 2>/dev/null || true
sleep 1

echo ""
echo "=== 启动 Directory ==="
./directory > directory.log 2>&1 &
DIRECTORY_PID=$!
sleep 3

echo "Directory 状态:"
ps aux | grep "[d]irectory" || echo "未运行"

echo ""
echo "=== 启动 Relay (Guard, port 9001) ==="
./relay -r guard -p 9001 > relay_guard.log 2>&1 &
RELAY1_PID=$!
sleep 2

echo ""
echo "=== 启动 Relay (Middle, port 9002) ==="
./relay -r middle -p 9002 > relay_middle.log 2>&1 &
RELAY2_PID=$!
sleep 2

echo ""
echo "=== 启动 Relay (Exit, port 9003) ==="
./relay -r exit -p 9003 > relay_exit.log 2>&1 &
RELAY3_PID=$!
sleep 2

echo ""
echo "=== 检查进程 ==="
ps aux | grep -E "[d]irectory|[r]elay" || echo "没有运行的进程"

echo ""
echo "=== 检查节点注册 ==="
curl -s http://127.0.0.1:5000/nodes | python3 -m json.tool || echo "查询失败"

echo ""
echo "=== 运行 Client ==="
./client 127.0.0.1 5000 pq 2>&1 | head -30
CLIENT_EXIT=${PIPESTATUS[0]}

echo ""
echo "=== Client 退出码: $CLIENT_EXIT ==="

echo ""
echo "=== Directory 日志 ==="
head -30 directory.log

echo ""
echo "=== Relay Guard 日志 ==="
cat relay_guard.log

echo ""
echo "=== Relay Middle 日志 ==="
cat relay_middle.log

echo ""
echo "=== Relay Exit 日志 ==="
cat relay_exit.log

# 清理
kill $DIRECTORY_PID $RELAY1_PID $RELAY2_PID $RELAY3_PID 2>/dev/null
"""

    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=90)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

    ssh.close()

if __name__ == "__main__":
    main()
