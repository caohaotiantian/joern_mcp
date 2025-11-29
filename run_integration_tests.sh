#!/bin/bash

# Joern MCP Server - 集成测试运行脚本
# 使用方法: ./run_integration_tests.sh [选项]

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 清理函数
cleanup_ports() {
    echo -e "${BLUE}🧹 清理端口占用...${NC}"
    
    # 查找并终止Joern进程
    if command -v pgrep &> /dev/null; then
        JOERN_PIDS=$(pgrep -f "joern.*--server" || true)
        if [ -n "$JOERN_PIDS" ]; then
            echo -e "${YELLOW}⚠️  发现Joern Server进程: $JOERN_PIDS${NC}"
            echo "$JOERN_PIDS" | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✅ Joern进程已清理${NC}"
            sleep 2  # 等待端口释放
        fi
    fi
}

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 设置trap捕获退出信号，确保清理
trap cleanup_ports EXIT INT TERM

# 在开始前清理端口
cleanup_ports

echo -e "${GREEN}🧪 Joern MCP Server - 集成测试${NC}"
echo "======================================"

# 检查Joern是否安装
echo -e "${BLUE}📦 检查Joern安装...${NC}"
if ! command -v joern &> /dev/null; then
    echo -e "${YELLOW}⚠️  警告：Joern未安装或不在PATH中${NC}"
    echo "   集成测试需要Joern环境"
    echo "   下载: https://joern.io"
    echo ""
    echo "   继续运行将跳过需要Joern的测试"
    read -p "   是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Joern已安装${NC}"
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ 错误：虚拟环境不存在${NC}"
    echo "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查pytest
if ! .venv/bin/python -m pytest --version > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  pytest未安装，正在安装...${NC}"
    .venv/bin/pip install pytest pytest-asyncio pytest-cov pytest-mock psutil
fi

# 设置PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/src"

echo ""
echo -e "${GREEN}📂 项目路径: ${PROJECT_ROOT}${NC}"
echo -e "${GREEN}🐍 Python路径: ${PYTHONPATH}${NC}"
echo ""

# 解析参数
TEST_MARKERS=""
VERBOSE="-v"

case "${1:-}" in
    --all|-a)
        echo -e "${GREEN}▶️  运行所有集成测试${NC}"
        TEST_MARKERS="-m integration"
        ;;
    --lifecycle|-l)
        echo -e "${GREEN}▶️  测试服务器生命周期${NC}"
        TEST_MARKERS="-m integration tests/integration/test_server_lifecycle.py"
        ;;
    --tools|-t)
        echo -e "${GREEN}▶️  测试工具集成${NC}"
        TEST_MARKERS="-m integration tests/integration/test_tools_integration.py"
        ;;
    --performance|-p)
        echo -e "${GREEN}▶️  性能测试${NC}"
        TEST_MARKERS="-m performance"
        ;;
    --stress|-s)
        echo -e "${GREEN}▶️  压力测试${NC}"
        TEST_MARKERS="-m stress"
        ;;
    --error|-e)
        echo -e "${GREEN}▶️  错误处理测试${NC}"
        TEST_MARKERS="-m integration tests/integration/test_error_handling.py"
        ;;
    --quick|-q)
        echo -e "${GREEN}▶️  快速集成测试（跳过性能测试）${NC}"
        TEST_MARKERS='-m "integration and not performance and not stress"'
        ;;
    --help|-h)
        echo "使用方法: ./run_integration_tests.sh [选项]"
        echo ""
        echo "选项:"
        echo "  --all, -a         运行所有集成测试"
        echo "  --lifecycle, -l   测试服务器生命周期"
        echo "  --tools, -t       测试工具集成"
        echo "  --performance, -p 性能测试"
        echo "  --stress, -s      压力测试"
        echo "  --error, -e       错误处理测试"
        echo "  --quick, -q       快速测试（跳过性能测试）"
        echo "  --help, -h        显示此帮助信息"
        echo ""
        echo "注意:"
        echo "  - 集成测试需要Joern环境"
        echo "  - 某些测试可能需要较长时间"
        echo "  - 性能测试需要足够的系统资源"
        exit 0
        ;;
    *)
        echo -e "${GREEN}▶️  快速集成测试（默认）${NC}"
        TEST_MARKERS='-m "integration and not performance and not stress"'
        ;;
esac

echo ""
echo -e "${YELLOW}运行测试...${NC}"
echo "======================================"

# 运行pytest  
if eval ".venv/bin/python -m pytest tests/integration/ ${TEST_MARKERS} ${VERBOSE} --tb=short"; then
    echo ""
    echo -e "${GREEN}✅ 集成测试完成！${NC}"
else
    echo ""
    echo -e "${RED}❌ 集成测试失败！${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}🎉 验证完成！${NC}"
echo ""
echo -e "${BLUE}💡 提示:${NC}"
echo "   - 使用 --all 运行完整测试"
echo "   - 使用 --performance 进行性能测试"
echo "   - 使用 --help 查看所有选项"

