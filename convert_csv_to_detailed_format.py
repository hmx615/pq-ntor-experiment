#!/usr/bin/env python3
"""
将简单的phase3_sagin_cbt.csv转换为带有网络参数详细信息的格式
用于兼容12月8日的原始可视化程序
"""

import pandas as pd
import json

# 拓扑参数 (2025-12-11修正版 - 统一使用卫星传播延迟2.71ms)
# 所有拓扑的传播延迟相同(卫星高度固定), 差异主要体现在带宽(传输延迟)上
TOPO_PARAMS = {
    'topo01': {'bw': 59.27, 'delay': 2.71, 'loss': 3.0, 'desc': 'Z1 Up - 直连NOMA'},
    'topo02': {'bw': 16.55, 'delay': 2.71, 'loss': 3.0, 'desc': 'Z1 Up - T协作接入'},
    'topo03': {'bw': 25.19, 'delay': 2.71, 'loss': 1.0, 'desc': 'Z1 Up - 双跳直连'},
    'topo04': {'bw': 23.64, 'delay': 2.71, 'loss': 3.0, 'desc': 'Z1 Up - T协作双跳'},
    'topo05': {'bw': 25.19, 'delay': 2.71, 'loss': 3.0, 'desc': 'Z1 Up - 并行NOMA'},
    'topo06': {'bw': 22.91, 'delay': 2.71, 'loss': 1.0, 'desc': 'Z1 Up - 并行协作'},
    'topo07': {'bw': 69.43, 'delay': 2.71, 'loss': 2.0, 'desc': 'Z1 Down - 直连NOMA'},
    'topo08': {'bw': 38.01, 'delay': 2.71, 'loss': 2.0, 'desc': 'Z1 Down - T协作接入'},
    'topo09': {'bw': 29.84, 'delay': 2.71, 'loss': 0.5, 'desc': 'Z1 Down - 双跳直连'},
    'topo10': {'bw': 18.64, 'delay': 2.71, 'loss': 2.0, 'desc': 'Z1 Down - T协作双跳'},
    'topo11': {'bw': 9.67,  'delay': 2.71, 'loss': 2.0, 'desc': 'Z1 Down - 并行NOMA'},
    'topo12': {'bw': 8.73,  'delay': 2.71, 'loss': 2.0, 'desc': 'Z1 Down - 并行协作'}
}

# Phase 2基准数据 (从实际测量获得)
CLASSIC_NTOR_HANDSHAKE_MS = 0.08682  # 86.82 μs
PQ_NTOR_HANDSHAKE_MS = 0.03705        # 37.05 μs

# 典型消息大小 (bytes)
CLASSIC_NTOR_MSG_SIZE = 84    # CREATE2 cell
PQ_NTOR_MSG_SIZE = 1472       # PQ-NTOR enlarged cell

def calculate_transmission_delay(bw_mbps, msg_size_bytes):
    """
    计算传输延迟 (ms)
    公式: delay = (message_size_bits) / (bandwidth_bps) * 1000
    """
    bw_bps = bw_mbps * 1_000_000  # Mbps -> bps
    msg_size_bits = msg_size_bytes * 8
    delay_sec = msg_size_bits / bw_bps
    return delay_sec * 1000  # 转换为ms

def calculate_retransmission_delay(delay_ms, loss_percent):
    """
    估算重传延迟 (简化模型)
    假设: RTT = 2 * delay, 重传概率 = loss_percent
    """
    rtt_ms = 2 * delay_ms
    retrans_delay = rtt_ms * (loss_percent / 100)
    return retrans_delay

def convert_csv_to_detailed(input_csv, output_csv):
    """
    转换CSV格式，添加详细的网络参数和CBT分解
    注意：由于原始测量没有网络延迟，我们需要重新计算Total_CBT
    """
    # 读取简单CSV
    df = pd.read_csv(input_csv)

    # 准备输出数据
    detailed_rows = []

    for _, row in df.iterrows():
        topo = row['Topology']
        protocol = row['Protocol']
        # 注意：忽略原始的Mean_ms，因为它没有包含网络延迟

        # 获取拓扑参数
        params = TOPO_PARAMS[topo]
        bw = params['bw']
        delay = params['delay']
        loss = params['loss']
        desc = params['desc']

        # 确定加密握手时间和消息大小
        if 'Classic' in protocol:
            crypto_cbt_ms = CLASSIC_NTOR_HANDSHAKE_MS
            msg_size = CLASSIC_NTOR_MSG_SIZE
        else:  # PQ-NTOR
            crypto_cbt_ms = PQ_NTOR_HANDSHAKE_MS
            msg_size = PQ_NTOR_MSG_SIZE

        # 计算各个延迟组成部分
        # 3-hop circuit: 每一跳都有 2*delay (RTT)
        network_delay_ms = 3 * 2 * delay  # 三跳，每跳一个RTT

        transmission_delay_ms = 3 * calculate_transmission_delay(bw, msg_size)

        retrans_delay_ms = 3 * calculate_retransmission_delay(delay, loss)

        # 重新计算Total_CBT（包含所有组成部分）
        total_cbt_ms = crypto_cbt_ms + network_delay_ms + transmission_delay_ms + retrans_delay_ms

        # 计算网络延迟占比
        network_ratio = (network_delay_ms / total_cbt_ms) * 100 if total_cbt_ms > 0 else 0

        # 构建详细记录
        detailed_row = {
            'Topology': topo,
            'Protocol': protocol,
            'Description': desc,
            'Bandwidth_Mbps': round(bw, 3),
            'Link_Delay_ms': round(delay, 3),
            'Loss_Percent': round(loss, 3),
            'Crypto_CBT_ms': round(crypto_cbt_ms, 3),
            'Network_Delay_ms': round(network_delay_ms, 3),
            'Transmission_Delay_ms': round(transmission_delay_ms, 3),
            'Retransmission_Delay_ms': round(retrans_delay_ms, 3),
            'Total_CBT_ms': round(total_cbt_ms, 3),
            'Network_Ratio': round(network_ratio, 3)
        }

        detailed_rows.append(detailed_row)

    # 创建详细DataFrame
    detailed_df = pd.DataFrame(detailed_rows)

    # 保存到CSV
    detailed_df.to_csv(output_csv, index=False)

    print(f"✅ 转换完成!")
    print(f"   输入: {input_csv}")
    print(f"   输出: {output_csv}")
    print(f"   记录数: {len(detailed_df)}")
    print(f"\n生成的列:")
    for col in detailed_df.columns:
        print(f"   - {col}")

if __name__ == '__main__':
    import sys

    input_csv = sys.argv[1] if len(sys.argv) > 1 else \
                '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase3_sagin_cbt.csv'
    output_csv = sys.argv[2] if len(sys.argv) > 2 else \
                 '/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c/phase3_sagin_cbt_with_network.csv'

    convert_csv_to_detailed(input_csv, output_csv)

    # 显示前几行作为预览
    df = pd.read_csv(output_csv)
    print(f"\n预览前3行:")
    print(df.head(3).to_string())
