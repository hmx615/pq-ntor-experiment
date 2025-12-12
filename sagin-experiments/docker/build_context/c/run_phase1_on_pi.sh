#!/bin/bash
# Phase 1 飞腾派快速测试脚本
# 用途: 在飞腾派上一键编译和运行Phase 1性能测试

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Phase 1: 密码学基元性能测试 - 飞腾派部署脚本${NC}"
echo -e "${GREEN}======================================================================${NC}"

# 1. 系统信息检查
echo -e "\n${YELLOW}[1/6] 检查系统信息...${NC}"
echo "CPU架构: $(uname -m)"
echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "CPU型号: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "CPU频率: $(lscpu | grep 'CPU MHz' | cut -d':' -f2 | xargs) MHz"
echo "内存: $(free -h | grep Mem | awk '{print $2}')"

# 检查是否是ARM64
if [ "$(uname -m)" != "aarch64" ]; then
    echo -e "${RED}错误: 当前不是ARM64架构!${NC}"
    exit 1
fi

# 2. 检查依赖
echo -e "\n${YELLOW}[2/6] 检查依赖...${NC}"

# 检查liboqs
LIBOQS_DIR="$HOME/pq-ntor-experiment/_oqs"
if [ ! -f "$LIBOQS_DIR/lib/liboqs.so" ]; then
    echo -e "${RED}错误: liboqs未找到!${NC}"
    echo "请先安装liboqs: https://github.com/open-quantum-safe/liboqs"
    exit 1
else
    echo -e "${GREEN}✓ liboqs已安装: $LIBOQS_DIR${NC}"
fi

# 检查GCC
if ! command -v gcc &> /dev/null; then
    echo -e "${RED}错误: GCC未安装!${NC}"
    exit 1
else
    echo -e "${GREEN}✓ GCC版本: $(gcc --version | head -1)${NC}"
fi

# 检查OpenSSL
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}错误: OpenSSL未安装!${NC}"
    exit 1
else
    echo -e "${GREEN}✓ OpenSSL版本: $(openssl version)${NC}"
fi

# 3. 设置CPU性能模式
echo -e "\n${YELLOW}[3/6] 优化CPU性能...${NC}"
if [ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo "设置CPU governor为performance模式..."
    echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    echo -e "${GREEN}✓ CPU已设置为performance模式${NC}"
else
    echo -e "${YELLOW}⚠ 无权限设置CPU模式,继续使用默认模式${NC}"
fi

# 4. 清理并编译
echo -e "\n${YELLOW}[4/6] 编译Phase 1测试程序...${NC}"
make clean > /dev/null 2>&1
if make phase1_crypto_primitives; then
    echo -e "${GREEN}✓ 编译成功!${NC}"
else
    echo -e "${RED}✗ 编译失败,请检查错误日志${NC}"
    exit 1
fi

# 5. 创建结果目录
RESULT_DIR="$HOME/phase1_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULT_DIR"
echo -e "\n${YELLOW}[5/6] 结果将保存到: $RESULT_DIR${NC}"

# 6. 运行测试
echo -e "\n${YELLOW}[6/6] 运行Phase 1性能测试 (约1-2分钟)...${NC}"
echo -e "${GREEN}======================================================================${NC}\n"

# 运行并同时显示和保存输出
./phase1_crypto_primitives 2>&1 | tee "$RESULT_DIR/phase1_output.txt"

# 7. 保存结果
if [ -f "phase1_crypto_benchmarks.csv" ]; then
    cp phase1_crypto_benchmarks.csv "$RESULT_DIR/"
    echo -e "\n${GREEN}✓ CSV结果已保存${NC}"
else
    echo -e "\n${RED}✗ CSV文件未生成!${NC}"
    exit 1
fi

# 保存系统信息
{
    echo "=== CPU信息 ==="
    lscpu
    echo -e "\n=== CPU详细信息 ==="
    cat /proc/cpuinfo
    echo -e "\n=== 内存信息 ==="
    free -h
    echo -e "\n=== 测试时间 ==="
    date
} > "$RESULT_DIR/system_info.txt"

# 8. 结果摘要
echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}Phase 1 测试完成!${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo "📊 结果文件:"
echo "  - CSV数据: $RESULT_DIR/phase1_crypto_benchmarks.csv"
echo "  - 完整输出: $RESULT_DIR/phase1_output.txt"
echo "  - 系统信息: $RESULT_DIR/system_info.txt"
echo ""
echo "📈 快速查看结果:"
echo "  cat $RESULT_DIR/phase1_crypto_benchmarks.csv | column -t -s,"
echo ""
echo "📤 回传结果到开发机:"
echo "  scp -r $RESULT_DIR user@dev-machine:/path/to/destination/"
echo ""

# 显示关键结果
echo -e "${YELLOW}关键性能指标 (Mean, μs):${NC}"
grep -E "Kyber-512|HKDF|HMAC" "$RESULT_DIR/phase1_crypto_benchmarks.csv" | \
    awk -F',' '{printf "  %-25s: %s μs\n", $1, $4}'

echo -e "\n${GREEN}✅ 所有测试完成!${NC}"
echo -e "${GREEN}======================================================================${NC}"
