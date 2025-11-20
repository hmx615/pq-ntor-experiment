#!/bin/bash
# API测试脚本 - 验证所有接口是否正常工作

API_BASE="http://localhost:8080/api"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Testing PQ-Tor SAGIN Monitor API..."
echo "===================================="

# 测试健康检查
echo -n "Testing /api/health... "
response=$(curl -s "$API_BASE/health" | grep "healthy")
if [ -n "$response" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# 测试状态接口
echo -n "Testing /api/status... "
response=$(curl -s "$API_BASE/status" | grep "timestamp")
if [ -n "$response" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# 测试性能接口
echo -n "Testing /api/performance... "
response=$(curl -s "$API_BASE/performance" | grep "handshake")
if [ -n "$response" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# 测试SAGIN对比接口
echo -n "Testing /api/sagin/comparison... "
response=$(curl -s "$API_BASE/sagin/comparison" | grep "leo")
if [ -n "$response" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo "===================================="
echo "All tests completed!"
