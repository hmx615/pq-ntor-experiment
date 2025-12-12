#!/usr/bin/env python3
"""
Phase 3 分析：密码学性能 + 网络延迟理论计算

方法论：
- 密码学CBT：实测值（纯计算时间）
- 网络延迟：理论值（3跳电路 = 6次单向传输）
- 总CBT = 密码学CBT + 网络往返延迟
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# SAGIN拓扑网络参数（真实NOMA数据）
TOPOLOGY_PARAMS = {
    'topo01': {'bw_mbps': 31.81, 'delay_ms': 2.72, 'loss_pct': 0.1, 'desc': 'LEO-GW (高带宽/低延迟)'},
    'topo02': {'bw_mbps': 31.81, 'delay_ms': 5.46, 'loss_pct': 0.1, 'desc': 'LEO-GW (高带宽/高延迟)'},
    'topo03': {'bw_mbps': 31.81, 'delay_ms': 5.46, 'loss_pct': 2.0, 'desc': 'LEO-GW (高带宽/高延迟/高丢包)'},
    'topo04': {'bw_mbps': 25.86, 'delay_ms': 2.72, 'loss_pct': 0.1, 'desc': 'UAV-LEO (中带宽/低延迟)'},
    'topo05': {'bw_mbps': 25.86, 'delay_ms': 5.46, 'loss_pct': 0.1, 'desc': 'UAV-LEO (中带宽/高延迟)'},
    'topo06': {'bw_mbps': 25.86, 'delay_ms': 5.46, 'loss_pct': 2.0, 'desc': 'UAV-LEO (中带宽/高延迟/高丢包)'},
    'topo07': {'bw_mbps': 6.02,  'delay_ms': 5.46, 'loss_pct': 2.0, 'desc': '恶劣条件'},
    'topo08': {'bw_mbps': 14.26, 'delay_ms': 2.72, 'loss_pct': 0.1, 'desc': '中等条件'},
    'topo09': {'bw_mbps': 14.26, 'delay_ms': 2.72, 'loss_pct': 2.0, 'desc': '中等延迟高丢包'},
    'topo10': {'bw_mbps': 3.60,  'delay_ms': 2.72, 'loss_pct': 0.1, 'desc': '低带宽'},
    'topo11': {'bw_mbps': 3.60,  'delay_ms': 2.72, 'loss_pct': 2.0, 'desc': '低带宽高丢包'},
    'topo12': {'bw_mbps': 3.60,  'delay_ms': 5.46, 'loss_pct': 2.0, 'desc': '最恶劣条件'},
}

def calculate_network_delay(delay_ms):
    """
    计算3跳电路的网络往返延迟

    3跳Tor电路: Client -> Guard -> Middle -> Exit

    握手过程（以第一跳为例）:
    1. Client -> Guard: CREATE cell (单向延迟)
    2. Guard -> Client: CREATED cell (单向延迟)

    总共3跳，每跳2次传输 = 6次单向延迟
    """
    return 6 * delay_ms

def calculate_transmission_delay(packet_size_bytes, bandwidth_mbps):
    """
    计算传输延迟（仅用于参考，实际影响较小）

    传输时间 = 数据大小 / 带宽
    """
    bandwidth_bytes_per_sec = bandwidth_mbps * 1024 * 1024 / 8
    transmission_ms = (packet_size_bytes / bandwidth_bytes_per_sec) * 1000
    return transmission_ms

def analyze_phase3(csv_path):
    """分析Phase 3结果并计算理论总CBT"""

    print("="*80)
    print("Phase 3 分析：SAGIN网络集成测试（密码学 + 网络延迟）")
    print("="*80)
    print()

    # 读取纯密码学测量结果
    df = pd.read_csv(csv_path)

    print("📊 数据概览:")
    print(f"  拓扑数量: {len(df['Topology'].unique())}")
    print(f"  协议类型: {', '.join(df['Protocol'].unique())}")
    print(f"  总测试数: {len(df)}")
    print()

    # 创建结果数据框
    results = []

    for _, row in df.iterrows():
        topo = row['Topology']
        protocol = row['Protocol']
        crypto_cbt = row['Mean_ms']

        # 获取网络参数
        params = TOPOLOGY_PARAMS[topo]
        delay_ms = params['delay_ms']
        bw_mbps = params['bw_mbps']
        loss_pct = params['loss_pct']

        # 计算网络延迟（传播延迟）
        network_delay = calculate_network_delay(delay_ms)

        # 估算数据包大小
        # Classic NTOR: ~128 bytes per onionskin
        # PQ-NTOR: ~1568 bytes per onionskin (Kyber-512 ciphertext ~800 bytes)
        if 'Classic' in protocol:
            packet_size = 128 * 6  # 3跳 × 2次传输
        else:
            packet_size = 1568 * 6

        # 传输延迟（通常可忽略）
        transmission_delay = calculate_transmission_delay(packet_size, bw_mbps)

        # 丢包导致的重传延迟（简化估算）
        # 假设每个数据包有loss_pct%的概率需要重传
        # 重传次数期望值 = loss_pct / 100
        retransmission_delay = (loss_pct / 100) * network_delay

        # 总CBT = 密码学时间 + 网络传播延迟 + 传输延迟 + 重传延迟
        total_cbt = crypto_cbt + network_delay + transmission_delay + retransmission_delay

        results.append({
            'Topology': topo,
            'Protocol': protocol,
            'Description': params['desc'],
            'Bandwidth_Mbps': bw_mbps,
            'Link_Delay_ms': delay_ms,
            'Loss_Percent': loss_pct,
            'Crypto_CBT_ms': crypto_cbt,
            'Network_Delay_ms': network_delay,
            'Transmission_Delay_ms': transmission_delay,
            'Retransmission_Delay_ms': retransmission_delay,
            'Total_CBT_ms': total_cbt,
            'Network_Ratio': (network_delay / total_cbt) * 100  # 网络延迟占比
        })

    results_df = pd.DataFrame(results)

    # 保存详细结果
    output_csv = csv_path.replace('.csv', '_with_network.csv')
    results_df.to_csv(output_csv, index=False, float_format='%.3f')
    print(f"✅ 详细结果已保存: {output_csv}")
    print()

    # 打印汇总表格
    print("="*80)
    print("📊 Phase 3 完整结果（含网络延迟）")
    print("="*80)
    print()

    # 按拓扑分组显示
    for topo in sorted(results_df['Topology'].unique()):
        topo_data = results_df[results_df['Topology'] == topo]
        params = TOPOLOGY_PARAMS[topo]

        print(f"\n{topo}: {params['desc']}")
        print(f"  网络参数: 带宽={params['bw_mbps']:.2f} Mbps, "
              f"延迟={params['delay_ms']:.2f} ms, 丢包={params['loss_pct']:.1f}%")
        print(f"  {'协议':<15} {'密码学CBT':<12} {'网络延迟':<12} {'总CBT':<12} {'网络占比':<10}")
        print(f"  {'-'*70}")

        for _, row in topo_data.iterrows():
            print(f"  {row['Protocol']:<15} "
                  f"{row['Crypto_CBT_ms']:>10.2f} ms "
                  f"{row['Network_Delay_ms']:>10.2f} ms "
                  f"{row['Total_CBT_ms']:>10.2f} ms "
                  f"{row['Network_Ratio']:>8.1f}%")

    print()
    print("="*80)
    print("📈 关键统计")
    print("="*80)
    print()

    # Classic vs PQ对比
    classic_data = results_df[results_df['Protocol'].str.contains('Classic')]
    pq_data = results_df[results_df['Protocol'].str.contains('PQ')]

    print("密码学性能（纯计算，无网络）:")
    print(f"  Classic NTOR平均: {classic_data['Crypto_CBT_ms'].mean():.3f} ms")
    print(f"  PQ-NTOR平均:      {pq_data['Crypto_CBT_ms'].mean():.3f} ms")
    print(f"  PQ密码学开销:     {pq_data['Crypto_CBT_ms'].mean() / classic_data['Crypto_CBT_ms'].mean():.2f}× "
          f"({pq_data['Crypto_CBT_ms'].mean() - classic_data['Crypto_CBT_ms'].mean():+.3f} ms)")
    print()

    print("端到端性能（含SAGIN网络延迟）:")
    print(f"  Classic NTOR平均: {classic_data['Total_CBT_ms'].mean():.3f} ms")
    print(f"  PQ-NTOR平均:      {pq_data['Total_CBT_ms'].mean():.3f} ms")
    print(f"  PQ总开销:         {pq_data['Total_CBT_ms'].mean() / classic_data['Total_CBT_ms'].mean():.2f}× "
          f"({pq_data['Total_CBT_ms'].mean() - classic_data['Total_CBT_ms'].mean():+.3f} ms)")
    print()

    print("网络延迟影响:")
    print(f"  网络延迟占总CBT比例: {results_df['Network_Ratio'].mean():.1f}% (平均)")
    print(f"  最低网络延迟拓扑: {results_df.loc[results_df['Link_Delay_ms'].idxmin(), 'Topology']} "
          f"({results_df['Link_Delay_ms'].min():.2f} ms)")
    print(f"  最高网络延迟拓扑: {results_df.loc[results_df['Link_Delay_ms'].idxmax(), 'Topology']} "
          f"({results_df['Link_Delay_ms'].max():.2f} ms)")
    print()

    # PQ开销在不同网络条件下的变化
    print("PQ相对开销在不同网络条件下:")
    for topo in sorted(results_df['Topology'].unique()):
        topo_data = results_df[results_df['Topology'] == topo]
        classic_cbt = topo_data[topo_data['Protocol'].str.contains('Classic')]['Total_CBT_ms'].values[0]
        pq_cbt = topo_data[topo_data['Protocol'].str.contains('PQ')]['Total_CBT_ms'].values[0]
        overhead = pq_cbt / classic_cbt
        abs_diff = pq_cbt - classic_cbt

        params = TOPOLOGY_PARAMS[topo]
        print(f"  {topo}: {overhead:.3f}× ({abs_diff:+.2f} ms) - {params['desc']}")

    print()
    print("="*80)
    print("💡 关键发现")
    print("="*80)

    # 计算关键洞察
    crypto_overhead_avg = pq_data['Crypto_CBT_ms'].mean() / classic_data['Crypto_CBT_ms'].mean()
    total_overhead_avg = pq_data['Total_CBT_ms'].mean() / classic_data['Total_CBT_ms'].mean()
    network_dominance = results_df['Network_Ratio'].mean()

    print()
    print(f"1. 密码学开销: PQ-NTOR的纯计算开销为 {crypto_overhead_avg:.2f}×")
    print(f"   - Classic NTOR: {classic_data['Crypto_CBT_ms'].mean():.3f} ms")
    print(f"   - PQ-NTOR: {pq_data['Crypto_CBT_ms'].mean():.3f} ms")
    print()

    print(f"2. 网络延迟主导: 在SAGIN网络中，网络延迟占总CBT的 {network_dominance:.1f}%")
    print(f"   - 这意味着密码学性能差异的影响被大幅稀释")
    print()

    print(f"3. 端到端开销: 包含网络延迟后，PQ-NTOR总开销降至 {total_overhead_avg:.2f}×")
    print(f"   - Classic NTOR总CBT: {classic_data['Total_CBT_ms'].mean():.2f} ms")
    print(f"   - PQ-NTOR总CBT: {pq_data['Total_CBT_ms'].mean():.2f} ms")
    print(f"   - 绝对差异: {pq_data['Total_CBT_ms'].mean() - classic_data['Total_CBT_ms'].mean():.2f} ms")
    print()

    print("4. 实用性评估:")
    avg_total_cbt = pq_data['Total_CBT_ms'].mean()
    if avg_total_cbt < 20:
        print(f"   ✅ 优秀: PQ-NTOR平均CBT为 {avg_total_cbt:.2f} ms < 20ms，用户几乎无感知")
    elif avg_total_cbt < 50:
        print(f"   ✅ 良好: PQ-NTOR平均CBT为 {avg_total_cbt:.2f} ms < 50ms，可接受延迟")
    elif avg_total_cbt < 100:
        print(f"   ⚠️  可接受: PQ-NTOR平均CBT为 {avg_total_cbt:.2f} ms < 100ms，轻微延迟")
    else:
        print(f"   ❌ 较高: PQ-NTOR平均CBT为 {avg_total_cbt:.2f} ms，可能影响用户体验")
    print()

    print("="*80)

    return results_df

def visualize_results(results_df, output_dir='.'):
    """生成可视化图表"""

    print()
    print("="*80)
    print("📊 生成可视化图表")
    print("="*80)
    print()

    # 图1: 密码学CBT vs 总CBT对比
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1.1 密码学CBT对比
    ax = axes[0, 0]
    classic_crypto = results_df[results_df['Protocol'].str.contains('Classic')].sort_values('Topology')
    pq_crypto = results_df[results_df['Protocol'].str.contains('PQ')].sort_values('Topology')

    x = np.arange(len(classic_crypto))
    width = 0.35

    ax.bar(x - width/2, classic_crypto['Crypto_CBT_ms'], width, label='Classic NTOR', color='#3498db')
    ax.bar(x + width/2, pq_crypto['Crypto_CBT_ms'], width, label='PQ-NTOR', color='#e74c3c')

    ax.set_xlabel('SAGIN Topology', fontsize=12)
    ax.set_ylabel('Cryptographic CBT (ms)', fontsize=12)
    ax.set_title('Cryptographic Performance (Pure Computation)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(classic_crypto['Topology'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 1.2 总CBT对比
    ax = axes[0, 1]
    classic_total = results_df[results_df['Protocol'].str.contains('Classic')].sort_values('Topology')
    pq_total = results_df[results_df['Protocol'].str.contains('PQ')].sort_values('Topology')

    ax.bar(x - width/2, classic_total['Total_CBT_ms'], width, label='Classic NTOR', color='#3498db')
    ax.bar(x + width/2, pq_total['Total_CBT_ms'], width, label='PQ-NTOR', color='#e74c3c')

    ax.set_xlabel('SAGIN Topology', fontsize=12)
    ax.set_ylabel('Total CBT (ms)', fontsize=12)
    ax.set_title('End-to-End Performance (Crypto + Network)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(classic_total['Topology'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 1.3 CBT组成堆叠图（PQ-NTOR）
    ax = axes[1, 0]
    pq_data = results_df[results_df['Protocol'].str.contains('PQ')].sort_values('Topology')

    ax.bar(x, pq_data['Crypto_CBT_ms'], width*2, label='Cryptographic Computation', color='#e74c3c')
    ax.bar(x, pq_data['Network_Delay_ms'], width*2, bottom=pq_data['Crypto_CBT_ms'],
           label='Network Propagation Delay', color='#95a5a6')
    bottom = pq_data['Crypto_CBT_ms'] + pq_data['Network_Delay_ms']
    ax.bar(x, pq_data['Retransmission_Delay_ms'], width*2, bottom=bottom,
           label='Retransmission Delay', color='#f39c12')

    ax.set_xlabel('SAGIN Topology', fontsize=12)
    ax.set_ylabel('Circuit Build Time (ms)', fontsize=12)
    ax.set_title('PQ-NTOR CBT Breakdown', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(pq_data['Topology'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 1.4 PQ开销倍数
    ax = axes[1, 1]

    overhead_crypto = pq_crypto['Crypto_CBT_ms'].values / classic_crypto['Crypto_CBT_ms'].values
    overhead_total = pq_total['Total_CBT_ms'].values / classic_total['Total_CBT_ms'].values

    ax.plot(x, overhead_crypto, 'o-', label='Crypto-only Overhead', linewidth=2, markersize=8, color='#e74c3c')
    ax.plot(x, overhead_total, 's-', label='End-to-End Overhead', linewidth=2, markersize=8, color='#3498db')
    ax.axhline(y=1.0, color='gray', linestyle='--', label='Baseline (1.0x)')

    ax.set_xlabel('SAGIN Topology', fontsize=12)
    ax.set_ylabel('PQ-NTOR Overhead (×)', fontsize=12)
    ax.set_title('PQ-NTOR Relative Overhead', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(pq_crypto['Topology'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_file = f'{output_dir}/phase3_sagin_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")

    # 图2: 网络延迟主导性分析
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 2.1 网络延迟占比
    ax = axes[0]
    classic_ratio = results_df[results_df['Protocol'].str.contains('Classic')].sort_values('Topology')
    pq_ratio = results_df[results_df['Protocol'].str.contains('PQ')].sort_values('Topology')

    ax.bar(x - width/2, classic_ratio['Network_Ratio'], width, label='Classic NTOR', color='#3498db')
    ax.bar(x + width/2, pq_ratio['Network_Ratio'], width, label='PQ-NTOR', color='#e74c3c')

    ax.set_xlabel('SAGIN Topology', fontsize=12)
    ax.set_ylabel('Network Delay Ratio (%)', fontsize=12)
    ax.set_title('Network Delay Dominance', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(classic_ratio['Topology'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim([0, 100])

    # 2.2 延迟-开销关系散点图
    ax = axes[1]

    for topo in results_df['Topology'].unique():
        topo_data = results_df[results_df['Topology'] == topo]
        classic_cbt = topo_data[topo_data['Protocol'].str.contains('Classic')]['Total_CBT_ms'].values[0]
        pq_cbt = topo_data[topo_data['Protocol'].str.contains('PQ')]['Total_CBT_ms'].values[0]
        overhead = pq_cbt / classic_cbt
        delay = TOPOLOGY_PARAMS[topo]['delay_ms']

        ax.scatter(delay, overhead, s=150, alpha=0.7, label=topo)

    ax.set_xlabel('Link Delay (ms)', fontsize=12)
    ax.set_ylabel('PQ-NTOR End-to-End Overhead (×)', fontsize=12)
    ax.set_title('Network Delay vs PQ Overhead', fontsize=14, fontweight='bold')
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    output_file = f'{output_dir}/phase3_network_dominance.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")

    print()
    print("✅ 可视化完成!")

def main():
    if len(sys.argv) < 2:
        csv_path = '/home/ccc/pq-ntor-experiment/essay/phase3_results_wsl2_20251204_102539/phase3_sagin_cbt.csv'
        print(f"使用默认路径: {csv_path}")
    else:
        csv_path = sys.argv[1]

    # 分析结果
    results_df = analyze_phase3(csv_path)

    # 生成可视化
    import os
    output_dir = os.path.dirname(csv_path)
    visualize_results(results_df, output_dir)

    print()
    print("="*80)
    print("✅ Phase 3 分析完成!")
    print("="*80)
    print()
    print("📁 输出文件:")
    print(f"  1. CSV结果: {csv_path.replace('.csv', '_with_network.csv')}")
    print(f"  2. 性能对比图: {output_dir}/phase3_sagin_analysis.png")
    print(f"  3. 网络主导性图: {output_dir}/phase3_network_dominance.png")
    print()

if __name__ == '__main__':
    main()
