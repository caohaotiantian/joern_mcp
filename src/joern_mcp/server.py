"""MCP服务器主入口"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from loguru import logger
from joern_mcp.config import settings
from joern_mcp.mcp_server import mcp, ServerState
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    """应用生命周期管理"""
    logger.info("Starting Joern MCP Server...")
    
    # 启动Joern Server
    ServerState.joern_server = JoernServerManager()
    await ServerState.joern_server.start()
    
    # 初始化查询执行器
    ServerState.query_executor = QueryExecutor(ServerState.joern_server)
    
    logger.info("Joern MCP Server started successfully")
    logger.info(f"Joern endpoint: {ServerState.joern_server.endpoint}")
    
    yield
    
    # 清理
    logger.info("Stopping Joern MCP Server...")
    if ServerState.joern_server:
        await ServerState.joern_server.stop()
    logger.info("Joern MCP Server stopped")


# 注册生命周期
mcp.app._lifespan = lifespan


# ===== MCP Tools =====

@mcp.tool()
async def health_check() -> dict:
    """
    检查服务器健康状态
    
    Returns:
        dict: 包含健康状态和服务器信息
        
    Example:
        >>> await health_check()
        {"status": "healthy", "joern_endpoint": "localhost:8080"}
    """
    if not ServerState.joern_server:
        return {
            "status": "unhealthy",
            "error": "Joern server not initialized"
        }
    
    is_healthy = await ServerState.joern_server.health_check()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "joern_endpoint": ServerState.joern_server.endpoint
    }


@mcp.tool()
async def execute_query(
    query: str,
    format: str = "json",
    timeout: int | None = None
) -> dict:
    """
    执行自定义Joern查询
    
    Args:
        query: Scala查询语句
        format: 输出格式 (json, dot)
        timeout: 超时时间（秒）
    
    Returns:
        dict: 查询结果
        
    Example:
        >>> await execute_query("cpg.method.name.l")
        {"success": True, "result": ["main", "foo", "bar"]}
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    if not settings.enable_custom_queries:
        return {
            "success": False,
            "error": "Custom queries are disabled"
        }
    
    try:
        result = await ServerState.query_executor.execute(
            query,
            format=format,
            timeout=timeout
        )
        return {
            "success": True,
            "result": result.get("stdout", ""),
            "raw": result
        }
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def main() -> None:
    """主函数"""
    # 导入所有工具模块以注册MCP工具（延迟导入避免循环依赖）
    from joern_mcp.tools import (
        project, query, callgraph, dataflow, 
        taint, cfg, batch, export
    )  # noqa: F401
    
    # 导入资源和提示模块
    from joern_mcp.resources import project_resources  # noqa: F401
    from joern_mcp.prompts import analysis_prompts  # noqa: F401
    
    logger.info("=" * 60)
    logger.info("Joern MCP Server")
    logger.info("=" * 60)
    logger.info(f"Joern Server: {settings.joern_server_host}:{settings.joern_server_port}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info("=" * 60)
    
    # 运行MCP服务器
    import sys
    
    # FastMCP通过stdio运行
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

