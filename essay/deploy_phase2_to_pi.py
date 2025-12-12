#!/usr/bin/env python3
"""
Phase 2 自动部署脚本 - 协议握手性能对比测试
"""

import paramiko
import os
import sys
import time
from datetime import datetime

PI_CONFIG = {
    'hostname': '192.168.5.185',
    'username': 'user',
    'password': 'user',
    'port': 22
}

LOCAL_BASE = '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c'
REMOTE_BASE = '/home/user/pq-ntor-experiment/c'

FILES_TO_TRANSFER = [
    'benchmark/phase2_handshake_comparison.c',
    'Makefile'
]


class PhytiumDeployer:
    def __init__(self, config):
        self.config = config
        self.ssh = None
        self.sftp = None

    def connect(self):
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
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print("\n🔌 SSH连接已关闭")

    def execute_command(self, command, print_output=True):
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

    def transfer_files(self):
        print(f"\n{'='*70}")
        print("📤 传输Phase 2文件...")
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
                print("✅")
            except Exception as e:
                print(f"❌ {e}")
                return False

        print("✅ 文件传输完成!")
        return True

    def compile_phase2(self):
        print(f"\n{'='*70}")
        print("🔨 编译Phase 2...")
        print(f"{'='*70}")

        # 清理
        self.execute_command(
            f"cd {REMOTE_BASE} && make clean 2>/dev/null || true",
            print_output=False
        )

        # 编译
        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && make phase2_handshake_comparison 2>&1"
        )

        if status == 0:
            print("✅ 编译成功!")
            self.execute_command(
                f"ls -lh {REMOTE_BASE}/phase2_handshake_comparison",
                print_output=True
            )
            return True
        else:
            print(f"❌ 编译失败!\n{error}")
            return False

    def run_phase2(self):
        print(f"\n{'='*70}")
        print("🚀 运行Phase 2性能测试")
        print(f"{'='*70}")
        print("⏱️  预计耗时: 2-3分钟")
        print("   - Classic NTOR: 1000次握手测试")
        print("   - PQ-NTOR: 1000次握手测试")
        print("")

        # 设置CPU性能模式
        self.execute_command(
            "echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo '使用默认CPU模式'",
            print_output=False
        )

        # 创建结果目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = f"/home/{self.config['username']}/phase2_results_{timestamp}"
        self.execute_command(f"mkdir -p {result_dir}", print_output=False)

        # 运行测试
        print("开始测试...\n")
        start_time = time.time()

        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && ./phase2_handshake_comparison 2>&1",
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
            f"cp {REMOTE_BASE}/phase2_handshake_comparison.csv {result_dir}/ 2>/dev/null || echo 'CSV文件未生成'",
            print_output=False
        )

        self.execute_command(
            f"echo '{output}' > {result_dir}/phase2_output.txt",
            print_output=False
        )

        return result_dir

    def download_results(self, remote_dir, local_dir):
        print(f"\n{'='*70}")
        print("📥 下载测试结果...")
        print(f"{'='*70}")

        os.makedirs(local_dir, exist_ok=True)

        files = ['phase2_handshake_comparison.csv', 'phase2_output.txt']

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
        print(f"\n{'='*70}")
        print("📊 结果分析")
        print(f"{'='*70}")

        csv_file = os.path.join(local_dir, 'phase2_handshake_comparison.csv')

        if not os.path.exists(csv_file):
            print("❌ CSV文件不存在!")
            return

        print("\n📈 握手性能对比:\n")
        with open(csv_file, 'r') as f:
            lines = f.readlines()
            print(lines[0].strip())  # Header
            print("-" * 100)
            for line in lines[1:]:
                print(line.strip())

        # 简单分析
        if len(lines) >= 3:
            classic_data = lines[1].strip().split(',')
            pq_data = lines[2].strip().split(',')

            classic_mean = float(classic_data[1])
            pq_mean = float(pq_data[1])
            overhead = pq_mean / classic_mean

            print(f"\n{'='*70}")
            print("关键指标:")
            print(f"{'='*70}")
            print(f"  Classic NTOR握手时间: {classic_mean:8.2f} μs")
            print(f"  PQ-NTOR握手时间:      {pq_mean:8.2f} μs")
            print(f"  开销倍数:              {overhead:8.2f}×")

            if 2.0 <= overhead <= 6.0:
                print(f"  状态: ✅ 开销在合理范围内 (2-6×)")
            elif overhead < 2.0:
                print(f"  状态: ⚠️  开销异常偏低 (<2×)")
            else:
                print(f"  状态: ⚠️  开销异常偏高 (>6×)")


def main():
    print("\n" + "="*70)
    print("🚀 Phase 2 飞腾派自动部署与测试")
    print("="*70)
    print(f"目标: {PI_CONFIG['username']}@{PI_CONFIG['hostname']}")
    print(f"测试内容: PQ-NTOR vs Classic NTOR 协议握手对比")
    print("="*70)

    deployer = PhytiumDeployer(PI_CONFIG)

    try:
        # 1. 连接
        if not deployer.connect():
            return 1

        # 2. 传输文件
        if not deployer.transfer_files():
            return 1

        # 3. 编译
        if not deployer.compile_phase2():
            return 1

        # 4. 运行测试
        remote_result_dir = deployer.run_phase2()
        if not remote_result_dir:
            return 1

        # 5. 下载结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_result_dir = f"/home/ccc/pq-ntor-experiment/essay/phase2_results_phytium_{timestamp}"
        deployer.download_results(remote_result_dir, local_result_dir)

        # 6. 分析结果
        deployer.analyze_results(local_result_dir)

        # 完成
        print("\n" + "="*70)
        print("✅ Phase 2 测试完成!")
        print("="*70)
        print(f"\n📁 本地结果: {local_result_dir}")
        print(f"📁 远程结果: {remote_result_dir}")
        print("\n🎯 下一步: 开发Phase 3 (SAGIN网络集成测试)")
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
