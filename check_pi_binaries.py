#!/usr/bin/env python3
"""检查飞腾派上已有的二进制文件"""

import paramiko

PI_IP = "192.168.5.186"
USERNAME = "user"
PASSWORD = "user"

def check_binaries():
    """检查Pi上的二进制文件"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        # 检查目录结构
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /home/user/pq-ntor-experiment/sagin-experiments/docker/build_context/c/ 2>/dev/null | head -20"
        )
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error and "No such file" in error:
            print("❌ C程序目录不存在")
            print()
            print("需要完整部署以下内容:")
            print("  - 编译好的二进制文件 (directory, relay, client)")
            print("  - 12拓扑配置文件 (topo01-12_tor_mapping.json)")
            print("  - 测试脚本 (run_simple_test.py)")
        else:
            print("✅ C程序目录存在")
            print()
            print("目录内容:")
            print("=" * 70)
            print(output)
            print("=" * 70)

        ssh.close()

    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("  检查飞腾派 Pi-186 二进制文件")
    print("=" * 70)
    print()
    check_binaries()
