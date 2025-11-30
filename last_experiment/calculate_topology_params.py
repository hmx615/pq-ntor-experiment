"""
使用师妹的物理模型计算12个拓扑的真实网络参数
"""

import numpy as np
import json
from topology_node_positions import TOPOLOGY_NODES

# 导入师妹的速率计算函数
from test_satellite_noma import oma_rate_single_device, noma_rate_two_devices
from test_uav_noma import uav_oma_rate, uav_noma_rate
from test_d2d_noma import d2d_oma_rate, d2d_noma_rate

# 物理常数
C = 3e8  # 光速

def calculate_propagation_delay(pos1, pos2):
    """计算传播延迟（ms）"""
    distance = np.linalg.norm(pos1 - pos2)
    delay_ms = (distance / C) * 1000
    return delay_ms

def sinr_to_packet_loss(sinr_db):
    """
    根据SINR估算丢包率
    基于经验模型
    """
    if sinr_db > 20:
        return 0.1
    elif sinr_db > 10:
        return 0.5
    elif sinr_db > 5:
        return 1.0
    elif sinr_db > 0:
        return 2.0
    elif sinr_db > -5:
        return 3.0
    else:
        return 5.0

def calculate_link_params(node1, node2, node1_name, node2_name):
    """
    计算单条链路的参数

    返回: (rate_mbps, delay_ms, sinr_db, link_type)
    """
    pos1 = node1
    pos2 = node2

    # 判断链路类型
    is_sat_link = ('sat' in node1_name or 'sat' in node2_name)
    is_uav_link = ('uav' in node1_name or 'uav' in node2_name) and not is_sat_link
    # D2D链路：两个地面节点之间（包含ground的节点，排除uav和sat）
    is_d2d_link = ('ground' in node1_name and 'ground' in node2_name)

    # 计算传播延迟
    delay_ms = calculate_propagation_delay(pos1, pos2)

    # 根据链路类型计算速率
    if is_sat_link:
        # 卫星链路
        if 'sat' in node1_name:
            sat_pos, dev_pos = pos1, pos2
        else:
            sat_pos, dev_pos = pos2, pos1

        is_uav = 'uav' in node2_name or 'uav' in node1_name
        rate_mbps, sinr, _ = oma_rate_single_device(
            sat_pos, dev_pos,
            P_tx_W=20.0,
            B_Hz=20e6,
            is_uav=is_uav
        )
        link_type = "satellite"

    elif is_uav_link:
        # UAV链路
        if 'uav' in node1_name:
            uav_pos, user_pos = pos1, pos2
        else:
            uav_pos, user_pos = pos2, pos1

        rate_mbps, sinr, _ = uav_oma_rate(
            uav_pos, user_pos,
            P_uav_W=3.16,
            B_Hz=2e6
        )
        link_type = "uav"

    elif is_d2d_link:
        # D2D链路
        rate_mbps, sinr, _ = d2d_oma_rate(
            pos1, pos2,
            P_tx_W=0.2,
            B_Hz=2e6
        )
        link_type = "d2d"
    else:
        # 未知链路类型，使用默认值
        rate_mbps = 10.0
        sinr = 100.0
        link_type = "unknown"

    sinr_db = 10 * np.log10(sinr) if sinr > 0 else -10.0

    return rate_mbps, delay_ms, sinr_db, link_type

def calculate_topology_end_to_end(topo_id):
    """
    计算拓扑的端到端参数

    对于多跳链路：
    - 速率 = min(所有跳的速率) - 瓶颈速率
    - 延迟 = sum(所有跳的延迟)
    - 丢包 = 基于最差SINR
    """
    config = TOPOLOGY_NODES[topo_id]
    nodes = config['nodes']
    links = config['links']

    # 计算每条链路的参数
    link_results = []

    for link_tuple in links:
        # 解包：links现在是(src, dst, description)的3元组
        if len(link_tuple) == 3:
            src_name, dst_name, link_desc = link_tuple
        else:
            src_name, dst_name = link_tuple
            link_desc = ""

        src_pos = nodes[src_name]
        dst_pos = nodes[dst_name]

        rate, delay, sinr_db, link_type = calculate_link_params(
            src_pos, dst_pos, src_name, dst_name
        )

        link_results.append({
            'link': f"{src_name}->{dst_name}",
            'description': link_desc,
            'rate_mbps': rate,
            'delay_ms': delay,
            'sinr_db': sinr_db,
            'link_type': link_type
        })

    # 端到端参数
    # 速率：取最小值（瓶颈）
    bottleneck_rate = min([r['rate_mbps'] for r in link_results])

    # 延迟：求和
    total_delay = sum([r['delay_ms'] for r in link_results])

    # SINR：取最小值（最差链路）
    worst_sinr = min([r['sinr_db'] for r in link_results])

    # 丢包率：基于最差SINR
    packet_loss = sinr_to_packet_loss(worst_sinr)

    return {
        'topo_id': topo_id,
        'name': config['name'],
        'description': config['description'],
        'end_to_end': {
            'rate_mbps': round(bottleneck_rate, 2),
            'delay_ms': round(total_delay, 2),
            'sinr_db': round(worst_sinr, 2),
            'packet_loss_percent': round(packet_loss, 2)
        },
        'links': link_results,
        'num_hops': len(links)
    }

def main():
    """计算所有12个拓扑的参数"""

    print("=" * 80)
    print("使用师妹的物理模型计算12拓扑参数")
    print("=" * 80)

    all_results = {}

    for topo_id in sorted(TOPOLOGY_NODES.keys()):
        print(f"\n计算 {topo_id}...")
        result = calculate_topology_end_to_end(topo_id)
        all_results[topo_id] = result

        # 打印结果
        e2e = result['end_to_end']
        print(f"  端到端参数:")
        print(f"    速率: {e2e['rate_mbps']:.2f} Mbps")
        print(f"    延迟: {e2e['delay_ms']:.2f} ms")
        print(f"    SINR: {e2e['sinr_db']:.2f} dB")
        print(f"    丢包: {e2e['packet_loss_percent']:.2f} %")
        print(f"  跳数: {result['num_hops']}")

    # 保存到JSON文件
    output_file = 'topology_params.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 参数已保存到: {output_file}")

    # 生成摘要统计
    print("\n" + "=" * 80)
    print("参数范围统计")
    print("=" * 80)

    rates = [r['end_to_end']['rate_mbps'] for r in all_results.values()]
    delays = [r['end_to_end']['delay_ms'] for r in all_results.values()]
    losses = [r['end_to_end']['packet_loss_percent'] for r in all_results.values()]

    print(f"速率范围: {min(rates):.2f} - {max(rates):.2f} Mbps")
    print(f"延迟范围: {min(delays):.2f} - {max(delays):.2f} ms")
    print(f"丢包范围: {min(losses):.2f} - {max(losses):.2f} %")

    # 生成简化版配置（用于TC应用）
    tc_params = {}
    for topo_id, result in all_results.items():
        e2e = result['end_to_end']
        tc_params[topo_id] = {
            'rate_mbps': e2e['rate_mbps'],
            'delay_ms': e2e['delay_ms'],
            'loss_percent': e2e['packet_loss_percent']
        }

    tc_file = 'topology_tc_params.json'
    with open(tc_file, 'w') as f:
        json.dump(tc_params, f, indent=2)

    print(f"✅ TC配置已保存到: {tc_file}")

    # 绘制参数分布图（可选）
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        topo_ids = list(all_results.keys())
        topo_nums = [int(t.replace('topo', '')) for t in topo_ids]

        # 速率分布
        axes[0].bar(topo_nums, rates)
        axes[0].set_xlabel('Topology ID')
        axes[0].set_ylabel('Rate (Mbps)')
        axes[0].set_title('Communication Rate Distribution')
        axes[0].grid(True, alpha=0.3)

        # 延迟分布
        axes[1].bar(topo_nums, delays)
        axes[1].set_xlabel('Topology ID')
        axes[1].set_ylabel('Delay (ms)')
        axes[1].set_title('Propagation Delay Distribution')
        axes[1].grid(True, alpha=0.3)

        # 丢包分布
        axes[2].bar(topo_nums, losses)
        axes[2].set_xlabel('Topology ID')
        axes[2].set_ylabel('Packet Loss (%)')
        axes[2].set_title('Packet Loss Rate Distribution')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('topology_params_distribution.png', dpi=150)
        print(f"✅ 参数分布图已保存到: topology_params_distribution.png")

    except ImportError:
        print("⚠️ matplotlib未安装，跳过绘图")

if __name__ == "__main__":
    main()
