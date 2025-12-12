#!/usr/bin/env python3
"""
SAGIN 12拓扑TC配置生成器
基于真实速率计算结果生成Linux TC配置
"""

import json
import math

# 速率计算结果 (从test_*_noma.py获取)
SAGIN_RATES = {
    # 卫星场景
    "sat_oma_center": {"rate_mbps": 35.06, "sinr_db": 3.75, "distance_m": 815000},
    "sat_oma_edge": {"rate_mbps": 18.70, "sinr_db": -0.40, "distance_m": 820000},
    "sat_noma_weak": {"rate_mbps": 11.72, "sinr_db": -3.00, "distance_m": 820000},
    "sat_noma_strong": {"rate_mbps": 15.50, "sinr_db": -1.48, "distance_m": 815000},

    # 无人机场景
    "uav_oma_near": {"rate_mbps": 29.86, "sinr_db": 44.94, "distance_m": 1000},
    "uav_oma_far": {"rate_mbps": 23.99, "sinr_db": 36.11, "distance_m": 2600},
    "uav_noma_weak": {"rate_mbps": 3.47, "sinr_db": 3.68, "distance_m": 2600},
    "uav_noma_strong": {"rate_mbps": 26.38, "sinr_db": 39.71, "distance_m": 1000},

    # D2D场景
    "d2d_oma_weak": {"rate_mbps": 22.56, "sinr_db": 33.95, "distance_m": 100},
    "d2d_oma_strong": {"rate_mbps": 32.98, "sinr_db": 49.64, "distance_m": 30},
    "d2d_noma_weak": {"rate_mbps": 3.47, "sinr_db": 3.67, "distance_m": 100},
    "d2d_noma_strong": {"rate_mbps": 29.51, "sinr_db": 44.41, "distance_m": 30},
}

def calculate_delay_ms(distance_m):
    """根据距离计算传播延迟 (ms)"""
    speed_of_light = 3e8  # m/s
    return (distance_m / speed_of_light) * 1000

def calculate_loss_from_sinr(sinr_db):
    """根据SINR估算丢包率 (%)"""
    # 简化模型：SINR越低，丢包率越高
    if sinr_db >= 20:
        return 0.01
    elif sinr_db >= 10:
        return 0.1
    elif sinr_db >= 0:
        return 0.5
    elif sinr_db >= -5:
        return 1.0
    else:
        return 2.0

# 12拓扑配置定义
TOPOLOGIES = [
    # 拓扑1-4: 卫星场景
    {
        "id": 1,
        "name": "Z1-SAT-OMA-Center",
        "desc": "卫星→中心用户 (OMA)",
        "link_type": "satellite",
        "access": "OMA",
        "user": "center",
        "params": SAGIN_RATES["sat_oma_center"],
        "nodes": ["client", "guard", "middle"]  # 前三跳
    },
    {
        "id": 2,
        "name": "Z1-SAT-OMA-Edge",
        "desc": "卫星→边缘用户 (OMA)",
        "link_type": "satellite",
        "access": "OMA",
        "user": "edge",
        "params": SAGIN_RATES["sat_oma_edge"],
        "nodes": ["client", "guard", "middle"]
    },
    {
        "id": 3,
        "name": "Z1-SAT-NOMA-Strong",
        "desc": "卫星→强用户 (NOMA)",
        "link_type": "satellite",
        "access": "NOMA",
        "user": "strong",
        "params": SAGIN_RATES["sat_noma_strong"],
        "nodes": ["client", "guard", "middle"]
    },
    {
        "id": 4,
        "name": "Z1-SAT-NOMA-Weak",
        "desc": "卫星→弱用户 (NOMA)",
        "link_type": "satellite",
        "access": "NOMA",
        "user": "weak",
        "params": SAGIN_RATES["sat_noma_weak"],
        "nodes": ["client", "guard", "middle"]
    },

    # 拓扑5-8: 无人机场景
    {
        "id": 5,
        "name": "Z2-UAV-OMA-Near",
        "desc": "无人机→近端用户 (OMA)",
        "link_type": "uav",
        "access": "OMA",
        "user": "near",
        "params": SAGIN_RATES["uav_oma_near"],
        "nodes": ["guard", "middle", "exit"]  # 三跳
    },
    {
        "id": 6,
        "name": "Z2-UAV-OMA-Far",
        "desc": "无人机→远端用户 (OMA)",
        "link_type": "uav",
        "access": "OMA",
        "user": "far",
        "params": SAGIN_RATES["uav_oma_far"],
        "nodes": ["guard", "middle", "exit"]
    },
    {
        "id": 7,
        "name": "Z2-UAV-NOMA-Strong",
        "desc": "无人机→强用户 (NOMA)",
        "link_type": "uav",
        "access": "NOMA",
        "user": "strong",
        "params": SAGIN_RATES["uav_noma_strong"],
        "nodes": ["guard", "middle", "exit"]
    },
    {
        "id": 8,
        "name": "Z2-UAV-NOMA-Weak",
        "desc": "无人机→弱用户 (NOMA)",
        "link_type": "uav",
        "access": "NOMA",
        "user": "weak",
        "params": SAGIN_RATES["uav_noma_weak"],
        "nodes": ["guard", "middle", "exit"]
    },

    # 拓扑9-12: D2D场景
    {
        "id": 9,
        "name": "Z3-D2D-OMA-Strong",
        "desc": "D2D→强用户 (OMA)",
        "link_type": "d2d",
        "access": "OMA",
        "user": "strong",
        "params": SAGIN_RATES["d2d_oma_strong"],
        "nodes": ["middle", "exit", "target"]  # 后三跳
    },
    {
        "id": 10,
        "name": "Z3-D2D-OMA-Weak",
        "desc": "D2D→弱用户 (OMA)",
        "link_type": "d2d",
        "access": "OMA",
        "user": "weak",
        "params": SAGIN_RATES["d2d_oma_weak"],
        "nodes": ["middle", "exit", "target"]
    },
    {
        "id": 11,
        "name": "Z3-D2D-NOMA-Strong",
        "desc": "D2D→强用户 (NOMA)",
        "link_type": "d2d",
        "access": "NOMA",
        "user": "strong",
        "params": SAGIN_RATES["d2d_noma_strong"],
        "nodes": ["middle", "exit", "target"]
    },
    {
        "id": 12,
        "name": "Z3-D2D-NOMA-Weak",
        "desc": "D2D→弱用户 (NOMA)",
        "link_type": "d2d",
        "access": "NOMA",
        "user": "weak",
        "params": SAGIN_RATES["d2d_noma_weak"],
        "nodes": ["middle", "exit", "target"]
    },
]

# 节点IP映射
NODE_IPS = {
    "client": "192.168.5.110",
    "directory": "192.168.5.185",
    "guard": "192.168.5.186",
    "middle": "192.168.5.187",
    "exit": "192.168.5.188",
    "target": "192.168.5.189",
}

def generate_tc_config(topo):
    """为单个拓扑生成TC配置"""
    params = topo["params"]
    rate_mbps = params["rate_mbps"]
    delay_ms = calculate_delay_ms(params["distance_m"])
    loss_pct = calculate_loss_from_sinr(params["sinr_db"])

    # 生成TC命令
    tc_commands = []

    for node_name in topo["nodes"]:
        interface = "eth0"  # 飞腾派默认网卡

        # 清除旧配置
        tc_commands.append({
            "node": node_name,
            "ip": NODE_IPS[node_name],
            "clear": f"sudo tc qdisc del dev {interface} root 2>/dev/null || true"
        })

        # 添加新配置 (使用netem + tbf)
        # netem控制延迟和丢包，tbf控制速率
        tc_commands.append({
            "node": node_name,
            "ip": NODE_IPS[node_name],
            "setup": f"sudo tc qdisc add dev {interface} root handle 1: netem delay {delay_ms:.3f}ms loss {loss_pct:.2f}%"
        })

        tc_commands.append({
            "node": node_name,
            "ip": NODE_IPS[node_name],
            "rate": f"sudo tc qdisc add dev {interface} parent 1: handle 2: tbf rate {rate_mbps}mbit burst 32kbit latency 400ms"
        })

    return {
        "topology": topo,
        "tc_config": {
            "rate_mbps": rate_mbps,
            "delay_ms": delay_ms,
            "loss_pct": loss_pct,
            "sinr_db": params["sinr_db"]
        },
        "tc_commands": tc_commands
    }

def generate_all_configs():
    """生成所有12个拓扑的配置"""
    all_configs = []

    for topo in TOPOLOGIES:
        config = generate_tc_config(topo)
        all_configs.append(config)

    return all_configs

def save_configs(configs, output_file="sagin_12topo_tc_configs.json"):
    """保存配置到JSON文件"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2, ensure_ascii=False)
    print(f"✅ 已生成配置文件: {output_file}")

def print_summary(configs):
    """打印配置摘要"""
    print("="*80)
    print("SAGIN 12拓扑TC配置汇总")
    print("="*80)
    print(f"{'ID':<4} {'拓扑名称':<25} {'速率':>10} {'延迟':>10} {'丢包率':>8} {'SINR':>8}")
    print("-"*80)

    for cfg in configs:
        topo = cfg["topology"]
        tc = cfg["tc_config"]
        print(f"{topo['id']:<4} {topo['name']:<25} {tc['rate_mbps']:>8.2f}M {tc['delay_ms']:>8.3f}ms {tc['loss_pct']:>7.2f}% {tc['sinr_db']:>7.2f}dB")

    print("="*80)

if __name__ == "__main__":
    print("生成SAGIN 12拓扑TC配置...\n")

    # 生成所有配置
    configs = generate_all_configs()

    # 打印摘要
    print_summary(configs)

    # 保存到文件
    save_configs(configs)

    print(f"\n下一步: 使用deploy_sagin_tc.py部署配置到所有节点")
