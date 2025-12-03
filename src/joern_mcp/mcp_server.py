"""MCP应用和全局状态"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from loguru import logger


# 全局状态类
class _ServerState:
    """服务器全局状态"""

    def __init__(self):
        self.joern_server = None
        self.query_executor = None


# 创建全局状态实例
server_state = _ServerState()


@asynccontextmanager
async def lifespan(_app) -> AsyncIterator[None]:
    """应用生命周期管理"""
    # 延迟导入避免循环依赖
    from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor
    from joern_mcp.joern.server import JoernServerManager

    logger.info("Starting Joern MCP Server...")

    # 启动 Joern Server
    server_state.joern_server = JoernServerManager()
    await server_state.joern_server.start()

    # 初始化优化的查询执行器
    server_state.query_executor = OptimizedQueryExecutor(server_state.joern_server)

    logger.info("Joern MCP Server started successfully")
    logger.info(f"Joern endpoint: {server_state.joern_server.endpoint}")

    yield

    # 清理
    logger.info("Stopping Joern MCP Server...")
    if server_state.joern_server:
        await server_state.joern_server.stop()
    logger.info("Joern MCP Server stopped")


# 创建 MCP 应用（带生命周期管理）
mcp = FastMCP("Joern Code Analysis", lifespan=lifespan)
