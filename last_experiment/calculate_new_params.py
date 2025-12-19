"""
使用新参数计算12个拓扑的网络参数
- 卫星带宽: 100 MHz (原20 MHz)
- UAV/D2D带宽: 10 MHz (原2 MHz)
- 功率调回正常水平
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

# ============================================================================
# 新参数设置
# ============================================================================
# 带宽设置（调大）
SAT_BANDWIDTH_HZ = 100e6   # 卫星: 100 MHz (原20 MHz)
UAV_BANDWIDTH_HZ = 10e6    # UAV: 10 MHz (原2 MHz)
D2D_BANDWIDTH_HZ = 10e6    # D2D: 10 MHz (原2 MHz)

# 功率设置（保持原值不变）
SAT_TX_POWER_W = 22.0      # 卫星下行: 22W (保持不变)
UAV_TX_UL_POWER_W = 5.0    # UAV上行到卫星: 5W (保持不变)
GROUND_TX_UL_POWER_W = 1.0 # 地面上行到卫星: 1W (保持不变)
UAV_TX_DL_POWER_W = 5.0    # UAV下行: 5W (保持不变)
GROUND_TX_UAV_POWER_W = 1.0 # 地面上行到UAV: 1W (保持不变)
D2D_TX_POWER_W = 1.0       # D2D: 1W (保持不变)

print("=" * 80)
print("新参数设置:")
print("=" * 80)
print(f"卫星带宽: {SAT_BANDWIDTH_HZ/1e6:.0f} MHz (原20 MHz, 调大5倍)")
print(f"UAV带宽: {UAV_BANDWIDTH_HZ/1e6:.0f} MHz (原2 MHz, 调大5倍)")
print(f"D2D带宽: {D2D_BANDWIDTH_HZ/1e6:.0f} MHz (原2 MHz, 调大5倍)")
print()
print(f"卫星下行功率: {SAT_TX_POWER_W} W (原22W)")
print(f"UAV上行功率: {UAV_TX_UL_POWER_W} W (原5W)")
print(f"地面上行功率: {GROUND_TX_UL_POWER_W} W (原1W)")
print(f"UAV下行功率: {UAV_TX_DL_POWER_W} W (原5W)")
print(f"D2D功率: {D2D_TX_POWER_W} W (原1W)")
print("=" * 80)

def calculate_propagation_delay(pos1, pos2):
    """计算传播延迟（ms）"""
    distance = np.linalg.norm(pos1 - pos2)
    delay_ms = (distance / C) * 1000
    return delay_ms

def sinr_to_packet_loss(sinr_db):
    """根据SINR估算丢包率"""
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
    """计算单条链路的参数 - 使用新参数"""
    pos1 = node1
    pos2 = node2

    is_sat_link = ('sat' in node1_name or 'sat' in node2_name)
    is_uav_link = ('uav' in node1_name or 'uav' in node2_name) and not is_sat_link
    is_d2d_link = ('ground' in node1_name and 'ground' in node2_name)

    delay_ms = calculate_propagation_delay(pos1, pos2)

    if is_sat_link:
        is_downlink = 'sat' in node1_name
        is_uplink = 'sat' in node2_name

        if is_downlink:
            sat_pos, dev_pos = pos1, pos2
            is_uav = 'uav' in node2_name
            rate_mbps, sinr, _ = oma_rate_single_device(
                sat_pos, dev_pos,
                P_tx_W=SAT_TX_POWER_W,  # 新功率
                B_Hz=SAT_BANDWIDTH_HZ,   # 新带宽
                is_uav=is_uav
            )
            link_type = "satellite_downlink"

        elif is_uplink:
            sat_pos, dev_pos = pos2, pos1
            is_uav = 'uav' in node1_name

            if is_uav:
                P_tx_W = UAV_TX_UL_POWER_W
                tx_gain_linear = G_UAV_TX_UL_LINEAR
            else:
                P_tx_W = GROUND_TX_UL_POWER_W
                tx_gain_linear = G_GROUND_TX_UL_LINEAR

            rate_mbps, sinr, _ = uplink_oma_rate_single_device(
                sat_pos, dev_pos,
                P_tx_W=P_tx_W,
                B_Hz=SAT_BANDWIDTH_HZ,  # 新带宽
                tx_gain_linear=tx_gain_linear,
                rx_gain_sat_linear=RX_GAIN_SAT_LINEAR
            )
            link_type = "satellite_uplink"
        else:
            raise ValueError(f"卫星链路方向判断错误: {node1_name} -> {node2_name}")

    elif is_uav_link:
        is_downlink = 'uav' in node1_name
        is_uplink = 'uav' in node2_name

        if is_downlink:
            uav_pos, user_pos = pos1, pos2
            P_tx_W = UAV_TX_DL_POWER_W
        elif is_uplink:
            uav_pos, user_pos = pos2, pos1
            P_tx_W = GROUND_TX_UAV_POWER_W
        else:
            raise ValueError(f"UAV链路方向判断错误: {node1_name} -> {node2_name}")

        rate_mbps, sinr, _ = uav_oma_rate(
            uav_pos, user_pos,
            P_uav_W=P_tx_W,
            B_Hz=UAV_BANDWIDTH_HZ  # 新带宽
        )
        link_type = "uav"

    elif is_d2d_link:
        rate_mbps, sinr, _ = d2d_oma_rate(
            pos1, pos2,
            P_tx_W=D2D_TX_POWER_W,
            B_Hz=D2D_BANDWIDTH_HZ  # 新带宽
        )
        link_type = "d2d"
    else:
        rate_mbps = 10.0
        sinr = 100.0
        link_type = "unknown"

    sinr_db = 10 * np.log10(sinr) if sinr > 0 else -10.0

    return rate_mbps, delay_ms, sinr_db, link_type

def calculate_topology_end_to_end(topo_id):
    """计算拓扑的端到端参数"""
    config = TOPOLOGY_NODES[topo_id]
    nodes = config['nodes']
    links = config['links']

    link_results = []
    incoming_links = {}

    for link_tuple in links:
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

        if dst_name not in incoming_links:
            incoming_links[dst_name] = []
        incoming_links[dst_name].append(link_info)

    parallel_reception_nodes = {node: links_list for node, links_list in incoming_links.items()
                                if len(links_list) > 1}

    is_uplink = 'Up' in config['name']
    is_downlink = 'Down' in config['name']

    node_effective_rates = {}
    for node, parallel_links in parallel_reception_nodes.items():
        if is_uplink and ('sat' in node or 'uav' in node):
            best_rate = max([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = best_rate
        elif is_downlink:
            total_rate = sum([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = total_rate
        else:
            best_rate = max([link['rate_mbps'] for link in parallel_links])
            node_effective_rates[node] = best_rate

    all_effective_rates = []
    processed_parallel_nodes = set()

    for link_info in link_results:
        dst = link_info['dst']
        if dst in parallel_reception_nodes and dst not in processed_parallel_nodes:
            all_effective_rates.append(node_effective_rates[dst])
            processed_parallel_nodes.add(dst)
        elif dst not in parallel_reception_nodes:
            all_effective_rates.append(link_info['rate_mbps'])

    bottleneck_rate = min(all_effective_rates) if all_effective_rates else min([r['rate_mbps'] for r in link_results])

    # 延迟计算
    satellite_delays = [l['delay_ms'] for l in link_results
                        if l['link_type'] in ('satellite_uplink', 'satellite_downlink')]

    total_delay = 0.0
    if satellite_delays:
        total_delay += max(satellite_delays)

    processed_rx_nodes = set()
    for link_info in link_results:
        if link_info['link_type'] in ('satellite_uplink', 'satellite_downlink'):
            continue

        dst = link_info['dst']
        is_cooperation_link = (dst in parallel_reception_nodes and
                               any(l['dst'] == dst and l['link_type'] in ('satellite_uplink', 'satellite_downlink')
                                   for l in link_results))

        if is_cooperation_link:
            if dst not in processed_rx_nodes:
                processed_rx_nodes.add(dst)
        elif dst in parallel_reception_nodes:
            if dst not in processed_rx_nodes:
                parallel_delays = [l['delay_ms'] for l in link_results if l['dst'] == dst]
                total_delay += max(parallel_delays)
                processed_rx_nodes.add(dst)
        else:
            total_delay += link_info['delay_ms']

    worst_sinr = min([r['sinr_db'] for r in link_results])
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

    print("\n" + "=" * 80)
    print("计算12拓扑新参数")
    print("=" * 80)

    all_results = {}

    # 打印表头
    print(f"\n{'Topo':<8} {'名称':<30} {'速率(Mbps)':<12} {'延迟(ms)':<10} {'丢包(%)':<10}")
    print("-" * 80)

    for topo_id in sorted(TOPOLOGY_NODES.keys()):
        result = calculate_topology_end_to_end(topo_id)
        all_results[topo_id] = result

        e2e = result['end_to_end']
        print(f"{topo_id:<8} {result['name']:<30} {e2e['rate_mbps']:<12.2f} {e2e['delay_ms']:<10.2f} {e2e['packet_loss_percent']:<10.2f}")

    # 统计
    print("\n" + "=" * 80)
    print("新参数统计")
    print("=" * 80)

    rates = [r['end_to_end']['rate_mbps'] for r in all_results.values()]
    delays = [r['end_to_end']['delay_ms'] for r in all_results.values()]
    losses = [r['end_to_end']['packet_loss_percent'] for r in all_results.values()]

    print(f"速率范围: {min(rates):.2f} - {max(rates):.2f} Mbps (平均: {np.mean(rates):.2f})")
    print(f"延迟范围: {min(delays):.2f} - {max(delays):.2f} ms (平均: {np.mean(delays):.2f})")
    print(f"丢包范围: {min(losses):.2f} - {max(losses):.2f} % (平均: {np.mean(losses):.2f})")

    # 与原参数对比
    print("\n" + "=" * 80)
    print("与原参数对比")
    print("=" * 80)

    # 原参数（从之前的结果）
    old_rates = [59.27, 16.55, 25.19, 23.64, 25.19, 22.91, 69.43, 44.84, 29.84, 28.29, 9.67, 8.73]

    print(f"原速率范围: {min(old_rates):.2f} - {max(old_rates):.2f} Mbps")
    print(f"新速率范围: {min(rates):.2f} - {max(rates):.2f} Mbps")
    print(f"速率变化: {np.mean(rates)/np.mean(old_rates):.2f}x")

    return all_results

if __name__ == "__main__":
    main()
