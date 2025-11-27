#!/usr/bin/env python3
"""
在飞腾派上运行PQ-NTOR benchmark测试
"""
import paramiko
import time
import json
from datetime import datetime

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       飞腾派 PQ-NTOR Benchmark 性能测试                        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # 1. 检查benchmark程序
    print("1️⃣ 检查benchmark程序...")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
cd ~/pq-ntor-experiment/c
ls -lh benchmark_pq_ntor 2>/dev/null || echo "程序不存在"
""")
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    print(output)

    if "程序不存在" in output:
        print("❌ benchmark程序未编译，需要先编译")
        ssh.close()
        exit(1)

    # 2. 运行benchmark
    print("\n2️⃣ 运行PQ-NTOR Benchmark测试...")
    print("-"*70)
    print("这将测试1000次PQ-NTOR握手，预计需要1-2分钟...\n")

    run_cmd = """
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH

# 运行benchmark
./benchmark_pq_ntor 2>&1

# 保存结果
if [ -f benchmark_results.csv ]; then
    mkdir -p ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi
    cp benchmark_results.csv ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_results_arm64_$(date +%Y%m%d_%H%M%S).csv
    echo ""
    echo "✅ Benchmark结果已保存"
fi
"""

    channel = ssh.get_transport().open_session()
    channel.exec_command(run_cmd)

    # 实时输出
    benchmark_output = ""
    while True:
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8')
            print(data, end='', flush=True)
            benchmark_output += data

        if channel.recv_stderr_ready():
            data = channel.recv_stderr(1024).decode('utf-8')
            print(data, end='', flush=True)
            benchmark_output += data

        if channel.exit_status_ready():
            break

        time.sleep(0.1)

    exit_code = channel.recv_exit_status()
    print(f"\n\nBenchmark完成，退出码: {exit_code}")

    # 3. 解析结果
    print("\n3️⃣ 解析Benchmark结果...")
    print("-"*70)

    # 从输出中提取性能数据
    lines = benchmark_output.split('\n')
    results = {}

    for line in lines:
        if 'Client create onionskin' in line and 'avg=' in line:
            avg = line.split('avg=')[1].split('μs')[0].strip()
            results['client_create_avg_us'] = float(avg)
        elif 'Server create reply' in line and 'avg=' in line:
            avg = line.split('avg=')[1].split('μs')[0].strip()
            results['server_create_avg_us'] = float(avg)
        elif 'Client finish handshake' in line and 'avg=' in line:
            avg = line.split('avg=')[1].split('μs')[0].strip()
            results['client_finish_avg_us'] = float(avg)
        elif 'Full handshake' in line and 'avg=' in line:
            avg = line.split('avg=')[1].split('μs')[0].strip()
            results['full_handshake_avg_us'] = float(avg)

    if results:
        print("\n📊 性能摘要:")
        print("="*70)
        print(f"平台: Phytium Pi (ARM64 - aarch64)")
        print(f"算法: Kyber-512 (PQ-NTOR)")
        print(f"测试次数: 1000次")
        print()
        print(f"Client create onionskin:  {results.get('client_create_avg_us', 'N/A')} μs")
        print(f"Server create reply:      {results.get('server_create_avg_us', 'N/A')} μs")
        print(f"Client finish handshake:  {results.get('client_finish_avg_us', 'N/A')} μs")
        print(f"Full handshake (总计):    {results.get('full_handshake_avg_us', 'N/A')} μs")
        print("="*70)

        # 与论文对比
        paper_value = 161  # Denis Berger论文在Pi 5上的理论值
        our_value = results.get('full_handshake_avg_us', 0)

        if our_value > 0:
            print(f"\n📈 与论文对比:")
            print(f"Denis Berger论文 (Raspberry Pi 5, 理论): {paper_value} μs")
            print(f"我们的实现 (Phytium Pi, 实测):         {our_value} μs")

            if our_value < paper_value:
                speedup = paper_value / our_value
                print(f"✅ 我们快 {speedup:.2f}x")
            else:
                slowdown = our_value / paper_value
                print(f"⚠️ 我们慢 {slowdown:.2f}x (ARM设备差异)")

        # 保存JSON格式结果
        result_data = {
            "experiment": "pq-ntor-benchmark",
            "platform": "Phytium Pi (ARM64)",
            "cpu_arch": "aarch64",
            "algorithm": "Kyber-512",
            "library": "liboqs",
            "iterations": 1000,
            "timestamp": datetime.now().isoformat(),
            "results_us": results
        }

        # 保存到飞腾派
        json_str = json.dumps(result_data, indent=2)
        stdin, stdout, stderr = ssh.exec_command(f"""
cat > ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_summary.json << 'JSONEOF'
{json_str}
JSONEOF
echo "✅ JSON结果已保存"
""")
        stdout.channel.recv_exit_status()
        print("\n" + stdout.read().decode())

    # 4. 查看CSV结果文件
    print("\n4️⃣ 查看详细结果文件...")
    print("-"*70)
    stdin, stdout, stderr = ssh.exec_command("""
ls -lth ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_* 2>/dev/null | head -3
""")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

    print("\n✅ Benchmark测试完成！")
    print("\n结果文件位置:")
    print("  - CSV: ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_results_arm64_*.csv")
    print("  - JSON: ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_summary.json")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
    print("\n🔌 SSH连接已关闭")
