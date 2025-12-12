#!/usr/bin/env python3
"""检查飞腾派上directory_server.c的IP配置"""

import paramiko

PI_IP = "192.168.5.186"
USERNAME = "user"
PASSWORD = "user"

def check_directory_config():
    """检查directory_server.c的配置"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        # 检查文件是否存在
        stdin, stdout, stderr = ssh.exec_command(
            "test -f /home/user/pq-ntor-experiment/sagin-experiments/docker/build_context/c/src/directory_server.c && echo 'EXISTS' || echo 'NOT_FOUND'"
        )
        exists = stdout.read().decode().strip()

        if exists == "NOT_FOUND":
            print("❌ directory_server.c 文件不存在")
            ssh.close()
            return

        print("✅ directory_server.c 文件存在")
        print()

        # 读取node配置
        stdin, stdout, stderr = ssh.exec_command(
            "grep -A30 'static node_info_t nodes' /home/user/pq-ntor-experiment/sagin-experiments/docker/build_context/c/src/directory_server.c | head -40"
        )
        config = stdout.read().decode()

        print("📋 当前配置:")
        print("=" * 70)
        print(config)
        print("=" * 70)

        # 检查是否是localhost配置
        if "127.0.0.1" in config:
            print()
            print("⚠️  发现localhost配置 (127.0.0.1) - 这是WSL2测试用的")
            print("   物理集群需要使用实际IP地址")
        elif "192.168.5" in config:
            print()
            print("✅ 使用物理集群IP (192.168.5.x) - 配置正确")
        elif "172.20" in config:
            print()
            print("⚠️  使用SAGIN网络IP (172.20.x.x) - 可能需要更新")

        ssh.close()

    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("  检查飞腾派 directory_server.c 配置")
    print("=" * 70)
    print()
    check_directory_config()
