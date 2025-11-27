#!/usr/bin/env python3
import paramiko
import time

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

print("╔══════════════════════════════════════════════════════════════╗")
print("║      飞腾派12拓扑PQ-NTOR实验 (修复版 - 完整HTTP测试)           ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"🔌 连接到 {HOST}...")
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    print("✅ 连接成功\n")

    # 上传脚本
    print("📤 上传修复版测试脚本...")
    sftp = ssh.open_sftp()
    sftp.put("/tmp/phytium_12topo_fixed.py", "/home/user/run_12topo_fixed.py")
    sftp.close()
    print("✅ 上传完成\n")

    # 运行实验
    print("="*70)
    print("  🏃 开始执行12拓扑实验")
    print("  - 每拓扑3次运行")
    print("  - 总共36次测试")
    print("  - 预计10-15分钟")
    print("="*70)
    print()

    run_cmd = """
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
cd ~
python3 run_12topo_fixed.py 2>&1
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
    print(f"\n\n✅ 实验完成，退出码: {exit_code}")

    # 获取结果
    print("\n" + "="*70)
    print("  📥 获取实验结果")
    print("="*70)

    stdin, stdout, stderr = ssh.exec_command(
        "ls -lt ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/*.json 2>/dev/null | head -1 | awk '{print $NF}'"
    )
    latest_result = stdout.read().decode().strip()

    if latest_result:
        print(f"\n📄 最新结果文件: {latest_result}\n")

        # 读取结果摘要
        stdin, stdout, stderr = ssh.exec_command(f"""
python3 << 'PYEOF'
import json
with open('{latest_result}') as f:
    data = json.load(f)

print("="*70)
print("  📊 实验结果摘要")
print("="*70)
print(f"平台: {{data['platform']}}")
print(f"模式: {{data['mode']}}")
print(f"总测试数: {{data['total_tests']}}")
print(f"成功数: {{data['total_success']}}")
print(f"成功率: {{data.get('success_rate_percent', 0):.1f}}%")
print()

# 统计每个拓扑
topo_stats = {{}}
for r in data['results']:
    tid = r['topology_id']
    if tid not in topo_stats:
        topo_stats[tid] = {{'total': 0, 'success': 0}}
    topo_stats[tid]['total'] += 1
    if r.get('success'):
        topo_stats[tid]['success'] += 1

print("各拓扑成功率:")
for tid in sorted(topo_stats.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
    stats = topo_stats[tid]
    rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"  拓扑 {{str(tid).zfill(2)}}: {{stats['success']}}/{{stats['total']}} ({rate:.1f}%)")
print("="*70)
PYEOF
""")
        print(stdout.read().decode())

    print("\n✅ 12拓扑实验全部完成！")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
    print("\n🔌 SSH连接已关闭")
