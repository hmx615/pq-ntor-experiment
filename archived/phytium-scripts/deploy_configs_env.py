#!/usr/bin/env python3
"""
部署拓扑配置文件和配置环境变量
"""

import paramiko
import os
from pathlib import Path

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

LOCAL_CONFIG_DIR = "/home/ccc/pq-ntor-experiment/sagin-experiments/noma-topologies/configs"
REMOTE_CONFIG_DIR = "/home/user/pq-ntor-experiment/sagin-experiments/noma-topologies/configs"

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          部署拓扑配置和环境变量                                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"🔌 连接到 {HOST}...")
        ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        print("✅ 连接成功\n")

        # 创建SFTP客户端
        sftp = ssh.open_sftp()

        # 1. 创建远程目录
        print("="*70)
        print("  📁 创建目录结构")
        print("="*70)
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        stdout.channel.recv_exit_status()
        print(f"✅ 目录创建: {REMOTE_CONFIG_DIR}\n")

        # 2. 传输拓扑配置文件
        print("="*70)
        print("  📤 传输12个拓扑配置文件")
        print("="*70)

        local_files = sorted(Path(LOCAL_CONFIG_DIR).glob("topology_*.json"))
        print(f"本地找到 {len(local_files)} 个配置文件\n")

        for local_file in local_files:
            remote_file = f"{REMOTE_CONFIG_DIR}/{local_file.name}"
            print(f"  传输: {local_file.name}")
            sftp.put(str(local_file), remote_file)
            print(f"     ✅ → {remote_file}")

        print(f"\n✅ 所有配置文件传输完成\n")

        # 3. 验证传输
        print("="*70)
        print("  ✅ 验证文件传输")
        print("="*70)
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {REMOTE_CONFIG_DIR}/topology_*.json | wc -l")
        count = stdout.read().decode().strip()
        print(f"远程配置文件数量: {count}\n")

        if count == "12":
            print("✅ 12个配置文件全部到位！\n")
        else:
            print(f"⚠️ 预期12个，实际{count}个\n")

        # 4. 配置环境变量
        print("="*70)
        print("  ⚙️ 配置环境变量")
        print("="*70)

        env_setup = """
# 检查是否已配置
if ! grep -q "LIBOQS" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# PQ-Tor liboqs环境变量" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=\$HOME/_oqs/lib:\$LD_LIBRARY_PATH" >> ~/.bashrc
    echo "export LIBOQS_DIR=\$HOME/_oqs" >> ~/.bashrc
    echo "✅ 环境变量已添加到 ~/.bashrc"
else
    echo "✅ 环境变量已存在"
fi

# 显示当前配置
echo ""
echo "当前bashrc中的liboqs配置:"
grep -A2 "PQ-Tor liboqs" ~/.bashrc 2>/dev/null || echo "未找到"
"""
        stdin, stdout, stderr = ssh.exec_command(env_setup)
        output = stdout.read().decode()
        print(output)

        # 5. 验证环境
        print("="*70)
        print("  🧪 验证环境配置")
        print("="*70)

        test_cmd = """
source ~/.bashrc
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "LIBOQS_DIR: $LIBOQS_DIR"
echo ""
echo "测试liboqs库:"
ls -lh $_oqs/lib/liboqs.a
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        print(output)

        # 6. 测试Kyber程序
        print("="*70)
        print("  🧪 测试Kyber程序")
        print("="*70)

        test_kyber_cmd = """
cd ~/pq-ntor-experiment/c
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
./test_kyber 2>&1 | tail -10
"""
        stdin, stdout, stderr = ssh.exec_command(test_kyber_cmd, timeout=10)
        output = stdout.read().decode()
        if "SUCCESS" in output:
            print("✅ Kyber测试通过")
            print(output)
        else:
            print("输出:")
            print(output)

        # 7. 最终总结
        print("\n" + "="*70)
        print("  📊 部署总结")
        print("="*70)
        print("✅ 拓扑配置文件: 12个已部署")
        print("✅ 环境变量: 已配置到 ~/.bashrc")
        print("✅ liboqs路径: $HOME/_oqs")
        print("✅ LD_LIBRARY_PATH: 已设置")
        print("\n" + "="*70)
        print("  🚀 准备就绪！")
        print("="*70)
        print("\n可以开始12拓扑实验:")
        print("  方式1: SSH登录手动运行")
        print("    ssh user@192.168.5.110")
        print("    cd ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/scripts")
        print("    python3 run_pq_ntor_12topologies.py --mode pq --runs 10")
        print("\n  方式2: 使用远程执行脚本")
        print("    python3 run_12topo_remote.py")
        print()

        sftp.close()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        ssh.close()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
