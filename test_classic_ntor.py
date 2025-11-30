#!/usr/bin/env python3
"""
在飞腾派上编译并测试Classic NTOR性能
"""
import paramiko
import sys

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

def exec_cmd(ssh, cmd, desc=""):
    if desc:
        print(f"\n{'='*70}")
        print(f"  {desc}")
        print('='*70)

    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120, get_pty=True)
    output = stdout.read().decode('utf-8')
    print(output)
    return output

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10,
               allow_agent=False, look_for_keys=False)
    print("✅ SSH连接成功\n")

    # 上传benchmark文件
    print("上传Classic NTOR benchmark代码...")
    sftp = ssh.open_sftp()
    sftp.put(
        "/home/ccc/pq-ntor-experiment/c/benchmark/benchmark_classic_ntor.c",
        "/home/user/pq-ntor-experiment/c/benchmark/benchmark_classic_ntor.c"
    )
    sftp.close()
    print("✓ 上传完成\n")

    # 编译
    exec_cmd(
        ssh,
        """
        cd ~/pq-ntor-experiment/c

        echo "编译benchmark_classic_ntor..."
        gcc -Wall -Wextra -O2 -g -std=c99 \\
            -o benchmark_classic_ntor \\
            benchmark/benchmark_classic_ntor.c \\
            -lssl -lcrypto -lm -lpthread

        ls -lh benchmark_classic_ntor 2>&1
        """,
        "编译Classic NTOR benchmark"
    )

    # 运行测试
    exec_cmd(
        ssh,
        """
        cd ~/pq-ntor-experiment/c
        ./benchmark_classic_ntor 1000
        """,
        "运行Classic NTOR性能测试（1000次）"
    )

    # 保存结果
    exec_cmd(
        ssh,
        """
        cd ~/pq-ntor-experiment/c
        ./benchmark_classic_ntor 1000 > ~/classic_ntor_results.txt 2>&1
        echo "结果已保存到 ~/classic_ntor_results.txt"
        """,
        "保存测试结果"
    )

    print("\n" + "="*70)
    print("  ✅ Classic NTOR测试完成")
    print("="*70)
    print("\n下一步:")
    print("  1. 查看结果: ssh user@192.168.5.110 'cat ~/classic_ntor_results.txt'")
    print("  2. 与PQ-NTOR对比分析")
    print("  3. 生成对比可视化图表")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
