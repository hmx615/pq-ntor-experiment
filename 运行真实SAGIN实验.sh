#!/bin/bash
# 快速运行真实化的 SAGIN 实验
# 使用修改后的参数（更高的丢包率和抖动）

set -e

echo "========================================"
echo "PQ-Tor SAGIN 真实化实验"
echo "========================================"
echo ""

# 检查是否在正确的目录
if [ ! -d "/home/ccc/pq-ntor-experiment" ]; then
    echo "错误: 未找到项目目录"
    exit 1
fi

echo "1. 显示新参数设置..."
echo ""
echo "卫星链路参数（已真实化）："
echo "  LEO: 丢包率 3.5%, 抖动 12ms  (Starlink级别)"
echo "  MEO: 丢包率 6.5%, 抖动 25ms  (O3b级别)"
echo "  GEO: 丢包率 10.0%, 抖动 40ms (传统卫星)"
echo ""
echo "测试次数: 每个配置 10 次（原 3 次）"
echo ""

# 备份旧结果
OLD_RESULTS="/home/ccc/pq-ntor-experiment/results/sagin"
if [ -d "$OLD_RESULTS" ] && [ "$(ls -A $OLD_RESULTS 2>/dev/null)" ]; then
    BACKUP_DIR="${OLD_RESULTS}_backup_$(date +%Y%m%d_%H%M%S)"
    echo "2. 备份旧结果到: $BACKUP_DIR"
    cp -r "$OLD_RESULTS" "$BACKUP_DIR"
    echo "   ✓ 备份完成"
    echo ""
fi

echo "3. 清理旧数据..."
rm -rf "$OLD_RESULTS"/*
echo "   ✓ 清理完成"
echo ""

echo "4. 开始运行实验..."
echo "   预计耗时: ~50 分钟"
echo "   (Baseline: 10min, LEO: 11min, MEO: 12min, GEO: 14min + 冷却)"
echo ""
echo "按 Ctrl+C 可随时中止"
echo ""

sleep 3

# 运行实验
cd /home/ccc/pq-ntor-experiment/sagin-experiments
sudo ./run_sagin_experiments.sh

echo ""
echo "========================================"
echo "实验完成！"
echo "========================================"
echo ""
echo "查看结果:"
echo "  1. 原始数据: cat $OLD_RESULTS/raw_results.csv"
echo "  2. 汇总统计: cat $OLD_RESULTS/summary.csv"
echo "  3. 可视化图: ls -lh $OLD_RESULTS/figures/"
echo ""
echo "预期结果:"
echo "  - Baseline: 98-100% 成功率"
echo "  - LEO:      85-92% 成功率"
echo "  - MEO:      75-85% 成功率"
echo "  - GEO:      65-78% 成功率"
echo ""
