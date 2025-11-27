#!/bin/bash
# 修复 apt 源问题并安装 LaTeX

set -e

echo "========================================"
echo "修复 apt 源并安装 LaTeX"
echo "========================================"
echo ""

# 配置代理
export http_proxy=http://192.168.64.1:7890
export https_proxy=http://192.168.64.1:7890

echo "步骤 1: 清理问题..."
sudo killall apt-get 2>/dev/null || true
sudo killall apt 2>/dev/null || true
sleep 3

sudo rm -f /var/lib/apt/lists/lock
sudo rm -f /var/cache/apt/archives/lock
sudo rm -f /var/lib/dpkg/lock*

echo ""
echo "步骤 2: 禁用有问题的 Google Cloud 源..."

# 备份并禁用 Google Cloud 源
if [ -f /etc/apt/sources.list.d/google-cloud-sdk.list ]; then
    sudo mv /etc/apt/sources.list.d/google-cloud-sdk.list \
            /etc/apt/sources.list.d/google-cloud-sdk.list.disabled 2>/dev/null || true
    echo "✅ 已禁用 Google Cloud 源"
fi

echo ""
echo "步骤 3: 临时禁用代理进行 apt 更新..."
echo "（Ubuntu 官方源不需要代理）"

# 移除 apt 代理配置
sudo rm -f /etc/apt/apt.conf.d/95proxies

# 不使用代理更新
echo "更新软件包列表（不使用代理）..."
sudo http_proxy= https_proxy= apt-get update

echo ""
echo "步骤 4: 安装 LaTeX（不使用代理）..."
echo "这将安装约 500MB 的软件包，可能需要 5-10 分钟"
echo ""

sudo http_proxy= https_proxy= apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-bibtex-extra

echo ""
echo "✅ LaTeX 安装完成！"
pdflatex --version | head -1

echo ""
echo "步骤 5: 编译论文..."
cd "$(dirname "$0")"

# 清理旧文件
rm -f *.aux *.log *.out *.bbl *.blg sections/*.aux

echo "编译第 1 遍..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true

echo "编译参考文献..."
bibtex main > /dev/null 2>&1 || true

echo "编译第 2 遍..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true

echo "编译第 3 遍（最终）..."
pdflatex -interaction=nonstopmode main.tex

if [ -f main.pdf ]; then
    FILE_SIZE=$(ls -lh main.pdf | awk '{print $5}')
    echo ""
    echo "========================================"
    echo "✅✅✅ 成功！PDF 已生成 ✅✅✅"
    echo "========================================"
    echo ""
    echo "PDF 文件信息:"
    echo "  位置: $(pwd)/main.pdf"
    echo "  大小: $FILE_SIZE"
    echo ""

    # 尝试打开 PDF
    echo "正在打开 PDF..."
    if explorer.exe main.pdf 2>/dev/null; then
        echo "✅ PDF 已在 Windows 中打开"
    else
        echo "请手动打开: $(pwd)/main.pdf"
    fi

    echo ""
    echo "========================================"
    echo "完成！🎉"
    echo "========================================"
else
    echo ""
    echo "❌ 编译失败，PDF 未生成"
    echo "查看错误日志: less main.log"
    exit 1
fi
