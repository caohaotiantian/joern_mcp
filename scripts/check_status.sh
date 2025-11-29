#!/bin/bash

# 快速检查Joern Server和测试状态

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Joern Server 状态检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Joern进程
echo -e "${YELLOW}📊 Joern进程:${NC}"
JOERN_PIDS=$(pgrep -f "joern" 2>/dev/null || true)
if [ -n "$JOERN_PIDS" ]; then
    echo -e "${GREEN}✅ 运行中${NC} (PID: $JOERN_PIDS)"
    for pid in $JOERN_PIDS; do
        ELAPSED=$(ps -p $pid -o etime= 2>/dev/null | tr -d ' ')
        CPU=$(ps -p $pid -o %cpu= 2>/dev/null | tr -d ' ')
        MEM=$(ps -p $pid -o %mem= 2>/dev/null | tr -d ' ')
        echo -e "   └─ PID ${pid}: 运行 ${ELAPSED}, CPU ${CPU}%, 内存 ${MEM}%"
    done
else
    echo -e "${RED}❌ 未运行${NC}"
fi
echo ""

# 2. 端口监听
echo -e "${YELLOW}🌐 端口监听:${NC}"
LISTENING=$(lsof -i :20000-30000 2>/dev/null | grep LISTEN || true)
if [ -n "$LISTENING" ]; then
    echo -e "${GREEN}✅ 端口已监听${NC}"
    echo "$LISTENING" | awk '{print "   └─ 端口 "$9" ("$1")"}'
else
    if [ -n "$JOERN_PIDS" ]; then
        echo -e "${YELLOW}⏳ 端口未就绪${NC} (Joern正在启动...)"
    else
        echo -e "${RED}❌ 无端口监听${NC}"
    fi
fi
echo ""

# 3. 测试进程
echo -e "${YELLOW}🧪 测试进程:${NC}"
PYTEST_PIDS=$(pgrep -f "pytest.*integration" 2>/dev/null || true)
if [ -n "$PYTEST_PIDS" ]; then
    echo -e "${GREEN}✅ 测试运行中${NC} (PID: $PYTEST_PIDS)"
    ELAPSED=$(ps -p $PYTEST_PIDS -o etime= 2>/dev/null | tr -d ' ')
    echo -e "   └─ 运行时间: ${ELAPSED}"
else
    echo -e "${YELLOW}⏸️  测试未运行${NC}"
fi
echo ""

# 4. 状态判断
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 状态总结:${NC}"
echo ""

if [ -n "$JOERN_PIDS" ] && [ -n "$LISTENING" ]; then
    echo -e "${GREEN}✅ Joern Server已就绪${NC}"
    echo -e "   测试应该正在执行或即将开始"
elif [ -n "$JOERN_PIDS" ] && [ -z "$LISTENING" ]; then
    echo -e "${YELLOW}⏳ Joern Server正在启动${NC}"
    echo -e "   预计还需要 30-120 秒"
    echo -e "   这是正常现象，请耐心等待"
else
    echo -e "${RED}❌ Joern Server未运行${NC}"
    if [ -n "$PYTEST_PIDS" ]; then
        echo -e "   测试可能正在启动服务器"
    else
        echo -e "   可以运行: ./run_integration_tests.sh"
    fi
fi
echo ""

# 5. 建议
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💡 建议:${NC}"

if [ -n "$JOERN_PIDS" ] && [ -z "$LISTENING" ]; then
    echo -e "   ${YELLOW}→${NC} 继续等待，Joern正在启动"
    echo -e "   ${YELLOW}→${NC} 可运行监控: ${GREEN}./scripts/monitor_joern.sh${NC}"
elif [ -n "$JOERN_PIDS" ] && [ -n "$LISTENING" ]; then
    echo -e "   ${GREEN}→${NC} Joern Server已就绪，可以运行测试"
else
    echo -e "   ${BLUE}→${NC} 运行测试: ${GREEN}./run_integration_tests.sh${NC}"
    echo -e "   ${BLUE}→${NC} 实时监控: ${GREEN}./scripts/monitor_joern.sh${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

