#!/usr/bin/env python3
"""
PQ-Tor SAGIN Performance Visualization
======================================

Generates multiple publication-quality PDF figures showing
PQ-Tor performance in SAGIN networks.

Author: Auto-generated
Date: 2025-11-10
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

# Configure matplotlib for publication-quality figures
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['pdf.fonttype'] = 42  # TrueType fonts for better PDF compatibility

# Color scheme for different network types
COLORS = {
    'baseline': '#2E7D32',  # Green
    'leo': '#1976D2',       # Blue
    'meo': '#F57C00',       # Orange
    'geo': '#C62828'        # Red
}

# Display names
NAMES = {
    'baseline': 'Baseline\n(Ground)',
    'leo': 'LEO\nSatellite',
    'meo': 'MEO\nSatellite',
    'geo': 'GEO\nSatellite'
}

def load_data():
    """Load and clean the experimental data"""
    try:
        # Read the file manually to handle the odd format
        data = []
        with open('realistic_results.csv', 'r') as f:
            lines = f.readlines()

        # Parse header
        header_line = [line for line in lines if line.startswith('#')][0]
        headers = header_line.strip('#').strip().split(',')

        # Parse data lines (skip header and "0" lines)
        for line in lines:
            line = line.strip()
            # Skip empty lines, comment lines, and "0" lines
            if not line or line.startswith('#') or line == '0':
                continue

            # Split and parse
            parts = line.split(',')
            if len(parts) >= 4:  # Config, Run, Time, Status minimum
                data.append({
                    'Config': parts[0].strip(),
                    'Run': int(parts[1].strip()),
                    'Time': float(parts[2].strip()),
                    'Status': parts[3].strip()
                })

        df = pd.DataFrame(data)
        print(f"Loaded {len(df)} data points")
        print(f"Configs: {df['Config'].unique()}")

        return df
    except FileNotFoundError:
        print("Error: realistic_results.csv not found!")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def calculate_statistics(df):
    """Calculate statistics for each configuration"""
    stats = []

    for config in ['baseline', 'leo', 'meo', 'geo']:
        config_data = df[df['Config'] == config]

        # Filter only successful runs for time statistics
        success_data = config_data[config_data['Status'] == 'SUCCESS']

        if len(success_data) > 0:
            stats.append({
                'config': config,
                'name': NAMES[config],
                'total_runs': len(config_data),
                'successful_runs': len(success_data),
                'timeout_runs': len(config_data[config_data['Status'] == 'TIMEOUT']),
                'timeout_rate': len(config_data[config_data['Status'] == 'TIMEOUT']) / len(config_data) * 100,
                'avg_time': success_data['Time'].mean(),
                'std_time': success_data['Time'].std(),
                'min_time': success_data['Time'].min(),
                'max_time': success_data['Time'].max(),
                'median_time': success_data['Time'].median(),
                'cv': success_data['Time'].std() / success_data['Time'].mean() * 100  # Coefficient of variation
            })

    return pd.DataFrame(stats)

def figure1_avg_construction_time(stats_df):
    """
    Figure 1: Average Circuit Construction Time
    Bar chart with error bars showing mean and standard deviation
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.arange(len(stats_df))
    width = 0.6

    bars = ax.bar(x, stats_df['avg_time'], width,
                   yerr=stats_df['std_time'],
                   capsize=5,
                   color=[COLORS[c] for c in stats_df['config']],
                   edgecolor='black',
                   linewidth=1.2,
                   alpha=0.8)

    # Customize
    ax.set_ylabel('Circuit Construction Time (seconds)', fontweight='bold')
    ax.set_xlabel('Network Configuration', fontweight='bold')
    ax.set_title('PQ-Tor Performance in SAGIN Networks:\nAverage Circuit Construction Time',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df['name'])
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on top of bars
    for i, (bar, row) in enumerate(zip(bars, stats_df.itertuples())):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + row.std_time + 1,
                f'{row.avg_time:.1f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Add legend showing what error bars represent
    ax.text(0.02, 0.98, 'Error bars: ±1 standard deviation',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_file = Path('figure1_circuit_construction_time.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def figure2_time_distribution(df):
    """
    Figure 2: Circuit Construction Time Distribution
    Box plots showing the distribution for each network type
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Prepare data for box plot (only successful runs)
    data_to_plot = []
    labels = []
    colors_list = []

    for config in ['baseline', 'leo', 'meo', 'geo']:
        config_data = df[(df['Config'] == config) & (df['Status'] == 'SUCCESS')]
        if len(config_data) > 0:
            data_to_plot.append(config_data['Time'].values)
            labels.append(NAMES[config])
            colors_list.append(COLORS[config])

    # Create box plot
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                    widths=0.6,
                    showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='red', markersize=6))

    # Color the boxes
    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Customize
    ax.set_ylabel('Circuit Construction Time (seconds)', fontweight='bold')
    ax.set_xlabel('Network Configuration', fontweight='bold')
    ax.set_title('PQ-Tor Performance in SAGIN Networks:\nCircuit Construction Time Distribution',
                 fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add legend
    ax.text(0.02, 0.98, 'Red diamond: mean\nOrange line: median',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_file = Path('figure2_time_distribution.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def figure3_timeout_analysis(stats_df):
    """
    Figure 3: Network Reliability - Timeout Rate Analysis
    Shows percentage of timeouts (network reliability metric)
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.arange(len(stats_df))
    width = 0.6

    bars = ax.bar(x, stats_df['timeout_rate'], width,
                   color=[COLORS[c] for c in stats_df['config']],
                   edgecolor='black',
                   linewidth=1.2,
                   alpha=0.8)

    # Customize
    ax.set_ylabel('Timeout Rate (%)', fontweight='bold')
    ax.set_xlabel('Network Configuration', fontweight='bold')
    ax.set_title('PQ-Tor Performance in SAGIN Networks:\nNetwork Reliability (Timeout Rate)',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df['name'])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, max(stats_df['timeout_rate']) * 1.3])

    # Add value labels
    for i, (bar, rate) in enumerate(zip(bars, stats_df['timeout_rate'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Add note
    ax.text(0.02, 0.98, 'Lower is better\nTimeout threshold: 90 seconds',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_file = Path('figure3_timeout_analysis.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def figure4_performance_overhead(stats_df):
    """
    Figure 4: Performance Overhead Compared to Baseline
    Shows how much slower each satellite network is compared to ground network
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Calculate overhead relative to baseline
    baseline_time = stats_df[stats_df['config'] == 'baseline']['avg_time'].values[0]

    # Exclude baseline from this plot
    satellite_stats = stats_df[stats_df['config'] != 'baseline'].copy()
    satellite_stats['overhead'] = ((satellite_stats['avg_time'] - baseline_time) / baseline_time) * 100

    x = np.arange(len(satellite_stats))
    width = 0.6

    bars = ax.bar(x, satellite_stats['overhead'], width,
                   color=[COLORS[c] for c in satellite_stats['config']],
                   edgecolor='black',
                   linewidth=1.2,
                   alpha=0.8)

    # Customize
    ax.set_ylabel('Performance Overhead (%)', fontweight='bold')
    ax.set_xlabel('Satellite Network Type', fontweight='bold')
    ax.set_title('PQ-Tor Performance in SAGIN Networks:\nPerformance Overhead vs. Baseline',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(satellite_stats['name'])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Baseline')

    # Add value labels
    for i, (bar, overhead) in enumerate(zip(bars, satellite_stats['overhead'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'+{overhead:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Add note
    ax.text(0.02, 0.98, f'Baseline time: {baseline_time:.1f}s\nOverhead = (Satellite - Baseline) / Baseline × 100%',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_file = Path('figure4_performance_overhead.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def figure5_time_variability(stats_df):
    """
    Figure 5: Performance Consistency - Coefficient of Variation
    Shows how consistent the performance is (lower CV = more consistent)
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.arange(len(stats_df))
    width = 0.6

    bars = ax.bar(x, stats_df['cv'], width,
                   color=[COLORS[c] for c in stats_df['config']],
                   edgecolor='black',
                   linewidth=1.2,
                   alpha=0.8)

    # Customize
    ax.set_ylabel('Coefficient of Variation (%)', fontweight='bold')
    ax.set_xlabel('Network Configuration', fontweight='bold')
    ax.set_title('PQ-Tor Performance in SAGIN Networks:\nPerformance Consistency',
                 fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df['name'])
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels
    for i, (bar, cv) in enumerate(zip(bars, stats_df['cv'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                f'{cv:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Add note
    ax.text(0.02, 0.98, 'Lower is better (more consistent)\nCV = (Std Dev / Mean) × 100%',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_file = Path('figure5_performance_consistency.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def figure6_comprehensive_comparison(stats_df):
    """
    Figure 6: Comprehensive Performance Comparison
    Multi-metric comparison showing Time, Timeout Rate, and CV
    """
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    x = np.arange(len(stats_df))
    width = 0.6

    # Subplot 1: Average Time
    ax1 = axes[0]
    bars1 = ax1.bar(x, stats_df['avg_time'], width,
                    color=[COLORS[c] for c in stats_df['config']],
                    edgecolor='black', linewidth=1.2, alpha=0.8)
    ax1.set_ylabel('Time (s)', fontweight='bold')
    ax1.set_title('Construction Time', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(stats_df['name'])
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, val in zip(bars1, stats_df['avg_time']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)

    # Subplot 2: Timeout Rate
    ax2 = axes[1]
    bars2 = ax2.bar(x, stats_df['timeout_rate'], width,
                    color=[COLORS[c] for c in stats_df['config']],
                    edgecolor='black', linewidth=1.2, alpha=0.8)
    ax2.set_ylabel('Timeout Rate (%)', fontweight='bold')
    ax2.set_title('Network Reliability', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(stats_df['name'])
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, val in zip(bars2, stats_df['timeout_rate']):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.0f}%', ha='center', va='bottom', fontsize=9)

    # Subplot 3: Coefficient of Variation
    ax3 = axes[2]
    bars3 = ax3.bar(x, stats_df['cv'], width,
                    color=[COLORS[c] for c in stats_df['config']],
                    edgecolor='black', linewidth=1.2, alpha=0.8)
    ax3.set_ylabel('CV (%)', fontweight='bold')
    ax3.set_title('Performance Consistency', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(stats_df['name'])
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, val in zip(bars3, stats_df['cv']):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

    fig.suptitle('PQ-Tor Performance in SAGIN Networks: Comprehensive Comparison',
                 fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()

    # Save
    output_file = Path('figure6_comprehensive_comparison.pdf')
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")

    plt.close()

def main():
    """Main execution function"""
    print("=" * 70)
    print("PQ-Tor SAGIN Performance Visualization")
    print("Generating Publication-Quality Figures (PDF)")
    print("=" * 70)
    print()

    # Load data
    print("Loading data...")
    df = load_data()
    print()

    # Calculate statistics
    print("Calculating statistics...")
    stats_df = calculate_statistics(df)
    print(f"Statistics calculated for {len(stats_df)} configurations")
    print()

    # Print summary table
    print("Summary Statistics:")
    print("-" * 70)
    print(f"{'Config':<12} {'Avg Time':>10} {'Std Dev':>10} {'Timeout':>10} {'CV':>10}")
    print("-" * 70)
    for _, row in stats_df.iterrows():
        print(f"{row['config']:<12} {row['avg_time']:>9.2f}s {row['std_time']:>9.2f}s "
              f"{row['timeout_rate']:>9.1f}% {row['cv']:>9.2f}%")
    print("-" * 70)
    print()

    # Generate figures
    print("Generating figures...")
    print()

    figure1_avg_construction_time(stats_df)
    figure2_time_distribution(df)
    figure3_timeout_analysis(stats_df)
    figure4_performance_overhead(stats_df)
    figure5_time_variability(stats_df)
    figure6_comprehensive_comparison(stats_df)

    print()
    print("=" * 70)
    print("✅ All figures generated successfully!")
    print("=" * 70)
    print()
    print("Generated files:")
    print("  1. figure1_circuit_construction_time.pdf")
    print("  2. figure2_time_distribution.pdf")
    print("  3. figure3_timeout_analysis.pdf")
    print("  4. figure4_performance_overhead.pdf")
    print("  5. figure5_performance_consistency.pdf")
    print("  6. figure6_comprehensive_comparison.pdf")
    print()
    print("All figures are publication-ready and can be used directly in papers.")
    print()

if __name__ == '__main__':
    main()
