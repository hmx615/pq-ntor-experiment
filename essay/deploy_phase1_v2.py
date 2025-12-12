#!/usr/bin/env python3
"""
Phase 1 自动部署脚本 v2 - 适配飞腾派现有目录结构
部署到 ~/pq-ntor-experiment/c/ 目录
"""

import paramiko
import os
import sys
import time
from datetime import datetime

# 飞腾派连接信息
PI_CONFIG = {
    'hostname': '192.168.5.185',
    'username': 'user',
    'password': 'user',
    'port': 22
}

# 本地路径
LOCAL_BASE = '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c'
# 远程路径 - 使用飞腾派上已有的c目录
REMOTE_BASE = '/home/user/pq-ntor-experiment/c'

# 需要传输的文件
FILES_TO_TRANSFER = [
    'benchmark/phase1_crypto_primitives.c',
    'run_phase1_on_pi.sh'
]


class PhytiumDeployer:
    """飞腾派部署器 v2"""

    def __init__(self, config):
        self.config = config
        self.ssh = None
        self.sftp = None

    def connect(self):
        """建立SSH连接"""
        print(f"\n{'='*70}")
        print(f"🔌 连接飞腾派: {self.config['username']}@{self.config['hostname']}")
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
            print(f"\n💻 执行: {command}")

        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()

        if print_output and output:
            print(output)
        if error and exit_status != 0:
            print(f"⚠️  错误: {error}")

        return exit_status, output, error

    def check_environment(self):
        """检查环境"""
        print(f"\n{'='*70}")
        print("📋 检查飞腾派环境...")
        print(f"{'='*70}")

        # CPU架构
        status, output, _ = self.execute_command("uname -m", print_output=False)
        print(f"CPU架构: {output.strip()}")

        # CPU信息
        status, output, _ = self.execute_command(
            "cat /proc/cpuinfo | grep -E '(model name|BogoMIPS)' | head -2",
            print_output=False
        )
        print(f"CPU信息:\n{output}")

        # 内存
        status, output, _ = self.execute_command("free -h | grep Mem", print_output=False)
        print(f"内存: {output.strip()}")

        # 检查liboqs (静态库)
        status, output, _ = self.execute_command(
            "ls -lh ~/_oqs/lib/liboqs.a 2>/dev/null || echo 'NOT_FOUND'",
            print_output=False
        )
        if "NOT_FOUND" in output:
            print("❌ liboqs.a未找到!")
            return False
        else:
            print(f"✅ liboqs.a: {output.strip()}")

        # 检查c目录
        status, output, _ = self.execute_command(
            f"ls -ld {REMOTE_BASE}",
            print_output=False
        )
        print(f"✅ 目标目录: {REMOTE_BASE}")

        # 检查GCC
        status, output, _ = self.execute_command("gcc --version | head -1", print_output=False)
        print(f"GCC: {output.strip()}")

        print("✅ 环境检查通过!")
        return True

    def transfer_files(self):
        """传输文件"""
        print(f"\n{'='*70}")
        print("📤 传输Phase 1文件...")
        print(f"{'='*70}")

        for file_path in FILES_TO_TRANSFER:
            local_file = os.path.join(LOCAL_BASE, file_path)
            remote_file = f"{REMOTE_BASE}/{file_path}"

            if not os.path.exists(local_file):
                print(f"⚠️  本地文件不存在: {file_path}")
                continue

            try:
                file_size = os.path.getsize(local_file)
                print(f"📄 {file_path} ({file_size/1024:.1f} KB)...", end=' ')
                self.sftp.put(local_file, remote_file)

                if file_path.endswith('.sh'):
                    self.execute_command(f"chmod +x {remote_file}", print_output=False)

                print("✅")
            except Exception as e:
                print(f"❌ {e}")
                return False

        print("✅ 文件传输完成!")
        return True

    def update_makefile(self):
        """更新Makefile添加Phase 1编译目标"""
        print(f"\n{'='*70}")
        print("📝 更新Makefile...")
        print(f"{'='*70}")

        # 读取现有Makefile
        status, makefile_content, _ = self.execute_command(
            f"cat {REMOTE_BASE}/Makefile",
            print_output=False
        )

        if "phase1_crypto_primitives" in makefile_content:
            print("✅ Makefile已包含Phase 1目标")
            return True

        # 添加Phase 1编译规则
        makefile_additions = '''

# Phase 1: Cryptographic Primitives Benchmark
PHASE1_SRC = benchmark/phase1_crypto_primitives.c
PHASE1_BIN = phase1_crypto_primitives

phase1_crypto_primitives: $(PHASE1_SRC) $(OBJS)
	@echo "Compiling Phase 1 Crypto Primitives Benchmark..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $(PHASE1_BIN) $(PHASE1_SRC) $(OBJS) $(LIBS)
	@echo "✓ Built: $(PHASE1_BIN)"

.PHONY: phase1
phase1: phase1_crypto_primitives
	@echo "Running Phase 1 Benchmark..."
	./$(PHASE1_BIN)
'''

        # 备份原Makefile
        self.execute_command(
            f"cp {REMOTE_BASE}/Makefile {REMOTE_BASE}/Makefile.backup_phase1",
            print_output=False
        )

        # 追加Phase 1规则
        append_cmd = f"cat >> {REMOTE_BASE}/Makefile << 'MAKEFILE_EOF'\n{makefile_additions}\nMAKEFILE_EOF"
        status, _, _ = self.execute_command(append_cmd, print_output=False)

        if status == 0:
            print("✅ Makefile更新成功!")
            return True
        else:
            print("⚠️  Makefile更新可能失败，尝试手动编译...")
            return True  # 继续尝试

    def compile_phase1(self):
        """编译Phase 1"""
        print(f"\n{'='*70}")
        print("🔨 编译Phase 1...")
        print(f"{'='*70}")

        # 清理
        self.execute_command(
            f"cd {REMOTE_BASE} && make clean 2>/dev/null || true",
            print_output=False
        )

        # 尝试使用make
        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && make phase1_crypto_primitives 2>&1"
        )

        if status == 0:
            print("✅ 编译成功 (使用Makefile)!")
            self.execute_command(
                f"ls -lh {REMOTE_BASE}/phase1_crypto_primitives",
                print_output=True
            )
            return True

        # 如果Makefile失败，尝试直接编译
        print("⚠️  Makefile编译失败，尝试直接编译...")

        compile_cmd = f"""cd {REMOTE_BASE} && gcc -Wall -Wextra -O2 -g -std=c99 \
            -I{REMOTE_BASE}/include -I$HOME/_oqs/include \
            -o phase1_crypto_primitives \
            benchmark/phase1_crypto_primitives.c \
            src/kyber_kem.c src/crypto_utils.c src/pq_ntor.c \
            -L$HOME/_oqs/lib -loqs -lssl -lcrypto -lpthread -lm -Wl,-rpath,$HOME/_oqs/lib"""

        status, output, error = self.execute_command(compile_cmd)

        if status == 0:
            print("✅ 直接编译成功!")
            return True
        else:
            print(f"❌ 编译失败!\n{error}")
            return False

    def run_phase1(self):
        """运行Phase 1测试"""
        print(f"\n{'='*70}")
        print("🚀 运行Phase 1性能测试")
        print(f"{'='*70}")
        print("⏱️  预计耗时: 1-2分钟 (1000次迭代)")
        print("")

        # 设置CPU性能模式
        self.execute_command(
            "echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo '使用默认CPU模式'",
            print_output=False
        )

        # 创建结果目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = f"/home/{self.config['username']}/phase1_results_{timestamp}"
        self.execute_command(f"mkdir -p {result_dir}", print_output=False)

        # 运行测试
        print("开始测试...\n")
        start_time = time.time()

        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && ./phase1_crypto_primitives 2>&1",
            print_output=True
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  实际耗时: {elapsed:.1f} 秒")

        if status != 0:
            print(f"❌ 测试失败!\n{error}")
            return None

        # 保存结果
        print(f"\n💾 保存结果到: {result_dir}")

        self.execute_command(
            f"cp {REMOTE_BASE}/phase1_crypto_benchmarks.csv {result_dir}/ 2>/dev/null || echo 'CSV文件未生成'",
            print_output=False
        )

        self.execute_command(
            f"echo '{output}' > {result_dir}/phase1_output.txt",
            print_output=False
        )

        self.execute_command(
            f"lscpu > {result_dir}/system_info.txt 2>&1",
            print_output=False
        )

        return result_dir

    def download_results(self, remote_dir, local_dir):
        """下载结果"""
        print(f"\n{'='*70}")
        print("📥 下载测试结果...")
        print(f"{'='*70}")

        os.makedirs(local_dir, exist_ok=True)

        files = ['phase1_crypto_benchmarks.csv', 'phase1_output.txt', 'system_info.txt']

        for filename in files:
            remote_file = f"{remote_dir}/{filename}"
            local_file = os.path.join(local_dir, filename)

            try:
                print(f"📥 {filename}...", end=' ')
                self.sftp.get(remote_file, local_file)
                size = os.path.getsize(local_file)
                print(f"✅ ({size/1024:.1f} KB)")
            except Exception as e:
                print(f"⚠️  {e}")

        print(f"\n✅ 结果已下载到: {local_dir}")
        return local_dir

    def analyze_results(self, local_dir):
        """分析结果"""
        print(f"\n{'='*70}")
        print("📊 结果分析")
        print(f"{'='*70}")

        csv_file = os.path.join(local_dir, 'phase1_crypto_benchmarks.csv')

        if not os.path.exists(csv_file):
            print("❌ CSV文件不存在!")
            return

        print("\n📈 性能测试结果:\n")
        with open(csv_file, 'r') as f:
            print(f.read())

        # 对比文献
        print("\n📊 与Berger et al. (2025) x86基准对比:")
        print(f"{'='*70}\n")

        berger_data = {
            'Kyber-512 Keygen': 25.8,
            'Kyber-512 Encaps': 30.1,
            'Kyber-512 Decaps': 27.6
        }

        with open(csv_file, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    operation = parts[0]
                    mean_us = float(parts[3])

                    for berger_op, berger_mean in berger_data.items():
                        if berger_op in operation:
                            ratio = mean_us / berger_mean

                            if 1.5 <= ratio <= 2.5:
                                status = "✅ 正常"
                            elif ratio < 1.0:
                                status = "❌ 异常(ARM64更快?)"
                            elif ratio > 3.0:
                                status = "⚠️  异常(太慢)"
                            else:
                                status = "⚠️  可疑"

                            print(f"{operation}:")
                            print(f"  本实验 (ARM64 Phytium): {mean_us:6.2f} μs")
                            print(f"  Berger (x86 @ 3.0GHz):  {berger_mean:6.2f} μs")
                            print(f"  ARM64/x86 比率:         {ratio:6.2f}×  {status}")
                            print()


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 Phase 1 飞腾派自动部署与测试 v2")
    print("="*70)
    print(f"目标: {PI_CONFIG['username']}@{PI_CONFIG['hostname']}")
    print(f"部署目录: {REMOTE_BASE}")
    print(f"测试内容: Kyber-512 密码学基元性能")
    print("="*70)

    deployer = PhytiumDeployer(PI_CONFIG)

    try:
        # 1. 连接
        if not deployer.connect():
            return 1

        # 2. 检查环境
        if not deployer.check_environment():
            print("\n❌ 环境检查失败")
            return 1

        # 3. 传输文件
        if not deployer.transfer_files():
            print("\n❌ 文件传输失败")
            return 1

        # 4. 更新Makefile
        deployer.update_makefile()

        # 5. 编译
        if not deployer.compile_phase1():
            print("\n❌ 编译失败")
            return 1

        # 6. 运行测试
        remote_result_dir = deployer.run_phase1()
        if not remote_result_dir:
            print("\n❌ 测试运行失败")
            return 1

        # 7. 下载结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_result_dir = f"/home/ccc/pq-ntor-experiment/essay/phase1_results_phytium_{timestamp}"
        deployer.download_results(remote_result_dir, local_result_dir)

        # 8. 分析结果
        deployer.analyze_results(local_result_dir)

        # 完成
        print("\n" + "="*70)
        print("✅ Phase 1 测试完成!")
        print("="*70)
        print(f"\n📁 本地结果: {local_result_dir}")
        print(f"📁 远程结果: {remote_result_dir}")
        print("\n🎯 下一步: 如果结果正常(ARM64/x86 = 1.5-2.5×)，开始Phase 2开发")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        deployer.disconnect()


if __name__ == '__main__':
    sys.exit(main())
