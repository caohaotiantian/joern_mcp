"""调用图分析MCP工具

提供调用图分析功能：
- get_callers: 获取函数的调用者
- get_callees: 获取函数调用的其他函数
- get_call_chain: 获取函数的调用链
- get_call_graph: 获取完整调用图

多项目支持：所有工具支持可选的 project_name 参数指定项目范围。
"""

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.services.callgraph import CallGraphService


@mcp.tool()
async def get_callers(
    function_name: str, depth: int = 1, project_name: str | None = None
) -> dict:
    """
    获取函数的调用者

    Args:
        function_name: 函数名称
        depth: 调用深度（默认1层，最大10层）
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 调用者列表

    Example:
        >>> await get_callers("buffer_overflow", depth=2, project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "buffer_overflow",
            "depth": 2,
            "callers": [
                {
                    "name": "process_data",
                    "filename": "vulnerable.c",
                    "lineNumber": 127
                }
            ],
            "count": 1
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if depth < 1 or depth > 10:
        return {"success": False, "error": "Depth must be between 1 and 10"}

    service = CallGraphService(server_state.query_executor)
    return await service.get_callers(function_name, depth, project_name)


@mcp.tool()
async def get_callees(
    function_name: str, depth: int = 1, project_name: str | None = None
) -> dict:
    """
    获取函数调用的其他函数

    Args:
        function_name: 函数名称
        depth: 调用深度（默认1层，最大10层）
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 被调用函数列表

    Example:
        >>> await get_callees("buffer_overflow", depth=1, project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "buffer_overflow",
            "callees": [
                {"name": "strcpy", "filename": "<empty>", "lineNumber": -1},
                {"name": "printf", "filename": "<empty>", "lineNumber": -1}
            ],
            "count": 2
        }

    Note:
        外部库函数（如 strcpy, printf）的 filename 为 "<empty>"
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if depth < 1 or depth > 10:
        return {"success": False, "error": "Depth must be between 1 and 10"}

    service = CallGraphService(server_state.query_executor)
    return await service.get_callees(function_name, depth, project_name)


@mcp.tool()
async def get_call_chain(
    function_name: str,
    max_depth: int = 5,
    direction: str = "up",
    project_name: str | None = None,
) -> dict:
    """
    获取函数的调用链

    Args:
        function_name: 函数名称
        max_depth: 最大深度（默认5层，最大10层）
        direction: 方向 ("up"=调用者链, "down"=被调用者链)
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 调用链数据

    Example:
        >>> await get_call_chain("strcpy", max_depth=3, direction="up", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "strcpy",
            "direction": "up",
            "chain": [
                {"name": "buffer_overflow", "filename": "vulnerable.c"},
                {"name": "main", "filename": "vulnerable.c"}
            ],
            "count": 2
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_depth < 1 or max_depth > 10:
        return {"success": False, "error": "Max depth must be between 1 and 10"}

    if direction not in ["up", "down"]:
        return {"success": False, "error": "Direction must be 'up' or 'down'"}

    service = CallGraphService(server_state.query_executor)
    return await service.get_call_chain(function_name, max_depth, direction, project_name)


@mcp.tool()
async def get_call_graph(
    function_name: str,
    include_callers: bool = True,
    include_callees: bool = True,
    depth: int = 2,
    project_name: str | None = None,
) -> dict:
    """
    获取函数的完整调用图

    Args:
        function_name: 函数名称
        include_callers: 是否包含调用者（默认True）
        include_callees: 是否包含被调用者（默认True）
        depth: 深度（默认2层，最大5层）
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 调用图数据（包含节点和边）

    Example:
        >>> await get_call_graph("buffer_overflow", depth=1, project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "buffer_overflow",
            "nodes": [
                {"id": "main", "type": "caller", "filename": "vulnerable.c"},
                {"id": "buffer_overflow", "type": "target"},
                {"id": "strcpy", "type": "callee"}
            ],
            "edges": [
                {"from": "main", "to": "buffer_overflow", "type": "calls"},
                {"from": "buffer_overflow", "to": "strcpy", "type": "calls"}
            ],
            "node_count": 3,
            "edge_count": 2
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if depth < 1 or depth > 5:
        return {"success": False, "error": "Depth must be between 1 and 5"}

    service = CallGraphService(server_state.query_executor)
    return await service.get_call_graph(
        function_name, include_callers, include_callees, depth, project_name
    )
