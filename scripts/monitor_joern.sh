#!/bin/bash

# Joern Server 实时监控脚本
# 用于监控Joern Server的启动和运行状态

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Joern Server 实时监控${NC}"
echo "按 Ctrl+C 退出"
echo "======================================"
echo ""

# 监控循环
while true; do
    clear
    echo -e "${BLUE}🔍 Joern Server 实时监控${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo "======================================"
    echo ""
    
    # 1. 检查Joern进程
    echo -e "${YELLOW}📊 Joern进程:${NC}"
    JOERN_PIDS=$(pgrep -f "joern" 2>/dev/null || true)
    if [ -n "$JOERN_PIDS" ]; then
        echo -e "${GREEN}✅ 找到Joern进程:${NC}"
        ps aux | grep -E "joern" | grep -v grep | grep -v monitor
        
        # 计算进程运行时间
        for pid in $JOERN_PIDS; do
            ELAPSED=$(ps -p $pid -o etime= 2>/dev/null || echo "N/A")
            echo -e "   PID $pid 运行时间: ${GREEN}$ELAPSED${NC}"
        done
    else
        echo -e "${RED}❌ 未发现Joern进程${NC}"
    fi
    echo ""
    
    # 2. 检查端口监听
    echo -e "${YELLOW}🌐 端口监听 (20000-30000):${NC}"
    LISTENING=$(lsof -i :20000-30000 2>/dev/null | grep LISTEN || true)
    if [ -n "$LISTENING" ]; then
        echo -e "${GREEN}✅ 发现端口监听:${NC}"
        echo "$LISTENING"
    else
        echo -e "${YELLOW}⏳ 暂无端口监听（服务器可能正在启动）${NC}"
    fi
    echo ""
    
    # 3. 检查系统资源
    echo -e "${YELLOW}💻 系统资源:${NC}"
    
    # CPU使用
    if [ -n "$JOERN_PIDS" ]; then
        for pid in $JOERN_PIDS; do
            CPU=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
            MEM=$(ps -p $pid -o %mem= 2>/dev/null || echo "0")
            echo -e "   PID $pid - CPU: ${GREEN}${CPU}%${NC}, 内存: ${GREEN}${MEM}%${NC}"
        done
    fi
    echo ""
    
    # 4. 测试进程状态
    echo -e "${YELLOW}🧪 测试进程:${NC}"
    PYTEST_PIDS=$(pgrep -f "pytest.*integration" 2>/dev/null || true)
    if [ -n "$PYTEST_PIDS" ]; then
        echo -e "${GREEN}✅ 测试正在运行 (PID: $PYTEST_PIDS)${NC}"
        ELAPSED=$(ps -p $PYTEST_PIDS -o etime= 2>/dev/null || echo "N/A")
        echo -e "   运行时间: ${GREEN}$ELAPSED${NC}"
    else
        echo -e "${YELLOW}⏸️  测试未运行${NC}"
    fi
    echo ""
    
    # 5. 状态总结
    echo "======================================"
    if [ -n "$JOERN_PIDS" ] && [ -n "$LISTENING" ]; then
        echo -e "${GREEN}✅ Joern Server运行中且端口已监听${NC}"
        echo -e "${GREEN}   测试应该正在执行...${NC}"
    elif [ -n "$JOERN_PIDS" ] && [ -z "$LISTENING" ]; then
        echo -e "${YELLOW}⏳ Joern进程运行中，等待端口监听...${NC}"
        echo -e "${YELLOW}   这可能需要1-3分钟${NC}"
    else
        echo -e "${RED}❌ Joern Server未运行${NC}"
        echo -e "${RED}   可能已停止或未启动${NC}"
    fi
    echo ""
    echo "下次刷新: 2秒后 (Ctrl+C 退出)"
    
    sleep 2
done

