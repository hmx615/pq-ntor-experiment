#!/bin/bash
# Phase 3运行脚本（带sudo）

cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c

echo "=========================================="
echo "Starting Phase 3 with sudo wrapper"
echo "=========================================="

# 确保清理旧的TC配置
sudo tc qdisc del dev lo root 2>/dev/null

# 使用sudo运行（整个程序在sudo环境下）
sudo -E LD_LIBRARY_PATH=/home/ccc/_oqs/lib ./phase3_sagin_network

echo ""
echo "=========================================="
echo "Phase 3 completed!"
echo "=========================================="
echo "Result file: phase3_sagin_cbt.csv"
