#!/usr/bin/env python3
"""在所有飞腾派上修复TC netem模块并配置sudo无密码"""

import paramiko
import time

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

def fix_pi(pi_config):
    """修复单个飞腾派的TC netem"""
    ip = pi_config["ip"]
    name = pi_config["name"]

    print(f"\n{'='*70}")
    print(f"🔧 修复 {name} ({ip})")
    print(f"{'='*70}")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=10)

        # 1. 直接加载netem模块（使用echo密码）
        print("📦 加载 sch_netem 模块...")
        cmd = f"echo '{PASSWORD}' | sudo -S modprobe sch_netem 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        time.sleep(1)

        # 验证模块是否加载
        stdin, stdout, stderr = ssh.exec_command("lsmod | grep sch_netem")
        result = stdout.read().decode().strip()

        if result:
            print(f"✅ netem模块已加载")
        else:
            print(f"⚠️  netem模块加载失败")
            if output:
                print(f"   输出: {output}")
            if error:
                print(f"   错误: {error}")

        # 2. 配置sudo无密码（for tc命令）
        print("🔐 配置 sudo 无密码...")
        sudoers_rule = f"{USERNAME} ALL=(ALL) NOPASSWD: /sbin/tc, /usr/sbin/tc, /bin/tc"
        cmd = f"echo '{PASSWORD}' | sudo -S bash -c 'echo \"{sudoers_rule}\" > /etc/sudoers.d/tc-nopasswd && chmod 0440 /etc/sudoers.d/tc-nopasswd' 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()

        # 验证配置
        stdin, stdout, stderr = ssh.exec_command("sudo -l | grep tc")
        result = stdout.read().decode().strip()

        if "NOPASSWD" in result and "tc" in result:
            print(f"✅ sudo 无密码已配置")
        else:
            print(f"⚠️  sudo 配置可能失败")
            if result:
                print(f"   {result}")

        ssh.close()
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("  修复所有飞腾派 TC netem 模块")
    print("=" * 70)
    print()

    success_count = 0
    for pi_config in PI_CONFIGS:
        if fix_pi(pi_config):
            success_count += 1

    print()
    print("=" * 70)
    print(f"📊 修复完成: {success_count}/{len(PI_CONFIGS)} 成功")
    print("=" * 70)

    if success_count == len(PI_CONFIGS):
        print()
        print("✅ 所有飞腾派 TC netem 模块已修复！")
        print()
        print("现在可以运行实验了:")
        print("  python3 /home/ccc/pq-ntor-experiment/run_experiment_on_pi.py")

if __name__ == "__main__":
    main()
