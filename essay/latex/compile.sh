#!/bin/bash
# LaTeX 编译脚本
# 自动编译 PQ-NTOR SAGIN 论文

set -e  # 遇到错误立即退出

echo "========================================"
echo "PQ-NTOR SAGIN 论文编译脚本"
echo "========================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 LaTeX 是否安装
check_latex() {
    if ! command -v pdflatex &> /dev/null; then
        echo -e "${RED}错误: pdflatex 未安装${NC}"
        echo ""
        echo "请安装 TeX Live:"
        echo "  Ubuntu/Debian: sudo apt-get install texlive-full"
        echo "  或轻量级版本: sudo apt-get install texlive-latex-base texlive-latex-extra"
        exit 1
    fi

    if ! command -v bibtex &> /dev/null; then
        echo -e "${YELLOW}警告: bibtex 未安装，将无法生成参考文献${NC}"
    fi
}

# 清理临时文件
clean() {
    echo -e "${YELLOW}清理临时文件...${NC}"
    rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
    rm -f sections/*.aux
    echo -e "${GREEN}清理完成${NC}"
}

# 完整编译（包括参考文献）
compile_full() {
    echo -e "${YELLOW}开始完整编译...${NC}"

    # 第一次编译
    echo "第一次 pdflatex 编译..."
    pdflatex -interaction=nonstopmode main.tex || true

    # 编译参考文献
    if command -v bibtex &> /dev/null; then
        echo "编译参考文献..."
        bibtex main || true
    fi

    # 第二次编译（解决引用）
    echo "第二次 pdflatex 编译..."
    pdflatex -interaction=nonstopmode main.tex || true

    # 第三次编译（确保所有引用正确）
    echo "第三次 pdflatex 编译..."
    pdflatex -interaction=nonstopmode main.tex

    echo -e "${GREEN}编译完成！${NC}"

    if [ -f main.pdf ]; then
        echo -e "${GREEN}PDF 文件已生成: main.pdf${NC}"
        ls -lh main.pdf
    else
        echo -e "${RED}错误: PDF 文件生成失败${NC}"
        exit 1
    fi
}

# 快速编译（仅一次，用于快速预览）
compile_quick() {
    echo -e "${YELLOW}快速编译模式...${NC}"
    pdflatex -interaction=nonstopmode main.tex

    if [ -f main.pdf ]; then
        echo -e "${GREEN}快速编译完成！${NC}"
        ls -lh main.pdf
    else
        echo -e "${RED}错误: PDF 文件生成失败${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "使用方法:"
    echo "  ./compile.sh [选项]"
    echo ""
    echo "选项:"
    echo "  full     完整编译（包括参考文献，默认）"
    echo "  quick    快速编译（仅一次，用于预览）"
    echo "  clean    清理临时文件"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./compile.sh           # 完整编译"
    echo "  ./compile.sh quick     # 快速编译"
    echo "  ./compile.sh clean     # 清理文件"
}

# 主逻辑
main() {
    cd "$(dirname "$0")"  # 切换到脚本所在目录

    check_latex

    case "${1:-full}" in
        full)
            compile_full
            ;;
        quick)
            compile_quick
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
