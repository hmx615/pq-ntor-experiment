#!/usr/bin/env python3
"""
集成真实卫星轨道的NOMA拓扑测试
使用师妹的satellite_orbit.py计算动态的传播延迟
"""

import json
import subprocess
import time
import os
import sys
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 导入卫星轨道模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'satellite-integration-test'))
from satellite_orbit import SatelliteOrbit

# 配置参数
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent
CONFIGS_DIR = BASE_DIR / "configs"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
NUM_RUNS = 10
PQ_NTOR_DIR = Path("/home/ccc/pq-ntor-experiment/c")

# 创建目录
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 全局变量
current_processes = []
satellite_orbit = None


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

    subprocess.run(['pkill', '-9', 'directory'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'relay'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'client'], stderr=subprocess.DEVNULL)
    time.sleep(1)


def initialize_satellite():
    """初始化卫星轨道"""
    global satellite_orbit
    print("\n" + "="*60)
    print("  Initializing Real Satellite Orbit")
    print("="*60)
    print("Using LEO satellite parameters:")
    print("  - Altitude: ~800km")
    print("  - Inclination: 49.974°")
    print("  - Semi-major axis: 7190.14km")
    print()

    satellite_orbit = SatelliteOrbit()
    print("✓ Satellite orbit initialized")
    print(f"✓ Best communication window selected")
    print()


def calculate_satellite_delay(timestamp):
    """
    基于真实卫星轨道计算传播延迟

    Returns:
        delay_ms: 单向传播延迟（毫秒）
        distance_km: 卫星到地面距离（公里）
    """
    global satellite_orbit

    # 获取卫星位置（ENU坐标系，单位：米）
    sat_pos = satellite_orbit.get_satellite_position_for_env(timestamp)

    # 转换为公里
    east_km = sat_pos[0] / 1000
    north_km = sat_pos[1] / 1000
    up_km = sat_pos[2] / 1000

    # 计算距离（勾股定理）
    distance_km = np.sqrt(east_km**2 + north_km**2 + up_km**2)

    # 计算传播延迟（光速 = 299792.458 km/s）
    c = 299792.458  # km/s
    delay_s = distance_km / c
    delay_ms = delay_s * 1000

    return delay_ms, distance_km


def configure_network_with_satellite(config_file, timestamp):
    """
    配置网络参数，使用真实卫星轨道计算的延迟
    """
    with open(config_file, 'r') as f:
        config = json.load(f)

    # 计算真实的卫星传播延迟
    sat_delay_ms, distance_km = calculate_satellite_delay(timestamp)

    # 获取配置中的其他参数
    links = config.get('links', [])
    if links:
        link = links[0]
        bandwidth_mbps = link['bandwidth_mbps']
        loss_percent = link['loss_percent']
    else:
        perf = config['expected_performance']
        bandwidth_mbps = perf['bottleneck_bw_mbps']
        loss_percent = 0.5

    # 清除现有tc规则
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                  stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    # 使用真实计算的卫星延迟
    cmd = [
        'sudo', 'tc', 'qdisc', 'add', 'dev', 'lo', 'root', 'netem',
        'delay', f'{sat_delay_ms:.2f}ms', '2ms',  # 使用动态计算的延迟
        'rate', f'{bandwidth_mbps}mbit',
        'loss', f'{loss_percent}%'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: tc configuration failed: {result.stderr}")
        return False, 0, 0

    return True, sat_delay_ms, distance_km


def start_tor_network(topo_id, run_id):
    """启动Tor网络节点"""
    global current_processes

    os.chdir(PQ_NTOR_DIR)

    # 启动directory
    log_file = LOGS_DIR / f"directory_topo{topo_id}_run{run_id}.log"
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(['./directory'], stdout=f, stderr=f)
        current_processes.append(proc)

    time.sleep(1)

    # 启动relays
    for role, port in [('guard', 6001), ('middle', 6002), ('exit', 6003)]:
        log_file = LOGS_DIR / f"{role}_topo{topo_id}_run{run_id}.log"
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(['./relay', '-r', role, '-p', str(port)],
                                   stdout=f, stderr=f)
            current_processes.append(proc)

    time.sleep(2)
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
            'exit_code': 124
        }


def test_single_topology_with_orbit(config_file, num_runs, results_writer):
    """测试单个拓扑，使用真实卫星轨道"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    topo_id = config['topology_id']
    topo_name = config['name']

    print()
    print("=" * 60)
    print(f"Testing Topology {topo_id}: {topo_name}")
    print("=" * 60)

    successful = 0
    failed = 0

    print(f"Running {num_runs} tests with real satellite orbit...")

    for run in range(1, num_runs + 1):
        print(f"  Run {run}/{num_runs}: ", end='', flush=True)

        try:
            # 为每次测试生成一个时间点（模拟不同的卫星位置）
            # 使用最佳通信窗口内的时间
            timestamp = satellite_orbit.best_window['start'] + timedelta(seconds=run*10)

            # 配置网络（使用真实卫星延迟）
            print("Calculating satellite delay... ", end='', flush=True)
            success_cfg, sat_delay, distance = configure_network_with_satellite(
                config_file, timestamp
            )

            if not success_cfg:
                print("❌ Network configuration failed")
                failed += 1
                continue

            print(f"[Delay={sat_delay:.2f}ms, Dist={distance:.1f}km] ", end='', flush=True)

            # 启动Tor网络
            print("Starting Tor... ", end='', flush=True)
            if not start_tor_network(topo_id, run):
                print("❌ Failed to start Tor")
                failed += 1
                continue

            # 运行客户端测试
            print("Testing... ", end='', flush=True)
            result = run_client_test(topo_id, run)

            if result['success']:
                print(f"✅ Success ({result['duration']:.2f}s)")
                successful += 1
            else:
                print(f"❌ Failed (exit code: {result['exit_code']})")
                failed += 1

            # 写入CSV（包含卫星延迟信息）
            results_writer.write(
                f"{topo_id},\"{topo_name}\",{run},PQ-NTOR,"
                f"{result['start_time']},{result['end_time']},"
                f"{result['duration']},{str(result['success']).lower()},"
                f"{result['exit_code']},{sat_delay:.2f},{distance:.1f}\n"
            )
            results_writer.flush()

        finally:
            cleanup_processes()
            time.sleep(1)

    # 清理网络配置
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                  stderr=subprocess.DEVNULL)

    print(f"✅ Topology {topo_id} completed: {successful}/{num_runs} successful")

    return successful, failed


def main():
    """主函数"""
    print("=" * 60)
    print("  NOMA Topology Testing with Real Satellite Orbit")
    print("=" * 60)

    # 初始化卫星轨道
    initialize_satellite()

    print(f"Configs directory: {CONFIGS_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Number of runs per topology: {NUM_RUNS}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_results_file = RESULTS_DIR / f"raw_results_satellite_{timestamp}.csv"

    print(f"Results file: {raw_results_file}")
    print()

    # 检查PQ-NTOR可执行文件
    for exe in ['directory', 'relay', 'client']:
        exe_path = PQ_NTOR_DIR / exe
        if not exe_path.exists():
            print(f"❌ Error: {exe} not found in {PQ_NTOR_DIR}")
            sys.exit(1)

    # 创建CSV文件并写入表头（增加卫星延迟和距离列）
    with open(raw_results_file, 'w') as f:
        f.write("topology_id,topology_name,run_id,protocol,start_time,end_time,"
                "duration_s,success,exit_code,satellite_delay_ms,satellite_distance_km\n")

    total_successful = 0
    total_failed = 0

    # 打开CSV文件用于追加写入
    with open(raw_results_file, 'a') as results_writer:
        # 遍历所有拓扑
        for topo_id in range(1, 13):
            config_pattern = f"topology_{topo_id:02d}_*.json"
            config_files = list(CONFIGS_DIR.glob(config_pattern))

            if not config_files:
                print(f"⚠️  Warning: Config for topology {topo_id} not found, skipping...")
                continue

            config_file = config_files[0]

            try:
                successful, failed = test_single_topology_with_orbit(
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
                import traceback
                traceback.print_exc()
                cleanup_processes()
                continue

    # 最终总结
    total_tests = total_successful + total_failed

    print()
    print("=" * 60)
    print("  Testing Summary")
    print("=" * 60)
    print(f"Total tests run: {total_tests}")
    print(f"Successful: {total_successful}")
    print(f"Failed: {total_failed}")
    if total_tests > 0:
        success_rate = (total_successful * 100.0 / total_tests)
        print(f"Success rate: {success_rate:.2f}%")
    print()
    print(f"📊 Raw results saved to: {raw_results_file}")
    print()
    print("✨ This test used REAL satellite orbit calculations!")
    print("   Delays were dynamically computed based on satellite position.")
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
        import traceback
        traceback.print_exc()
        cleanup_processes()
        sys.exit(1)
