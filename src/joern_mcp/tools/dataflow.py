"""数据流分析MCP工具

提供数据流追踪和分析功能：
- track_dataflow: 追踪数据流
- analyze_variable_flow: 分析变量流向
- find_data_dependencies: 查找数据依赖

多项目支持：所有工具要求指定 project_name 参数。
"""

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.services.dataflow import DataFlowService


@mcp.tool()
async def track_dataflow(
    project_name: str,
    source_method: str,
    sink_method: str,
    max_flows: int = 10,
) -> dict:
    """
    追踪从源方法到汇方法的数据流

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        source_method: 源方法名称
        sink_method: 汇方法名称
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 数据流信息

    Example:
        >>> await track_dataflow("webapp", "gets", "system")
        {
            "success": true,
            "project": "webapp",
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
    return await service.track_dataflow(source_method, sink_method, max_flows, project_name)


@mcp.tool()
async def analyze_variable_flow(
    project_name: str,
    variable_name: str,
    sink_method: str | None = None,
    max_flows: int = 10,
) -> dict:
    """
    分析变量的数据流

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        variable_name: 变量名称
        sink_method: 目标汇方法（可选）
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 变量流信息

    Example:
        >>> await analyze_variable_flow("webapp", "user_input", sink_method="system")
        {
            "success": true,
            "project": "webapp",
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
    return await service.analyze_variable_flow(variable_name, sink_method, max_flows, project_name)


@mcp.tool()
async def find_data_dependencies(
    project_name: str,
    function_name: str,
    variable_name: str | None = None,
) -> dict:
    """
    查找函数中的数据依赖关系

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_name: 函数名称
        variable_name: 变量名称（可选，如果指定则只查找该变量）

    Returns:
        dict: 数据依赖信息

    Example:
        >>> await find_data_dependencies("webapp", "main", variable_name="buf")
        {
            "success": true,
            "project": "webapp",
            "function": "main",
            "variable": "buf",
            "dependencies": [...],
            "count": 5
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    service = DataFlowService(server_state.query_executor)
    return await service.find_data_dependencies(function_name, variable_name, project_name)
