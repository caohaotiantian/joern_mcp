#!/bin/bash
# E2E测试运行脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   Joern MCP E2E测试套件${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}错误: 找不到虚拟环境${NC}"
    exit 1
fi

# 默认参数
TEST_MARKERS=${TEST_MARKERS:-"e2e"}
COVERAGE=${COVERAGE:-"yes"}
VERBOSE=${VERBOSE:-""}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        --no-cov)
            COVERAGE="no"
            shift
            ;;
        -k)
            TEST_PATTERN="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}配置:${NC}"
echo "  测试标记: $TEST_MARKERS"
echo "  覆盖率: $COVERAGE"
echo "  详细输出: ${VERBOSE:-否}"
echo ""

# 构建pytest命令
PYTEST_CMD="python -m pytest tests/e2e -m \"$TEST_MARKERS\" $VERBOSE"

# 添加覆盖率选项
if [ "$COVERAGE" = "yes" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=joern_mcp --cov-report=term --cov-report=html"
fi

# 添加测试模式过滤
if [ -n "$TEST_PATTERN" ]; then
    PYTEST_CMD="$PYTEST_CMD -k \"$TEST_PATTERN\""
fi

echo -e "${YELLOW}运行测试...${NC}"
echo "命令: $PYTEST_CMD"
echo ""

# 执行测试
eval $PYTEST_CMD

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}   E2E测试通过！ ✓${NC}"
    echo -e "${GREEN}=====================================${NC}"
    
    if [ "$COVERAGE" = "yes" ]; then
        echo ""
        echo -e "${YELLOW}HTML覆盖率报告: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}=====================================${NC}"
    echo -e "${RED}   E2E测试失败 ✗${NC}"
    echo -e "${RED}=====================================${NC}"
    exit 1
fi

