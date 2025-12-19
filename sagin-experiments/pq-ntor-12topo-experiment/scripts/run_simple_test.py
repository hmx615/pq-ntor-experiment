#!/usr/bin/env python3
"""
简化版12拓扑测试脚本
用于调试和快速测试

作者: Claude Code
日期: 2025-12-11
"""

import json
import subprocess
import time
import sys
import socket
from pathlib import Path
from datetime import datetime

# 配置
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_DIR = SCRIPT_DIR.parent / "configs"
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "local_wsl"

# 自动检测PQ-NTOR目录（支持WSL2和飞腾派）
# 从scripts目录向上找: scripts -> pq-ntor-12topo-experiment -> sagin-experiments
sagin_dir = SCRIPT_DIR.parent.parent  # scripts -> pq-ntor-12topo-experiment -> sagin-experiments
PQ_NTOR_DIR = sagin_dir / "docker" / "build_context" / "c"

if not PQ_NTOR_DIR.exists():
    print(f"❌ PQ-NTOR目录不存在: {PQ_NTOR_DIR}")
    print(f"   当前脚本位置: {SCRIPT_DIR}")
    print(f"   SAGIN目录: {sagin_dir}")
    sys.exit(1)

# 创建结果目录
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def wait_for_port(port, host='localhost', timeout=10):
    """等待端口可用"""
    for i in range(timeout):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            sock.close()
            return True
        except:
            time.sleep(1)
        finally:
            sock.close()
    return False

def cleanup():
    """清理进程和TC配置"""
    print("🧹 清理进程...")
    subprocess.run(['pkill', '-9', 'directory'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'relay'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', 'client'], stderr=subprocess.DEVNULL)
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                   stderr=subprocess.DEVNULL)
    time.sleep(1)
    print("✅ 清理完成")

def load_config(topo_id):
    """加载拓扑配置"""
    config_file = CONFIG_DIR / f"topo{topo_id:02d}_tor_mapping.json"
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)

def configure_tc(config):
    """配置TC网络参数"""
    print("🌐 配置网络参数...")

    # 清除旧配置
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'lo', 'root'],
                   stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    # 应用新配置
    tc_commands = config['network_simulation']['tc_commands']
    for cmd in tc_commands:
        if 'add' in cmd:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  TC配置警告: {result.stderr}")
                return False

    params = config['network_simulation']['aggregate_params']
    print(f"  ✅ 延迟={params['delay_ms']:.2f}ms, "
          f"带宽={params['bandwidth_mbps']:.2f}Mbps, "
          f"丢包={params['loss_percent']:.2f}%")
    return True

def start_services(config):
    """启动所有服务"""
    print("🚀 启动服务...")
    services = []

    # Directory (includes built-in HTTP test server on port 8000)
    print("  启动 Directory (端口 5000, HTTP 8000)...")
    proc = subprocess.Popen(
        [str(PQ_NTOR_DIR / 'directory'), '-p', '5000', '-t', '8000'],
        stdout=open('/tmp/directory.log', 'w'),
        stderr=subprocess.STDOUT,
        cwd=PQ_NTOR_DIR
    )
    services.append(proc)

    # 等待两个端口都就绪
    if wait_for_port(5000, timeout=10):
        print("    ✅ Directory (5000) 已就绪")
    else:
        print("    ❌ Directory 启动失败或超时")
        print("    查看日志: /tmp/directory.log")
        return None

    if wait_for_port(8000, timeout=5):
        print("    ✅ HTTP Test Server (8000) 已就绪")
    else:
        print("    ⚠️  HTTP Test Server 端口检查超时")
        print("    查看日志: /tmp/directory.log")

    # Relays
    roles = config['tor_circuit_mapping']['roles']
    for role_name in ['guard', 'middle', 'exit']:
        role_info = roles[role_name]
        port = role_info['port']
        print(f"  启动 {role_name} Relay (端口 {port})...")
        proc = subprocess.Popen(
            [str(PQ_NTOR_DIR / 'relay'), '-r', role_name, '-p', str(port)],
            stdout=open(f'/tmp/relay_{role_name}.log', 'w'),
            stderr=subprocess.STDOUT,
            cwd=PQ_NTOR_DIR
        )
        services.append(proc)
        if wait_for_port(port, timeout=5):
            print(f"    ✅ {role_name} Relay 已就绪")
        else:
            print(f"    ⚠️  {role_name} Relay 端口检查超时")

    print("  ✅ 所有服务已启动")
    return services

def run_client_test(topo_id, run_id):
    """运行客户端测试"""
    print(f"  🔬 运行测试 {run_id}...")

    try:
        result = subprocess.run(
            [str(PQ_NTOR_DIR / 'client'), '-d', 'localhost', '-p', '5000',
             '-u', 'http://localhost:8000/'],
            capture_output=True,
            text=True,
            timeout=60,  # 增加超时时间以适应网络延迟
            cwd=PQ_NTOR_DIR
        )

        success = result.returncode == 0
        if success:
            print(f"    ✅ 测试 {run_id} 成功")
        else:
            print(f"    ❌ 测试 {run_id} 失败 (返回码: {result.returncode})")

        return {
            'run_id': run_id,
            'success': success,
            'returncode': result.returncode,
            'stdout': result.stdout[:500] if result.stdout else '',
            'stderr': result.stderr[:500] if result.stderr else ''
        }

    except subprocess.TimeoutExpired:
        print(f"    ⏱️  测试 {run_id} 超时")
        return {
            'run_id': run_id,
            'success': False,
            'error': 'timeout'
        }
    except Exception as e:
        print(f"    ❌ 测试 {run_id} 异常: {e}")
        return {
            'run_id': run_id,
            'success': False,
            'error': str(e)
        }

def test_topology(topo_id, num_runs=3):
    """测试单个拓扑"""
    print("\n" + "=" * 70)
    print(f"📡 测试拓扑 {topo_id:02d}")
    print("=" * 70)

    try:
        # 加载配置
        config = load_config(topo_id)
        print(f"拓扑: {config['topology_name']}")
        print(f"方向: {config['physical_topology']['direction']}")

        # 清理环境
        cleanup()

        # 配置网络
        if not configure_tc(config):
            print("❌ TC配置失败")
            return None

        # 启动服务
        services = start_services(config)
        if services is None:
            print("❌ 服务启动失败")
            return None

        # 运行测试
        results = []
        for i in range(num_runs):
            result = run_client_test(topo_id, i + 1)
            results.append(result)
            time.sleep(1)

        # 统计结果
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"\n📊 结果: {success_count}/{num_runs} 成功")

        # 保存结果
        output = {
            'topology_id': topo_id,
            'topology_name': config['topology_name'],
            'config': config,
            'test_runs': results,
            'summary': {
                'total_runs': num_runs,
                'success_count': success_count,
                'success_rate': (success_count / num_runs * 100) if num_runs > 0 else 0
            },
            'test_date': datetime.now().isoformat()
        }

        result_file = RESULTS_DIR / f"topo{topo_id:02d}_results.json"
        with open(result_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✅ 结果已保存: {result_file}")

        return output

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        cleanup()

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='简化版12拓扑测试')
    parser.add_argument('--topo', type=int, help='测试单个拓扑 (1-12)')
    parser.add_argument('--all', action='store_true', help='测试所有12个拓扑')
    parser.add_argument('--runs', type=int, default=3, help='每个拓扑运行次数 (默认: 3)')

    args = parser.parse_args()

    # 验证环境
    if not PQ_NTOR_DIR.exists():
        print(f"❌ PQ-NTOR目录不存在: {PQ_NTOR_DIR}")
        sys.exit(1)

    for exe in ['directory', 'relay', 'client']:
        if not (PQ_NTOR_DIR / exe).exists():
            print(f"❌ 可执行文件不存在: {PQ_NTOR_DIR / exe}")
            sys.exit(1)

    try:
        if args.topo:
            # 测试单个拓扑
            if not (1 <= args.topo <= 12):
                print("❌ 拓扑ID必须在1-12之间")
                sys.exit(1)
            test_topology(args.topo, args.runs)

        elif args.all:
            # 测试所有拓扑
            print("🚀 开始测试所有12个拓扑")
            print(f"每个拓扑运行 {args.runs} 次\n")

            for topo_id in range(1, 13):
                test_topology(topo_id, args.runs)
                time.sleep(2)

            print("\n" + "=" * 70)
            print("✅ 所有拓扑测试完成!")
            print("=" * 70)

        else:
            parser.print_help()
            print("\n示例:")
            print("  测试单个拓扑:    python3 run_simple_test.py --topo 1 --runs 5")
            print("  测试所有拓扑:    python3 run_simple_test.py --all --runs 10")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
