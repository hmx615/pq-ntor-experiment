#!/usr/bin/env python3
"""改进版对比图"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['figure.dpi'] = 150

# 常量
TRAD_HANDSHAKE_US = 100
PQ_HANDSHAKE_US = 147
OVERHEAD_US = 47

df = pd.read_csv('../results/raw_results_satellite_20251121_155031.csv')
avg_duration_ms = df['duration_s'].mean() * 1000
avg_sat_delay = df['satellite_delay_ms'].mean()

output_dir = Path('../results/figures')

# 图1: 双Y轴对比图 - 左轴总时间，右轴握手时间
fig, ax1 = plt.subplots(figsize=(10, 6))

x = np.arange(2)
width = 0.35

# 左轴：总电路建立时间 (秒)
ax1.bar(x, [avg_duration_ms/1000, avg_duration_ms/1000], width, 
        color=['#3498db', '#e74c3c'], alpha=0.3, label='Total Circuit Time')
ax1.set_ylabel('Total Circuit Setup Time (s)', fontsize=12, color='gray')
ax1.set_ylim(0, 70)
ax1.tick_params(axis='y', labelcolor='gray')

# 右轴：握手时间 (微秒)
ax2 = ax1.twinx()
bars = ax2.bar(x + 0.02, [TRAD_HANDSHAKE_US, PQ_HANDSHAKE_US], width*0.6,
               color=['#3498db', '#e74c3c'], alpha=1.0, label='Handshake Time')
ax2.set_ylabel('Handshake Time (μs)', fontsize=12, fontweight='bold')
ax2.set_ylim(0, 200)

# 添加数值标签
for i, (bar, val) in enumerate(zip(bars, [TRAD_HANDSHAKE_US, PQ_HANDSHAKE_US])):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 5,
             f'{val} μs', ha='center', va='bottom', fontsize=12, fontweight='bold')

ax1.set_xticks(x)
ax1.set_xticklabels(['Traditional NTOR', 'PQ-NTOR (Kyber-512)'], fontsize=11)
ax1.set_title('Time Comparison: Total vs Handshake\n(Handshake is only 0.0003% of total time)',
              fontsize=14, fontweight='bold')

# 添加说明
ax1.text(0.5, -0.12, f'Total Time: {avg_duration_ms/1000:.1f}s | Handshake Overhead: +{OVERHEAD_US}μs (+47%) | Impact: Negligible',
         transform=ax1.transAxes, ha='center', fontsize=10,
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig(output_dir / 'comparison_dual_axis.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'comparison_dual_axis.pdf', bbox_inches='tight')
print("✓ comparison_dual_axis")
plt.close()

# 图2: 只对比握手时间（放大视图）
fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(['Traditional\nNTOR', 'PQ-NTOR\n(Kyber-512)'], 
              [TRAD_HANDSHAKE_US, PQ_HANDSHAKE_US],
              color=['#3498db', '#e74c3c'], alpha=0.8, width=0.5)

# 标注数值
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., h + 3, f'{h} μs',
            ha='center', fontsize=14, fontweight='bold')

# 差值标注
ax.annotate('', xy=(1, PQ_HANDSHAKE_US), xytext=(0, TRAD_HANDSHAKE_US),
            arrowprops=dict(arrowstyle='->', color='green', lw=2, 
                          connectionstyle='arc3,rad=0.2'))
ax.text(0.5, 130, f'+{OVERHEAD_US} μs\n(+47%)', ha='center', fontsize=12, 
        fontweight='bold', color='green')

ax.set_ylabel('Handshake Time (μs)', fontsize=12, fontweight='bold')
ax.set_title('Handshake Time Comparison\n(Zoomed View - Microsecond Scale)', fontsize=14, fontweight='bold')
ax.set_ylim(0, 180)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# 底部说明
ax.text(0.5, -0.15, f'Note: Total circuit setup time is {avg_duration_ms/1000:.1f}s. '
        f'The {OVERHEAD_US}μs overhead = {OVERHEAD_US/1000/avg_duration_ms*100*1000:.4f}% of total.',
        transform=ax.transAxes, ha='center', fontsize=10, style='italic')

plt.tight_layout()
plt.savefig(output_dir / 'handshake_only_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'handshake_only_comparison.pdf', bbox_inches='tight')
print("✓ handshake_only_comparison")
plt.close()

# 图3: 饼图展示时间占比
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 左：展示握手在总时间中的占比
handshake_ms = PQ_HANDSHAKE_US / 1000
network_ms = avg_duration_ms - handshake_ms
sizes = [network_ms, handshake_ms]
labels = [f'Network & Processing\n{network_ms/1000:.1f}s (99.9997%)', 
          f'PQ Handshake\n{handshake_ms*1000:.0f}μs (0.0003%)']
colors = ['#95a5a6', '#e74c3c']
explode = (0, 0.1)

axes[0].pie(sizes, explode=explode, labels=labels, colors=colors, autopct='',
            shadow=True, startangle=90)
axes[0].set_title('Time Distribution in Circuit Setup', fontsize=12, fontweight='bold')

# 右：握手时间内部对比
sizes2 = [TRAD_HANDSHAKE_US, OVERHEAD_US]
labels2 = [f'Base NTOR\n{TRAD_HANDSHAKE_US}μs (68%)', f'PQ Overhead\n{OVERHEAD_US}μs (32%)']
colors2 = ['#3498db', '#e74c3c']

axes[1].pie(sizes2, labels=labels2, colors=colors2, autopct='',
            shadow=True, startangle=90)
axes[1].set_title('PQ-NTOR Handshake Breakdown', fontsize=12, fontweight='bold')

plt.suptitle('PQ-NTOR Overhead Analysis', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(output_dir / 'time_distribution_pie.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'time_distribution_pie.pdf', bbox_inches='tight')
print("✓ time_distribution_pie")
plt.close()

print("\n新图表已生成！")
