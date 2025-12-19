#!/usr/bin/env python3
"""
基于WSL2实测Crypto_CBT和最新拓扑参数计算Total_CBT

使用计算模型法（替代TC netem模拟）:
- Crypto_CBT: 从WSL2实验数据获取
- Network_Delay: 6 × link_delay (三跳往返)
- Transmission_Delay: message_size / bandwidth
- Retransmission_Delay: 基于丢包率估算

作者: Claude Code
日期: 2025-12-15
"""

import json
import csv
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

# 最新拓扑参数
TOPOLOGY_PARAMS_FILE = PROJECT_ROOT / "last_experiment" / "topology_params.json"

# WSL2实验数据 (Crypto_CBT)
WSL2_CSV_FILE = Path("/tmp/phase3_sagin_cbt.csv")

# 输出文件
OUTPUT_CSV = SCRIPT_DIR.parent / "results" / "local_wsl" / "phase3_sagin_cbt_with_network_20251215.csv"

# 消息大小 (bytes)
MESSAGE_SIZES = {
    "Classic NTOR": 116,      # ~116 bytes total (CREATE2 + CREATED2)
    "PQ-NTOR": 1620,          # Kyber768 public key + ciphertext
    "Hybrid NTOR": 1684       # X25519 + Kyber768
}

# 拓扑描述
TOPO_DESCRIPTIONS = {
    "topo01": "Z1 Up - 直连NOMA",
    "topo02": "Z2 Up - T协作接入",
    "topo03": "Z3 Up - T用户协作NOMA",
    "topo04": "Z4 Up - 混合直连+协作",
    "topo05": "Z5 Up - 多层树形结构",
    "topo06": "Z6 Up - 双UAV中继+T",
    "topo07": "Z1 Down - 直连NOMA+协作",
    "topo08": "Z2 Down - T协作接入+协作",
    "topo09": "Z3 Down - T用户协作下行",
    "topo10": "Z4 Down - 混合直连+协作",
    "topo11": "Z5 Down - NOMA接收+转发",
    "topo12": "Z6 Down - 双中继NOMA+协作"
}


def load_topology_params():
    """加载最新拓扑参数"""
    with open(TOPOLOGY_PARAMS_FILE, 'r') as f:
        return json.load(f)


def load_wsl2_crypto_cbt():
    """加载WSL2实验的Crypto_CBT数据"""
    crypto_cbt = {}
    with open(WSL2_CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            topo = row['Topology']
            protocol = row['Protocol']
            mean_ms = float(row['Mean_ms'])
            if topo not in crypto_cbt:
                crypto_cbt[topo] = {}
            crypto_cbt[topo][protocol] = mean_ms
    return crypto_cbt


def calculate_network_delay(delay_ms):
    """
    计算网络传播延迟
    三跳电路: Client -> Guard -> Middle -> Exit
    每跳往返 = 2 × single_delay
    总共 3 跳 × 2 = 6 × single_delay
    """
    return 6 * delay_ms


def calculate_transmission_delay(message_size_bytes, bandwidth_mbps):
    """
    计算传输延迟
    Time = Size / Bandwidth
    """
    # 转换: bytes -> bits, Mbps -> bps
    size_bits = message_size_bytes * 8
    bandwidth_bps = bandwidth_mbps * 1e6

    # 三跳电路，每跳需要传输消息
    # 简化模型: 假设往返共传输 3 × message_size
    total_bits = size_bits * 3

    delay_sec = total_bits / bandwidth_bps
    return delay_sec * 1000  # 转换为 ms


def calculate_retransmission_delay(loss_percent, base_delay_ms):
    """
    估算重传延迟
    基于丢包率和基础延迟
    简化模型: retrans_delay = loss_rate × base_delay × retrans_factor
    """
    loss_rate = loss_percent / 100
    # 假设重传因子为 2 (TCP-like)
    retrans_factor = 2.0
    return loss_rate * base_delay_ms * retrans_factor


def main():
    print("=" * 70)
    print("  计算Total_CBT (基于最新拓扑参数)")
    print("=" * 70)
    print()

    # 加载数据
    print("加载拓扑参数...")
    topo_params = load_topology_params()

    print("加载WSL2 Crypto_CBT数据...")
    crypto_cbt = load_wsl2_crypto_cbt()

    # 计算结果
    results = []

    print()
    print("计算Total_CBT:")
    print("-" * 70)

    for i in range(1, 13):
        topo_id = f"topo{i:02d}"
        params = topo_params[topo_id]

        e2e = params["end_to_end"]
        bandwidth = e2e["rate_mbps"]
        delay = e2e["delay_ms"]
        loss = e2e["packet_loss_percent"]

        for protocol in ["Classic NTOR", "PQ-NTOR", "Hybrid NTOR"]:
            # Crypto_CBT from WSL2 experiment
            crypto_ms = crypto_cbt.get(topo_id, {}).get(protocol, 0.5)

            # Network delay
            network_delay = calculate_network_delay(delay)

            # Transmission delay
            msg_size = MESSAGE_SIZES[protocol]
            trans_delay = calculate_transmission_delay(msg_size, bandwidth)

            # Retransmission delay
            retrans_delay = calculate_retransmission_delay(loss, network_delay + trans_delay)

            # Total CBT
            total_cbt = crypto_ms + network_delay + trans_delay + retrans_delay

            # Network ratio
            network_ratio = (network_delay + trans_delay + retrans_delay) / total_cbt * 100

            results.append({
                "Topology": topo_id,
                "Protocol": protocol,
                "Description": TOPO_DESCRIPTIONS.get(topo_id, ""),
                "Bandwidth_Mbps": bandwidth,
                "Link_Delay_ms": delay,
                "Loss_Percent": loss,
                "Crypto_CBT_ms": round(crypto_ms, 3),
                "Network_Delay_ms": round(network_delay, 3),
                "Transmission_Delay_ms": round(trans_delay, 3),
                "Retransmission_Delay_ms": round(retrans_delay, 3),
                "Total_CBT_ms": round(total_cbt, 3),
                "Network_Ratio": round(network_ratio, 2)
            })

            print(f"{topo_id} | {protocol:15} | Crypto={crypto_ms:.3f}ms | "
                  f"Net={network_delay:.2f}ms | Trans={trans_delay:.3f}ms | "
                  f"Total={total_cbt:.2f}ms")

    # 保存CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["Topology", "Protocol", "Description", "Bandwidth_Mbps",
                  "Link_Delay_ms", "Loss_Percent", "Crypto_CBT_ms",
                  "Network_Delay_ms", "Transmission_Delay_ms",
                  "Retransmission_Delay_ms", "Total_CBT_ms", "Network_Ratio"]

    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print("-" * 70)
    print(f"结果已保存至: {OUTPUT_CSV}")
    print()

    # 汇总统计
    print("=" * 70)
    print("  汇总统计")
    print("=" * 70)

    for protocol in ["Classic NTOR", "PQ-NTOR", "Hybrid NTOR"]:
        proto_results = [r for r in results if r["Protocol"] == protocol]
        total_cbts = [r["Total_CBT_ms"] for r in proto_results]
        crypto_cbts = [r["Crypto_CBT_ms"] for r in proto_results]

        print(f"\n{protocol}:")
        print(f"  Crypto_CBT: {min(crypto_cbts):.3f} - {max(crypto_cbts):.3f} ms (avg: {sum(crypto_cbts)/len(crypto_cbts):.3f} ms)")
        print(f"  Total_CBT:  {min(total_cbts):.2f} - {max(total_cbts):.2f} ms (avg: {sum(total_cbts)/len(total_cbts):.2f} ms)")

    # 开销对比
    print("\n" + "=" * 70)
    print("  PQ-NTOR vs Classic NTOR 开销对比")
    print("=" * 70)

    for i in range(1, 13):
        topo_id = f"topo{i:02d}"
        classic = next(r for r in results if r["Topology"] == topo_id and r["Protocol"] == "Classic NTOR")
        pq = next(r for r in results if r["Topology"] == topo_id and r["Protocol"] == "PQ-NTOR")

        overhead_ratio = pq["Total_CBT_ms"] / classic["Total_CBT_ms"]
        overhead_abs = pq["Total_CBT_ms"] - classic["Total_CBT_ms"]

        print(f"{topo_id}: {overhead_ratio:.2f}x (+{overhead_abs:.2f}ms)")


if __name__ == "__main__":
    main()
