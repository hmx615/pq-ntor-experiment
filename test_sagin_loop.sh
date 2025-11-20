#!/bin/bash
# 简化测试脚本 - 测试循环是否工作

set -e

echo "开始循环测试..."
echo "预期运行3次"

for i in {1..3}; do
    echo "[测试 $i/3] 开始..."
    sleep 2
    echo "[测试 $i/3] 完成"
done

echo "所有测试完成！"
