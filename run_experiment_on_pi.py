#!/usr/bin/env python3
"""在主派上启动12拓扑实验"""

import paramiko
import time

PI_IP = "192.168.5.110"
USERNAME = "user"
PASSWORD = "user"

def run_experiment():
    """在主派上运行实验"""
    try:
        print("=" * 70)
        print("  在主派 (192.168.5.110) 上启动12拓扑实验")
        print("=" * 70)
        print()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("📡 连接到主派...")
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)
        print("✅ SSH连接成功")
        print()

        # 检查目录和文件
        print("📁 检查实验环境...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment && "
            "ls -la configs/ scripts/ 2>&1 | head -20"
        )
        output = stdout.read().decode()
        print(output)

        # 启动实验（后台运行）
        print("=" * 70)
        print("🚀 启动实验...")
        print("=" * 70)
        print()

        cmd = """
cd /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment/scripts && \
nohup python3 run_simple_test.py --all --runs 10 > /tmp/experiment_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo $! > /tmp/experiment.pid
sleep 2
PID=$(cat /tmp/experiment.pid 2>/dev/null)
if [ -n "$PID" ] && ps -p $PID > /dev/null 2>&1; then
    echo "✅ 实验已启动，PID: $PID"
    echo "日志文件: /tmp/experiment_*.log"
else
    echo "❌ 实验启动失败"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()

        print(output)
        if error:
            print("stderr:", error)

        print()
        print("=" * 70)
        print("📊 实验监控")
        print("=" * 70)
        print()
        print("实验将在后台运行，预计需要 30-60 分钟完成")
        print()
        print("监控命令（在主派上运行）：")
        print("  ssh user@192.168.5.110")
        print("  tail -f /tmp/experiment_*.log")
        print()
        print("或使用以下命令查看实时进度：")
        print("  watch -n 5 'ls -lh /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment/results/local_wsl/*.json | wc -l'")
        print()

        # 等待几秒，显示初始日志
        print("等待5秒，查看初始日志...")
        time.sleep(5)

        stdin, stdout, stderr = ssh.exec_command(
            "tail -30 /tmp/experiment_*.log 2>/dev/null | tail -20"
        )
        initial_log = stdout.read().decode()

        if initial_log.strip():
            print()
            print("=" * 70)
            print("📝 初始日志输出:")
            print("=" * 70)
            print(initial_log)

        ssh.close()

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    run_experiment()
