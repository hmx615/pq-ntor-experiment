#!/usr/bin/env python3
"""
在飞腾派上编译benchmark_pq_ntor
"""

import paramiko
import os

PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
PHYTIUM_PASS = "user"
REMOTE_DIR = "/home/user/pq-ntor-test"

def main():
    print("=" * 60)
    print("  在飞腾派上编译PQ-NTOR benchmark程序")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PHYTIUM_IP, username=PHYTIUM_USER, password=PHYTIUM_PASS)

    try:
        # 1. 检查编译工具
        print("\n步骤 1/4: 检查编译环境...")
        commands = [
            ("gcc --version", "检查GCC"),
            ("make --version", "检查Make"),
        ]

        for cmd, desc in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8').split('\n')[0]
            if out:
                print(f"  ✓ {desc}: {out}")

        # 2. 上传源码
        print("\n步骤 2/4: 上传PQ-NTOR源码...")

        # 找到所有需要的C源码文件
        c_dir = "../../c"
        if not os.path.exists(c_dir):
            print("错误: 找不到c目录")
            return

        # 创建远程c目录
        ssh.exec_command(f"mkdir -p {REMOTE_DIR}/c")

        sftp = ssh.open_sftp()

        # 上传必要的文件
        files_to_upload = [
            "benchmark_pq_ntor.c",
            "pq_ntor.c",
            "pq_ntor.h",
            "Makefile",
        ]

        for fname in files_to_upload:
            local_path = os.path.join(c_dir, fname)
            if os.path.exists(local_path):
                print(f"  上传: {fname}")
                sftp.put(local_path, f"{REMOTE_DIR}/c/{fname}")
            else:
                print(f"  警告: {fname} 不存在")

        # 检查是否有lib目录
        lib_dir = os.path.join(c_dir, "lib")
        if os.path.exists(lib_dir):
            print("  上传: lib/ 目录...")
            ssh.exec_command(f"mkdir -p {REMOTE_DIR}/c/lib")
            for root, dirs, files in os.walk(lib_dir):
                for file in files:
                    local_file = os.path.join(root, file)
                    # 计算相对路径
                    rel_path = os.path.relpath(local_file, c_dir)
                    remote_file = f"{REMOTE_DIR}/c/{rel_path}"
                    # 创建远程目录
                    remote_dir = os.path.dirname(remote_file)
                    ssh.exec_command(f"mkdir -p {remote_dir}")
                    sftp.put(local_file, remote_file)

        sftp.close()

        # 3. 编译
        print("\n步骤 3/4: 编译benchmark程序...")
        print("-" * 60)

        command = f"cd {REMOTE_DIR}/c && make benchmark_pq_ntor 2>&1"
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

        for line in iter(stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break

        print("-" * 60)

        # 4. 验证编译结果
        print("\n步骤 4/4: 验证编译结果...")

        stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR}/c && file benchmark_pq_ntor")
        out = stdout.read().decode('utf-8')
        print(f"  文件类型: {out.strip()}")

        # 测试运行
        print("\n尝试运行benchmark程序...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR}/c && ./benchmark_pq_ntor 5 2>&1")
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')

        if out:
            print(out)
        if err and "error" in err.lower():
            print(f"错误: {err}")

        # 复制到测试目录
        print("\n复制到测试目录...")
        ssh.exec_command(f"cp {REMOTE_DIR}/c/benchmark_pq_ntor {REMOTE_DIR}/")
        print("  ✓ 完成")

        print("\n" + "=" * 60)
        print("✓ 编译完成！")
        print("=" * 60)

        print("\n现在可以运行测试:")
        print(f"  cd {REMOTE_DIR}")
        print(f"  python3 test_pq_ntor_phytium.py")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
