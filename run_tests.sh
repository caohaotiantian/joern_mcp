#!/bin/bash

# Joern MCP Server - 测试运行脚本
# 使用方法: ./run_tests.sh [选项]

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}🧪 Joern MCP Server - 测试运行${NC}"
echo "======================================"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ 错误：虚拟环境不存在${NC}"
    echo "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查pytest
if ! .venv/bin/python -m pytest --version > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  pytest未安装，正在安装...${NC}"
    .venv/bin/pip install pytest pytest-asyncio pytest-cov pytest-mock
fi

# 设置PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/src"

echo -e "${GREEN}📂 项目路径: ${PROJECT_ROOT}${NC}"
echo -e "${GREEN}🐍 Python路径: ${PYTHONPATH}${NC}"
echo ""

# 解析参数
TEST_PATH="tests/"
VERBOSE="-v"
COVERAGE=""

case "${1:-}" in
    --all|-a)
        echo -e "${GREEN}▶️  运行所有测试（带覆盖率）${NC}"
        COVERAGE="--cov=src/joern_mcp --cov-report=term --cov-report=html"
        ;;
    --fast|-f)
        echo -e "${GREEN}▶️  快速测试（无覆盖率）${NC}"
        ;;
    --service|-s)
        echo -e "${GREEN}▶️  只测试服务层${NC}"
        TEST_PATH="tests/test_services/"
        ;;
    --taint|-t)
        echo -e "${GREEN}▶️  只测试污点分析${NC}"
        TEST_PATH="tests/test_services/test_taint.py"
        ;;
    --callgraph|-c)
        echo -e "${GREEN}▶️  只测试调用图${NC}"
        TEST_PATH="tests/test_services/test_callgraph.py"
        ;;
    --dataflow|-d)
        echo -e "${GREEN}▶️  只测试数据流${NC}"
        TEST_PATH="tests/test_services/test_dataflow.py"
        ;;
    --help|-h)
        echo "使用方法: ./run_tests.sh [选项]"
        echo ""
        echo "选项:"
        echo "  --all, -a       运行所有测试（带覆盖率报告）"
        echo "  --fast, -f      快速测试（无覆盖率，默认）"
        echo "  --service, -s   只测试服务层"
        echo "  --taint, -t     只测试污点分析"
        echo "  --callgraph, -c 只测试调用图"
        echo "  --dataflow, -d  只测试数据流"
        echo "  --help, -h      显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  ./run_tests.sh              # 快速运行所有测试"
        echo "  ./run_tests.sh --all        # 运行所有测试并生成覆盖率报告"
        echo "  ./run_tests.sh --taint      # 只测试污点分析"
        exit 0
        ;;
    *)
        echo -e "${GREEN}▶️  快速测试（默认）${NC}"
        ;;
esac

echo ""
echo -e "${YELLOW}运行测试...${NC}"
echo "======================================"

# 运行pytest
if .venv/bin/python -m pytest ${TEST_PATH} ${VERBOSE} --tb=short ${COVERAGE}; then
    echo ""
    echo -e "${GREEN}✅ 测试完成！${NC}"
    
    if [ -n "$COVERAGE" ]; then
        echo ""
        echo -e "${GREEN}📊 覆盖率报告已生成${NC}"
        echo "   HTML报告: htmlcov/index.html"
        echo "   运行以下命令查看: open htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${RED}❌ 测试失败！${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}🎉 验证完成！${NC}"

