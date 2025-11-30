#!/usr/bin/env python3
"""
部署飞腾派优化版本并运行测试
"""

import paramiko
import time

# 配置
PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def main():
    print("=" * 60)
    print("  部署并运行飞腾派优化版本测试")
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
        sftp = ssh.open_sftp()

        # 上传优化版本
        print("上传飞腾派优化版测试脚本...")
        sftp.put("test_pq_ntor_phytium.py", f"{REMOTE_DIR}/test_pq_ntor_phytium.py")
        print("✓ 上传完成\n")

        # 设置权限
        ssh.exec_command(f"chmod +x {REMOTE_DIR}/test_pq_ntor_phytium.py")

        sftp.close()

        # 运行测试
        print("开始运行测试（这可能需要几分钟）...")
        print("-" * 60)

        command = f"cd {REMOTE_DIR} && python3 test_pq_ntor_phytium.py 2>&1"
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
            print("\n✓ 测试完成成功！")

            # 获取结果
            print("\n获取测试结果...")
            sftp = ssh.open_sftp()

            try:
                # CSV结果
                print("\n" + "=" * 60)
                print("飞腾派测试结果 (performance_summary.csv):")
                print("=" * 60)
                with sftp.open(f"{REMOTE_DIR}/results/performance_summary.csv", 'r') as f:
                    csv_content = f.read().decode('utf-8')
                    print(csv_content)

                # 下载结果文件到本地
                print("\n下载结果文件到本地...")
                import os
                os.makedirs("phytium_results", exist_ok=True)

                files = ["performance_summary.csv", "handshake_times.json"]
                for fname in files:
                    try:
                        sftp.get(
                            f"{REMOTE_DIR}/results/{fname}",
                            f"phytium_results/{fname}"
                        )
                        print(f"  ✓ 下载: {fname}")
                    except:
                        pass

                try:
                    sftp.get(
                        f"{REMOTE_DIR}/results/comparison_plots.png",
                        f"phytium_results/comparison_plots.png"
                    )
                    print(f"  ✓ 下载: comparison_plots.png")
                except:
                    print(f"  - 跳过: comparison_plots.png (可能未生成)")

                print(f"\n✓ 结果已保存到: phytium_results/")

            except Exception as e:
                print(f"获取结果时出错: {e}")
            finally:
                sftp.close()

        else:
            print(f"\n✗ 测试失败 (退出码: {exit_status})")

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
