#!/bin/bash
# configure_node.sh - 配置克隆后的飞腾派节点
#
# 用途: 在SD卡克隆后，为每个节点设置唯一的主机名和IP地址
# 使用: sudo ./configure_node.sh <节点编号 1-5>

set -e

if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

if [ -z "$1" ]; then
    echo "用法: sudo ./configure_node.sh <节点编号 1-5>"
    echo ""
    echo "示例:"
    echo "  sudo ./configure_node.sh 1  # 配置为派1 (Directory, 192.168.1.10)"
    echo "  sudo ./configure_node.sh 2  # 配置为派2 (Guard, 192.168.1.11)"
    echo "  sudo ./configure_node.sh 3  # 配置为派3 (Middle, 192.168.1.12)"
    echo "  sudo ./configure_node.sh 4  # 配置为派4 (Exit, 192.168.1.13)"
    echo "  sudo ./configure_node.sh 5  # 配置为派5 (Client, 192.168.1.14)"
    exit 1
fi

NODE_NUM=$1

# 验证节点编号
if [ "$NODE_NUM" -lt 1 ] || [ "$NODE_NUM" -gt 5 ]; then
    echo "❌ 节点编号必须在 1-5 之间"
    exit 1
fi

# 节点配置映射
case $NODE_NUM in
    1)
        HOSTNAME="phytiumpi-dir"
        IP="192.168.1.10"
        ROLE="Directory + HTTP Server"
        ;;
    2)
        HOSTNAME="phytiumpi-guard"
        IP="192.168.1.11"
        ROLE="Guard Relay"
        ;;
    3)
        HOSTNAME="phytiumpi-middle"
        IP="192.168.1.12"
        ROLE="Middle Relay"
        ;;
    4)
        HOSTNAME="phytiumpi-exit"
        IP="192.168.1.13"
        ROLE="Exit Relay"
        ;;
    5)
        HOSTNAME="phytiumpi-client"
        IP="192.168.1.14"
        ROLE="Client"
        ;;
esac

echo "======================================"
echo "  飞腾派节点配置脚本"
echo "======================================"
echo ""
echo "节点编号: $NODE_NUM"
echo "主机名:   $HOSTNAME"
echo "IP地址:   $IP"
echo "角色:     $ROLE"
echo ""
read -p "确认配置此节点？ [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消配置"
    exit 0
fi

# 1. 设置主机名
echo ""
echo "[1/4] 设置主机名为 $HOSTNAME ..."
hostnamectl set-hostname $HOSTNAME
echo "      ✅ 主机名已设置"

# 2. 配置静态IP（假设使用netplan）
echo ""
echo "[2/4] 配置静态IP $IP ..."

NETPLAN_FILE="/etc/netplan/01-netcfg.yaml"

# 备份原配置
if [ -f "$NETPLAN_FILE" ]; then
    cp "$NETPLAN_FILE" "${NETPLAN_FILE}.backup"
fi

# 创建新配置
cat > "$NETPLAN_FILE" << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: no
      addresses: [$IP/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 114.114.114.114]
EOF

echo "      ✅ 网络配置已更新"

# 3. 重新生成SSH密钥
echo ""
echo "[3/4] 重新生成SSH主机密钥..."
rm -f /etc/ssh/ssh_host_*
ssh-keygen -A
echo "      ✅ SSH密钥已重新生成"

# 4. 更新 /etc/hosts
echo ""
echo "[4/4] 更新 /etc/hosts ..."
cat > /etc/hosts << EOF
127.0.0.1       localhost
127.0.1.1       $HOSTNAME

# PQ-Tor 网络节点
192.168.1.10    phytiumpi-dir      # Directory + HTTP
192.168.1.11    phytiumpi-guard    # Guard Relay
192.168.1.12    phytiumpi-middle   # Middle Relay
192.168.1.13    phytiumpi-exit     # Exit Relay
192.168.1.14    phytiumpi-client   # Client

# IPv6
::1             localhost ip6-localhost ip6-loopback
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters
EOF
echo "      ✅ /etc/hosts 已更新"

echo ""
echo "======================================"
echo "  ✅ 配置完成！"
echo "======================================"
echo ""
echo "节点信息:"
echo "  主机名: $HOSTNAME"
echo "  IP地址: $IP"
echo "  角色:   $ROLE"
echo ""
echo "下一步:"
echo "  1. 运行: sudo netplan apply"
echo "  2. 运行: sudo reboot"
echo "  3. 重启后验证: ip addr show"
echo ""
