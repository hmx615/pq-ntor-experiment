#!/usr/bin/env python3
"""
SAGIN TC部署并运行批量PQ-NTOR测试
完整自动化流程：配置TC → 运行测试 → 收集数据
"""

import paramiko
import json
import time
import csv
from datetime import datetime

SSH_USER = "user"
SSH_PASS = "user"
TIMEOUT = 30

def ssh_connect(ip, retries=3, delay=2):
    """SSH连接,带重试机制"""
    for attempt in range(retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=TIMEOUT)
            return ssh
        except Exception as e:
            if attempt < retries - 1:
                print(f"  ⚠️  SSH连接失败 ({ip}), 重试 {attempt+1}/{retries-1}...", flush=True)
                time.sleep(delay)
            else:
                raise e

def exec_ssh_command(ssh, cmd, timeout=30):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='ignore')
        return exit_code == 0, output
    except Exception as e:
        return False, str(e)

def clear_tc_on_node(ip, interface="eth0"):
    """清除节点上的TC配置"""
    ssh = ssh_connect(ip)
    exec_ssh_command(ssh, f"sudo tc qdisc del dev {interface} root 2>/dev/null || true")
    ssh.close()

def apply_tc_config(tc_commands):
    """应用TC配置到相应节点"""
    applied = {}

    for cmd_info in tc_commands:
        node = cmd_info["node"]
        ip = cmd_info["ip"]

        if node not in applied:
            # 首先清除旧配置
            ssh = ssh_connect(ip)

            if "clear" in cmd_info:
                exec_ssh_command(ssh, cmd_info["clear"])

            if "setup" in cmd_info:
                success, output = exec_ssh_command(ssh, cmd_info["setup"])
                if not success:
                    print(f"  ⚠️  {node} setup failed: {output[:100]}")

            if "rate" in cmd_info:
                success, output = exec_ssh_command(ssh, cmd_info["rate"])
                if not success:
                    print(f"  ⚠️  {node} rate config failed: {output[:100]}")

            ssh.close()
            applied[node] = True

    return len(applied)

def verify_tc_config(node_ips):
    """验证TC配置是否生效"""
    verified = 0
    for node, ip in node_ips.items():
        ssh = ssh_connect(ip)
        success, output = exec_ssh_command(ssh, "sudo tc qdisc show dev eth0")
        if success and ("netem" in output or "tbf" in output):
            verified += 1
        ssh.close()
    return verified

def run_pq_ntor_test(directory_ip, directory_port, target_url, iterations=100):
    """运行PQ-NTOR测试"""
    client_ip = "192.168.5.110"
    ssh = ssh_connect(client_ip)

    results = []

    print(f"    运行{iterations}次PQ-NTOR握手测试...")

    for i in range(iterations):
        start_time = time.time()

        cmd = f"cd ~/pq-ntor-experiment/c && timeout 60 ./client --mode pq -d {directory_ip} -p {directory_port} -u {target_url} 2>&1"

        success, output = exec_ssh_command(ssh, cmd, timeout=90)

        elapsed_ms = (time.time() - start_time) * 1000

        # 解析输出
        handshake_success = "Test completed successfully" in output
        circuit_established = "3-hop circuit established" in output

        result = {
            "iteration": i + 1,
            "success": handshake_success,
            "circuit_ok": circuit_established,
            "total_time_ms": elapsed_ms,
            "timestamp": datetime.now().isoformat()
        }

        results.append(result)

        if (i + 1) % 10 == 0:
            success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
            print(f"      进度: {i+1}/{iterations}, 成功率: {success_rate:.1f}%")

    ssh.close()
    return results

def calculate_statistics(results):
    """计算测试统计"""
    successful = [r for r in results if r["success"]]

    if not successful:
        return {
            "total_tests": len(results),
            "successful": 0,
            "success_rate": 0,
            "avg_time_ms": 0,
            "min_time_ms": 0,
            "max_time_ms": 0,
            "std_dev_ms": 0
        }

    times = [r["total_time_ms"] for r in successful]
    avg_time = sum(times) / len(times)

    # 计算标准差
    variance = sum((t - avg_time) ** 2 for t in times) / len(times)
    std_dev = variance ** 0.5

    return {
        "total_tests": len(results),
        "successful": len(successful),
        "success_rate": len(successful) / len(results) * 100,
        "avg_time_ms": avg_time,
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "std_dev_ms": std_dev
    }

def save_results_csv(all_results, filename="sagin_pq_ntor_results.csv"):
    """保存结果到CSV"""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # 写入表头
        writer.writerow([
            "Topology_ID", "Topology_Name", "Link_Type", "Access_Method",
            "Rate_Mbps", "Delay_ms", "Loss_%", "SINR_dB",
            "Total_Tests", "Successful", "Success_Rate_%",
            "Avg_Time_ms", "Min_Time_ms", "Max_Time_ms", "Std_Dev_ms"
        ])

        # 写入数据
        for result in all_results:
            topo = result["topology"]
            tc = result["tc_config"]
            stats = result["statistics"]

            writer.writerow([
                topo["id"], topo["name"], topo["link_type"], topo["access"],
                tc["rate_mbps"], tc["delay_ms"], tc["loss_pct"], tc["sinr_db"],
                stats["total_tests"], stats["successful"], stats["success_rate"],
                stats["avg_time_ms"], stats["min_time_ms"], stats["max_time_ms"], stats["std_dev_ms"]
            ])

    print(f"✅ 结果已保存到: {filename}")

def run_full_experiment(iterations_per_topo=100):
    """运行完整实验流程"""
    print("="*80, flush=True)
    print("SAGIN 12拓扑PQ-NTOR性能测试", flush=True)
    print("="*80, flush=True)

    # 1. 加载配置
    print("\n[1/4] 加载TC配置...", flush=True)
    with open("sagin_12topo_tc_configs.json", "r", encoding="utf-8") as f:
        all_configs = json.load(f)
    print(f"  ✅ 已加载{len(all_configs)}个拓扑配置", flush=True)

    all_results = []

    # 2. 对每个拓扑进行测试
    for idx, config in enumerate(all_configs, 1):
        topo = config["topology"]
        tc_cmds = config["tc_commands"]

        print(f"\n[拓扑 {idx}/12] {topo['name']}", flush=True)
        print("-"*80, flush=True)

        # 2a. 应用TC配置
        print(f"  [1/3] 应用TC配置...", flush=True)
        num_nodes = apply_tc_config(tc_cmds)
        print(f"    ✅ 已配置{num_nodes}个节点", flush=True)

        time.sleep(2)  # 等待TC配置生效

        # 2b. 运行测试
        print(f"  [2/3] 运行PQ-NTOR测试 ({iterations_per_topo}次)...", flush=True)
        test_results = run_pq_ntor_test("192.168.5.185", 5000, "http://192.168.5.189:8000/", iterations_per_topo)

        # 2c. 计算统计
        print(f"  [3/3] 计算统计...", flush=True)
        statistics = calculate_statistics(test_results)

        print(f"    成功率: {statistics['success_rate']:.1f}%", flush=True)
        print(f"    平均时间: {statistics['avg_time_ms']:.2f} ms", flush=True)
        print(f"    时间范围: [{statistics['min_time_ms']:.2f}, {statistics['max_time_ms']:.2f}] ms", flush=True)

        # 保存结果
        all_results.append({
            "topology": topo,
            "tc_config": config["tc_config"],
            "test_results": test_results,
            "statistics": statistics
        })

        # 清除TC配置，为下一个拓扑准备
        print(f"    清除TC配置...", flush=True)
        for cmd_info in tc_cmds:
            clear_tc_on_node(cmd_info["ip"])

        time.sleep(1)

    # 3. 保存所有结果
    print(f"\n[3/4] 保存实验结果...", flush=True)
    save_results_csv(all_results)

    # 保存完整JSON
    with open("sagin_pq_ntor_full_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 完整结果已保存到: sagin_pq_ntor_full_results.json", flush=True)

    # 4. 打印汇总
    print(f"\n[4/4] 实验汇总", flush=True)
    print("="*80, flush=True)
    print(f"{'拓扑':<25} {'成功率':>10} {'平均时间':>12} {'速率':>10} {'延迟':>10}")
    print("-"*80)

    for result in all_results:
        topo = result["topology"]
        tc = result["tc_config"]
        stats = result["statistics"]

        print(f"{topo['name']:<25} {stats['success_rate']:>9.1f}% {stats['avg_time_ms']:>10.2f}ms {tc['rate_mbps']:>8.2f}M {tc['delay_ms']:>8.3f}ms")

    print("="*80)
    print("\n✅ 所有实验完成！")

if __name__ == "__main__":
    import sys

    iterations = 100
    if len(sys.argv) > 1:
        iterations = int(sys.argv[1])

    print(f"每个拓扑将运行{iterations}次测试\n")

    try:
        run_full_experiment(iterations_per_topo=iterations)
    except KeyboardInterrupt:
        print("\n\n⚠️  实验被用户中断")
    except Exception as e:
        print(f"\n\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()
