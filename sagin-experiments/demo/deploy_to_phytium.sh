#!/bin/bash

# 部署3D DEMO到飞腾派
# 飞腾派地址: 192.168.5.110
# 用户名/密码: user/user

PHYTIUM_IP="192.168.5.110"
PHYTIUM_USER="user"
DEMO_DIR="/home/ccc/pq-ntor-experiment/sagin-experiments/demo"

echo "=========================================="
echo "  部署3D可视化DEMO到飞腾派"
echo "=========================================="
echo ""
echo "飞腾派地址: $PHYTIUM_IP"
echo "用户名: $PHYTIUM_USER"
echo ""

# 创建远程目录
echo "1. 创建远程目录..."
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} "mkdir -p ~/sagin-demo"

# 复制文件
echo "2. 复制DEMO文件..."
scp ${DEMO_DIR}/3d_globe_demo.html ${PHYTIUM_USER}@${PHYTIUM_IP}:~/sagin-demo/
scp ${DEMO_DIR}/start_demo.sh ${PHYTIUM_USER}@${PHYTIUM_IP}:~/sagin-demo/
scp ${DEMO_DIR}/README.md ${PHYTIUM_USER}@${PHYTIUM_IP}:~/sagin-demo/

# 设置执行权限
echo "3. 设置执行权限..."
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} "chmod +x ~/sagin-demo/start_demo.sh"

# 启动服务器
echo "4. 在飞腾派上启动HTTP服务器..."
ssh ${PHYTIUM_USER}@${PHYTIUM_IP} "cd ~/sagin-demo && nohup ./start_demo.sh 8080 > server.log 2>&1 &"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "请在浏览器访问:"
echo "  👉 http://192.168.5.110:8080/3d_globe_demo.html"
echo ""
echo "查看服务器日志:"
echo "  ssh ${PHYTIUM_USER}@${PHYTIUM_IP}"
echo "  cat ~/sagin-demo/server.log"
echo ""
