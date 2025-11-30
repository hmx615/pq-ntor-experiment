#!/usr/bin/env python3
"""
上传完整c目录到飞腾派并编译
"""

import paramiko
import os
import time

PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def upload_directory(sftp, ssh, local_dir, remote_dir):
    """递归上传目录"""

    # 创建远程目录
    try:
        sftp.stat(remote_dir)
    except IOError:
        ssh.exec_command(f"mkdir -p {remote_dir}")

    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"

        if os.path.isfile(local_path):
            print(f"  上传: {item}")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            # 跳过不需要的目录
            if item in ['.git', '__pycache__', '.vscode', 'build']:
                continue
            print(f"  目录: {item}/")
            upload_directory(sftp, ssh, local_path, remote_path)

def main():
    print("=" * 60)
    print("  上传PQ-NTOR源码到飞腾派并编译")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PHYTIUM_IP, username=PHYTIUM_USER, password=PHYTIUM_PASS)

    try:
        # 1. 检查编译环境
        print("\n步骤 1/4: 检查编译环境...")
        stdin, stdout, stderr = ssh.exec_command("gcc --version && make --version")
        out = stdout.read().decode('utf-8').split('\n')[0]
        print(f"  ✓ GCC: {out}")

        # 2. 上传整个c目录
        print("\n步骤 2/4: 上传PQ-NTOR源码（这可能需要几分钟）...")

        c_dir = "/home/ccc/pq-ntor-experiment/c"
        if not os.path.exists(c_dir):
            print(f"错误: 找不到c目录: {c_dir}")
            return

        sftp = ssh.open_sftp()
        remote_c_dir = f"{REMOTE_DIR}/c"

        print(f"  上传目录: {c_dir} -> {remote_c_dir}")
        upload_directory(sftp, ssh, c_dir, remote_c_dir)

        sftp.close()

        print("\n  ✓ 上传完成")

        # 3. 清理并编译
        print("\n步骤 3/4: 编译benchmark程序...")
        print("-" * 60)

        commands = [
            "cd /home/user/pq-ntor-test/c",
            "make clean",
            "make benchmark_pq_ntor"
        ]

        command = " && ".join(commands) + " 2>&1"
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

        for line in iter(stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break

        exit_status = stdout.channel.recv_exit_status()

        print("-" * 60)

        if exit_status != 0:
            print("\n✗ 编译失败")
            return

        # 4. 验证并测试
        print("\n步骤 4/4: 验证编译结果...")

        # 检查文件类型
        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_c_dir} && file benchmark_pq_ntor")
        out = stdout.read().decode('utf-8')
        print(f"\n  文件类型: {out.strip()}")

        # 测试运行
        print("\n  测试运行 (5次握手)...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_c_dir} && ./benchmark_pq_ntor 5 2>&1", get_pty=True)
        out = stdout.read().decode('utf-8')
        print(out)

        # 复制到测试目录
        print("  复制到测试目录...")
        ssh.exec_command(f"cp {remote_c_dir}/benchmark_pq_ntor {REMOTE_DIR}/")

        print("\n" + "=" * 60)
        print("✓ 编译完成！")
        print("=" * 60)

        # 现在运行测试
        print("\n继续运行完整测试？")
        print("运行测试脚本...")

        stdin, stdout, stderr = ssh.exec_command(
            f"cd {REMOTE_DIR} && python3 test_pq_ntor_phytium.py 2>&1",
            get_pty=True
        )

        print("\n" + "=" * 60)
        print("飞腾派测试运行中...")
        print("=" * 60 + "\n")

        for line in iter(stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break

        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            print("\n✓ 测试完成成功！")

            # 下载结果
            print("\n下载测试结果...")
            os.makedirs("phytium_results", exist_ok=True)

            sftp = ssh.open_sftp()
            files = ["performance_summary.csv", "handshake_times.json"]

            for fname in files:
                try:
                    sftp.get(
                        f"{REMOTE_DIR}/results/{fname}",
                        f"phytium_results/{fname}"
                    )
                    print(f"  ✓ 下载: {fname}")
                except Exception as e:
                    print(f"  ✗ {fname}: {e}")

            # 显示CSV结果
            try:
                with sftp.open(f"{REMOTE_DIR}/results/performance_summary.csv", 'r') as f:
                    csv_content = f.read().decode('utf-8')

                print("\n" + "=" * 60)
                print("飞腾派测试结果:")
                print("=" * 60)
                print(csv_content)

            except:
                pass

            sftp.close()

        else:
            print(f"\n✗ 测试失败 (退出码: {exit_status})")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
