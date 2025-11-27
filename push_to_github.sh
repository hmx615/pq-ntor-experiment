#!/bin/bash

echo "=========================================="
echo "PQ-NTOR SAGIN 项目推送到 GitHub"
echo "=========================================="
echo ""

# 检查是否已有 remote
if git remote get-url origin &>/dev/null; then
    echo "✓ Remote 'origin' 已配置"
    git remote -v
else
    echo "请先在 GitHub 创建仓库，然后执行："
    echo ""
    echo "git remote add origin https://github.com/YOUR_USERNAME/pq-ntor-experiment.git"
    echo ""
    exit 1
fi

echo ""
echo "准备推送到 GitHub..."
echo ""

# 推送到 GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 推送成功！"
    echo "=========================================="
    echo ""
    echo "你的项目已上传到 GitHub！"
    echo ""
    echo "下一步："
    echo "1. 在 GitHub 上查看你的仓库"
    echo "2. 添加 Topics 标签: post-quantum, tor, sagin, satellite"
    echo "3. 考虑添加 LICENSE 文件"
    echo ""
else
    echo ""
    echo "❌ 推送失败"
    echo "可能的原因："
    echo "1. 尚未配置 GitHub 认证"
    echo "2. 仓库 URL 不正确"
    echo "3. 网络连接问题"
    echo ""
    echo "解决方法："
    echo "首次推送需要 GitHub 认证，建议使用："
    echo "- Personal Access Token (推荐)"
    echo "- SSH Key"
    echo ""
fi
