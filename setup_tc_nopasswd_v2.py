#!/usr/bin/env python3
"""
配置Pi节点无密码sudo for TC命令 (Version 2 - 使用临时脚本)
"""

import paramiko
import sys
import time

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

        # 步骤1: 创建临时脚本
        print(f"  [1/4] 创建配置脚本...")
        script_content = """#!/bin/bash
echo 'user ALL=(ALL) NOPASSWD: /sbin/tc' | sudo tee /etc/sudoers.d/tc-nopasswd > /dev/null
sudo chmod 440 /etc/sudoers.d/tc-nopasswd
"""
        stdin, stdout, stderr = ssh.exec_command("cat > /tmp/setup_tc.sh")
        stdin.write(script_content)
        stdin.channel.shutdown_write()
        stdout.read()

        # 步骤2: 添加执行权限
        print(f"  [2/4] 添加执行权限...")
        ssh.exec_command("chmod +x /tmp/setup_tc.sh")
        time.sleep(0.5)

        # 步骤3: 执行脚本 (提供密码)
        print(f"  [3/4] 执行配置...")
        stdin, stdout, stderr = ssh.exec_command("/tmp/setup_tc.sh", get_pty=True)
        stdin.write(f"{SSH_PASS}\n")
        stdin.flush()

        output = stdout.read().decode()
        exit_code = stdout.channel.recv_exit_status()

        # 步骤4: 验证
        print(f"  [4/4] 验证配置...")
        time.sleep(0.5)
        stdin2, stdout2, stderr2 = ssh.exec_command("sudo -n tc qdisc show dev eth0 2>&1")
        test_output = stdout2.read().decode()
        test_error = stderr2.read().decode()

        if "需要密码" in test_output or "password" in test_output.lower():
            print(f"  ❌ {name} 验证失败 - 仍需要密码")
            print(f"     输出: {test_output[:150]}")
            return False
        else:
            print(f"  ✅ {name} 配置成功！TC命令现在可以无密码执行")
            return True

    except Exception as e:
        print(f"  ❌ {name} 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        try:
            ssh.exec_command("rm -f /tmp/setup_tc.sh")
            ssh.close()
        except:
            pass

if __name__ == "__main__":
    print("="*60)
    print("配置Pi节点TC命令无密码sudo (Version 2)")
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
