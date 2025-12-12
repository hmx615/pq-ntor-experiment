#!/bin/bash
# 配置sudo无密码（仅用于Phase 3测试）

echo "========================================================================"
echo "⚙️  配置sudo无密码 - 用于Phase 3自动化测试"
echo "========================================================================"
echo ""
echo "⚠️  警告: 此脚本会配置sudo无密码权限"
echo "   仅建议在测试环境中使用"
echo ""
echo "将配置以下命令无需密码:"
echo "  - tc (流量控制工具)"
echo "  - modprobe (内核模块加载)"
echo ""
read -p "是否继续? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

echo ""
echo "请输入sudo密码以配置无密码权限..."

# 创建sudoers.d配置文件
sudo bash -c "cat > /etc/sudoers.d/phase3-testing <<EOF
# Phase 3 SAGIN Network Testing - Passwordless sudo for tc and modprobe
# Created: $(date)
# User: $USER

$USER ALL=(ALL) NOPASSWD: /usr/sbin/tc
$USER ALL=(ALL) NOPASSWD: /usr/sbin/modprobe
$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
EOF"

# 设置正确的权限
sudo chmod 0440 /etc/sudoers.d/phase3-testing

# 验证配置
if sudo visudo -c -f /etc/sudoers.d/phase3-testing > /dev/null 2>&1; then
    echo ""
    echo "========================================================================"
    echo "✅ 配置成功!"
    echo "========================================================================"
    echo ""
    echo "已配置无密码sudo权限:"
    cat /etc/sudoers.d/phase3-testing
    echo ""
    echo "🧪 测试无密码sudo..."
    if sudo -n tc -Version > /dev/null 2>&1; then
        echo "✅ tc命令可以无密码使用"
    else
        echo "⚠️  tc命令仍需要密码 - 可能需要注销重新登录"
    fi
    echo ""
    echo "🚀 现在可以运行Phase 3测试:"
    echo "   cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
    echo "   sudo ./run_phase3_with_sudo.sh"
    echo ""
    echo "⚠️  测试完成后如需撤销配置:"
    echo "   sudo rm /etc/sudoers.d/phase3-testing"
    echo ""
else
    echo ""
    echo "❌ 配置失败! sudoers语法错误"
    sudo rm /etc/sudoers.d/phase3-testing
    exit 1
fi
