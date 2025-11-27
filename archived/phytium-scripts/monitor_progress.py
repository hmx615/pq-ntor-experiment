#!/usr/bin/env python3
import paramiko
import time
import sys

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

    print("🔍 监控实验进度...\n")

    # 检查进程是否在运行
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'run_12topo_fixed.py' | grep -v grep")
    stdout.channel.recv_exit_status()
    proc_output = stdout.read().decode()

    if proc_output:
        print("✅ 实验正在运行中\n")
        print("进程信息:")
        print(proc_output)
    else:
        print("⚠️ 未检测到运行中的实验进程")

    # 检查是否有结果文件正在生成
    print("\n📊 检查实验进度:")
    print("-" * 70)

    stdin, stdout, stderr = ssh.exec_command("""
# 检查最近的进程活动
echo "=== 当前PQ-NTOR进程 ==="
ps aux | grep -E 'directory|relay|client' | grep -v grep || echo "无进程"

echo ""
echo "=== 端口占用情况 ==="
netstat -tuln | grep -E '5000|6001|6002|8000' || echo "无端口占用"

echo ""
echo "=== 已生成的结果文件 ==="
ls -lth ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/*.json 2>/dev/null | head -3 || echo "暂无结果文件"
""")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

    # 估算时间
    print("\n⏱️ 时间估算:")
    print("-" * 70)
    print("实验配置:")
    print("  - 12个拓扑")
    print("  - 每拓扑3次运行")
    print("  - 总计：36次测试")
    print()
    print("单次测试耗时估算:")
    print("  - 清理进程：1秒")
    print("  - 启动directory：3秒")
    print("  - 启动relays：3秒")
    print("  - Client测试：5-15秒（取决于网络）")
    print("  - 清理：1秒")
    print("  ≈ 平均每次测试：13-23秒")
    print()
    print("总时间估算:")
    print("  - 最快：36次 × 13秒 ≈ 8分钟")
    print("  - 平均：36次 × 18秒 ≈ 11分钟")
    print("  - 最慢：36次 × 23秒 ≈ 14分钟")
    print()
    print("💡 建议：等待10-15分钟后查看结果")

finally:
    ssh.close()
