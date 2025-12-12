#!/usr/bin/env python3
"""
Phase 1 自动部署脚本 - 通过SSH部署到飞腾派并运行测试
使用paramiko库实现SSH连接和文件传输
"""

import paramiko
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 飞腾派连接信息
PI_CONFIG = {
    'hostname': '192.168.5.185',  # 使用185号飞腾派
    'username': 'user',
    'password': 'user',
    'port': 22
}

# 本地路径
LOCAL_BASE = '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c'
REMOTE_BASE = '/home/user/pq-ntor-experiment/sagin-experiments/docker/build_context/c'

# 需要传输的文件列表
FILES_TO_TRANSFER = [
    'benchmark/phase1_crypto_primitives.c',
    'src/kyber_kem.c',
    'src/crypto_utils.c',
    'src/pq_ntor.c',
    'include/kyber_kem.h',
    'include/crypto_utils.h',
    'include/pq_ntor.h',
    'include/ntor_utils.h',
    'Makefile',
    'run_phase1_on_pi.sh'
]


class PhytiumDeployer:
    """飞腾派部署器"""

    def __init__(self, config):
        self.config = config
        self.ssh = None
        self.sftp = None

    def connect(self):
        """建立SSH连接"""
        print(f"\n{'='*70}")
        print(f"🔌 正在连接飞腾派: {self.config['username']}@{self.config['hostname']}")
        print(f"{'='*70}")

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=self.config['hostname'],
                port=self.config['port'],
                username=self.config['username'],
                password=self.config['password'],
                timeout=10
            )
            self.sftp = self.ssh.open_sftp()
            print("✅ SSH连接成功!")
            return True
        except Exception as e:
            print(f"❌ SSH连接失败: {e}")
            return False

    def disconnect(self):
        """关闭连接"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print("\n🔌 SSH连接已关闭")

    def execute_command(self, command, print_output=True):
        """执行SSH命令"""
        if print_output:
            print(f"\n💻 执行命令: {command}")

        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()

        if print_output and output:
            print(output)
        if error and exit_status != 0:
            print(f"⚠️  错误输出: {error}")

        return exit_status, output, error

    def check_remote_environment(self):
        """检查远程环境"""
        print(f"\n{'='*70}")
        print("📋 检查飞腾派环境...")
        print(f"{'='*70}")

        # 检查CPU架构
        status, output, _ = self.execute_command("uname -m", print_output=False)
        arch = output.strip()
        print(f"CPU架构: {arch}")
        if arch != "aarch64":
            print("⚠️  警告: 不是ARM64架构!")

        # 检查CPU信息
        status, output, _ = self.execute_command(
            "lscpu | grep -E '(Model name|CPU MHz)' || cat /proc/cpuinfo | grep -E '(model name|cpu MHz)' | head -2",
            print_output=False
        )
        print(f"CPU信息:\n{output}")

        # 检查内存
        status, output, _ = self.execute_command("free -h | grep Mem", print_output=False)
        print(f"内存: {output.strip()}")

        # 检查liboqs
        status, output, _ = self.execute_command(
            "ls -lh ~/pq-ntor-experiment/_oqs/lib/liboqs.so* 2>/dev/null || echo 'liboqs未找到'",
            print_output=False
        )
        if "liboqs未找到" in output:
            print("❌ liboqs未安装! 需要先安装liboqs")
            return False
        else:
            print(f"✅ liboqs已安装: {output.strip()}")

        # 检查GCC
        status, output, _ = self.execute_command("gcc --version | head -1", print_output=False)
        print(f"GCC版本: {output.strip()}")

        # 检查OpenSSL
        status, output, _ = self.execute_command("openssl version", print_output=False)
        print(f"OpenSSL版本: {output.strip()}")

        print("✅ 环境检查完成!")
        return True

    def create_remote_directories(self):
        """创建远程目录结构"""
        print(f"\n{'='*70}")
        print("📁 创建远程目录结构...")
        print(f"{'='*70}")

        dirs = [
            REMOTE_BASE,
            f"{REMOTE_BASE}/benchmark",
            f"{REMOTE_BASE}/src",
            f"{REMOTE_BASE}/include"
        ]

        for dir_path in dirs:
            status, _, _ = self.execute_command(f"mkdir -p {dir_path}", print_output=False)
            if status == 0:
                print(f"✅ 创建目录: {dir_path}")
            else:
                print(f"⚠️  目录可能已存在: {dir_path}")

    def transfer_files(self):
        """传输文件到飞腾派"""
        print(f"\n{'='*70}")
        print("📤 传输文件到飞腾派...")
        print(f"{'='*70}")

        for file_path in FILES_TO_TRANSFER:
            local_file = os.path.join(LOCAL_BASE, file_path)
            remote_file = f"{REMOTE_BASE}/{file_path}"

            if not os.path.exists(local_file):
                print(f"⚠️  本地文件不存在,跳过: {file_path}")
                continue

            try:
                # 获取文件大小
                file_size = os.path.getsize(local_file)
                print(f"📄 传输: {file_path} ({file_size/1024:.1f} KB)...", end=' ')

                # 传输文件
                self.sftp.put(local_file, remote_file)

                # 如果是脚本文件,设置执行权限
                if file_path.endswith('.sh'):
                    self.execute_command(f"chmod +x {remote_file}", print_output=False)

                print("✅")
            except Exception as e:
                print(f"❌ 失败: {e}")
                return False

        print("✅ 所有文件传输完成!")
        return True

    def compile_phase1(self):
        """编译Phase 1测试程序"""
        print(f"\n{'='*70}")
        print("🔨 编译Phase 1测试程序...")
        print(f"{'='*70}")

        # 清理旧文件
        self.execute_command(f"cd {REMOTE_BASE} && make clean 2>/dev/null || true", print_output=False)

        # 编译
        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && make phase1_crypto_primitives"
        )

        if status == 0:
            print("✅ 编译成功!")
            # 检查可执行文件
            status, output, _ = self.execute_command(
                f"ls -lh {REMOTE_BASE}/phase1_crypto_primitives",
                print_output=False
            )
            print(f"可执行文件: {output.strip()}")
            return True
        else:
            print(f"❌ 编译失败!")
            print(f"错误输出: {error}")
            return False

    def run_phase1_test(self):
        """运行Phase 1测试"""
        print(f"\n{'='*70}")
        print("🚀 运行Phase 1性能测试...")
        print(f"{'='*70}")
        print("⏱️  预计耗时: 1-2分钟 (1000次迭代)")
        print("")

        # 设置CPU性能模式
        print("⚡ 设置CPU性能模式...")
        self.execute_command(
            "echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo '无sudo权限,使用默认CPU模式'",
            print_output=False
        )

        # 创建结果目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = f"/home/{self.config['username']}/phase1_results_{timestamp}"
        self.execute_command(f"mkdir -p {result_dir}", print_output=False)

        # 运行测试
        start_time = time.time()
        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && ./phase1_crypto_primitives 2>&1",
            print_output=True
        )
        elapsed_time = time.time() - start_time

        print(f"\n⏱️  测试耗时: {elapsed_time:.1f} 秒")

        if status != 0:
            print(f"❌ 测试运行失败!")
            print(f"错误: {error}")
            return None, None

        # 保存结果
        print(f"\n💾 保存结果到: {result_dir}")

        # 复制CSV文件
        self.execute_command(
            f"cp {REMOTE_BASE}/phase1_crypto_benchmarks.csv {result_dir}/",
            print_output=False
        )

        # 保存完整输出
        self.execute_command(
            f"echo '{output}' > {result_dir}/phase1_output.txt",
            print_output=False
        )

        # 保存系统信息
        self.execute_command(
            f"lscpu > {result_dir}/system_info.txt 2>&1 && "
            f"cat /proc/cpuinfo >> {result_dir}/system_info.txt 2>&1 && "
            f"free -h >> {result_dir}/system_info.txt 2>&1",
            print_output=False
        )

        print("✅ 结果保存完成!")

        return result_dir, output

    def download_results(self, remote_result_dir, local_result_dir):
        """下载测试结果"""
        print(f"\n{'='*70}")
        print("📥 下载测试结果到本地...")
        print(f"{'='*70}")

        # 创建本地目录
        os.makedirs(local_result_dir, exist_ok=True)

        # 下载文件
        files_to_download = [
            'phase1_crypto_benchmarks.csv',
            'phase1_output.txt',
            'system_info.txt'
        ]

        for filename in files_to_download:
            remote_file = f"{remote_result_dir}/{filename}"
            local_file = os.path.join(local_result_dir, filename)

            try:
                print(f"📥 下载: {filename}...", end=' ')
                self.sftp.get(remote_file, local_file)
                file_size = os.path.getsize(local_file)
                print(f"✅ ({file_size/1024:.1f} KB)")
            except Exception as e:
                print(f"❌ 失败: {e}")

        print(f"\n✅ 结果已下载到: {local_result_dir}")
        return local_result_dir

    def analyze_results(self, local_result_dir):
        """分析测试结果"""
        print(f"\n{'='*70}")
        print("📊 分析测试结果...")
        print(f"{'='*70}")

        csv_file = os.path.join(local_result_dir, 'phase1_crypto_benchmarks.csv')

        if not os.path.exists(csv_file):
            print("❌ CSV文件不存在!")
            return

        # 读取并显示CSV数据
        print("\n📈 性能测试结果:\n")
        with open(csv_file, 'r') as f:
            content = f.read()
            print(content)

        # 解析CSV并对比文献
        print("\n📊 与文献对比分析:")
        print(f"{'='*70}")

        # Berger et al. (2025) x86基准数据
        berger_data = {
            'Kyber-512 Keygen': 25.8,
            'Kyber-512 Encaps': 30.1,
            'Kyber-512 Decaps': 27.6
        }

        with open(csv_file, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # 跳过表头
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    operation = parts[0]
                    mean_us = float(parts[3])

                    # 查找对应的文献数据
                    for berger_op, berger_mean in berger_data.items():
                        if berger_op in operation:
                            ratio = mean_us / berger_mean
                            status = "✅" if 1.5 <= ratio <= 2.5 else "⚠️"

                            print(f"{status} {operation}:")
                            print(f"   本实验(ARM64): {mean_us:.2f} μs")
                            print(f"   Berger(x86):   {berger_mean:.2f} μs")
                            print(f"   ARM64/x86比率: {ratio:.2f}× ", end='')

                            if ratio < 1.0:
                                print("(异常: ARM64更快?)")
                            elif ratio > 3.0:
                                print("(异常: ARM64太慢)")
                            elif 1.5 <= ratio <= 2.5:
                                print("(✅ 正常范围)")
                            else:
                                print("(⚠️ 可疑)")
                            print()

        print(f"{'='*70}")
        print("📊 分析完成!")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 Phase 1 飞腾派自动部署与测试")
    print("="*70)
    print(f"目标设备: {PI_CONFIG['username']}@{PI_CONFIG['hostname']}")
    print(f"测试内容: Kyber-512, HKDF-SHA256, HMAC-SHA256 性能测试")
    print(f"测试规模: 1000次迭代 + 100次预热")
    print("="*70)

    deployer = PhytiumDeployer(PI_CONFIG)

    try:
        # 1. 连接飞腾派
        if not deployer.connect():
            return 1

        # 2. 检查环境
        if not deployer.check_remote_environment():
            print("\n❌ 环境检查失败,请先安装依赖(liboqs)")
            return 1

        # 3. 创建目录
        deployer.create_remote_directories()

        # 4. 传输文件
        if not deployer.transfer_files():
            return 1

        # 5. 编译
        if not deployer.compile_phase1():
            return 1

        # 6. 运行测试
        remote_result_dir, output = deployer.run_phase1_test()
        if not remote_result_dir:
            return 1

        # 7. 下载结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_result_dir = f"/home/ccc/pq-ntor-experiment/essay/phase1_results_phytium_{timestamp}"
        deployer.download_results(remote_result_dir, local_result_dir)

        # 8. 分析结果
        deployer.analyze_results(local_result_dir)

        # 完成
        print("\n" + "="*70)
        print("✅ Phase 1 部署与测试完成!")
        print("="*70)
        print(f"\n📁 本地结果目录: {local_result_dir}")
        print(f"📁 远程结果目录: {remote_result_dir}")
        print("\n🎯 下一步:")
        print("   1. 查看CSV结果: cat {}/phase1_crypto_benchmarks.csv".format(local_result_dir))
        print("   2. 验证性能范围是否正常 (ARM64应为x86的1.5-2.5倍)")
        print("   3. 如果结果正常,开始开发Phase 2 (协议握手测试)")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ 部署过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        deployer.disconnect()


if __name__ == '__main__':
    sys.exit(main())
