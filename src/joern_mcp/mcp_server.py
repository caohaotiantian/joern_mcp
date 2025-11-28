"""MCP应用和全局状态"""

from fastmcp import FastMCP


# 创建MCP应用
mcp = FastMCP("Joern Code Analysis")


# 全局状态类
class _ServerState:
    """服务器全局状态"""

    def __init__(self):
        self.joern_server_manager = None
        self.query_executor = None


# 创建全局状态实例
server_state = _ServerState()
