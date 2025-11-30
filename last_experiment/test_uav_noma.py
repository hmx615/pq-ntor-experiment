import numpy as np

C = 3e8
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


def main():
    uav_pos = np.array([0.0, 0.0, 1000.0])
    user_near = np.array([0.0, 0.0, 0.0])
    user_far = np.array([2500.0, 500.0, 0.0])

    P_uav_W = 3.16  # 35 dBm
    B_Hz = 2e6
    alpha = 0.7

    rate_near, sinr_near, gain_near = uav_oma_rate(uav_pos, user_near, P_uav_W, B_Hz)
    rate_far, sinr_far, gain_far = uav_oma_rate(uav_pos, user_far, P_uav_W, B_Hz)
    print("--- UAV→UE OMA ---")
    print(
        f"近端用户: {rate_near:.2f} Mbps, SINR={10 * np.log10(sinr_near):.2f} dB, "
        f"Gain={10 * np.log10(gain_near):.2f} dB"
    )
    print(
        f"远端用户: {rate_far:.2f} Mbps, SINR={10 * np.log10(sinr_far):.2f} dB, "
        f"Gain={10 * np.log10(gain_far):.2f} dB"
    )

    (rate_weak, rate_strong), (sinr_weak, sinr_strong), (gain_weak, gain_strong) = uav_noma_rate(
        uav_pos,
        weak_user_pos=user_far,
        strong_user_pos=user_near,
        P_uav_W=P_uav_W,
        B_Hz=B_Hz,
        alpha_power=alpha,
    )
    print("\n--- UAV→UE NOMA ---")
    print(
        f"弱用户(远端): {rate_weak:.2f} Mbps, SINR={10 * np.log10(sinr_weak):.2f} dB, "
        f"Gain={10 * np.log10(gain_weak):.2f} dB"
    )
    print(
        f"强用户(近端): {rate_strong:.2f} Mbps, SINR={10 * np.log10(sinr_strong):.2f} dB, "
        f"Gain={10 * np.log10(gain_strong):.2f} dB"
    )


if __name__ == "__main__":
    main()

