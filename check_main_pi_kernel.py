#!/usr/bin/env python3
"""检查主派内核和TC支持情况"""

import paramiko

PI_IP = "192.168.5.110"
USERNAME = "user"
PASSWORD = "user"

def check_kernel():
    """检查内核配置"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        print("=" * 70)
        print("  检查主派内核和TC支持")
        print("=" * 70)
        print()

        # 1. 内核版本
        print("1️⃣  内核版本:")
        stdin, stdout, stderr = ssh.exec_command("uname -r")
        kernel = stdout.read().decode().strip()
        print(f"   {kernel}")
        print()

        # 2. 检查可用的内核模块目录
        print("2️⃣  内核模块目录:")
        stdin, stdout, stderr = ssh.exec_command("ls -la /lib/modules/")
        print(stdout.read().decode())

        # 3. 检查是否有netem相关的.ko文件
        print("3️⃣  搜索netem模块文件:")
        stdin, stdout, stderr = ssh.exec_command("find /lib/modules/ -name '*netem*.ko*' 2>/dev/null")
        netem_modules = stdout.read().decode().strip()
        if netem_modules:
            print(f"✅ 找到netem模块:")
            print(netem_modules)
        else:
            print("❌ 未找到netem模块文件")
        print()

        # 4. 检查内核配置
        print("4️⃣  检查内核配置文件:")
        stdin, stdout, stderr = ssh.exec_command("ls /boot/config-* 2>/dev/null | head -1")
        config_file = stdout.read().decode().strip()
        if config_file:
            print(f"   找到: {config_file}")
            stdin, stdout, stderr = ssh.exec_command(f"grep -i netem {config_file} 2>/dev/null | head -5")
            config = stdout.read().decode().strip()
            if config:
                print(f"   配置:")
                print(f"   {config}")
            else:
                print("   未找到netem配置")
        else:
            print("   ❌ 未找到内核配置文件")
        print()

        # 5. 测试基本TC命令
        print("5️⃣  测试基本TC命令:")
        stdin, stdout, stderr = ssh.exec_command("echo 'user' | sudo -S tc qdisc show dev lo 2>&1")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(f"   输出: {output}")
        if error:
            print(f"   错误: {error}")
        print()

        # 6. 检查是否可以使用tbf (token bucket filter)
        print("6️⃣  尝试使用tbf限速 (不需要netem):")
        cmd = "echo 'user' | sudo -S tc qdisc add dev lo root tbf rate 50mbit burst 32kbit latency 400ms 2>&1; echo 'user' | sudo -S tc qdisc del dev lo root 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        if "Error" in output or "FATAL" in output:
            print(f"   ❌ tbf也不支持: {output}")
        else:
            print(f"   ✅ tbf可用（可以做带宽限制）")

        ssh.close()

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_kernel()
