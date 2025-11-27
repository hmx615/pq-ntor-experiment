#!/usr/bin/env python3
import paramiko
import json

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("="*70)
    print("  🔍 检查实验状态和结果")
    print("="*70)

    # 检查进程
    print("\n1️⃣ 检查进程状态:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'run_12topo_fixed.py' | grep -v grep")
    stdout.channel.recv_exit_status()
    proc = stdout.read().decode()

    if proc:
        print("✅ 实验仍在运行")
    else:
        print("✅ 实验已完成")

    # 查看最新结果文件
    print("\n2️⃣ 最新结果文件:")
    stdin, stdout, stderr = ssh.exec_command("""
ls -lt ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/*.json 2>/dev/null | head -1 | awk '{print $NF}'
""")
    stdout.channel.recv_exit_status()
    latest_file = stdout.read().decode().strip()

    if latest_file:
        print(f"📄 {latest_file}")

        # 读取并解析结果
        print("\n3️⃣ 实验结果摘要:")
        print("-"*70)

        stdin, stdout, stderr = ssh.exec_command(f"""
python3 << 'EOF'
import json
try:
    with open('{latest_file}') as f:
        data = json.load(f)

    print(f"实验: {{data.get('experiment', 'N/A')}}")
    print(f"平台: {{data.get('platform', 'N/A')}}")
    print(f"模式: {{data.get('mode', 'N/A')}}")
    print(f"总测试数: {{data.get('total_tests', 0)}}")
    print(f"成功数: {{data.get('total_success', 0)}}")
    print(f"成功率: {{data.get('success_rate_percent', 0):.1f}}%")
    print()

    # 统计每个拓扑
    print("各拓扑详情:")
    print("-"*70)

    topo_stats = {{}}
    for r in data.get('results', []):
        tid = str(r.get('topology_id', 'unknown'))
        if tid not in topo_stats:
            topo_stats[tid] = {{
                'total': 0,
                'success': 0,
                'durations': [],
                'file': r.get('topology_file', 'N/A')
            }}
        topo_stats[tid]['total'] += 1
        if r.get('success'):
            topo_stats[tid]['success'] += 1
        if 'duration_sec' in r:
            topo_stats[tid]['durations'].append(r['duration_sec'])

    for tid in sorted(topo_stats.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        stats = topo_stats[tid]
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_dur = sum(stats['durations']) / len(stats['durations']) if stats['durations'] else 0

        status = "✅" if rate >= 66 else "⚠️" if rate > 0 else "❌"
        print(f"{{status}} 拓扑{{tid.zfill(2)}}: {{stats['success']}}/{{stats['total']}} ({{rate:.0f}}%) - 平均{{avg_dur:.1f}}s - {{stats['file']}}")

    # 显示一些详细结果
    print()
    print("最近5次测试详情:")
    print("-"*70)
    for r in data.get('results', [])[-5:]:
        status = "✅" if r.get('success') else "❌"
        tid = r.get('topology_id', '?')
        run = r.get('run', '?')
        dur = r.get('duration_sec', 0)
        has_http = r.get('has_http_response', False)
        print(f"{{status}} 拓扑{{str(tid).zfill(2)}} 运行{{run}}: {{dur:.1f}}s - HTTP响应:{{'是' if has_http else '否'}}")

except Exception as e:
    print(f"读取结果出错: {{e}}")
    import traceback
    traceback.print_exc()
EOF
""", timeout=10)
        stdout.channel.recv_exit_status()
        print(stdout.read().decode())
    else:
        print("❌ 未找到结果文件")

finally:
    ssh.close()
