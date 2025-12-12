#!/usr/bin/env python3
"""检查飞腾派TC netem模块状态"""

import paramiko

PI_IP = "192.168.5.110"
USERNAME = "user"
PASSWORD = "user"

def check_tc_netem():
    """检查TC netem模块"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        print("=" * 70)
        print("  检查主派 TC netem 模块状态")
        print("=" * 70)
        print()

        # 检查netem模块是否加载
        print("1. 检查netem模块...")
        stdin, stdout, stderr = ssh.exec_command("lsmod | grep sch_netem")
        output = stdout.read().decode().strip()
        if output:
            print(f"✅ netem模块已加载:")
            print(f"   {output}")
        else:
            print("❌ netem模块未加载")

        print()

        # 尝试加载netem模块
        print("2. 尝试加载netem模块...")
        stdin, stdout, stderr = ssh.exec_command("sudo modprobe sch_netem")
        error = stderr.read().decode().strip()
        if error:
            print(f"❌ 加载失败: {error}")
        else:
            print("✅ 加载命令执行成功")

        print()

        # 再次检查
        stdin, stdout, stderr = ssh.exec_command("lsmod | grep sch_netem")
        output = stdout.read().decode().strip()
        if output:
            print(f"✅ netem模块现在已加载:")
            print(f"   {output}")
        else:
            print("❌ netem模块仍未加载")

        print()

        # 检查fix脚本
        print("3. 检查fix_phytium_tc.sh脚本...")
        stdin, stdout, stderr = ssh.exec_command("ls -la ~/fix_phytium_tc.sh")
        output = stdout.read().decode().strip()
        if output and "fix_phytium_tc.sh" in output:
            print("✅ 修复脚本存在")
            print(f"   {output}")

            # 显示脚本内容前几行
            stdin, stdout, stderr = ssh.exec_command("head -20 ~/fix_phytium_tc.sh")
            content = stdout.read().decode()
            print()
            print("脚本内容:")
            print("-" * 70)
            print(content)
            print("-" * 70)
        else:
            print("❌ 修复脚本不存在")

        ssh.close()

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_tc_netem()
