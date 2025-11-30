import numpy as np

C = 3e8
FREQ_D2D = 2.4e9
PATH_LOSS_EXP = 3.0
REF_DIST = 1.0
N0_W_PER_HZ = 10 ** ((-174 - 30) / 10)


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


def main():
    tx = np.array([0.0, 0.0, 0.0])
    weak_rx = np.array([100.0, 0.0, 0.0])
    strong_rx = np.array([30.0, 0.0, 0.0])

    P_tx_W = 0.2  # 23 dBm
    B_Hz = 2e6
    alpha = 0.7

    rate_weak_oma, sinr_weak_oma, gain_weak_oma = d2d_oma_rate(tx, weak_rx, P_tx_W, B_Hz)
    rate_strong_oma, sinr_strong_oma, gain_strong_oma = d2d_oma_rate(tx, strong_rx, P_tx_W, B_Hz)
    print("--- D2D OMA ---")
    print(
        f"弱用户: {rate_weak_oma:.2f} Mbps, SINR={10 * np.log10(sinr_weak_oma):.2f} dB, "
        f"Gain={10 * np.log10(gain_weak_oma):.2f} dB"
    )
    print(
        f"强用户: {rate_strong_oma:.2f} Mbps, SINR={10 * np.log10(sinr_strong_oma):.2f} dB, "
        f"Gain={10 * np.log10(gain_strong_oma):.2f} dB"
    )

    (rate_w, rate_s), (sinr_w, sinr_s), (gain_w, gain_s) = d2d_noma_rate(
        tx,
        weak_rx_pos=weak_rx,
        strong_rx_pos=strong_rx,
        P_tx_W=P_tx_W,
        B_Hz=B_Hz,
        alpha_power=alpha,
    )
    print("\n--- D2D NOMA ---")
    print(
        f"弱用户: {rate_w:.2f} Mbps, SINR={10 * np.log10(sinr_w):.2f} dB, "
        f"Gain={10 * np.log10(gain_w):.2f} dB"
    )
    print(
        f"强用户: {rate_s:.2f} Mbps, SINR={10 * np.log10(sinr_s):.2f} dB, "
        f"Gain={10 * np.log10(gain_s):.2f} dB"
    )


if __name__ == "__main__":
    main()

