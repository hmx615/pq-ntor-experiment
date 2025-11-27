#!/bin/bash
# LaTeX 安装和编译脚本（支持代理）
# 创建日期: 2025-11-27

set -e  # 遇到错误立即退出

echo "========================================"
echo "LaTeX 自动安装和编译脚本（代理模式）"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo -e "${BLUE}步骤 0/5: 配置代理...${NC}"

# 设置代理
export http_proxy=http://192.168.64.1:7890
export https_proxy=http://192.168.64.1:7890
export all_proxy=http://192.168.64.1:7890
export NO_PROXY="localhost,127.0.0.1,gaccode.com"
export no_proxy="localhost,127.0.0.1,gaccode.com"

echo "✅ 代理已配置:"
echo "   http_proxy=$http_proxy"
echo "   https_proxy=$https_proxy"

# 测试代理连接
echo ""
echo "测试代理连接..."
if curl -I --connect-timeout 5 -x $http_proxy https://www.google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 代理连接正常${NC}"
else
    echo -e "${YELLOW}⚠️  代理连接测试失败，但继续尝试...${NC}"
fi

echo ""
echo -e "${BLUE}步骤 1/5: 检查 LaTeX 是否已安装...${NC}"
if command -v pdflatex &> /dev/null; then
    echo -e "${GREEN}✅ LaTeX 已安装${NC}"
    pdflatex --version | head -1
    LATEX_INSTALLED=1
else
    echo -e "${YELLOW}⚠️  LaTeX 未安装${NC}"
    LATEX_INSTALLED=0
fi

if [ $LATEX_INSTALLED -eq 0 ]; then
    echo ""
    echo -e "${BLUE}步骤 2/5: 等待 apt 进程完成...${NC}"

    # 等待其他 apt 进程完成
    if ps aux | grep -v grep | grep -E "apt-get|apt.systemd" > /dev/null; then
        echo "⏳ 检测到系统正在自动更新，等待完成..."
        COUNT=0
        while ps aux | grep -v grep | grep -E "apt-get|apt.systemd" > /dev/null; do
            echo -n "."
            sleep 5
            COUNT=$((COUNT + 1))
            if [ $((COUNT % 6)) -eq 0 ]; then
                echo ""
                echo "   已等待 $((COUNT * 5)) 秒..."
            fi

            # 超过3分钟提示
            if [ $COUNT -gt 36 ]; then
                echo ""
                echo -e "${YELLOW}⚠️  等待时间较长，您可以按 Ctrl+C 退出，稍后重试${NC}"
                COUNT=0
            fi
        done
        echo ""
        echo -e "${GREEN}✅ apt 进程已完成${NC}"
    else
        echo "✅ 没有其他 apt 进程"
    fi

    echo ""
    echo -e "${BLUE}步骤 3/5: 更新软件包列表（使用代理）...${NC}"

    # 配置 apt 使用代理
    echo "配置 apt 代理..."
    sudo tee /etc/apt/apt.conf.d/95proxies > /dev/null << EOF
Acquire::http::Proxy "http://192.168.64.1:7890";
Acquire::https::Proxy "http://192.168.64.1:7890";
EOF

    echo "正在更新软件包列表（这可能需要几分钟）..."
    sudo apt-get update || {
        echo -e "${YELLOW}⚠️  apt-get update 失败，尝试清理缓存...${NC}"
        sudo rm -rf /var/lib/apt/lists/*
        sudo apt-get update
    }

    echo ""
    echo -e "${BLUE}步骤 4/5: 安装 LaTeX（约500MB，5-10分钟）...${NC}"
    echo "这将安装以下软件包:"
    echo "  - texlive-latex-base"
    echo "  - texlive-latex-extra"
    echo "  - texlive-fonts-recommended"
    echo "  - texlive-fonts-extra"
    echo "  - texlive-bibtex-extra"
    echo ""

    sudo apt-get install -y \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-bibtex-extra

    echo ""
    echo -e "${GREEN}✅ LaTeX 安装完成！${NC}"
    pdflatex --version | head -1
else
    echo -e "${BLUE}步骤 2-4/5: 跳过安装（已安装）${NC}"
fi

echo ""
echo -e "${BLUE}步骤 5/5: 编译 LaTeX 文档...${NC}"
echo "这可能需要 1-2 分钟，请耐心等待..."
echo ""

# 清理旧文件
echo "清理旧的编译文件..."
rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
rm -f sections/*.aux

# 第一次编译
echo -e "${YELLOW}[1/4] 第一次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > compile_log_1.txt 2>&1 || {
    echo -e "${YELLOW}⚠️  第一次编译有警告（正常）${NC}"
}

# 编译参考文献
if command -v bibtex &> /dev/null; then
    echo -e "${YELLOW}[2/4] 编译参考文献...${NC}"
    bibtex main > bibtex_log.txt 2>&1 || {
        echo -e "${YELLOW}⚠️  参考文献编译有警告${NC}"
    }
else
    echo -e "${YELLOW}⚠️  bibtex 未安装，跳过参考文献${NC}"
fi

# 第二次编译
echo -e "${YELLOW}[3/4] 第二次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > compile_log_2.txt 2>&1 || {
    echo -e "${YELLOW}⚠️  第二次编译有警告${NC}"
}

# 第三次编译（确保所有引用正确）
echo -e "${YELLOW}[4/4] 第三次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > compile_log_3.txt 2>&1 || {
    echo -e "${YELLOW}⚠️  第三次编译有警告${NC}"
}

echo ""
echo -e "${BLUE}验证编译结果...${NC}"

if [ -f main.pdf ]; then
    FILE_SIZE=$(ls -lh main.pdf | awk '{print $5}')
    echo -e "${GREEN}✅✅✅ 编译成功！✅✅✅${NC}"
    echo ""
    echo "PDF 文件已生成:"
    echo "  位置: $(pwd)/main.pdf"
    echo "  大小: $FILE_SIZE"
    echo ""

    # 统计页数
    if command -v pdfinfo &> /dev/null; then
        PAGES=$(pdfinfo main.pdf 2>/dev/null | grep Pages | awk '{print $2}')
        echo "  页数: $PAGES 页"
    fi

    echo ""
    echo "========================================"
    echo "下一步："
    echo "========================================"
    echo ""
    echo "1. 在 WSL 中用 Windows 打开 PDF:"
    echo "   explorer.exe main.pdf"
    echo ""
    echo "2. 或复制到 Windows 桌面:"
    echo "   cp main.pdf /mnt/c/Users/\$(whoami)/Desktop/ 2>/dev/null || \\"
    echo "   cp main.pdf /mnt/c/Users/你的用户名/Desktop/"
    echo ""
    echo "3. 查看详细编译日志（如果有问题）:"
    echo "   less main.log"
    echo ""

    # 自动在 Windows 中打开 PDF（如果可能）
    echo -e "${YELLOW}尝试自动打开 PDF...${NC}"
    if explorer.exe main.pdf 2>/dev/null; then
        echo -e "${GREEN}✅ PDF 已在 Windows 中打开${NC}"
    else
        echo -e "${YELLOW}⚠️  无法自动打开，请手动打开 main.pdf${NC}"
    fi

else
    echo -e "${RED}❌ 编译失败！PDF 文件未生成${NC}"
    echo ""
    echo "请查看错误日志："
    echo "  tail -50 main.log"
    echo "或者:"
    echo "  cat compile_log_3.txt"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "编译完成！🎉"
echo "========================================"
echo ""
echo "提示: 如果要重新编译，直接运行:"
echo "  ./compile.sh quick"
