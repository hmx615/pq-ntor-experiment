#!/bin/bash
##############################################################################
# 环境检查脚本
# 验证所有依赖和配置是否就绪
##############################################################################

echo "=========================================="
echo "  Environment Check for NOMA Testing"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# 1. 检查必需的系统工具
echo "[1/5] Checking system tools..."
for cmd in jq bc sudo tc; do
    if command -v $cmd &> /dev/null; then
        echo "  ✓ $cmd found"
    else
        echo "  ✗ $cmd NOT FOUND"
        ((ERRORS++))
    fi
done
echo ""

# 2. 检查PQ-NTOR可执行文件
echo "[2/5] Checking PQ-NTOR executables..."
PQ_NTOR_DIR="/home/ccc/pq-ntor-experiment/c"

if [ -d "$PQ_NTOR_DIR" ]; then
    for exe in directory relay client; do
        if [ -f "$PQ_NTOR_DIR/$exe" ] && [ -x "$PQ_NTOR_DIR/$exe" ]; then
            echo "  ✓ $exe found and executable"
        else
            echo "  ✗ $exe NOT FOUND or not executable"
            ((ERRORS++))
        fi
    done
else
    echo "  ✗ PQ-NTOR directory not found: $PQ_NTOR_DIR"
    ((ERRORS++))
fi
echo ""

# 3. 检查Python依赖
echo "[3/5] Checking Python dependencies..."
for module in pandas numpy matplotlib seaborn; do
    if python3 -c "import $module" 2>/dev/null; then
        echo "  ✓ $module installed"
    else
        echo "  ✗ $module NOT INSTALLED"
        ((WARNINGS++))
    fi
done
echo ""

# 4. 检查拓扑配置文件
echo "[4/5] Checking topology configs..."
CONFIGS_DIR="../configs"
CONFIG_COUNT=$(ls "$CONFIGS_DIR"/topology_*.json 2>/dev/null | wc -l)

if [ "$CONFIG_COUNT" -eq 12 ]; then
    echo "  ✓ All 12 topology configs found"
else
    echo "  ⚠ Only $CONFIG_COUNT/12 topology configs found"
    ((WARNINGS++))
fi
echo ""

# 5. 检查目录结构
echo "[5/5] Checking directory structure..."
for dir in configs scripts results logs; do
    if [ -d "../$dir" ]; then
        echo "  ✓ ../$dir exists"
    else
        echo "  ⚠ ../$dir does not exist (will be created)"
        mkdir -p "../$dir"
        ((WARNINGS++))
    fi
done
echo ""

# 总结
echo "=========================================="
echo "  Summary"
echo "=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready to run tests."
    echo ""
    echo "Next step:"
    echo "  ./test_all_topologies.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Passed with $WARNINGS warnings"
    echo ""
    echo "You can proceed, but some optional features may not work."
    echo ""
    echo "To fix warnings:"
    echo "  pip3 install pandas numpy matplotlib seaborn"
    exit 0
else
    echo "❌ Failed with $ERRORS errors and $WARNINGS warnings"
    echo ""
    echo "Please fix the following issues:"
    echo ""
    if ! command -v jq &> /dev/null; then
        echo "  - Install jq: sudo apt-get install jq"
    fi
    if ! command -v bc &> /dev/null; then
        echo "  - Install bc: sudo apt-get install bc"
    fi
    if [ ! -f "$PQ_NTOR_DIR/directory" ]; then
        echo "  - Compile PQ-NTOR: cd $PQ_NTOR_DIR && make all"
    fi
    echo ""
    exit 1
fi
