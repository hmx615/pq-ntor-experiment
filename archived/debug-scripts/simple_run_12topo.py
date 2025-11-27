#!/usr/bin/env python3
import paramiko
import time

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

print("╔══════════════════════════════════════════════════════════════╗")
print("║          飞腾派12拓扑PQ-NTOR实验                               ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"🔌 连接到 {HOST}...")
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    print("✅ 连接成功\n")

    # 上传脚本
    print("📤 上传测试脚本...")
    sftp = ssh.open_sftp()
    sftp.put("/tmp/phytium_12topo_test.py", "/home/user/run_12topo.py")
    sftp.close()
    print("✅ 上传完成\n")

    # 运行实验
    print("="*70)
    print("  🏃 开始执行实验（这可能需要5-10分钟）")
    print("="*70)
    print()

    run_cmd = """
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
cd ~
python3 run_12topo.py 2>&1
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
    print(f"\n\n实验完成，退出码: {exit_code}")

    # 获取结果
    print("\n" + "="*70)
    print("  📥 获取结果")
    print("="*70)

    stdin, stdout, stderr = ssh.exec_command(
        "ls -lt ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/*.json 2>/dev/null | head -1 | awk '{print $NF}'"
    )
    latest_result = stdout.read().decode().strip()

    if latest_result:
        print(f"\n最新结果: {latest_result}\n")
        stdin, stdout, stderr = ssh.exec_command(f"python3 -m json.tool {latest_result} | head -60")
        print(stdout.read().decode())

    print("\n✅ 实验完成！")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
    print("\n🔌 SSH连接已关闭")
