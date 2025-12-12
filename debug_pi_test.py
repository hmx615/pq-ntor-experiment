#!/usr/bin/env python3
"""调试主派上的测试脚本"""

import paramiko

PI_IP = "192.168.5.110"
USERNAME = "user"
PASSWORD = "user"

def debug_test():
    """调试测试脚本"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        print("=" * 70)
        print("  调试主派测试脚本")
        print("=" * 70)
        print()

        # 直接运行测试脚本，查看详细错误
        cmd = """
cd /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment/scripts && \
python3 run_simple_test.py --topo 1 --runs 1 2>&1 | head -50
"""
        print("🔍 运行单个拓扑测试（调试模式）...")
        print()

        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        output = stdout.read().decode()
        error = stderr.read().decode()

        print("输出:")
        print("=" * 70)
        print(output)
        print("=" * 70)

        if error:
            print()
            print("错误:")
            print("=" * 70)
            print(error)
            print("=" * 70)

        ssh.close()

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    debug_test()
