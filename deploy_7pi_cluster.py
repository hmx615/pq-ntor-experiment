#!/usr/bin/env python3
"""
7π集群自动部署脚本
基于实际IP: 110, 185-190
"""

import paramiko
import time
import sys
from pathlib import Path

# 节点配置
NODES = {
    "client": {"ip": "192.168.5.110", "role": "Client"},
    "directory": {"ip": "192.168.5.185", "role": "Directory", "port": 5000},
    "guard": {"ip": "192.168.5.186", "role": "Guard", "port": 6000},
    "middle": {"ip": "192.168.5.187", "role": "Middle", "port": 6001},
    "exit": {"ip": "192.168.5.188", "role": "Exit", "port": 6002},
    "target": {"ip": "192.168.5.189", "role": "Target", "port": 8000},
    "monitor": {"ip": "192.168.5.190", "role": "Monitor"},
}

SSH_USER = "user"
SSH_PASS = "user"
TIMEOUT = 30

def ssh_connect(ip, username=SSH_USER, password=SSH_PASS):
    """建立SSH连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=username, password=password, timeout=TIMEOUT)
        return ssh
    except Exception as e:
        print(f"  ❌ 连接 {ip} 失败: {e}")
        return None

def exec_command(ssh, cmd, description="", timeout=120):
    """执行SSH命令"""
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if description:
            if exit_code == 0:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} (exit code: {exit_code})")
                if error:
                    print(f"     错误: {error[:200]}")

        return exit_code == 0, output, error
    except Exception as e:
        print(f"  ❌ 执行命令失败: {e}")
        return False, "", str(e)

def check_connectivity():
    """检查所有节点连通性"""
    print("\n" + "="*70)
    print("步骤1: 检查节点连通性")
    print("="*70)

    all_ok = True
    for name, config in NODES.items():
        ip = config["ip"]
        role = config["role"]
        print(f"\n检查 {role} ({ip})...")

        ssh = ssh_connect(ip)
        if ssh:
            success, output, _ = exec_command(ssh, "hostname", f"获取主机名")
            if success:
                print(f"  ✅ {role} 在线")
            ssh.close()
        else:
            all_ok = False
            print(f"  ❌ {role} 无法连接")

    return all_ok

def deploy_code_to_node(ip, role):
    """部署代码到单个节点"""
    print(f"\n部署到 {role} ({ip})...")

    ssh = ssh_connect(ip)
    if not ssh:
        return False

    # 1. 检查是否已有代码目录
    success, output, _ = exec_command(ssh, "ls ~/pq-ntor-experiment", "检查代码目录")

    if not success:
        print("  📦 代码目录不存在，需要从Pi #1复制...")
        # 从Pi #1复制代码（使用scp）
        cmd = f"sshpass -p '{SSH_PASS}' scp -r -o StrictHostKeyChecking=no user@192.168.5.110:~/pq-ntor-experiment ~/pq-ntor-experiment"
        exec_command(ssh, cmd, "从Pi #1复制代码", timeout=180)
    else:
        print("  ✅ 代码目录已存在")

    # 2. 编译代码
    print("  🔨 开始编译...")
    cmd = "cd ~/pq-ntor-experiment/c && make clean && make all"
    success, output, error = exec_command(ssh, cmd, "编译所有组件", timeout=180)

    if not success:
        print(f"  ⚠️  编译输出:\n{output[-500:]}")

    # 3. 验证二进制文件
    success, output, _ = exec_command(ssh, "ls -lh ~/pq-ntor-experiment/c/ | grep -E '(directory|relay|benchmark)'")
    if success and output:
        print(f"  ✅ 编译成功，二进制文件:\n{output}")

    ssh.close()
    return True

def deploy_all_nodes():
    """部署到所有节点（除了client）"""
    print("\n" + "="*70)
    print("步骤2: 部署代码到所有节点")
    print("="*70)

    # 跳过client (110)，因为它已经有代码了
    for name, config in NODES.items():
        if name == "client":
            print(f"\n跳过 {config['role']} ({config['ip']}) - 已有代码")
            continue

        deploy_code_to_node(config["ip"], config["role"])
        time.sleep(1)  # 避免过载

def start_directory_server():
    """启动Directory服务器"""
    print("\n" + "="*70)
    print("步骤3: 启动Directory服务器")
    print("="*70)

    ip = NODES["directory"]["ip"]
    port = NODES["directory"]["port"]

    print(f"\n启动Directory服务器 ({ip}:{port})...")

    ssh = ssh_connect(ip)
    if not ssh:
        return False

    # 停止旧进程
    exec_command(ssh, "pkill -9 directory", "停止旧进程")
    time.sleep(1)

    # 启动新进程
    cmd = f"cd ~/pq-ntor-experiment/c && nohup sh -c 'while true; do ./directory {port} 2>&1; sleep 1; done' > ~/directory.log 2>&1 &"
    exec_command(ssh, cmd, f"启动Directory服务器")

    time.sleep(2)

    # 验证启动
    success, output, _ = exec_command(ssh, "ps aux | grep directory | grep -v grep")
    if success and output:
        print(f"  ✅ Directory服务器已启动")
        print(f"     进程: {output.strip()[:100]}")
    else:
        print(f"  ❌ Directory服务器启动失败")
        ssh.close()
        return False

    ssh.close()

    # 测试Directory服务
    time.sleep(2)
    print(f"\n  📡 测试Directory服务...")
    ssh = ssh_connect(ip)
    success, output, _ = exec_command(ssh, f"curl -s http://localhost:{port}/nodes")
    if success:
        print(f"  ✅ Directory响应正常: {output[:100]}")
    else:
        print(f"  ⚠️  Directory可能还在启动中")
    ssh.close()

    return True

def start_relay_nodes():
    """启动3个Relay节点"""
    print("\n" + "="*70)
    print("步骤4: 启动Relay节点")
    print("="*70)

    directory_ip = NODES["directory"]["ip"]
    directory_port = NODES["directory"]["port"]

    relay_nodes = ["guard", "middle", "exit"]

    for name in relay_nodes:
        config = NODES[name]
        ip = config["ip"]
        port = config["port"]
        role = config["role"]

        print(f"\n启动 {role} ({ip}:{port})...")

        ssh = ssh_connect(ip)
        if not ssh:
            continue

        # 停止旧进程
        exec_command(ssh, "pkill -9 relay", "停止旧进程")
        time.sleep(1)

        # 启动Relay
        cmd = f"cd ~/pq-ntor-experiment/c && nohup ./relay {port} {directory_ip} {directory_port} > ~/{name}.log 2>&1 &"
        exec_command(ssh, cmd, f"启动{role}节点")

        time.sleep(2)

        # 验证启动
        success, output, _ = exec_command(ssh, "ps aux | grep relay | grep -v grep")
        if success and output:
            print(f"  ✅ {role}已启动")
        else:
            print(f"  ❌ {role}启动失败")

        ssh.close()
        time.sleep(1)

def start_target_server():
    """启动Target HTTP服务器"""
    print("\n" + "="*70)
    print("步骤5: 启动Target HTTP服务器")
    print("="*70)

    ip = NODES["target"]["ip"]
    port = NODES["target"]["port"]

    print(f"\n启动Target HTTP服务器 ({ip}:{port})...")

    ssh = ssh_connect(ip)
    if not ssh:
        return False

    # 停止旧进程
    exec_command(ssh, "pkill -9 -f 'python.*http.server'", "停止旧HTTP服务器")
    time.sleep(1)

    # 启动HTTP服务器
    cmd = f"cd ~ && nohup python3 -m http.server {port} > ~/target.log 2>&1 &"
    exec_command(ssh, cmd, "启动HTTP服务器")

    time.sleep(2)

    # 验证启动
    success, output, _ = exec_command(ssh, "ps aux | grep 'http.server' | grep -v grep")
    if success and output:
        print(f"  ✅ Target HTTP服务器已启动")
    else:
        print(f"  ❌ Target启动失败")

    # 测试HTTP服务
    success, output, _ = exec_command(ssh, f"curl -s http://localhost:{port}/ | head -5")
    if success and output:
        print(f"  ✅ HTTP响应正常")

    ssh.close()
    return True

def run_basic_test():
    """运行基础三跳电路测试"""
    print("\n" + "="*70)
    print("步骤6: 运行基础三跳电路测试")
    print("="*70)

    client_ip = NODES["client"]["ip"]
    directory_ip = NODES["directory"]["ip"]
    directory_port = NODES["directory"]["port"]

    print(f"\n在Client ({client_ip})上运行测试...")

    ssh = ssh_connect(client_ip)
    if not ssh:
        return False

    # 检查是否有benchmark_3hop_circuit
    success, output, _ = exec_command(ssh, "ls ~/pq-ntor-experiment/c/benchmark_3hop_circuit")

    if not success:
        print("  ⚠️  benchmark_3hop_circuit不存在，需要编译...")
        cmd = "cd ~/pq-ntor-experiment/c && make benchmark_3hop_circuit"
        exec_command(ssh, cmd, "编译benchmark_3hop_circuit", timeout=60)

    # 运行测试（10次）
    print(f"\n  🧪 运行10次三跳电路测试...")
    cmd = f"cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 10 {directory_ip} {directory_port}"
    success, output, error = exec_command(ssh, cmd, "三跳电路测试", timeout=120)

    if success:
        print(f"\n  ✅ 测试完成！")
        print(f"\n{'='*70}")
        print("测试结果:")
        print('='*70)
        print(output)
    else:
        print(f"\n  ❌ 测试失败")
        print(f"错误输出: {error[:500]}")

    ssh.close()
    return success

def show_cluster_status():
    """显示集群状态"""
    print("\n" + "="*70)
    print("7π集群状态")
    print("="*70)

    for name, config in NODES.items():
        ip = config["ip"]
        role = config["role"]

        ssh = ssh_connect(ip)
        if ssh:
            # 检查进程
            if name == "directory":
                success, output, _ = exec_command(ssh, "ps aux | grep directory | grep -v grep | wc -l")
                status = "🟢 运行中" if success and int(output.strip()) > 0 else "🔴 未运行"
            elif name in ["guard", "middle", "exit"]:
                success, output, _ = exec_command(ssh, "ps aux | grep relay | grep -v grep | wc -l")
                status = "🟢 运行中" if success and int(output.strip()) > 0 else "🔴 未运行"
            elif name == "target":
                success, output, _ = exec_command(ssh, "ps aux | grep 'http.server' | grep -v grep | wc -l")
                status = "🟢 运行中" if success and int(output.strip()) > 0 else "🔴 未运行"
            else:
                status = "⚪ 客户端/监控"

            print(f"{role:12} ({ip}) - {status}")
            ssh.close()
        else:
            print(f"{role:12} ({ip}) - 🔴 离线")

def main():
    """主流程"""
    print("\n" + "="*70)
    print("7π PQ-NTOR集群自动部署")
    print("="*70)
    print("\n节点配置:")
    for name, config in NODES.items():
        port_info = f":{config['port']}" if 'port' in config else ""
        print(f"  {config['role']:12} - {config['ip']}{port_info}")

    print("\n开始部署...")

    # 步骤1: 检查连通性
    if not check_connectivity():
        print("\n❌ 部分节点无法连接，请检查网络配置")
        return

    # 步骤2: 部署代码
    deploy_all_nodes()

    # 步骤3: 启动Directory
    if not start_directory_server():
        print("\n❌ Directory服务器启动失败")
        return

    time.sleep(3)  # 等待Directory完全启动

    # 步骤4: 启动Relay节点
    start_relay_nodes()

    time.sleep(3)  # 等待Relay注册

    # 步骤5: 启动Target
    start_target_server()

    time.sleep(2)

    # 步骤6: 显示状态
    show_cluster_status()

    # 步骤7: 运行测试
    print("\n" + "="*70)
    print("准备运行测试...")
    print("="*70)
    input("\n按Enter键开始三跳电路测试...")

    run_basic_test()

    print("\n" + "="*70)
    print("✅ 7π集群部署完成！")
    print("="*70)
    print("\n下一步:")
    print("  1. 查看集群状态: python3 deploy_7pi_cluster.py --status")
    print("  2. 运行完整测试: ssh user@192.168.5.110 'cd ~/pq-ntor-experiment/c && ./benchmark_3hop_circuit 100 192.168.5.185 5000'")
    print("  3. 开始12拓扑测试: python3 test_12topo_7pi.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_cluster_status()
    else:
        main()
