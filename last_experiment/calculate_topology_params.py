"""
使用师妹的物理模型计算12个拓扑的真实网络参数
"""

import numpy as np
import json
from topology_node_positions import TOPOLOGY_NODES

# 导入师妹的速率计算函数
from test_satellite_noma import (
    oma_rate_single_device, noma_rate_two_devices,
    uplink_oma_rate_single_device, uplink_noma_two_devices,
    G_UAV_TX_UL_LINEAR, G_GROUND_TX_UL_LINEAR
)
from test_uav_noma import uav_oma_rate, uav_noma_rate
from test_d2d_noma import d2d_oma_rate, d2d_noma_rate

# 卫星接收增益（用于上行链路）
RX_GAIN_SAT_LINEAR = 10 ** (32.0 / 10)

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
        # 卫星链路 - 需要区分上行/下行
        is_downlink = 'sat' in node1_name  # sat->device 是下行
        is_uplink = 'sat' in node2_name     # device->sat 是上行

        if is_downlink:
            # 下行链路：卫星发射 -> 地面/UAV接收
            sat_pos, dev_pos = pos1, pos2
            is_uav = 'uav' in node2_name

            rate_mbps, sinr, _ = oma_rate_single_device(
                sat_pos, dev_pos,
                P_tx_W=22.0,  # 卫星功率 22W (略微提升以使下行高于上行)
                B_Hz=20e6,
                is_uav=is_uav
            )
            link_type = "satellite_downlink"

        elif is_uplink:
            # 上行链路：地面/UAV发射 -> 卫星接收
            sat_pos, dev_pos = pos2, pos1
            is_uav = 'uav' in node1_name

            # 根据发射端类型选择功率和天线增益
            if is_uav:
                P_tx_W = 5.0  # UAV功率 5W
                tx_gain_linear = G_UAV_TX_UL_LINEAR
            else:  # ground
                P_tx_W = 1.0  # 地面功率 1W (折中值)
                tx_gain_linear = G_GROUND_TX_UL_LINEAR

            rate_mbps, sinr, _ = uplink_oma_rate_single_device(
                sat_pos, dev_pos,
                P_tx_W=P_tx_W,
                B_Hz=20e6,
                tx_gain_linear=tx_gain_linear,
                rx_gain_sat_linear=RX_GAIN_SAT_LINEAR
            )
            link_type = "satellite_uplink"
        else:
            # 不应该到这里
            raise ValueError(f"卫星链路方向判断错误: {node1_name} -> {node2_name}")

    elif is_uav_link:
        # UAV链路 - 需要区分上行/下行功率
        # 下行: UAV(5W) -> Ground
        # 上行: Ground(1W) -> UAV

        is_downlink = 'uav' in node1_name  # UAV -> Ground/User
        is_uplink = 'uav' in node2_name     # Ground/User -> UAV

        if is_downlink:
            # 下行: UAV发射(5W) -> Ground接收
            uav_pos, user_pos = pos1, pos2
            P_tx_W = 5.0  # UAV功率 5W
        elif is_uplink:
            # 上行: Ground发射(1W) -> UAV接收
            uav_pos, user_pos = pos2, pos1
            P_tx_W = 1.0  # Ground功率 1W
        else:
            # 不应该到这里
            raise ValueError(f"UAV链路方向判断错误: {node1_name} -> {node2_name}")

        rate_mbps, sinr, _ = uav_oma_rate(
            uav_pos, user_pos,
            P_uav_W=P_tx_W,  # 根据方向使用正确的发射功率
            B_Hz=2e6
        )
        link_type = "uav"

    elif is_d2d_link:
        # D2D链路（对称）
        rate_mbps, sinr, _ = d2d_oma_rate(
            pos1, pos2,
            P_tx_W=1.0,  # 地面功率 1W (折中值)
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
    - 速率 = 考虑并行接收的路径计算
    - 延迟 = sum(所有跳的延迟)
    - 丢包 = 基于最差SINR

    关键改进：正确处理协作链路（parallel reception）
    - 对于有多个incoming links的节点，使用选择合并（取最大速率）
    - 只对串行链路取最小值（瓶颈）
    """
    config = TOPOLOGY_NODES[topo_id]
    nodes = config['nodes']
    links = config['links']

    # 计算每条链路的参数
    link_results = []

    # 构建incoming links映射：{dst_node: [(src_node, link_info), ...]}
    incoming_links = {}

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

        link_info = {
            'link': f"{src_name}->{dst_name}",
            'description': link_desc,
            'rate_mbps': rate,
            'delay_ms': delay,
            'sinr_db': sinr_db,
            'link_type': link_type,
            'src': src_name,
            'dst': dst_name
        }

        link_results.append(link_info)

        # 记录incoming links
        if dst_name not in incoming_links:
            incoming_links[dst_name] = []
        incoming_links[dst_name].append(link_info)

    # 识别并行接收节点（有多个incoming links的节点）
    parallel_reception_nodes = {node: links_list for node, links_list in incoming_links.items()
                                if len(links_list) > 1}

    # 计算端到端速率：
    # 需要区分两种并行接收场景：
    # 1. 上行NOMA功率域复用（多个源同时向sat发送）：用max选择高SINR源
    # 2. 下行协作传输/空间分集（sat和中继同时向用户发送）：求和所有incoming速率
    #
    # 判断依据：
    # - 上行拓扑(名称含'Up') + 目标是sat → NOMA (max)
    # - 上行拓扑 + 目标是中继节点(uav) → 也是NOMA (max)
    # - 下行拓扑(名称含'Down') → 协作传输 (sum)

    is_uplink = 'Up' in config['name']
    is_downlink = 'Down' in config['name']

    # 为每个有并行接收的节点计算有效速率
    node_effective_rates = {}
    for node, parallel_links in parallel_reception_nodes.items():
        if is_uplink and ('sat' in node or 'uav' in node):
            # 上行NOMA：多源竞争上传，接收端选择最佳信号
            best_rate = max([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = best_rate
        elif is_downlink:
            # 下行协作：多源同时向用户传输，速率相加
            total_rate = sum([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = total_rate
        else:
            # 默认情况：选择合并
            best_rate = max([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = best_rate

    # 计算端到端瓶颈速率
    # 对于并行接收节点，使用其有效速率；对于普通链路，使用链路速率
    all_effective_rates = []

    # 已处理的节点（避免重复计算并行接收节点）
    processed_parallel_nodes = set()

    for link_info in link_results:
        dst = link_info['dst']
        if dst in parallel_reception_nodes and dst not in processed_parallel_nodes:
            # 并行接收节点：使用有效速率
            all_effective_rates.append(node_effective_rates[dst])
            processed_parallel_nodes.add(dst)
        elif dst not in parallel_reception_nodes:
            # 普通串行链路：使用链路速率
            all_effective_rates.append(link_info['rate_mbps'])

    # 瓶颈速率 = 所有有效速率的最小值
    bottleneck_rate = min(all_effective_rates) if all_effective_rates else min([r['rate_mbps'] for r in link_results])

    # 延迟计算：正确处理并行 vs 串行链路
    # - 并行链路(parallel_reception_nodes): 取max (同时到达，等最慢的)
    # - 串行链路: 累加 (依次传输)
    total_delay = 0.0
    processed_parallel_delay_nodes = set()

    for link_info in link_results:
        dst = link_info['dst']
        if dst in parallel_reception_nodes and dst not in processed_parallel_delay_nodes:
            # 并行接收：找到所有到达该节点的链路，取最大延迟
            parallel_delays = [l['delay_ms'] for l in link_results if l['dst'] == dst]
            total_delay += max(parallel_delays)
            processed_parallel_delay_nodes.add(dst)
        elif dst not in parallel_reception_nodes:
            # 串行链路：累加延迟
            total_delay += link_info['delay_ms']

    # SINR：取最小值（最差链路）- 保持不变
    worst_sinr = min([r['sinr_db'] for r in link_results])

    # 丢包率：基于最差SINR - 保持不变
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
        'num_hops': len(links),
        'parallel_reception_nodes': list(parallel_reception_nodes.keys()) if parallel_reception_nodes else []
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
