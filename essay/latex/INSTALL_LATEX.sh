#!/bin/bash
# 自动安装 LaTeX 环境

echo "========================================"
echo "LaTeX 环境自动安装脚本"
echo "========================================"

# 检查是否有 sudo 权限
if ! sudo -v; then
    echo "错误: 需要 sudo 权限"
    exit 1
fi

echo "正在更新软件包列表..."
sudo apt-get update

echo ""
echo "选择安装类型:"
echo "  1) 轻量级安装 (~500MB, 推荐)"
echo "  2) 完整安装 (~5GB)"
read -p "请选择 [1/2]: " choice

case $choice in
    1)
        echo "开始轻量级安装..."
        sudo apt-get install -y \
            texlive-latex-base \
            texlive-latex-extra \
            texlive-fonts-recommended \
            texlive-fonts-extra
        ;;
    2)
        echo "开始完整安装（这可能需要较长时间）..."
        sudo apt-get install -y texlive-full
        ;;
    *)
        echo "无效选择，退出"
        exit 1
        ;;
esac

echo ""
echo "验证安装..."
if command -v pdflatex &> /dev/null; then
    echo "✅ pdflatex 安装成功"
    pdflatex --version | head -1
else
    echo "❌ pdflatex 安装失败"
    exit 1
fi

if command -v bibtex &> /dev/null; then
    echo "✅ bibtex 安装成功"
else
    echo "⚠️  bibtex 未安装（可选）"
fi

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "现在可以运行: ./compile.sh full"
