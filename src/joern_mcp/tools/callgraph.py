"""调用图分析MCP工具"""
from typing import Optional
from loguru import logger
from joern_mcp.mcp_server import mcp, ServerState
from joern_mcp.services.callgraph import CallGraphService


@mcp.tool()
async def get_callers(
    function_name: str,
    depth: int = 1
) -> dict:
    """
    获取函数的调用者
    
    Args:
        function_name: 函数名称
        depth: 调用深度（默认1层，最大10层）
    
    Returns:
        dict: 调用者列表
    
    Example:
        >>> await get_callers("vulnerable_function", depth=2)
        {
            "success": True,
            "function": "vulnerable_function",
            "callers": [{"name": "main", "filename": "main.c", ...}],
            "count": 1
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    if depth < 1 or depth > 10:
        return {
            "success": False,
            "error": "Depth must be between 1 and 10"
        }
    
    service = CallGraphService(ServerState.query_executor)
    return await service.get_callers(function_name, depth)


@mcp.tool()
async def get_callees(
    function_name: str,
    depth: int = 1
) -> dict:
    """
    获取函数调用的其他函数
    
    Args:
        function_name: 函数名称
        depth: 调用深度（默认1层，最大10层）
    
    Returns:
        dict: 被调用函数列表
    
    Example:
        >>> await get_callees("main", depth=2)
        {
            "success": True,
            "function": "main",
            "callees": [{"name": "printf", "filename": "stdio.h", ...}],
            "count": 5
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    if depth < 1 or depth > 10:
        return {
            "success": False,
            "error": "Depth must be between 1 and 10"
        }
    
    service = CallGraphService(ServerState.query_executor)
    return await service.get_callees(function_name, depth)


@mcp.tool()
async def get_call_chain(
    function_name: str,
    max_depth: int = 5,
    direction: str = "up"
) -> dict:
    """
    获取函数的调用链
    
    Args:
        function_name: 函数名称
        max_depth: 最大深度（默认5层，最大10层）
        direction: 方向 ("up"=调用者链, "down"=被调用者链)
    
    Returns:
        dict: 调用链数据
    
    Example:
        >>> await get_call_chain("process_input", max_depth=5, direction="up")
        {
            "success": True,
            "function": "process_input",
            "direction": "up",
            "chain": [...],
            "count": 3
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    if max_depth < 1 or max_depth > 10:
        return {
            "success": False,
            "error": "Max depth must be between 1 and 10"
        }
    
    if direction not in ["up", "down"]:
        return {
            "success": False,
            "error": "Direction must be 'up' or 'down'"
        }
    
    service = CallGraphService(ServerState.query_executor)
    return await service.get_call_chain(function_name, max_depth, direction)


@mcp.tool()
async def get_call_graph(
    function_name: str,
    include_callers: bool = True,
    include_callees: bool = True,
    depth: int = 2
) -> dict:
    """
    获取函数的完整调用图
    
    Args:
        function_name: 函数名称
        include_callers: 是否包含调用者（默认True）
        include_callees: 是否包含被调用者（默认True）
        depth: 深度（默认2层，最大5层）
    
    Returns:
        dict: 调用图数据（包含节点和边）
    
    Example:
        >>> await get_call_graph("main", depth=2)
        {
            "success": True,
            "function": "main",
            "nodes": [{...}, {...}],
            "edges": [{...}, {...}],
            "node_count": 10,
            "edge_count": 12
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    if depth < 1 or depth > 5:
        return {
            "success": False,
            "error": "Depth must be between 1 and 5"
        }
    
    service = CallGraphService(ServerState.query_executor)
    return await service.get_call_graph(
        function_name,
        include_callers,
        include_callees,
        depth
    )

