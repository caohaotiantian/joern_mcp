"""数据流分析MCP工具"""

from typing import Optional
from loguru import logger
from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.services.dataflow import DataFlowService


@mcp.tool()
async def track_dataflow(
    source_method: str, sink_method: str, max_flows: int = 10
) -> dict:
    """
    追踪从源方法到汇方法的数据流

    Args:
        source_method: 源方法名称
        sink_method: 汇方法名称
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 数据流信息

    Example:
        >>> await track_dataflow("gets", "system", max_flows=5)
        {
            "success": True,
            "source_method": "gets",
            "sink_method": "system",
            "flows": [...],
            "count": 3
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_flows < 1 or max_flows > 50:
        return {"success": False, "error": "Max flows must be between 1 and 50"}

    service = DataFlowService(server_state.query_executor)
    return await service.track_dataflow(source_method, sink_method, max_flows)


@mcp.tool()
async def analyze_variable_flow(
    variable_name: str, sink_method: Optional[str] = None, max_flows: int = 10
) -> dict:
    """
    分析变量的数据流

    Args:
        variable_name: 变量名称
        sink_method: 目标汇方法（可选）
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 变量流信息

    Example:
        >>> await analyze_variable_flow("user_input", sink_method="system")
        {
            "success": True,
            "variable": "user_input",
            "flows": [...],
            "count": 2
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_flows < 1 or max_flows > 50:
        return {"success": False, "error": "Max flows must be between 1 and 50"}

    service = DataFlowService(server_state.query_executor)
    return await service.analyze_variable_flow(variable_name, sink_method, max_flows)


@mcp.tool()
async def find_data_dependencies(
    function_name: str, variable_name: Optional[str] = None
) -> dict:
    """
    查找函数中的数据依赖关系

    Args:
        function_name: 函数名称
        variable_name: 变量名称（可选，如果指定则只查找该变量）

    Returns:
        dict: 数据依赖信息

    Example:
        >>> await find_data_dependencies("main", variable_name="buf")
        {
            "success": True,
            "function": "main",
            "variable": "buf",
            "dependencies": [...],
            "count": 5
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    service = DataFlowService(server_state.query_executor)
    return await service.find_data_dependencies(function_name, variable_name)
