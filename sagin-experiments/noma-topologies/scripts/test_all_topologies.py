#!/usr/bin/env python3
"""
自动化测试所有12种NOMA拓扑 (Python版本)
更稳定、更可靠的测试框架
"""

import json
import subprocess
import time
import os
import sys
import signal
from datetime import datetime
from pathlib import Path

# 配置参数
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent
CONFIGS_DIR = BASE_DIR / "configs"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
NUM_RUNS = 10  # 每个拓扑测试次数
PQ_NTOR_DIR = Path("/home/ccc/pq-ntor-experiment/c")

# 创建目录
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 全局变量存储进程
current_processes = []


def cleanup_processes():
    """清理所有Tor进程"""
    global current_processes
    for proc in current_processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass
    current_processes = []

    # 额外清理
    subprocess.run(['pkill', '-9', 'directory'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'relay'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'client'], stderr=subprocess.DEVNULL)
    time.sleep(1)


def configure_network(config_file):
    """配置网络参数使用tc/netem"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    topo_id = config['topology_id']
    topo_name = config['name']

    # 清除现有tc规则
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                  stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    # 应用网络参数
    links = config.get('links', [])
    if links:
        link = links[0]
        delay_ms = link['delay_ms']
        bandwidth_mbps = link['bandwidth_mbps']
        loss_percent = link['loss_percent']
    else:
        # 使用预期性能参数
        perf = config['expected_performance']
        delay_ms = perf['total_delay_ms']
        bandwidth_mbps = perf['bottleneck_bw_mbps']
        loss_percent = 0.5

    cmd = [
        'sudo', 'tc', 'qdisc', 'add', 'dev', 'lo', 'root', 'netem',
        'delay', f'{delay_ms}ms', '2ms',
        'rate', f'{bandwidth_mbps}mbit',
        'loss', f'{loss_percent}%'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: tc configuration failed: {result.stderr}")
        return False

    return True


def start_tor_network(topo_id, run_id):
    """启动Tor网络节点"""
    global current_processes

    # 切换到PQ-NTOR目录
    os.chdir(PQ_NTOR_DIR)

    # 启动directory
    log_file = LOGS_DIR / f"directory_topo{topo_id}_run{run_id}.log"
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(['./directory'], stdout=f, stderr=f)
        current_processes.append(proc)
        dir_pid = proc.pid

    time.sleep(1)

    # 启动relays
    for role, port in [('guard', 6001), ('middle', 6002), ('exit', 6003)]:
        log_file = LOGS_DIR / f"{role}_topo{topo_id}_run{run_id}.log"
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(['./relay', '-r', role, '-p', str(port)],
                                   stdout=f, stderr=f)
            current_processes.append(proc)

    time.sleep(2)  # 等待节点启动
    return True


def run_client_test(topo_id, run_id, timeout=120):
    """运行客户端测试"""
    os.chdir(PQ_NTOR_DIR)

    log_file = LOGS_DIR / f"client_topo{topo_id}_run{run_id}.log"

    start_time = time.time()

    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(
                ['./client', 'http://127.0.0.1:8000/'],
                stdout=f,
                stderr=f,
                timeout=timeout
            )

        end_time = time.time()
        duration = end_time - start_time
        success = (result.returncode == 0)
        exit_code = result.returncode

        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'success': success,
            'exit_code': exit_code
        }

    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'success': False,
            'exit_code': 124  # timeout exit code
        }


def test_single_topology(config_file, num_runs, results_writer):
    """测试单个拓扑"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    topo_id = config['topology_id']
    topo_name = config['name']

    print()
    print("=" * 50)
    print(f"Testing Topology {topo_id}: {topo_name}")
    print("=" * 50)

    # 配置网络
    print("[Step 1/3] Configuring network parameters...")
    if not configure_network(config_file):
        print("❌ Network configuration failed, skipping...")
        return 0, 0

    successful = 0
    failed = 0

    print(f"[Step 2/3] Running {num_runs} tests...")

    for run in range(1, num_runs + 1):
        print(f"  Run {run}/{num_runs}: ", end='', flush=True)

        try:
            # 启动Tor网络
            print("Starting... ", end='', flush=True)
            if not start_tor_network(topo_id, run):
                print("❌ Failed to start Tor network")
                failed += 1
                continue

            # 运行客户端测试
            print("Testing... ", end='', flush=True)
            result = run_client_test(topo_id, run)

            # 输出结果
            if result['success']:
                print(f"✅ Success ({result['duration']:.2f}s)")
                successful += 1
            else:
                print(f"❌ Failed (exit code: {result['exit_code']})")
                failed += 1

            # 写入CSV（立即刷新）
            results_writer.write(
                f"{topo_id},\"{topo_name}\",{run},PQ-NTOR,"
                f"{result['start_time']},{result['end_time']},"
                f"{result['duration']},{str(result['success']).lower()},"
                f"{result['exit_code']}\n"
            )
            results_writer.flush()  # 立即刷新到磁盘

        finally:
            # 清理进程
            cleanup_processes()
            time.sleep(1)

    # 清理网络配置
    print("[Step 3/3] Cleaning up network configuration...")
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                  stderr=subprocess.DEVNULL)

    print(f"✅ Topology {topo_id} completed: {successful}/{num_runs} successful")

    return successful, failed


def main():
    """主函数"""
    print("=" * 50)
    print("  NOMA Topology Automated Testing (Python)")
    print("=" * 50)
    print(f"Configs directory: {CONFIGS_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Number of runs per topology: {NUM_RUNS}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_results_file = RESULTS_DIR / f"raw_results_{timestamp}.csv"

    print(f"Results file: {raw_results_file}")
    print()

    # 检查PQ-NTOR可执行文件
    for exe in ['directory', 'relay', 'client']:
        exe_path = PQ_NTOR_DIR / exe
        if not exe_path.exists():
            print(f"❌ Error: {exe} not found in {PQ_NTOR_DIR}")
            sys.exit(1)

    # 创建CSV文件并写入表头
    with open(raw_results_file, 'w') as f:
        f.write("topology_id,topology_name,run_id,protocol,start_time,end_time,duration_s,success,exit_code\n")

    total_successful = 0
    total_failed = 0

    # 打开CSV文件用于追加写入
    with open(raw_results_file, 'a') as results_writer:
        # 遍历所有拓扑
        for topo_id in range(1, 13):
            # 查找配置文件
            config_pattern = f"topology_{topo_id:02d}_*.json"
            config_files = list(CONFIGS_DIR.glob(config_pattern))

            if not config_files:
                print(f"⚠️  Warning: Config for topology {topo_id} not found, skipping...")
                continue

            config_file = config_files[0]

            try:
                successful, failed = test_single_topology(
                    config_file, NUM_RUNS, results_writer
                )
                total_successful += successful
                total_failed += failed

            except KeyboardInterrupt:
                print("\n\n⚠️  Test interrupted by user")
                cleanup_processes()
                break

            except Exception as e:
                print(f"❌ Error testing topology {topo_id}: {e}")
                cleanup_processes()
                continue

    # 最终总结
    total_tests = total_successful + total_failed

    print()
    print("=" * 50)
    print("  Testing Summary")
    print("=" * 50)
    print(f"Total tests run: {total_tests}")
    print(f"Successful: {total_successful}")
    print(f"Failed: {total_failed}")
    if total_tests > 0:
        success_rate = (total_successful * 100.0 / total_tests)
        print(f"Success rate: {success_rate:.2f}%")
    print()
    print(f"📊 Raw results saved to: {raw_results_file}")
    print()
    print("Next step: Run analysis script to generate summary and plots")
    print(f"  python3 analyze_noma_results.py {raw_results_file}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        cleanup_processes()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        cleanup_processes()
        sys.exit(1)
