import numpy as np
import math
from scipy.special import jv

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


def main():
    # 时间槽15的卫星坐标（单位: m）
    sat_pos = np.array([-118056.04, 14085.41, 813291.98])

    # 选择两个地面用户：一个靠近中心，一个接近波束边缘
    user_center = np.array([0.0, 5000.0, 0.0])
    user_edge = np.array([0.0, 15000.0, 0.0])

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


if __name__ == "__main__":
    main()

