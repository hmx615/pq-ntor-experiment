#!/usr/bin/env python3
"""
在飞腾派上只编译benchmark_pq_ntor (不编译classic_ntor)
"""

import paramiko

PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def main():
    print("=" * 60)
    print("  在飞腾派上编译benchmark_pq_ntor (PQ-only)")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PHYTIUM_IP, username=PHYTIUM_USER, password=PHYTIUM_PASS)

    try:
        print("\n编译策略: 只编译PQ-NTOR相关代码，跳过classic_ntor\n")

        # 创建自定义编译脚本
        compile_script = """#!/bin/bash
set -e

cd /home/user/pq-ntor-test/c

echo "Step 1: 编译依赖的.o文件..."

# 编译kyber_kem.o
echo "  - kyber_kem.o"
gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc -c src/kyber_kem.c -o src/kyber_kem.o

# 编译crypto_utils.o
echo "  - crypto_utils.o"
gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc -c src/crypto_utils.c -o src/crypto_utils.o

# 编译pq_ntor.o
echo "  - pq_ntor.o"
gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc -c src/pq_ntor.c -o src/pq_ntor.o

echo ""
echo "Step 2: 链接benchmark_pq_ntor..."

gcc -O2 -g -o benchmark_pq_ntor \\
    benchmark/benchmark_pq_ntor.c \\
    src/kyber_kem.o \\
    src/crypto_utils.o \\
    src/pq_ntor.o \\
    -I/home/user/_oqs/include \\
    -Isrc \\
    -L/home/user/_oqs/lib \\
    -loqs \\
    -lssl -lcrypto -lm

echo ""
echo "Step 3: 验证..."
file benchmark_pq_ntor
ls -lh benchmark_pq_ntor

echo ""
echo "✓ 编译完成！"
"""

        # 上传编译脚本
        print("上传编译脚本...")
        sftp = ssh.open_sftp()
        sftp.open(f"{REMOTE_DIR}/c/compile_benchmark.sh", 'w').write(compile_script.encode('utf-8'))
        sftp.close()

        # 执行编译
        print("\n开始编译...")
        print("-" * 60)

        stdin, stdout, stderr = ssh.exec_command(
            f"cd {REMOTE_DIR}/c && chmod +x compile_benchmark.sh && ./compile_benchmark.sh 2>&1",
            get_pty=True
        )

        for line in iter(stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break

        exit_status = stdout.channel.recv_exit_status()

        print("-" * 60)

        if exit_status == 0:
            print("\n✓ 编译成功！")

            # 测试运行
            print("\n测试运行 (10次握手)...")
            print("-" * 60)

            stdin, stdout, stderr = ssh.exec_command(
                f"cd {REMOTE_DIR}/c && ./benchmark_pq_ntor 10 2>&1",
                get_pty=True
            )

            out = stdout.read().decode('utf-8')
            print(out)

            print("-" * 60)

            # 复制到测试目录
            print("\n复制到测试目录...")
            ssh.exec_command(f"cp {REMOTE_DIR}/c/benchmark_pq_ntor {REMOTE_DIR}/")

            print("\n" + "=" * 60)
            print("✓ 准备完成！可以运行测试了")
            print("=" * 60)

            # 运行完整测试
            print("\n是否继续运行完整测试？开始测试...")

            stdin, stdout, stderr = ssh.exec_command(
                f"cd {REMOTE_DIR} && python3 test_pq_ntor_phytium.py 2>&1",
                get_pty=True
            )

            print("\n" + "=" * 60)
            print("飞腾派PQ-NTOR性能测试")
            print("=" * 60 + "\n")

            for line in iter(stdout.readline, ''):
                if line:
                    print(line, end='')
                else:
                    break

            test_exit = stdout.channel.recv_exit_status()

            if test_exit == 0:
                print("\n✓ 测试完成！")

                # 下载结果
                print("\n下载测试结果...")
                import os
                os.makedirs("phytium_results", exist_ok=True)

                sftp = ssh.open_sftp()

                try:
                    # 下载CSV
                    sftp.get(
                        f"{REMOTE_DIR}/results/performance_summary.csv",
                        "phytium_results/performance_summary.csv"
                    )
                    print("  ✓ performance_summary.csv")

                    # 下载JSON
                    sftp.get(
                        f"{REMOTE_DIR}/results/handshake_times.json",
                        "phytium_results/handshake_times.json"
                    )
                    print("  ✓ handshake_times.json")

                    # 显示结果
                    with sftp.open(f"{REMOTE_DIR}/results/performance_summary.csv", 'r') as f:
                        csv_content = f.read().decode('utf-8')

                    print("\n" + "=" * 60)
                    print("飞腾派测试结果:")
                    print("=" * 60)
                    print(csv_content)

                    print("\n结果已保存到: phytium_results/")

                except Exception as e:
                    print(f"下载结果失败: {e}")

                sftp.close()

            else:
                print(f"\n✗ 测试失败 (退出码: {test_exit})")

        else:
            print(f"\n✗ 编译失败 (退出码: {exit_status})")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
