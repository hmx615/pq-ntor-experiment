#!/usr/bin/env python3
"""
飞腾派自动部署脚本
使用paramiko库进行SSH连接和文件传输
"""

import os
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("错误: paramiko未安装")
    print("安装命令: pip3 install paramiko")
    sys.exit(1)

# 配置
PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def connect_ssh():
    """建立SSH连接"""
    print(f"连接到飞腾派 {PHYTIUM_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            PHYTIUM_IP,
            username=PHYTIUM_USER,
            password=PHYTIUM_PASS,
            timeout=10
        )
        print("✓ SSH连接成功")
        return ssh
    except Exception as e:
        print(f"✗ SSH连接失败: {e}")
        return None

def run_command(ssh, command, description=""):
    """执行远程命令"""
    if description:
        print(f"\n执行: {description}")

    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if output:
        print(output)
    if error and exit_status != 0:
        print(f"错误: {error}")

    return exit_status == 0, output

def transfer_file(ssh, local_path, remote_path):
    """传输文件到飞腾派"""
    sftp = ssh.open_sftp()
    try:
        print(f"  传输: {os.path.basename(local_path)}")
        sftp.put(local_path, remote_path)
        print(f"  ✓ 完成")
        return True
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("=" * 60)
    print("  PQ-NTOR测试脚本 - 飞腾派自动部署工具")
    print("=" * 60)

    # 连接SSH
    ssh = connect_ssh()
    if not ssh:
        sys.exit(1)

    try:
        # 步骤1: 检查飞腾派环境
        print("\n步骤 1/5: 检查飞腾派环境...")
        success, arch = run_command(ssh, "uname -m")
        if success:
            print(f"  架构: {arch}")

        success, py_version = run_command(ssh, "python3 --version")
        if success:
            print(f"  Python: {py_version}")

        # 步骤2: 创建远程目录
        print("\n步骤 2/5: 创建远程目录...")
        run_command(ssh, f"mkdir -p {REMOTE_DIR}", f"mkdir -p {REMOTE_DIR}")

        # 步骤3: 传输测试文件
        print("\n步骤 3/5: 传输测试文件...")

        files_to_transfer = [
            ("test_pq_ntor_single_machine.py", f"{REMOTE_DIR}/test_pq_ntor_single_machine.py"),
            ("topology_tc_params.json", f"{REMOTE_DIR}/topology_tc_params.json"),
        ]

        # 检查benchmark程序
        benchmark_path = "../../c/benchmark_pq_ntor"
        if os.path.exists(benchmark_path):
            print("  发现benchmark程序")
            files_to_transfer.append((benchmark_path, f"{REMOTE_DIR}/benchmark_pq_ntor"))
        else:
            print("  警告: benchmark_pq_ntor未找到，需要在飞腾派上编译")

        for local, remote in files_to_transfer:
            if os.path.exists(local):
                transfer_file(ssh, local, remote)

        # 步骤4: 设置权限
        print("\n步骤 4/5: 设置权限...")
        run_command(ssh, f"chmod +x {REMOTE_DIR}/test_pq_ntor_single_machine.py")
        if os.path.exists(benchmark_path):
            run_command(ssh, f"chmod +x {REMOTE_DIR}/benchmark_pq_ntor")

        # 步骤5: 验证部署
        print("\n步骤 5/5: 验证部署...")
        run_command(ssh, f"ls -lh {REMOTE_DIR}", "列出部署文件")

        # 完成
        print("\n" + "=" * 60)
        print("✓ 部署完成！")
        print("=" * 60)

        print(f"\n下一步操作:")
        print(f"1. SSH登录到飞腾派:")
        print(f"   ssh {PHYTIUM_USER}@{PHYTIUM_IP}  (密码: {PHYTIUM_PASS})")
        print(f"\n2. 运行测试:")
        print(f"   cd {REMOTE_DIR}")
        print(f"   python3 test_pq_ntor_single_machine.py")
        print(f"\n3. 查看结果:")
        print(f"   cat results/performance_summary.csv")

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
