#!/usr/bin/env python3
"""
配置Pi节点无密码sudo for TC命令
"""

import paramiko
import sys

SSH_USER = "user"
SSH_PASS = "user"

# 需要配置的节点
NODES = [
    ("192.168.5.186", "Guard"),
    ("192.168.5.187", "Middle"),
    ("192.168.5.188", "Exit"),
]

def setup_tc_nopasswd(ip, name):
    """配置单个节点的TC无密码sudo"""
    try:
        print(f"\n[{name}] 配置 {ip}...")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)

        # 创建sudoers配置 - 使用密码提供的方式
        sudoers_content = "user ALL=(ALL) NOPASSWD: /sbin/tc"

        # 方法1: 使用tee和echo (避免直接写入sudoers)
        cmd = f'echo "{sudoers_content}" | sudo -S tee /etc/sudoers.d/tc-nopasswd > /dev/null 2>&1'
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        stdin.write(f"{SSH_PASS}\n")
        stdin.flush()

        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            # 验证配置
            stdin2, stdout2, stderr2 = ssh.exec_command("sudo -n tc qdisc show dev eth0 2>&1", timeout=5)
            test_output = stdout2.read().decode()

            if "需要密码" not in test_output and "password" not in test_output.lower():
                print(f"  ✅ {name} 配置成功 - TC命令现在可以无密码执行")
            else:
                print(f"  ⚠️ {name} 配置可能失败 - 仍需要密码")
                print(f"     测试输出: {test_output[:100]}")
        else:
            print(f"  ❌ {name} 配置失败 (exit code: {exit_code})")

        ssh.close()
        return exit_code == 0

    except Exception as e:
        print(f"  ❌ {name} 错误: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("配置Pi节点TC命令无密码sudo")
    print("="*60)

    success_count = 0
    for ip, name in NODES:
        if setup_tc_nopasswd(ip, name):
            success_count += 1

    print("\n" + "="*60)
    print(f"配置完成: {success_count}/{len(NODES)} 节点成功")
    print("="*60)

    if success_count == len(NODES):
        print("\n✅ 所有节点配置完成！现在可以运行SAGIN测试了")
        sys.exit(0)
    else:
        print(f"\n⚠️ 只有{success_count}个节点配置成功")
        sys.exit(1)
