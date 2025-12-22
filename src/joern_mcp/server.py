"""MCP服务器主入口"""

from loguru import logger

from joern_mcp.config import settings
from joern_mcp.mcp_server import mcp, server_state

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
    if not server_state.joern_server:
        return {"status": "unhealthy", "error": "Joern server not initialized"}

    # 检查进程状态
    process_running = server_state.joern_server.is_running()

    # 执行健康检查查询
    is_healthy = await server_state.joern_server.health_check()

    result = {
        "status": "healthy" if is_healthy else "unhealthy",
        "joern_endpoint": server_state.joern_server.endpoint,
        "process_running": process_running,
    }

    if not is_healthy:
        # 添加更多诊断信息
        if not process_running:
            result["error"] = (
                "Joern server process is not running. It may have crashed or failed to start."
            )
        else:
            result["error"] = (
                "Joern server process is running but not responding. "
                f"Check if WebSocket endpoint is available at ws://{server_state.joern_server.endpoint}/connect"
            )

    return result


@mcp.tool()
async def execute_query(
    query: str, format: str = "json", timeout: int | None = None
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
        >>> await execute_query("cpg.method.name")
        {"success": True, "result": ["main", "foo", "bar"]}
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if not settings.enable_custom_queries:
        return {"success": False, "error": "Custom queries are disabled"}

    try:
        result = await server_state.query_executor.execute(
            query, format=format, timeout=timeout
        )
        return {"success": True, "result": result.get("stdout", ""), "raw": result}
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {"success": False, "error": str(e)}


def main() -> None:
    """主函数"""
    # 导入所有工具模块以注册MCP工具（延迟导入避免循环依赖）

    # 导入工具模块
    # 导入资源和提示模块
    from joern_mcp.prompts import analysis_prompts  # noqa: F401
    from joern_mcp.resources import project_resources  # noqa: F401
    from joern_mcp.tools import (
        batch,  # noqa: F401
        callgraph,  # noqa: F401
        cfg,  # noqa: F401
        dataflow,  # noqa: F401
        export,  # noqa: F401
        performance,  # noqa: F401
        project,  # noqa: F401
        query,  # noqa: F401
        taint,  # noqa: F401
    )

    logger.info("=" * 60)
    logger.info("Joern MCP Server")
    logger.info("=" * 60)
    logger.info(
        f"Joern Server: {settings.joern_server_host}:{settings.joern_server_port}"
    )
    logger.info(f"Log level: {settings.log_level}")
    logger.info("=" * 60)

    # 运行MCP服务器
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
