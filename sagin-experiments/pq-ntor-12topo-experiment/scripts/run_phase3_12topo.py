#!/usr/bin/env python3
"""
使用Phase3基准测试程序运行12拓扑实验
读取最新的topology_params.json参数并生成实验数据

作者: Claude Code
日期: 2025-12-15
"""

import json
import subprocess
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# 配置路径
SCRIPT_DIR = Path(__file__).parent.absolute()
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"
PARAMS_FILE = Path("/home/ccc/pq-ntor-experiment/last_experiment/topology_params.json")
PHASE3_DIR = Path("/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c")
PHASE3_EXE = PHASE3_DIR / "phase3_sagin_network"

# 确保结果目录存在
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def cleanup():
    """清理TC配置"""
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                   stderr=subprocess.DEVNULL)
    time.sleep(0.5)

def configure_tc(delay_ms, bandwidth_mbps, loss_percent):
    """配置TC网络仿真参数"""
    cleanup()

    # 计算延迟抖动 (25%)
    jitter = delay_ms * 0.25

    cmd = f"sudo tc qdisc add dev lo root netem delay {delay_ms:.2f}ms {jitter:.2f}ms distribution normal rate {bandwidth_mbps:.2f}mbit loss {loss_percent:.2f}%"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  TC配置失败: {result.stderr}")
        return False

    return True

def run_phase3_test(topo_id, params, num_runs=10):
    """运行Phase3基准测试"""
    print(f"\n{'='*70}")
    print(f"📡 测试拓扑 {topo_id:02d}: {params['name']}")
    print(f"{'='*70}")

    # 获取网络参数
    e2e = params['end_to_end']
    delay_ms = e2e['delay_ms']
    bandwidth_mbps = e2e['rate_mbps']
    loss_percent = e2e['packet_loss_percent']

    print(f"  延迟: {delay_ms:.2f}ms")
    print(f"  带宽: {bandwidth_mbps:.2f}Mbps")
    print(f"  丢包: {loss_percent:.1f}%")

    # 配置网络
    print("\n🌐 配置网络仿真...")
    if not configure_tc(delay_ms, bandwidth_mbps, loss_percent):
        return None
    print("  ✅ TC配置成功")

    # 运行Phase3测试
    print(f"\n🔬 运行Phase3测试 ({num_runs}次)...")

    results = {
        'topology_id': topo_id,
        'topology_name': params['name'],
        'description': params.get('description', ''),
        'network_params': {
            'delay_ms': delay_ms,
            'bandwidth_mbps': bandwidth_mbps,
            'loss_percent': loss_percent
        },
        'runs': [],
        'test_date': datetime.now().isoformat()
    }

    try:
        # 运行phase3_sagin_network
        # 该程序会自动在本地建立电路并测量CBT
        result = subprocess.run(
            ['sudo', str(PHASE3_EXE)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=PHASE3_DIR
        )

        # 解析输出
        output = result.stdout
        print(f"  输出: {len(output)} bytes")

        # 检查CSV输出文件
        csv_file = PHASE3_DIR / "phase3_sagin_cbt.csv"
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                csv_content = f.read()
            results['csv_output'] = csv_content
            print(f"  ✅ CSV数据已生成")

        results['stdout'] = output[:2000] if output else ''
        results['returncode'] = result.returncode
        results['success'] = result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  测试超时")
        results['success'] = False
        results['error'] = 'timeout'
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        results['success'] = False
        results['error'] = str(e)

    # 保存结果
    result_file = RESULTS_DIR / f"topo{topo_id:02d}_phase3_results.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  📁 结果已保存: {result_file}")

    cleanup()
    return results

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='使用Phase3运行12拓扑实验')
    parser.add_argument('--topo', type=int, help='测试单个拓扑 (1-12)')
    parser.add_argument('--all', action='store_true', help='测试所有12个拓扑')
    parser.add_argument('--runs', type=int, default=10, help='每个拓扑运行次数')

    args = parser.parse_args()

    # 检查必要文件
    if not PARAMS_FILE.exists():
        print(f"❌ 参数文件不存在: {PARAMS_FILE}")
        sys.exit(1)

    if not PHASE3_EXE.exists():
        print(f"❌ Phase3程序不存在: {PHASE3_EXE}")
        sys.exit(1)

    # 加载拓扑参数
    print(f"📖 加载拓扑参数: {PARAMS_FILE}")
    with open(PARAMS_FILE, 'r') as f:
        all_params = json.load(f)
    print(f"✅ 已加载 {len(all_params)} 个拓扑参数")

    try:
        if args.topo:
            if not (1 <= args.topo <= 12):
                print("❌ 拓扑ID必须在1-12之间")
                sys.exit(1)

            topo_key = f"topo{args.topo:02d}"
            if topo_key in all_params:
                run_phase3_test(args.topo, all_params[topo_key], args.runs)
            else:
                print(f"❌ 找不到拓扑参数: {topo_key}")

        elif args.all:
            print("\n🚀 开始测试所有12个拓扑")
            all_results = []

            for topo_id in range(1, 13):
                topo_key = f"topo{topo_id:02d}"
                if topo_key in all_params:
                    result = run_phase3_test(topo_id, all_params[topo_key], args.runs)
                    if result:
                        all_results.append(result)
                    time.sleep(2)

            # 保存汇总结果
            summary_file = RESULTS_DIR / "all_phase3_results.json"
            with open(summary_file, 'w') as f:
                json.dump({
                    'test_date': datetime.now().isoformat(),
                    'total_topologies': len(all_results),
                    'results': all_results
                }, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 汇总结果已保存: {summary_file}")

        else:
            parser.print_help()
            print("\n示例:")
            print("  测试单个拓扑:    python3 run_phase3_12topo.py --topo 1")
            print("  测试所有拓扑:    python3 run_phase3_12topo.py --all")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        cleanup()
        sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
