#!/usr/bin/env python3
"""
在飞腾派上运行12拓扑PQ-NTOR实验
"""

import paramiko
import time
import sys

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

def run_experiment(ssh, mode="pq", runs=10):
    """运行12拓扑实验"""

    print("="*70)
    print(f"  🚀 启动12拓扑实验 (mode={mode}, runs={runs})")
    print("="*70)

    # 准备运行脚本 - 在飞腾派上直接创建一个简化版本
    setup_script = f"""
cd ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment

# 创建运行脚本
cat > run_simple_12topo.py << 'PYSCRIPT'
#!/usr/bin/env python3
import json
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime

# 配置
CONFIG_DIR = Path.home() / "pq-ntor-experiment/sagin-experiments/noma-topologies/configs"
RESULTS_DIR = Path.home() / "pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi"
C_DIR = Path.home() / "pq-ntor-experiment/c"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 设置环境变量
os.environ["LD_LIBRARY_PATH"] = str(Path.home() / "_oqs/lib") + ":" + os.environ.get("LD_LIBRARY_PATH", "")

MODE = "{mode}"
RUNS_PER_TOPO = {runs}

print("="*70)
print("  🧪 PQ-NTOR 12拓扑测试 - 飞腾派 (ARM64)")
print("="*70)
print(f"  模式: {{MODE}}")
print(f"  每拓扑运行次数: {{RUNS_PER_TOPO}}")
print(f"  结果目录: {{RESULTS_DIR}}")
print("="*70)

# 获取拓扑列表
topology_files = sorted(CONFIG_DIR.glob("topology_*.json"))
print(f"\\n找到 {{len(topology_files)}} 个拓扑配置\\n")

all_results = []

for topo_idx, topo_file in enumerate(topology_files, 1):
    print(f"\\\\n{{'='*70}}")
    print(f"  [{{topo_idx}}/{{{{len(topology_files)}}}}] 测试拓扑: {{{{topo_file.name}}}}")
    print('='*70)

    # 读取拓扑配置
    with open(topo_file) as f:
        config = json.load(f)

    topo_id = config.get("topology_id", f"topo_{{topo_idx:02d}}")
    print(f"  拓扑ID: {{topo_id}}")
    print(f"  链路数: {{len(config.get('links', []))}}")

    # 运行多次测试
    topo_results = []

    for run_idx in range(1, RUNS_PER_TOPO + 1):
        print(f"\\n  运行 {{run_idx}}/{{RUNS_PER_TOPO}}:")

        # 清理旧进程
        subprocess.run(['pkill', '-9', 'directory'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', 'relay'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', 'client'], stderr=subprocess.DEVNULL)
        time.sleep(0.5)

        try:
            # 启动directory
            print("    启动 directory...")
            dir_proc = subprocess.Popen(
                [C_DIR / "directory"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=C_DIR
            )
            time.sleep(1)

            # 启动relays
            relay_procs = []
            for link in config.get('links', []):
                if 'relay' in link.get('type', '').lower():
                    port = link.get('port', 6001)
                    role = link.get('role', 'guard')
                    print(f"    启动 relay (port={{port}}, role={{role}})...")

                    proc = subprocess.Popen(
                        [C_DIR / "relay", "-r", role, "-p", str(port)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=C_DIR
                    )
                    relay_procs.append(proc)
                    time.sleep(0.3)

            time.sleep(1)

            # 运行client测试
            print(f"    运行 client (mode={{MODE}})...")
            client_start = time.time()

            client_proc = subprocess.run(
                [C_DIR / "client", "-u", "http://example.com", "--mode", MODE],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                cwd=C_DIR
            )

            client_end = time.time()
            client_duration = client_end - client_start

            # 解析结果
            output = client_proc.stdout.decode('utf-8', errors='ignore')
            stderr = client_proc.stderr.decode('utf-8', errors='ignore')

            success = client_proc.returncode == 0 and ("SUCCESS" in output or "Circuit" in output)

            result = {{
                "topology_id": topo_id,
                "run": run_idx,
                "mode": MODE,
                "success": success,
                "duration_sec": round(client_duration, 3),
                "return_code": client_proc.returncode,
                "timestamp": datetime.now().isoformat()
            }}

            topo_results.append(result)

            status = "✅" if success else "❌"
            print(f"    {{status}} 结果: {{'成功' if success else '失败'}} ({{client_duration:.3f}}s)")

        except subprocess.TimeoutExpired:
            print("    ❌ 超时")
            result = {{
                "topology_id": topo_id,
                "run": run_idx,
                "mode": MODE,
                "success": False,
                "duration_sec": 30.0,
                "error": "timeout",
                "timestamp": datetime.now().isoformat()
            }}
            topo_results.append(result)

        except Exception as e:
            print(f"    ❌ 错误: {{e}}")
            result = {{
                "topology_id": topo_id,
                "run": run_idx,
                "mode": MODE,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }}
            topo_results.append(result)

        finally:
            # 清理进程
            try:
                dir_proc.kill()
            except:
                pass
            for proc in relay_procs:
                try:
                    proc.kill()
                except:
                    pass

            subprocess.run(['pkill', '-9', 'directory'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', 'relay'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', 'client'], stderr=subprocess.DEVNULL)
            time.sleep(0.3)

    # 拓扑统计
    success_count = sum(1 for r in topo_results if r.get('success'))
    print(f"\\n  📊 拓扑 {{topo_id}} 统计: {{success_count}}/{{len(topo_results)}} 成功")

    all_results.extend(topo_results)

# 保存结果
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
result_file = RESULTS_DIR / f"12topo_{{MODE}}_{{timestamp}}.json"

with open(result_file, 'w') as f:
    json.dump({{
        "experiment": "12-topology-pq-ntor",
        "platform": "Phytium Pi (ARM64)",
        "mode": MODE,
        "runs_per_topology": RUNS_PER_TOPO,
        "total_tests": len(all_results),
        "total_success": sum(1 for r in all_results if r.get('success')),
        "timestamp": timestamp,
        "results": all_results
    }}, f, indent=2)

print(f"\\n{'='*70}")
print("  📊 实验完成")
print('='*70)
print(f"  总测试数: {{len(all_results)}}")
print(f"  成功: {{sum(1 for r in all_results if r.get('success'))}}")
print(f"  失败: {{sum(1 for r in all_results if not r.get('success'))}}")
print(f"  结果文件: {{result_file}}")
print('='*70)
PYSCRIPT

chmod +x run_simple_12topo.py
"""

    print("📝 创建运行脚本...")
    stdin, stdout, stderr = ssh.exec_command(setup_script)
    stdout.channel.recv_exit_status()
    print("✅ 脚本创建完成\n")

    # 运行实验
    print("="*70)
    print("  🏃 开始执行实验（这可能需要几分钟）")
    print("="*70)
    print()

    run_cmd = """
cd ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
python3 run_simple_12topo.py 2>&1
"""

    channel = ssh.get_transport().open_session()
    channel.exec_command(run_cmd)

    # 实时输出
    while True:
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8')
            print(data, end='', flush=True)

        if channel.recv_stderr_ready():
            data = channel.recv_stderr(1024).decode('utf-8')
            print(data, end='', flush=True)

        if channel.exit_status_ready():
            break

        time.sleep(0.1)

    exit_code = channel.recv_exit_status()

    print(f"\\n实验执行完成，退出码: {exit_code}")

    # 获取结果文件
    print("\\n" + "="*70)
    print("  📥 获取结果文件")
    print("="*70)

    stdin, stdout, stderr = ssh.exec_command(
        "ls -lt ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/*.json | head -1 | awk '{{print $NF}}'"
    )
    latest_result = stdout.read().decode().strip()

    if latest_result:
        print(f"\\n最新结果文件: {latest_result}")
        print("\\n结果内容预览:")
        stdin, stdout, stderr = ssh.exec_command(f"cat {latest_result} | python3 -m json.tool | head -50")
        print(stdout.read().decode())

    return exit_code == 0

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          飞腾派12拓扑PQ-NTOR实验                               ║")
    print("╚══════════════════════════════════════════════════════════════╝\\n")

    # 解析参数
    mode = sys.argv[1] if len(sys.argv) > 1 else "pq"
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"  模式: {mode}")
    print(f"  每拓扑运行次数: {runs}\\n")

    # SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"🔌 连接到 {HOST}...")
        ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        print("✅ 连接成功\\n")

        success = run_experiment(ssh, mode=mode, runs=runs)

        if success:
            print("\\n✅ 实验成功完成！")
            return 0
        else:
            print("\\n⚠️ 实验执行遇到问题")
            return 1

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        ssh.close()
        print("\\n🔌 SSH连接已关闭")

if __name__ == "__main__":
    sys.exit(main())
