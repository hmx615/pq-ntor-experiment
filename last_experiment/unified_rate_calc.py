#!/usr/bin/env python3
"""
统一速率计算模块
整合三个计算程序，提供统一接口
"""

import numpy as np
import math
import sys
import os
from scipy.special import jv

# 添加路径以导入计算模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'last_experiment'))

# ============================================================================
# 卫星链路计算 (from test_satellite_noma.py)
# ============================================================================

C = 3e8
FREQ = 20e9
G_SAT_TX_LINEAR = 10 ** (32.0 / 10)
G_USER_RX_LINEAR = 10 ** (5.0 / 10)
G_UAV_RX_LINEAR = 10 ** (25.0 / 10)
BEAM_ANGLE_B_DEG = 0.85
BEAM_UK_N_COEFF = 2.07123
NOISE_DENSITY_W_PER_HZ = 10 ** ((-174 - 30) / 10)

def beam_pattern_single_beam(user_pos_3d, sat_pos_3d):
    beam_center_3d = np.zeros(3)
    vec_sat_to_beam = beam_center_3d - sat_pos_3d
    vec_sat_to_user = np.array(user_pos_3d) - sat_pos_3d
    norm_beam = np.linalg.norm(vec_sat_to_beam)
    norm_user = np.linalg.norm(vec_sat_to_user)
    if norm_beam == 0 or norm_user == 0:
        return 0.0
    cos_phi = np.clip(np.dot(vec_sat_to_beam, vec_sat_to_user) / (norm_beam * norm_user), -1.0, 1.0)
    phi_rad = np.arccos(cos_phi)
    if phi_rad < 1e-9:
        return 1.0
    sin_B = math.sin(math.radians(BEAM_ANGLE_B_DEG))
    if abs(sin_B) < 1e-9:
        return 1e-10
    uk_n = BEAM_UK_N_COEFF * math.sin(phi_rad) / sin_B
    if abs(uk_n) < 1e-9:
        return 1.0
    term1 = jv(1, uk_n) / (2 * uk_n)
    term2 = 36 * jv(3, uk_n) / (uk_n ** 3)
    return float(np.clip((term1 + term2) ** 2, 1e-10, 1.0))

def sat_effective_gain(sat_pos, dev_pos, is_uav):
    distance = np.linalg.norm(dev_pos - sat_pos)
    distance = max(distance, 1e-9)
    path_loss_inv = (C / (4 * math.pi * distance * FREQ)) ** 2
    beam_gain = beam_pattern_single_beam(dev_pos, sat_pos)
    G_rx = G_UAV_RX_LINEAR if is_uav else G_USER_RX_LINEAR
    return path_loss_inv * G_SAT_TX_LINEAR * G_rx * beam_gain

def sat_oma(sat_pos, dev_pos, P_tx_W, B_Hz, is_uav=False):
    gain = sat_effective_gain(sat_pos, dev_pos, is_uav)
    signal_W = P_tx_W * gain
    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz
    sinr = signal_W / noise_W
    rate_mbps = B_Hz * np.log2(1 + sinr) / 1e6
    return rate_mbps, sinr, gain

def sat_noma(sat_pos, weak_pos, strong_pos, P_tx_W, B_Hz, alpha_power,
             weak_is_uav=False, strong_is_uav=False):
    gain_weak = sat_effective_gain(sat_pos, weak_pos, weak_is_uav)
    gain_strong = sat_effective_gain(sat_pos, strong_pos, strong_is_uav)

    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz
    signal_weak = alpha_power * P_tx_W * gain_weak
    interference_weak = (1 - alpha_power) * P_tx_W * gain_weak
    sinr_weak = signal_weak / (interference_weak + noise_W)

    signal_strong = (1 - alpha_power) * P_tx_W * gain_strong
    sinr_strong = signal_strong / noise_W

    rate_weak = B_Hz * np.log2(1 + sinr_weak) / 1e6
    rate_strong = B_Hz * np.log2(1 + sinr_strong) / 1e6
    return (rate_weak, rate_strong), (sinr_weak, sinr_strong), (gain_weak, gain_strong)

# ============================================================================
# UAV 链路计算 (from test_uav_noma.py)
# ============================================================================

FREQ_UAV = 2.4e9
A_SUB, B_SUB = 4.88, 0.43
ETA_LOS_DB, ETA_NLOS_DB = 1.0, 21.0
N0_W_PER_HZ = 10 ** ((-174 - 30) / 10)

def uav_to_user_gain(uav_pos, user_pos):
    horiz_dist = np.linalg.norm(uav_pos[:2] - user_pos[:2])
    height = max(uav_pos[2] - user_pos[2], 1e-9)
    theta_deg = 90.0 if horiz_dist <= 0 else np.degrees(np.arctan(height / horiz_dist))
    P_los = 1.0 / (1.0 + A_SUB * np.exp(-B_SUB * (theta_deg - A_SUB)))
    d_slant = np.sqrt(height ** 2 + horiz_dist ** 2)
    fspl_dB = 20 * np.log10(d_slant) + 20 * np.log10(FREQ_UAV) + 20 * np.log10(4 * np.pi / C)
    excess_dB = P_los * ETA_LOS_DB + (1 - P_los) * ETA_NLOS_DB
    total_dB = fspl_dB + excess_dB
    return 10 ** (-total_dB / 10.0)

def uav_oma_rate(uav_pos, user_pos, P_uav_W, B_Hz):
    gain = uav_to_user_gain(uav_pos, user_pos)
    signal = P_uav_W * gain
    noise = N0_W_PER_HZ * B_Hz
    sinr = signal / noise
    rate_mbps = B_Hz * np.log2(1 + sinr) / 1e6
    return rate_mbps, sinr, gain

def uav_noma_rate(uav_pos, weak_user_pos, strong_user_pos, P_uav_W, B_Hz, alpha_power):
    gain_w = uav_to_user_gain(uav_pos, weak_user_pos)
    gain_s = uav_to_user_gain(uav_pos, strong_user_pos)
    noise = N0_W_PER_HZ * B_Hz

    sig_w = alpha_power * P_uav_W * gain_w
    int_w = (1 - alpha_power) * P_uav_W * gain_w
    sinr_w = sig_w / (int_w + noise)

    sig_s = (1 - alpha_power) * P_uav_W * gain_s
    sinr_s = sig_s / noise

    rate_w = B_Hz * np.log2(1 + sinr_w) / 1e6
    rate_s = B_Hz * np.log2(1 + sinr_s) / 1e6
    return (rate_w, rate_s), (sinr_w, sinr_s), (gain_w, gain_s)

# ============================================================================
# D2D 链路计算 (from test_d2d_noma.py)
# ============================================================================

FREQ_D2D = 2.4e9
PATH_LOSS_EXP = 3.0
REF_DIST = 1.0

def d2d_channel_gain(user_a_pos, user_b_pos):
    distance = np.linalg.norm(np.array(user_a_pos) - np.array(user_b_pos))
    if distance <= 0:
        return 0.0
    fspl_d0_dB = 20 * np.log10(REF_DIST) + 20 * np.log10(FREQ_D2D) + 20 * np.log10(4 * np.pi / C)
    if distance > REF_DIST:
        path_loss_dB = fspl_d0_dB + 10 * PATH_LOSS_EXP * np.log10(distance / REF_DIST)
    else:
        path_loss_dB = 20 * np.log10(distance) + 20 * np.log10(FREQ_D2D) + 20 * np.log10(4 * np.pi / C)
    return 10 ** (-path_loss_dB / 10.0)

def d2d_oma_rate(user_a_pos, user_b_pos, P_tx_W, B_Hz):
    gain = d2d_channel_gain(user_a_pos, user_b_pos)
    signal = P_tx_W * gain
    noise = N0_W_PER_HZ * B_Hz
    sinr = signal / noise
    rate_mbps = B_Hz * np.log2(1 + sinr) / 1e6
    return rate_mbps, sinr, gain

def d2d_noma_rate(tx_pos, weak_rx_pos, strong_rx_pos, P_tx_W, B_Hz, alpha_power):
    gain_w = d2d_channel_gain(tx_pos, weak_rx_pos)
    gain_s = d2d_channel_gain(tx_pos, strong_rx_pos)
    noise = N0_W_PER_HZ * B_Hz

    sig_w = alpha_power * P_tx_W * gain_w
    int_w = (1 - alpha_power) * P_tx_W * gain_w
    sinr_w = sig_w / (int_w + noise)

    sig_s = (1 - alpha_power) * P_tx_W * gain_s
    sinr_s = sig_s / noise

    rate_w = B_Hz * np.log2(1 + sinr_w) / 1e6
    rate_s = B_Hz * np.log2(1 + sinr_s) / 1e6
    return (rate_w, rate_s), (sinr_w, sinr_s), (gain_w, gain_s)

# ============================================================================
# 统一计算所有场景
# ============================================================================

def calculate_all_scenarios():
    """计算所有 12+ 个拓扑的速率"""

    results = {}

    # === 场景 1-2: 卫星链路 ===
    sat_pos = np.array([-118056.04, 14085.41, 813291.98])
    user_center = np.array([0.0, 5000.0, 0.0])
    user_edge = np.array([0.0, 15000.0, 0.0])
    P_sat = 20.0
    B_sat = 20e6

    # OMA
    rate_c, sinr_c, gain_c = sat_oma(sat_pos, user_center, P_sat, B_sat)
    rate_e, sinr_e, gain_e = sat_oma(sat_pos, user_edge, P_sat, B_sat)

    results['Z1-UP1-OMA-center'] = {
        'rate_mbps': float(rate_c),
        'sinr_db': float(10 * np.log10(sinr_c)),
        'gain_db': float(10 * np.log10(gain_c)),
        'link_type': 'satellite',
        'access_method': 'OMA'
    }
    results['Z1-UP1-OMA-edge'] = {
        'rate_mbps': float(rate_e),
        'sinr_db': float(10 * np.log10(sinr_e)),
        'gain_db': float(10 * np.log10(gain_e)),
        'link_type': 'satellite',
        'access_method': 'OMA'
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = sat_noma(
        sat_pos, user_edge, user_center, P_sat, B_sat, 0.7,
        weak_is_uav=False, strong_is_uav=False
    )

    results['Z1-UP1-NOMA-weak'] = {
        'rate_mbps': float(rw),
        'sinr_db': float(10 * np.log10(sw)),
        'gain_db': float(10 * np.log10(gw)),
        'link_type': 'satellite',
        'access_method': 'NOMA',
        'user_type': 'weak'
    }
    results['Z1-UP1-NOMA-strong'] = {
        'rate_mbps': float(rs),
        'sinr_db': float(10 * np.log10(ss)),
        'gain_db': float(10 * np.log10(gs)),
        'link_type': 'satellite',
        'access_method': 'NOMA',
        'user_type': 'strong'
    }

    # === 场景 3-4: 无人机链路 ===
    uav_pos = np.array([0.0, 0.0, 1000.0])
    user_near = np.array([0.0, 0.0, 0.0])
    user_far = np.array([2500.0, 500.0, 0.0])
    P_uav = 3.16
    B_uav = 2e6

    # OMA
    rate_n, sinr_n, gain_n = uav_oma_rate(uav_pos, user_near, P_uav, B_uav)
    rate_f, sinr_f, gain_f = uav_oma_rate(uav_pos, user_far, P_uav, B_uav)

    results['Z1-UP2-OMA-near'] = {
        'rate_mbps': float(rate_n),
        'sinr_db': float(10 * np.log10(sinr_n)),
        'gain_db': float(10 * np.log10(gain_n)),
        'link_type': 'uav',
        'access_method': 'OMA'
    }
    results['Z1-UP2-OMA-far'] = {
        'rate_mbps': float(rate_f),
        'sinr_db': float(10 * np.log10(sinr_f)),
        'gain_db': float(10 * np.log10(gain_f)),
        'link_type': 'uav',
        'access_method': 'OMA'
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = uav_noma_rate(
        uav_pos, user_far, user_near, P_uav, B_uav, 0.7
    )

    results['Z1-UP2-NOMA-weak'] = {
        'rate_mbps': float(rw),
        'sinr_db': float(10 * np.log10(sw)),
        'gain_db': float(10 * np.log10(gw)),
        'link_type': 'uav',
        'access_method': 'NOMA',
        'user_type': 'weak'
    }
    results['Z1-UP2-NOMA-strong'] = {
        'rate_mbps': float(rs),
        'sinr_db': float(10 * np.log10(ss)),
        'gain_db': float(10 * np.log10(gs)),
        'link_type': 'uav',
        'access_method': 'NOMA',
        'user_type': 'strong'
    }

    # === 场景 5-6: D2D 链路 ===
    tx_pos = np.array([0.0, 0.0, 0.0])
    strong_rx = np.array([30.0, 0.0, 0.0])
    weak_rx = np.array([100.0, 0.0, 0.0])
    P_d2d = 0.2
    B_d2d = 2e6

    # OMA
    rate_s, sinr_s, gain_s = d2d_oma_rate(tx_pos, strong_rx, P_d2d, B_d2d)
    rate_w, sinr_w, gain_w = d2d_oma_rate(tx_pos, weak_rx, P_d2d, B_d2d)

    results['Z2-D2D-OMA-strong'] = {
        'rate_mbps': float(rate_s),
        'sinr_db': float(10 * np.log10(sinr_s)),
        'gain_db': float(10 * np.log10(gain_s)),
        'link_type': 'd2d',
        'access_method': 'OMA'
    }
    results['Z2-D2D-OMA-weak'] = {
        'rate_mbps': float(rate_w),
        'sinr_db': float(10 * np.log10(sinr_w)),
        'gain_db': float(10 * np.log10(gain_w)),
        'link_type': 'd2d',
        'access_method': 'OMA'
    }

    # NOMA
    (rw, rs), (sw, ss), (gw, gs) = d2d_noma_rate(
        tx_pos, weak_rx, strong_rx, P_d2d, B_d2d, 0.7
    )

    results['Z2-D2D-NOMA-weak'] = {
        'rate_mbps': float(rw),
        'sinr_db': float(10 * np.log10(sw)),
        'gain_db': float(10 * np.log10(gw)),
        'link_type': 'd2d',
        'access_method': 'NOMA',
        'user_type': 'weak'
    }
    results['Z2-D2D-NOMA-strong'] = {
        'rate_mbps': float(rs),
        'sinr_db': float(10 * np.log10(ss)),
        'gain_db': float(10 * np.log10(gs)),
        'link_type': 'd2d',
        'access_method': 'NOMA',
        'user_type': 'strong'
    }

    # === 场景 7-9: 两跳链路 ===
    # 第一跳: 卫星→无人机
    rate_hop1, sinr_hop1, gain_hop1 = sat_oma(
        sat_pos, uav_pos, P_sat, B_sat, is_uav=True
    )

    # 第二跳: 无人机→远端用户
    rate_hop2, sinr_hop2, gain_hop2 = uav_oma_rate(
        uav_pos, user_far, P_uav, B_uav
    )

    # 端到端速率 = min(hop1, hop2)
    rate_e2e = min(rate_hop1, rate_hop2)

    results['Z3-2Hop-Sat'] = {
        'rate_mbps': float(rate_hop1),
        'sinr_db': float(10 * np.log10(sinr_hop1)),
        'gain_db': float(10 * np.log10(gain_hop1)),
        'link_type': 'satellite',
        'access_method': 'OMA',
        'hop': 'first'
    }
    results['Z3-2Hop-UAV'] = {
        'rate_mbps': float(rate_hop2),
        'sinr_db': float(10 * np.log10(sinr_hop2)),
        'gain_db': float(10 * np.log10(gain_hop2)),
        'link_type': 'uav',
        'access_method': 'OMA',
        'hop': 'second'
    }
    results['Z3-2Hop-Full'] = {
        'rate_mbps': float(rate_e2e),
        'sinr_db': float(min(10*np.log10(sinr_hop1), 10*np.log10(sinr_hop2))),
        'gain_db': float(10 * np.log10(gain_hop1 * gain_hop2)),
        'link_type': 'two_hop',
        'access_method': 'OMA',
        'bottleneck': 'hop1' if rate_hop1 < rate_hop2 else 'hop2'
    }

    return results

def main():
    import json

    print("=" * 70)
    print("SAGIN 网络速率计算 - 所有场景")
    print("=" * 70)

    results = calculate_all_scenarios()

    print(f"\n共计算 {len(results)} 个场景\n")

    # 按链路类型分组显示
    for link_type in ['satellite', 'uav', 'd2d', 'two_hop']:
        scenarios = {k: v for k, v in results.items() if v.get('link_type') == link_type}
        if not scenarios:
            continue

        type_names = {
            'satellite': '卫星链路',
            'uav': '无人机链路',
            'd2d': 'D2D链路',
            'two_hop': '两跳链路'
        }

        print(f"\n{'=' * 70}")
        print(f"{type_names[link_type]}")
        print('=' * 70)

        for scenario, metrics in sorted(scenarios.items()):
            print(f"\n{scenario}:")
            print(f"  速率: {metrics['rate_mbps']:>8.2f} Mbps")
            print(f"  SINR: {metrics['sinr_db']:>8.2f} dB")
            print(f"  增益: {metrics['gain_db']:>8.2f} dB")
            if 'user_type' in metrics:
                print(f"  用户类型: {metrics['user_type']}")
            if 'bottleneck' in metrics:
                print(f"  瓶颈: {metrics['bottleneck']}")

    # 保存为 JSON
    output_file = 'results/all_scenarios_rates.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"✅ 结果已保存到: {output_file}")
    print('=' * 70)

    # 生成简单的对比表
    print("\n\n" + "=" * 70)
    print("OMA vs NOMA 速率对比")
    print("=" * 70)

    print("\n卫星链路:")
    print(f"  中心用户 OMA: {results['Z1-UP1-OMA-center']['rate_mbps']:.2f} Mbps")
    print(f"  中心用户 NOMA: {results['Z1-UP1-NOMA-strong']['rate_mbps']:.2f} Mbps")
    print(f"  边缘用户 OMA: {results['Z1-UP1-OMA-edge']['rate_mbps']:.2f} Mbps")
    print(f"  边缘用户 NOMA: {results['Z1-UP1-NOMA-weak']['rate_mbps']:.2f} Mbps")

    print("\n无人机链路:")
    print(f"  近端用户 OMA: {results['Z1-UP2-OMA-near']['rate_mbps']:.2f} Mbps")
    print(f"  近端用户 NOMA: {results['Z1-UP2-NOMA-strong']['rate_mbps']:.2f} Mbps")
    print(f"  远端用户 OMA: {results['Z1-UP2-OMA-far']['rate_mbps']:.2f} Mbps")
    print(f"  远端用户 NOMA: {results['Z1-UP2-NOMA-weak']['rate_mbps']:.2f} Mbps")

    print("\nD2D链路:")
    print(f"  强用户 OMA: {results['Z2-D2D-OMA-strong']['rate_mbps']:.2f} Mbps")
    print(f"  强用户 NOMA: {results['Z2-D2D-NOMA-strong']['rate_mbps']:.2f} Mbps")
    print(f"  弱用户 OMA: {results['Z2-D2D-OMA-weak']['rate_mbps']:.2f} Mbps")
    print(f"  弱用户 NOMA: {results['Z2-D2D-NOMA-weak']['rate_mbps']:.2f} Mbps")

    print("\n两跳链路:")
    print(f"  第一跳 (卫星→UAV): {results['Z3-2Hop-Sat']['rate_mbps']:.2f} Mbps")
    print(f"  第二跳 (UAV→用户): {results['Z3-2Hop-UAV']['rate_mbps']:.2f} Mbps")
    print(f"  端到端速率: {results['Z3-2Hop-Full']['rate_mbps']:.2f} Mbps")
    print(f"  瓶颈: {results['Z3-2Hop-Full']['bottleneck']}")

    return 0

if __name__ == '__main__':
    exit(main())
