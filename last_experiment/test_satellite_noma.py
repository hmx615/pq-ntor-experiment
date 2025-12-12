import numpy as np
import math
from scipy.special import jv

C = 3e8
FREQ = 20e9
G_SAT_TX_LINEAR = 10 ** (32.0 / 10)
G_USER_RX_LINEAR = 10 ** (5.0 / 10)
G_UAV_RX_LINEAR = 10 ** (25.0 / 10)
# Uplink TX gains (linear) - 优化后
G_UAV_TX_UL_LINEAR = 10 ** (15.0 / 10)   # 15 dBi ≈ 31.62
G_GROUND_TX_UL_LINEAR = 10 ** (10.0 / 10)  # 10 dBi ≈ 10 (从1 dBi提升)
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

def effective_gain(sat_pos, dev_pos, is_uav):
    distance = np.linalg.norm(dev_pos - sat_pos)
    distance = max(distance, 1e-9)
    path_loss_inv = (C / (4 * math.pi * distance * FREQ)) ** 2
    beam_gain = beam_pattern_single_beam(dev_pos, sat_pos)
    G_rx = G_UAV_RX_LINEAR if is_uav else G_USER_RX_LINEAR
    return path_loss_inv * G_SAT_TX_LINEAR * G_rx * beam_gain

def oma_rate_single_device(sat_pos, dev_pos, P_tx_W, B_Hz, is_uav=False):
    gain = effective_gain(sat_pos, dev_pos, is_uav)
    signal_W = P_tx_W * gain
    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz
    sinr = signal_W / noise_W
    rate_mbps = B_Hz * np.log2(1 + sinr) / 1e6
    return rate_mbps, sinr, gain

def noma_rate_two_devices(sat_pos, weak_pos, strong_pos,
                          P_tx_W, B_Hz, alpha_power,
                          weak_is_uav=False, strong_is_uav=False):
    gain_weak = effective_gain(sat_pos, weak_pos, weak_is_uav)
    gain_strong = effective_gain(sat_pos, strong_pos, strong_is_uav)

    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz
    signal_weak = alpha_power * P_tx_W * gain_weak
    interference_weak = (1 - alpha_power) * P_tx_W * gain_weak
    sinr_weak = signal_weak / (interference_weak + noise_W)

    signal_strong = (1 - alpha_power) * P_tx_W * gain_strong
    sinr_strong = signal_strong / noise_W

    rate_weak = B_Hz * np.log2(1 + sinr_weak) / 1e6
    rate_strong = B_Hz * np.log2(1 + sinr_strong) / 1e6
    return (rate_weak, rate_strong), (sinr_weak, sinr_strong), (gain_weak, gain_strong)



def effective_gain_uplink(sat_pos, dev_pos, tx_gain_linear, rx_gain_sat_linear):
    """Uplink effective gain: path loss + TX gain + sat RX gain * beam pattern."""
    distance = np.linalg.norm(dev_pos - sat_pos)
    distance = max(distance, 1e-9)
    path_loss_inv = (C / (4 * math.pi * distance * FREQ)) ** 2
    beam_gain = beam_pattern_single_beam(dev_pos, sat_pos)
    rx_gain = rx_gain_sat_linear * beam_gain
    return path_loss_inv * tx_gain_linear * rx_gain


def uplink_oma_rate_single_device(sat_pos, dev_pos, P_tx_W, B_Hz,
                                  tx_gain_linear, rx_gain_sat_linear):
    gain = effective_gain_uplink(sat_pos, dev_pos, tx_gain_linear, rx_gain_sat_linear)
    signal_W = P_tx_W * gain
    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz
    sinr = signal_W / noise_W
    rate_mbps = B_Hz * np.log2(1 + sinr) / 1e6
    return rate_mbps, sinr, gain


def uplink_noma_two_devices(sat_pos,
                            weak_pos, strong_pos,
                            P_tx_weak_W, P_tx_strong_W,
                            B_Hz, alpha_power,
                            tx_gain_weak_linear, tx_gain_strong_linear,
                            rx_gain_sat_linear):
    """
    Uplink NOMA: weak user uses alpha_power, strong user uses (1-alpha_power).
    rx_gain_sat_linear will be multiplied by beam_gain internally.
    """
    gain_weak = effective_gain_uplink(sat_pos, weak_pos, tx_gain_weak_linear, rx_gain_sat_linear)
    gain_strong = effective_gain_uplink(sat_pos, strong_pos, tx_gain_strong_linear, rx_gain_sat_linear)

    noise_W = NOISE_DENSITY_W_PER_HZ * B_Hz

    signal_weak = alpha_power * P_tx_weak_W * gain_weak
    interference_weak = (1 - alpha_power) * P_tx_strong_W * gain_weak
    sinr_weak = signal_weak / (interference_weak + noise_W)

    signal_strong = (1 - alpha_power) * P_tx_strong_W * gain_strong
    sinr_strong = signal_strong / noise_W  # assume SIC for strong user

    rate_weak = B_Hz * np.log2(1 + sinr_weak) / 1e6
    rate_strong = B_Hz * np.log2(1 + sinr_strong) / 1e6

    return (rate_weak, rate_strong), (sinr_weak, sinr_strong), (gain_weak, gain_strong)


def main():
    # 时间槽15的卫星坐标（单位: m）
    sat_pos = np.array([-118056.04, 14085.41, 813291.98])

    # 选择两个地面用户：一个靠近中心，一个接近波束边缘
    user_center = np.array([0.0, 5000.0, 0.0])
    user_edge = np.array([5000, 15000.0, 0.0])

    # 卫星参数
    P_sat_W = 20.0     # 43 dBm ≈ 20W
    B_sat_Hz = 20e6    # 单信道带宽 20 MHz
    alpha = 0.7        # 弱用户（边缘）占 70% 功率

    # OMA 速率
    rate_center, sinr_center, gain_center = oma_rate_single_device(
        sat_pos, user_center, P_sat_W, B_sat_Hz, is_uav=False
    )
    rate_edge, sinr_edge, gain_edge = oma_rate_single_device(
        sat_pos, user_edge, P_sat_W, B_sat_Hz, is_uav=False
    )

    print("--- OMA ---")
    print(
        f"中心用户: {rate_center:.2f} Mbps, SINR={10 * np.log10(sinr_center):.2f} dB, "
        f"Gain={10 * np.log10(gain_center):.2f} dB"
    )
    print(
        f"边缘用户: {rate_edge:.2f} Mbps, SINR={10 * np.log10(sinr_edge):.2f} dB, "
        f"Gain={10 * np.log10(gain_edge):.2f} dB"
    )

    # NOMA 速率
    (rate_weak, rate_strong), (sinr_weak, sinr_strong), (gain_weak, gain_strong) = noma_rate_two_devices(
        sat_pos,
        weak_pos=user_edge,
        strong_pos=user_center,
        P_tx_W=P_sat_W,
        B_Hz=B_sat_Hz,
        alpha_power=alpha,
        weak_is_uav=False,
        strong_is_uav=False,
    )

    print("\n--- NOMA ---")
    print(
        f"弱用户(边缘): {rate_weak:.2f} Mbps, SINR={10 * np.log10(sinr_weak):.2f} dB, "
        f"Gain={10 * np.log10(gain_weak):.2f} dB"
    )
    print(
        f"强用户(中心): {rate_strong:.2f} Mbps, SINR={10 * np.log10(sinr_strong):.2f} dB, "
        f"Gain={10 * np.log10(gain_strong):.2f} dB"
    )

    # ===== Uplink demo =====
    # 配置：地面上行0.2W，Tx增益1 dBi；UAV上行3W，Tx增益15 dBi。
    # 卫星接收增益：32 dBi 基础增益 * beam_gain（在effective_gain_uplink内部处理）。
    RX_GAIN_SAT_LINEAR = 10 ** (32.0 / 10)
    P_ground_W = 0.2
    P_uav_W = 3.0  # 可改为5.0测试
    B_ul_Hz = 20e6
    alpha_ul = 0.7  # 弱用户（地面）占比

    # OMA: ground only
    rate_g_ul, sinr_g_ul, gain_g_ul = uplink_oma_rate_single_device(
        sat_pos, user_center, P_ground_W, B_ul_Hz,
        tx_gain_linear=G_GROUND_TX_UL_LINEAR,
        rx_gain_sat_linear=RX_GAIN_SAT_LINEAR,
    )
    print("\n--- Uplink OMA (Ground) ---")
    print(f"Ground UL: {rate_g_ul:.2f} Mbps, SINR={10 * np.log10(sinr_g_ul):.2f} dB, "
          f"Gain={10 * np.log10(gain_g_ul):.2f} dB")

    # === Uplink NOMA 例子1：地-地 NOMA 接入卫星 ===
    # 弱用户=边缘地面(0.2W, 1 dBi)，强用户=中心地面(0.2W, 1 dBi)
    (rate_ul_weak_g, rate_ul_strong_g), (sinr_ul_weak_g, sinr_ul_strong_g), (gain_ul_weak_g, gain_ul_strong_g) = \
        uplink_noma_two_devices(
            sat_pos,
            weak_pos=user_edge, strong_pos=user_center,
            P_tx_weak_W=P_ground_W, P_tx_strong_W=P_ground_W,
            B_Hz=B_ul_Hz, alpha_power=alpha_ul,
            tx_gain_weak_linear=G_GROUND_TX_UL_LINEAR,
            tx_gain_strong_linear=G_GROUND_TX_UL_LINEAR,
            rx_gain_sat_linear=RX_GAIN_SAT_LINEAR,
        )
    print("\n--- Uplink NOMA (Ground-Ground) ---")
    print(f"Weak (Ground edge): {rate_ul_weak_g:.2f} Mbps, SINR={10 * np.log10(sinr_ul_weak_g):.2f} dB, "
          f"Gain={10 * np.log10(gain_ul_weak_g):.2f} dB")
    print(f"Strong (Ground center): {rate_ul_strong_g:.2f} Mbps, SINR={10 * np.log10(sinr_ul_strong_g):.2f} dB, "
          f"Gain={10 * np.log10(gain_ul_strong_g):.2f} dB")

    # === Uplink NOMA 例子2：空-地 NOMA 接入卫星 ===
    # 弱用户=地面(0.2W, 1 dBi)，强用户=UAV(3W, 15 dBi)
    (rate_ul_weak, rate_ul_strong), (sinr_ul_weak, sinr_ul_strong), (gain_ul_weak, gain_ul_strong) = \
        uplink_noma_two_devices(
            sat_pos,
            weak_pos=user_edge, strong_pos=user_center,
            P_tx_weak_W=P_ground_W, P_tx_strong_W=P_uav_W,
            B_Hz=B_ul_Hz, alpha_power=alpha_ul,
            tx_gain_weak_linear=G_GROUND_TX_UL_LINEAR,
            tx_gain_strong_linear=G_UAV_TX_UL_LINEAR,
            rx_gain_sat_linear=RX_GAIN_SAT_LINEAR,
        )
    print("\n--- Uplink NOMA (Ground weak, UAV strong) ---")
    print(f"Weak (Ground): {rate_ul_weak:.2f} Mbps, SINR={10 * np.log10(sinr_ul_weak):.2f} dB, "
          f"Gain={10 * np.log10(gain_ul_weak):.2f} dB")
    print(f"Strong (UAV): {rate_ul_strong:.2f} Mbps, SINR={10 * np.log10(sinr_ul_strong):.2f} dB, "
          f"Gain={10 * np.log10(gain_ul_strong):.2f} dB")


if __name__ == "__main__":
    main()

