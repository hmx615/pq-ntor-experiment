#!/usr/bin/env python3
"""检查Pi上的配置文件版本 (是否是修复后的)"""

import paramiko
import json

PI_IP = "192.168.5.186"
USERNAME = "user"
PASSWORD = "user"

def check_config_version():
    """检查配置文件版本"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=USERNAME, password=PASSWORD, timeout=10)

        # 读取topo01配置
        stdin, stdout, stderr = ssh.exec_command(
            "cat /home/user/Desktop/pq-ntor-experiment-main/sagin-experiments/pq-ntor-12topo-experiment/configs/topo01_tor_mapping.json"
        )
        config_content = stdout.read().decode()

        if not config_content:
            print("❌ 配置文件读取失败")
            ssh.close()
            return

        config = json.loads(config_content)

        print("📋 Topo01 当前配置:")
        print("=" * 70)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print("=" * 70)
        print()

        # 检查关键参数
        params = config.get("network_simulation", {}).get("aggregate_params", {})
        delay = params.get("delay_ms")
        bandwidth = params.get("bandwidth_mbps")
        loss = params.get("loss_percent")

        print(f"当前参数: delay={delay}ms, bandwidth={bandwidth}Mbps, loss={loss}%")
        print()

        # 正确的参数 (from topology_params.json)
        correct_delay = 5.42
        correct_bandwidth = 59.27
        correct_loss = 3.0

        if (abs(delay - correct_delay) < 0.01 and
            abs(bandwidth - correct_bandwidth) < 0.01 and
            abs(loss - correct_loss) < 0.01):
            print("✅ 配置参数正确！")
        else:
            print("❌ 配置参数不正确")
            print(f"   应该是: delay={correct_delay}ms, bandwidth={correct_bandwidth}Mbps, loss={correct_loss}%")
            print()
            print("需要部署修复后的配置文件")

        ssh.close()

    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("  检查飞腾派配置文件版本")
    print("=" * 70)
    print()
    check_config_version()
