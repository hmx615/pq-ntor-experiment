#!/bin/bash

# SAGIN NOMA 3D可视化DEMO启动脚本
# 创建时间: 2025-11-14
# 用途: 在飞腾派或本地快速启动演示服务器

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PORT=${1:-8080}

echo "=========================================="
echo "  SAGIN NOMA 3D可视化DEMO"
echo "=========================================="
echo ""
echo "📁 工作目录: $SCRIPT_DIR"
echo "🌐 服务端口: $PORT"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    echo "   请安装: sudo apt install python3"
    exit 1
fi

echo "✅ Python3版本: $(python3 --version)"
echo ""

# 检查HTML文件是否存在
if [ ! -f "$SCRIPT_DIR/3d_globe_demo.html" ]; then
    echo "❌ 错误: 找不到 3d_globe_demo.html"
    exit 1
fi

echo "✅ DEMO文件已找到"
echo ""

# 获取本机IP地址
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "=========================================="
echo "  🚀 启动HTTP服务器..."
echo "=========================================="
echo ""
echo "本地访问:"
echo "  👉 http://localhost:$PORT/3d_globe_demo.html"
echo "  👉 http://127.0.0.1:$PORT/3d_globe_demo.html"
echo ""
echo "局域网访问:"
echo "  👉 http://$LOCAL_IP:$PORT/3d_globe_demo.html"
echo ""
echo "飞腾派访问 (如果在飞腾派上运行):"
echo "  👉 http://192.168.5.110:$PORT/3d_globe_demo.html"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=========================================="
echo ""

# 切换到demo目录
cd "$SCRIPT_DIR"

# 启动HTTP服务器
python3 -m http.server $PORT
