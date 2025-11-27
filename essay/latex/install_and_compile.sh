#!/bin/bash
# LaTeX 安装和编译一键脚本
# 创建日期: 2025-11-27

set -e  # 遇到错误立即退出

echo "========================================"
echo "LaTeX 自动安装和编译脚本"
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

echo -e "${BLUE}步骤 1/4: 检查 LaTeX 是否已安装...${NC}"
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
    echo -e "${BLUE}步骤 2/4: 安装 LaTeX...${NC}"
    echo "这将安装约 500MB 的软件包，可能需要 5-10 分钟"
    echo ""

    echo "正在更新软件包列表..."
    sudo apt-get update

    echo ""
    echo "正在安装 LaTeX（轻量级版本）..."
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
    echo -e "${BLUE}步骤 2/4: 跳过安装（已安装）${NC}"
fi

echo ""
echo -e "${BLUE}步骤 3/4: 编译 LaTeX 文档...${NC}"
echo "这可能需要 1-2 分钟，请耐心等待..."
echo ""

# 清理旧文件
echo "清理旧的编译文件..."
rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
rm -f sections/*.aux

# 第一次编译
echo -e "${YELLOW}[1/4] 第一次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️  第一次编译有警告（正常）${NC}"
}

# 编译参考文献
if command -v bibtex &> /dev/null; then
    echo -e "${YELLOW}[2/4] 编译参考文献...${NC}"
    bibtex main > /dev/null 2>&1 || {
        echo -e "${YELLOW}⚠️  参考文献编译有警告（可能是因为占位符）${NC}"
    }
else
    echo -e "${YELLOW}⚠️  bibtex 未安装，跳过参考文献${NC}"
fi

# 第二次编译
echo -e "${YELLOW}[3/4] 第二次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️  第二次编译有警告${NC}"
}

# 第三次编译（确保所有引用正确）
echo -e "${YELLOW}[4/4] 第三次 pdflatex 编译...${NC}"
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️  第三次编译有警告${NC}"
}

echo ""
echo -e "${BLUE}步骤 4/4: 验证编译结果...${NC}"

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
    echo "   cp main.pdf /mnt/c/Users/你的用户名/Desktop/"
    echo ""
    echo "3. 查看详细编译日志（如果有问题）:"
    echo "   less main.log"
    echo ""

    # 自动在 Windows 中打开 PDF（如果可能）
    echo -e "${YELLOW}尝试自动打开 PDF...${NC}"
    explorer.exe main.pdf 2>/dev/null && echo -e "${GREEN}✅ PDF 已在 Windows 中打开${NC}" || echo -e "${YELLOW}⚠️  无法自动打开，请手动打开${NC}"

else
    echo -e "${RED}❌ 编译失败！PDF 文件未生成${NC}"
    echo ""
    echo "请查看错误日志："
    echo "  tail -50 main.log"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "编译完成！🎉"
echo "========================================"
