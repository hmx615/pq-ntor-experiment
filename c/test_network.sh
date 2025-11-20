#!/bin/bash
#
# test_network.sh - 本地模拟5节点PQ-Tor网络测试
#
# 启动顺序：
# 1. Directory + Test Server (端口5000/8000)
# 2. Guard节点 (端口6001)
# 3. Middle节点 (端口6002)
# 4. Exit节点 (端口6003)
# 5. Client (发送HTTP请求)
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  PQ-Tor 本地网络测试${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"
    pkill -f "./directory" 2>/dev/null || true
    pkill -f "./relay" 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}所有服务已停止${NC}"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 检查程序是否存在
if [ ! -f "./directory" ] || [ ! -f "./relay" ] || [ ! -f "./client" ]; then
    echo -e "${RED}错误：请先编译程序 (make all)${NC}"
    exit 1
fi

# 步骤1：启动目录服务器 + 测试HTTP服务器
echo -e "${BLUE}[1/5] 启动目录服务器和测试HTTP服务器...${NC}"
./directory > directory.log 2>&1 &
DIRECTORY_PID=$!
sleep 2

# 检查是否成功启动
if ! ps -p $DIRECTORY_PID > /dev/null; then
    echo -e "${RED}目录服务器启动失败${NC}"
    cat directory.log
    exit 1
fi

echo -e "${GREEN}✓ 目录服务器运行中 (PID: $DIRECTORY_PID)${NC}"
echo -e "  - Directory API: http://localhost:5000/nodes"
echo -e "  - Test Server:   http://localhost:8000/"
echo ""

# 步骤2：启动Guard节点
echo -e "${BLUE}[2/5] 启动Guard节点...${NC}"
./relay -r guard -p 6001 > guard.log 2>&1 &
GUARD_PID=$!
sleep 1

if ! ps -p $GUARD_PID > /dev/null; then
    echo -e "${RED}Guard节点启动失败${NC}"
    cat guard.log
    exit 1
fi

echo -e "${GREEN}✓ Guard节点运行中 (PID: $GUARD_PID)${NC}"
echo -e "  - Port: 6001"
echo ""

# 步骤3：启动Middle节点
echo -e "${BLUE}[3/5] 启动Middle节点...${NC}"
./relay -r middle -p 6002 > middle.log 2>&1 &
MIDDLE_PID=$!
sleep 1

if ! ps -p $MIDDLE_PID > /dev/null; then
    echo -e "${RED}Middle节点启动失败${NC}"
    cat middle.log
    exit 1
fi

echo -e "${GREEN}✓ Middle节点运行中 (PID: $MIDDLE_PID)${NC}"
echo -e "  - Port: 6002"
echo ""

# 步骤4：启动Exit节点
echo -e "${BLUE}[4/5] 启动Exit节点...${NC}"
./relay -r exit -p 6003 > exit.log 2>&1 &
EXIT_PID=$!
sleep 1

if ! ps -p $EXIT_PID > /dev/null; then
    echo -e "${RED}Exit节点启动失败${NC}"
    cat exit.log
    exit 1
fi

echo -e "${GREEN}✓ Exit节点运行中 (PID: $EXIT_PID)${NC}"
echo -e "  - Port: 6003"
echo ""

# 等待所有节点完全启动
echo -e "${YELLOW}等待所有节点初始化完成...${NC}"
sleep 2
echo ""

# 步骤5：运行客户端测试
echo -e "${BLUE}[5/5] 运行客户端测试...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

./client -u http://localhost:8000/

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ 测试完成！${NC}"
echo ""

# 显示日志摘要
echo -e "${BLUE}日志文件：${NC}"
echo "  - directory.log"
echo "  - guard.log"
echo "  - middle.log"
echo "  - exit.log"
echo ""

# 询问是否查看日志
read -p "是否查看节点日志? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}=== Guard节点日志 ===${NC}"
    tail -20 guard.log
    echo ""
    echo -e "${BLUE}=== Middle节点日志 ===${NC}"
    tail -20 middle.log
    echo ""
    echo -e "${BLUE}=== Exit节点日志 ===${NC}"
    tail -20 exit.log
fi

echo ""
echo -e "${GREEN}测试脚本结束${NC}"
