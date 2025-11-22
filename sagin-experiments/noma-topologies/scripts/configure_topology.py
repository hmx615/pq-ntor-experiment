#!/usr/bin/env python3
"""
配置NOMA拓扑的网络参数 (Python版本，不依赖jq)
使用Linux tc/netem模拟不同链路的延迟、带宽、丢包率
"""

import json
import sys
import subprocess
import os

def run_command(cmd, check=True):
    """执行shell命令"""
    try:
        result = subprocess.run(cmd, shell=True, check=check,
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def configure_topology(config_file):
    """配置拓扑网络参数"""

    # 1. 读取配置文件
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        return False

    with open(config_file, 'r') as f:
        config = json.load(f)

    topo_id = config['topology_id']
    topo_name = config['name']
    total_delay = config['expected_performance']['total_delay_ms']
    bandwidth = config['expected_performance']['bottleneck_bw_mbps']

    print("=" * 42)
    print(f"Configuring Topology {topo_id}: {topo_name}")
    print("=" * 42)

    # 2. 清除现有tc规则
    print("[1/3] Cleaning existing tc rules...")
    run_command("sudo tc qdisc del dev lo root 2>/dev/null", check=False)
    subprocess.run(['sleep', '0.5'])

    # 3. 应用网络参数
    print("[2/3] Applying network parameters...")

    links = config.get('links', [])

    if len(links) == 0:
        print("Warning: No links defined in config, using default parameters")
        # 使用总体延迟和带宽
        cmd = f"sudo tc qdisc add dev lo root netem delay {total_delay}ms 2ms rate {bandwidth}mbit loss 0.5%"
    else:
        # 使用第一个链路的参数 (简化版)
        link = links[0]
        link_delay = link['delay_ms']
        link_bw = link['bandwidth_mbps']
        link_loss = link['loss_percent']

        print(f"  Delay: {link_delay}ms")
        print(f"  Bandwidth: {link_bw}mbps")
        print(f"  Loss: {link_loss}%")

        cmd = f"sudo tc qdisc add dev lo root netem delay {link_delay}ms 2ms rate {link_bw}mbit loss {link_loss}%"

    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"Error applying tc rules: {stderr}")
        return False

    # 4. 验证配置
    print("[3/3] Verifying configuration...")
    print("")
    success, stdout, stderr = run_command("sudo tc qdisc show dev lo")
    if success:
        print(stdout)

    print("")
    print(f"✅ Topology {topo_id} configured successfully!")
    print(f"   Expected circuit setup time: ~{total_delay}ms")
    print(f"   Expected bandwidth: {bandwidth}Mbps")
    print("")

    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 configure_topology.py <topology_config.json>")
        sys.exit(1)

    config_file = sys.argv[1]

    if configure_topology(config_file):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
