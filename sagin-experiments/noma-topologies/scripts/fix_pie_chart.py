#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['figure.dpi'] = 150

TRAD_HANDSHAKE_US = 100
PQ_HANDSHAKE_US = 147
OVERHEAD_US = 47

df = pd.read_csv('../results/raw_results_satellite_20251121_155031.csv')
avg_duration_ms = df['duration_s'].mean() * 1000
output_dir = Path('../results/figures')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左：总时间分布
handshake_ms = PQ_HANDSHAKE_US / 1000
network_ms = avg_duration_ms - handshake_ms
sizes = [network_ms, handshake_ms]
labels = [f'Network & Processing\n{network_ms/1000:.1f}s (99.9997%)', 
          f'PQ Handshake\n{handshake_ms*1000:.0f}μs (0.0003%)']
colors = ['#3498db', '#e74c3c']
explode = (0, 0.2)

wedges, texts = axes[0].pie(sizes, explode=explode, labels=labels, colors=colors, 
                            shadow=False, startangle=45,  # 关闭阴影
                            labeldistance=1.25)
axes[0].set_title('Time Distribution in Circuit Setup', fontsize=12, fontweight='bold')

# 右：握手时间分解
sizes2 = [TRAD_HANDSHAKE_US, OVERHEAD_US]
labels2 = [f'Base NTOR\n{TRAD_HANDSHAKE_US}μs (68%)', f'PQ Overhead\n{OVERHEAD_US}μs (32%)']
colors2 = ['#2ecc71', '#e74c3c']

axes[1].pie(sizes2, labels=labels2, colors=colors2, autopct='',
            shadow=False, startangle=90, labeldistance=1.2)  # 关闭阴影
axes[1].set_title('PQ-NTOR Handshake Breakdown', fontsize=12, fontweight='bold')

plt.suptitle('PQ-NTOR Overhead Analysis', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(output_dir / 'time_distribution_pie.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'time_distribution_pie.pdf', bbox_inches='tight')
print("✓ 饼图已更新 - 去掉阴影")
plt.close()
