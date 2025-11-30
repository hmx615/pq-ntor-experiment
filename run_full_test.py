#!/usr/bin/env python3
"""
运行完整三跳测试 - 启动directory + 3个relay + 测试
"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.5.110", username="user", password="user")

print("="*70)
print("  完整三跳电路测试")
print("="*70)

# 清理旧进程
print("\n[1/5] 清理旧进程...")
ssh.exec_command("pkill -f directory; pkill -f relay")
time.sleep(1)

# 启动directory
print("\n[2/5] 启动directory服务器...")
stdin, stdout, stderr = ssh.exec_command(
    "cd ~/pq-ntor-experiment/c && nohup ./directory 5000 > ~/directory.log 2>&1 &"
)
time.sleep(2)

# 检查directory
stdin, stdout, stderr = ssh.exec_command("pgrep -a directory")
dir_proc = stdout.read().decode()
if dir_proc:
    print(f"  ✓ Directory运行中: {dir_proc.strip()}")
else:
    print("  ❌ Directory未启动")
    ssh.close()
    exit(1)

# 启动3个relay
print("\n[3/5] 启动3个relay节点...")
commands = [
    "cd ~/pq-ntor-experiment/c && nohup ./relay 6000 guard localhost:5000 > ~/guard.log 2>&1 &",
    "cd ~/pq-ntor-experiment/c && nohup ./relay 6001 middle localhost:5000 > ~/middle.log 2>&1 &",
    "cd ~/pq-ntor-experiment/c && nohup ./relay 6002 exit localhost:5000 > ~/exit.log 2>&1 &"
]

for cmd in commands:
    ssh.exec_command(cmd)
    time.sleep(1)

time.sleep(2)

# 检查relay
stdin, stdout, stderr = ssh.exec_command("pgrep -a relay")
relay_procs = stdout.read().decode()
if relay_procs:
    print(f"  ✓ Relay节点:\n{relay_procs}")
else:
    print("  ❌ Relay未启动")

# 查看日志
print("\n[4/5] 检查日志...")
for log_name in ["directory", "guard", "middle", "exit"]:
    stdin, stdout, stderr = ssh.exec_command(f"tail -5 ~/{log_name}.log 2>&1")
    log_content = stdout.read().decode()
    print(f"\n  {log_name}.log (最后5行):")
    print(f"    {log_content.strip()}")

# 等待服务稳定
print("\n  等待服务稳定...")
time.sleep(5)

# 运行三跳测试
print("\n[5/5] 运行三跳电路测试...")
stdin, stdout, stderr = ssh.exec_command(
    "cd ~/pq-ntor-experiment/last_experiment/phytium_deployment && "
    "./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tee /tmp/3hop_test.log",
    timeout=60
)
test_output = stdout.read().decode()
print(test_output)

# 清理
print("\n清理进程...")
ssh.exec_command("pkill -f directory; pkill -f relay")

print("\n" + "="*70)
print("  测试完成")
print("="*70)

ssh.close()
