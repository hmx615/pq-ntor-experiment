#!/usr/bin/env python3
"""检查所有7个飞腾派的连接和状态"""

import paramiko
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# 7个飞腾派配置
PI_CONFIGS = [
    {"ip": "192.168.5.110", "name": "Pi-110 (主派)", "rotate_screen": True},
    {"ip": "192.168.5.185", "name": "Pi-185 (带屏)", "rotate_screen": True},
    {"ip": "192.168.5.186", "name": "Pi-186"},
    {"ip": "192.168.5.187", "name": "Pi-187"},
    {"ip": "192.168.5.188", "name": "Pi-188"},
    {"ip": "192.168.5.189", "name": "Pi-189"},
    {"ip": "192.168.5.190", "name": "Pi-190"},
]

USERNAME = "user"
PASSWORD = "user"

def check_pi(config):
    """检查单个飞腾派的状态"""
    ip = config["ip"]
    name = config["name"]
    result = {
        "ip": ip,
        "name": name,
        "ping": False,
        "ssh": False,
        "hostname": None,
        "arch": None,
        "uptime": None,
        "error": None
    }

    # 1. Ping测试
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result["ping"] = sock.connect_ex((ip, 22)) == 0
        sock.close()
    except:
        result["ping"] = False

    if not result["ping"]:
        result["error"] = "Ping失败 (端口22不通)"
        return result

    # 2. SSH连接测试
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)

        result["ssh"] = True

        # 获取系统信息
        stdin, stdout, stderr = ssh.exec_command("hostname && uname -m && uptime")
        output = stdout.read().decode().strip().split('\n')

        if len(output) >= 3:
            result["hostname"] = output[0]
            result["arch"] = output[1]
            result["uptime"] = output[2]

        ssh.close()

    except paramiko.AuthenticationException:
        result["error"] = "SSH认证失败 (用户名或密码错误)"
    except paramiko.SSHException as e:
        result["error"] = f"SSH连接错误: {str(e)}"
    except Exception as e:
        result["error"] = f"未知错误: {str(e)}"

    return result

def main():
    print("=" * 80)
    print("🔍 检查7个飞腾派状态")
    print("=" * 80)
    print()

    # 并行检查所有派
    results = []
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(check_pi, config): config for config in PI_CONFIGS}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # 按IP排序
    results.sort(key=lambda x: x["ip"])

    # 输出结果
    online_count = 0
    ssh_ok_count = 0

    for r in results:
        print(f"{'='*80}")
        print(f"📍 {r['name']} ({r['ip']})")
        print(f"{'='*80}")

        if r["ping"]:
            print("✅ Ping: 在线")
        else:
            print("❌ Ping: 离线")
            print()
            continue

        online_count += 1

        if r["ssh"]:
            print("✅ SSH: 连接成功")
            ssh_ok_count += 1
            if r["hostname"]:
                print(f"   主机名: {r['hostname']}")
            if r["arch"]:
                print(f"   架构: {r['arch']}")
            if r["uptime"]:
                print(f"   运行时间: {r['uptime']}")
        else:
            print(f"❌ SSH: 连接失败")
            if r["error"]:
                print(f"   错误: {r['error']}")

        print()

    # 汇总
    print("=" * 80)
    print("📊 汇总统计")
    print("=" * 80)
    print(f"在线设备: {online_count}/7")
    print(f"SSH可用: {ssh_ok_count}/7")
    print()

    if ssh_ok_count == 7:
        print("✅ 所有飞腾派都可以正常访问！")
    else:
        print(f"⚠️  有 {7 - ssh_ok_count} 个飞腾派无法SSH访问")

    return ssh_ok_count == 7

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
