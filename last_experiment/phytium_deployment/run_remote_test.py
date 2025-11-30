#!/usr/bin/env python3
"""
在飞腾派上远程执行PQ-NTOR测试
"""

import paramiko
import time

# 配置
PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def run_remote_test():
    """在飞腾派上远程运行测试"""

    print("=" * 60)
    print("  在飞腾派上运行PQ-NTOR测试")
    print("=" * 60)

    # 连接SSH
    print(f"\n连接到飞腾派 {PHYTIUM_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            PHYTIUM_IP,
            username=PHYTIUM_USER,
            password=PHYTIUM_PASS,
            timeout=10
        )
        print("✓ SSH连接成功\n")

        # 修改测试脚本中的路径（因为benchmark在同一目录）
        print("准备测试环境...")

        # 创建一个包装脚本来修改路径
        wrapper_script = f"""#!/bin/bash
cd {REMOTE_DIR}

# 临时修改benchmark路径
sed -i 's|../c/benchmark_pq_ntor|./benchmark_pq_ntor|g' test_pq_ntor_single_machine.py

# 运行测试
python3 test_pq_ntor_single_machine.py

# 恢复原路径
sed -i 's|./benchmark_pq_ntor|../c/benchmark_pq_ntor|g' test_pq_ntor_single_machine.py
"""

        # 执行测试
        print("开始测试...\n")
        print("-" * 60)

        command = f"cd {REMOTE_DIR} && sed -i 's|../c/benchmark_pq_ntor|./benchmark_pq_ntor|g' test_pq_ntor_single_machine.py && python3 test_pq_ntor_single_machine.py"

        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

        # 实时输出
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end='')

        # 等待命令完成
        exit_status = stdout.channel.recv_exit_status()

        print("-" * 60)

        if exit_status == 0:
            print("\n✓ 测试完成成功！")

            # 获取结果文件
            print("\n获取测试结果...")
            sftp = ssh.open_sftp()

            try:
                # 检查results目录
                try:
                    sftp.stat(f"{REMOTE_DIR}/results")
                    print("✓ results目录存在")

                    # 列出结果文件
                    files = sftp.listdir(f"{REMOTE_DIR}/results")
                    print(f"\n生成的结果文件:")
                    for f in files:
                        print(f"  - {f}")

                    # 读取CSV内容
                    if "performance_summary.csv" in files:
                        print("\n" + "=" * 60)
                        print("性能测试结果 (performance_summary.csv):")
                        print("=" * 60)
                        with sftp.open(f"{REMOTE_DIR}/results/performance_summary.csv", 'r') as f:
                            print(f.read().decode('utf-8'))

                except IOError:
                    print("✗ results目录不存在，测试可能失败")

            finally:
                sftp.close()

        else:
            print(f"\n✗ 测试失败 (退出码: {exit_status})")

            # 输出错误信息
            error = stderr.read().decode('utf-8')
            if error:
                print("\n错误信息:")
                print(error)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ssh.close()

if __name__ == "__main__":
    run_remote_test()
