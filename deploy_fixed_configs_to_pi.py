#!/usr/bin/env python3
"""
部署修复后的12拓扑配置到飞腾派集群
"""

import paramiko
import os
from pathlib import Path

# 飞腾派配置 - 部署到所有7个Pi
PI_CONFIGS = [
    {"ip": "192.168.5.110", "name": "Pi-110 (主派)"},
    {"ip": "192.168.5.185", "name": "Pi-185 (带屏)"},
    {"ip": "192.168.5.186", "name": "Pi-186 (Guard)"},
    {"ip": "192.168.5.187", "name": "Pi-187 (Middle)"},
    {"ip": "192.168.5.188", "name": "Pi-188 (Exit)"},
    {"ip": "192.168.5.189", "name": "Pi-189"},
    {"ip": "192.168.5.190", "name": "Pi-190"},
]

USERNAME = "user"
PASSWORD = "user"

# 本地配置文件目录
LOCAL_CONFIG_DIR = Path("/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/configs")
LOCAL_SCRIPTS_DIR = Path("/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/scripts")

# 远程目标目录 (使用Desktop上的部署)
REMOTE_BASE = "/home/user/Desktop/pq-ntor-experiment-main"
REMOTE_CONFIG_DIR = f"{REMOTE_BASE}/sagin-experiments/pq-ntor-12topo-experiment/configs"
REMOTE_SCRIPTS_DIR = f"{REMOTE_BASE}/sagin-experiments/pq-ntor-12topo-experiment/scripts"

def deploy_to_pi(pi_config):
    """部署配置到单个飞腾派"""
    ip = pi_config["ip"]
    name = pi_config["name"]

    print(f"\n{'='*70}")
    print(f"📡 部署到 {name} ({ip})")
    print(f"{'='*70}")

    try:
        # 连接SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=10)

        # 创建目录
        print("📁 创建目录...")
        ssh.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        ssh.exec_command(f"mkdir -p {REMOTE_SCRIPTS_DIR}")

        # 上传配置文件
        sftp = ssh.open_sftp()

        print("📤 上传配置文件...")
        config_files = list(LOCAL_CONFIG_DIR.glob("topo*.json"))
        for local_file in config_files:
            remote_file = f"{REMOTE_CONFIG_DIR}/{local_file.name}"
            print(f"  {local_file.name}")
            sftp.put(str(local_file), remote_file)

        print(f"✅ 上传了 {len(config_files)} 个配置文件")

        # 上传测试脚本
        print("📤 上传测试脚本...")
        script_files = [
            "run_simple_test.py",
            "regenerate_configs_with_correct_params.py"
        ]
        for script_name in script_files:
            local_script = LOCAL_SCRIPTS_DIR / script_name
            if local_script.exists():
                remote_script = f"{REMOTE_SCRIPTS_DIR}/{script_name}"
                print(f"  {script_name}")
                sftp.put(str(local_script), remote_script)
                # 设置执行权限
                ssh.exec_command(f"chmod +x {remote_script}")

        # 验证
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {REMOTE_CONFIG_DIR} | wc -l")
        count = stdout.read().decode().strip()
        print(f"✅ 远程配置文件数: {count}")

        sftp.close()
        ssh.close()

        return True

    except Exception as e:
        print(f"❌ 部署失败: {e}")
        return False

def main():
    """主函数"""
    print("="*70)
    print("  部署修复后的12拓扑配置到飞腾派集群")
    print("="*70)
    print()

    # 检查本地文件
    if not LOCAL_CONFIG_DIR.exists():
        print(f"❌ 本地配置目录不存在: {LOCAL_CONFIG_DIR}")
        return

    config_files = list(LOCAL_CONFIG_DIR.glob("topo*.json"))
    print(f"📁 本地配置文件: {len(config_files)} 个")

    if len(config_files) == 0:
        print("❌ 没有找到配置文件")
        return

    # 部署到所有飞腾派
    success_count = 0
    for pi_config in PI_CONFIGS:
        if deploy_to_pi(pi_config):
            success_count += 1

    print()
    print("="*70)
    print(f"📊 部署完成: {success_count}/{len(PI_CONFIGS)} 成功")
    print("="*70)

    if success_count == len(PI_CONFIGS):
        print()
        print("✅ 所有飞腾派部署成功！")
        print()
        print("下一步：")
        print("  在主派 (192.168.5.110) 上运行实验")
        print("  ssh user@192.168.5.110")
        print("  cd /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment/scripts")
        print("  python3 run_simple_test.py --all --runs 10")

if __name__ == "__main__":
    main()
