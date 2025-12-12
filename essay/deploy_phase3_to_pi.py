#!/usr/bin/env python3
"""
Phase 3 自动部署脚本 - SAGIN网络集成测试
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
    'benchmark/phase3_sagin_network.c',
    'benchmark/configure_tc_netem.sh',
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
        print("📤 传输Phase 3文件...")
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

        # Make script executable
        print("\n🔧 设置脚本可执行权限...")
        self.execute_command(
            f"chmod +x {REMOTE_BASE}/benchmark/configure_tc_netem.sh",
            print_output=False
        )

        print("✅ 文件传输完成!")
        return True

    def compile_phase3(self):
        print(f"\n{'='*70}")
        print("🔨 编译Phase 3...")
        print(f"{'='*70}")

        # 清理
        self.execute_command(
            f"cd {REMOTE_BASE} && make clean 2>/dev/null || true",
            print_output=False
        )

        # 编译
        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && make phase3_sagin_network 2>&1"
        )

        if status == 0:
            print("✅ 编译成功!")
            self.execute_command(
                f"ls -lh {REMOTE_BASE}/phase3_sagin_network",
                print_output=True
            )
            return True
        else:
            print(f"❌ 编译失败!\n{error}")
            return False

    def check_tc_support(self):
        print(f"\n{'='*70}")
        print("🔍 检查tc/netem支持...")
        print(f"{'='*70}")

        # 检查tc工具
        status, output, error = self.execute_command(
            "which tc && tc -Version 2>&1",
            print_output=True
        )

        if status != 0:
            print("❌ tc工具不可用")
            return False

        print("✅ tc工具可用")

        # 检查sudo权限
        print("\n🔑 配置sudo无密码权限...")
        status, output, error = self.execute_command(
            "echo '{self.config['password']}' | sudo -S echo 'sudo test' 2>&1",
            print_output=False
        )

        if status == 0:
            print("✅ sudo权限可用")
        else:
            print("⚠️  需要配置sudo无密码...")
            # 尝试配置sudo无密码（需要用户已在sudoers中）
            self.execute_command(
                f"echo '{self.config['password']}' | sudo -S sh -c \"echo '{self.config['username']} ALL=(ALL) NOPASSWD: /usr/sbin/tc' | sudo tee /etc/sudoers.d/tc-nopasswd\"",
                print_output=False
            )
            print("   已尝试配置tc命令无密码sudo")

        return True

    def run_phase3(self):
        print(f"\n{'='*70}")
        print("🚀 运行Phase 3 SAGIN网络集成测试")
        print(f"{'='*70}")
        print("⏱️  预计耗时: 10-15分钟")
        print("   - 12个拓扑")
        print("   - 2种协议 (Classic NTOR + PQ-NTOR)")
        print("   - 每个20次迭代 + 3次预热")
        print("   - 总计: 480次电路构建测试")
        print("")

        # 设置CPU性能模式
        self.execute_command(
            "echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo '使用默认CPU模式'",
            print_output=False
        )

        # 创建结果目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = f"/home/{self.config['username']}/phase3_results_{timestamp}"
        self.execute_command(f"mkdir -p {result_dir}", print_output=False)

        # 运行测试
        print("开始测试...\n")
        start_time = time.time()

        status, output, error = self.execute_command(
            f"cd {REMOTE_BASE} && ./phase3_sagin_network 2>&1",
            print_output=True
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  实际耗时: {elapsed/60:.1f} 分钟 ({elapsed:.1f} 秒)")

        if status != 0:
            print(f"❌ 测试失败!\n{error}")
            return None

        # 保存结果
        print(f"\n💾 保存结果到: {result_dir}")

        self.execute_command(
            f"cp {REMOTE_BASE}/phase3_sagin_cbt.csv {result_dir}/ 2>/dev/null || echo 'CSV文件未生成'",
            print_output=False
        )

        self.execute_command(
            f"echo '{output}' > {result_dir}/phase3_output.txt",
            print_output=False
        )

        return result_dir

    def download_results(self, remote_dir, local_dir):
        print(f"\n{'='*70}")
        print("📥 下载测试结果...")
        print(f"{'='*70}")

        os.makedirs(local_dir, exist_ok=True)

        files = ['phase3_sagin_cbt.csv', 'phase3_output.txt']

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
        print("📊 结果预览")
        print(f"{'='*70}")

        csv_file = os.path.join(local_dir, 'phase3_sagin_cbt.csv')

        if not os.path.exists(csv_file):
            print("❌ CSV文件不存在!")
            return

        print("\n📈 SAGIN拓扑Circuit Build Time (CBT):\n")
        with open(csv_file, 'r') as f:
            lines = f.readlines()
            # Show header
            print(lines[0].strip())
            print("-" * 120)
            # Show first few results
            for i, line in enumerate(lines[1:], 1):
                print(line.strip())
                if i >= 6:  # Show first 3 topologies (2 protocols each)
                    if len(lines) > 7:
                        print(f"... ({len(lines) - 7} more rows)")
                    break

        # Simple summary
        if len(lines) > 1:
            print(f"\n{'='*70}")
            print("快速统计:")
            print(f"{'='*70}")

            classic_times = []
            pq_times = []

            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    protocol = parts[1]
                    mean_ms = float(parts[2])
                    if 'Classic' in protocol:
                        classic_times.append(mean_ms)
                    elif 'PQ' in protocol:
                        pq_times.append(mean_ms)

            if classic_times and pq_times:
                avg_classic = sum(classic_times) / len(classic_times)
                avg_pq = sum(pq_times) / len(pq_times)
                overhead = avg_pq / avg_classic

                print(f"  平均Classic NTOR CBT: {avg_classic:8.2f} ms")
                print(f"  平均PQ-NTOR CBT:      {avg_pq:8.2f} ms")
                print(f"  PQ开销倍数:            {overhead:8.2f}×")

                if overhead < 1.0:
                    print(f"  状态: ⚠️  PQ反而更快 ({overhead:.2f}×) - 需要检查")
                elif overhead <= 1.5:
                    print(f"  状态: ✅ PQ开销很小 ({overhead:.2f}×) - 优秀!")
                elif overhead <= 2.5:
                    print(f"  状态: ✅ PQ开销合理 ({overhead:.2f}×)")
                else:
                    print(f"  状态: ⚠️  PQ开销较大 ({overhead:.2f}×)")


def main():
    print("\n" + "="*70)
    print("🚀 Phase 3 飞腾派自动部署与测试")
    print("="*70)
    print(f"目标: {PI_CONFIG['username']}@{PI_CONFIG['hostname']}")
    print(f"测试内容: SAGIN网络集成 - 12拓扑×2协议×20迭代")
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
        if not deployer.compile_phase3():
            return 1

        # 4. 检查tc/netem支持
        deployer.check_tc_support()

        # 5. 运行测试
        remote_result_dir = deployer.run_phase3()
        if not remote_result_dir:
            return 1

        # 6. 下载结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_result_dir = f"/home/ccc/pq-ntor-experiment/essay/phase3_results_phytium_{timestamp}"
        deployer.download_results(remote_result_dir, local_result_dir)

        # 7. 分析结果
        deployer.analyze_results(local_result_dir)

        # 完成
        print("\n" + "="*70)
        print("✅ Phase 3 测试完成!")
        print("="*70)
        print(f"\n📁 本地结果: {local_result_dir}")
        print(f"📁 远程结果: {remote_result_dir}")
        print("\n🎯 下一步:")
        print("  1. 生成可视化图表: python3 visualize_phase3.py")
        print("  2. 综合分析Phase 1+2+3: python3 comprehensive_analysis.py")
        print("  3. 撰写论文实验章节")
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
