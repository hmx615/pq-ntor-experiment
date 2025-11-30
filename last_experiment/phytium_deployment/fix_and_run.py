#!/usr/bin/env python3
"""
修复路径并在飞腾派上运行测试
"""

import paramiko

# 配置
PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def main():
    print("=" * 60)
    print("  修复并运行飞腾派测试")
    print("=" * 60)

    # 连接SSH
    print(f"\n连接到飞腾派 {PHYTIUM_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        PHYTIUM_IP,
        username=PHYTIUM_USER,
        password=PHYTIUM_PASS,
        timeout=10
    )
    print("✓ SSH连接成功\n")

    try:
        # 读取原始测试脚本
        sftp = ssh.open_sftp()
        print("读取测试脚本...")
        with sftp.open(f"{REMOTE_DIR}/test_pq_ntor_single_machine.py", 'r') as f:
            content = f.read().decode('utf-8')

        # 修改benchmark路径
        print("修改benchmark程序路径...")
        content = content.replace(
            'BENCHMARK_PATH = "../c/benchmark_pq_ntor"',
            'BENCHMARK_PATH = "./benchmark_pq_ntor"'
        )

        # 也修改检查路径的部分
        content = content.replace(
            'Path("../c/benchmark_pq_ntor")',
            'Path("./benchmark_pq_ntor")'
        )

        # 写回文件
        print("保存修改后的脚本...")
        with sftp.open(f"{REMOTE_DIR}/test_pq_ntor_single_machine.py", 'w') as f:
            f.write(content.encode('utf-8'))

        sftp.close()
        print("✓ 路径修复完成\n")

        # 运行测试
        print("开始运行测试...")
        print("-" * 60)

        command = f"cd {REMOTE_DIR} && python3 test_pq_ntor_single_machine.py 2>&1"
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

        # 实时输出
        for line in iter(stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break

        exit_status = stdout.channel.recv_exit_status()

        print("-" * 60)

        if exit_status == 0:
            print("\n✓ 测试完成！")

            # 获取CSV结果
            print("\n获取测试结果...")
            sftp = ssh.open_sftp()
            try:
                with sftp.open(f"{REMOTE_DIR}/results/performance_summary.csv", 'r') as f:
                    csv_content = f.read().decode('utf-8')

                print("\n" + "=" * 60)
                print("飞腾派测试结果 (performance_summary.csv):")
                print("=" * 60)
                print(csv_content)

            except IOError as e:
                print(f"无法读取结果文件: {e}")
            finally:
                sftp.close()

        else:
            print(f"\n✗ 测试失败 (退出码: {exit_status})")

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
