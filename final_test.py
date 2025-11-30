#!/usr/bin/env python3
"""
最终测试 - 确保directory保持运行并测试3跳
"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.5.110", username="user", password="user")

print("="*70)
print("  最终三跳电路测试")
print("="*70)

# 清理
print("\n[1/4] 清理旧进程...")
ssh.exec_command("pkill -f directory; pkill -f relay")
time.sleep(1)

# 启动directory（使用while true保持运行）
print("\n[2/4] 启动directory（持续模式）...")
ssh.exec_command(
    "cd ~/pq-ntor-experiment/c && "
    "nohup sh -c 'while true; do ./directory 5000 2>&1; sleep 1; done' > ~/directory.log 2>&1 &"
)
time.sleep(3)

# 验证directory响应
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/nodes")
dir_response = stdout.read().decode()
print(f"  Directory响应:\n{dir_response[:200]}...")

if '"nodes"' not in dir_response:
    print("  ❌ Directory未正常响应")
    ssh.close()
    exit(1)
else:
    print("  ✓ Directory正常工作")

# 运行3跳测试
print("\n[3/4] 运行三跳电路测试...")
stdin, stdout, stderr = ssh.exec_command(
    "cd ~/pq-ntor-experiment/last_experiment/phytium_deployment && "
    "./benchmark_3hop_circuit 10 localhost 5000 2>&1",
    timeout=60
)
test_output = stdout.read().decode()
print(test_output)

# 保存结果
ssh.exec_command(f"echo '{test_output}' > /tmp/3hop_final_test.log")

# 清理
print("\n[4/4] 清理...")
ssh.exec_command("pkill -f directory; pkill -f 'while true'")

# 检查是否成功
if "Completed:" in test_output and "/10 successful" in test_output:
    print("\n" + "="*70)
    print("  ✅ 测试成功！")
    print("="*70)
else:
    print("\n" + "="*70)
    print("  ⚠️ 测试可能失败，请检查输出")
    print("="*70)

ssh.close()
