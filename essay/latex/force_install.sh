#!/bin/bash
# 强制安装脚本（跳过等待，直接处理）

set -e

echo "========================================"
echo "强制安装 LaTeX 脚本"
echo "========================================"
echo ""

# 配置代理
export http_proxy=http://192.168.64.1:7890
export https_proxy=http://192.168.64.1:7890
export all_proxy=http://192.168.64.1:7890

echo "步骤 1: 强制终止所有 apt 进程..."
sudo killall apt-get 2>/dev/null || true
sudo killall apt 2>/dev/null || true
sudo killall unattended-upgrade 2>/dev/null || true

echo "等待 5 秒..."
sleep 5

echo ""
echo "步骤 2: 清理 apt 锁定文件..."
sudo rm -f /var/lib/apt/lists/lock
sudo rm -f /var/cache/apt/archives/lock
sudo rm -f /var/lib/dpkg/lock*

echo ""
echo "步骤 3: 重新配置 dpkg..."
sudo dpkg --configure -a

echo ""
echo "步骤 4: 配置 apt 代理..."
sudo tee /etc/apt/apt.conf.d/95proxies > /dev/null << EOF
Acquire::http::Proxy "http://192.168.64.1:7890";
Acquire::https::Proxy "http://192.168.64.1:7890";
EOF

echo "✅ apt 代理已配置"

echo ""
echo "步骤 5: 更新软件包列表（使用代理）..."
sudo apt-get update

echo ""
echo "步骤 6: 安装 LaTeX..."
sudo apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-bibtex-extra

echo ""
echo "✅ LaTeX 安装完成！"
pdflatex --version | head -1

echo ""
echo "步骤 7: 编译论文..."
cd "$(dirname "$0")"

rm -f *.aux *.log *.out *.bbl *.blg sections/*.aux

echo "编译中（1/3）..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true

echo "编译中（2/3）..."
bibtex main > /dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true

echo "编译中（3/3）..."
pdflatex -interaction=nonstopmode main.tex

if [ -f main.pdf ]; then
    echo ""
    echo "========================================"
    echo "✅✅✅ 成功！✅✅✅"
    echo "========================================"
    echo ""
    ls -lh main.pdf
    echo ""
    echo "打开 PDF:"
    echo "  explorer.exe main.pdf"
    echo ""
    explorer.exe main.pdf 2>/dev/null || true
else
    echo "❌ 编译失败"
    exit 1
fi
