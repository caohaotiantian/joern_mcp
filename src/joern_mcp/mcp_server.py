"""MCP应用和全局状态"""
from fastmcp import FastMCP
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor


# 全局状态
class ServerState:
    """服务器全局状态"""
    joern_server: JoernServerManager | None = None
    query_executor: QueryExecutor | None = None


# 创建MCP应用
mcp = FastMCP("Joern Code Analysis")

