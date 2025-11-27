#!/bin/bash
# 快速编译脚本（假设 LaTeX 已安装）

cd "$(dirname "$0")"

echo "快速编译中..."

# 清理
rm -f *.aux *.log *.out *.bbl *.blg sections/*.aux

# 编译
pdflatex -interaction=nonstopmode main.tex && \
echo "✅ 编译完成！" && \
ls -lh main.pdf && \
explorer.exe main.pdf 2>/dev/null

echo ""
echo "PDF 位置: $(pwd)/main.pdf"
