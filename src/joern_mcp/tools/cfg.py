"""控制流分析MCP工具

提供控制流分析功能：
- get_control_flow_graph: 获取控制流图
- get_dominators: 获取支配树
- analyze_control_structures: 分析控制结构

多项目支持：所有工具支持可选的 project_name 参数。
"""

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state


def _get_cpg_prefix(project_name: str | None) -> str:
    """获取 CPG 访问前缀"""
    if project_name:
        return f'workspace.project("{project_name}").cpg.get'
    return "cpg"


@mcp.tool()
async def get_control_flow_graph(
    function_name: str, format: str = "dot", project_name: str | None = None
) -> dict:
    """
    获取函数的控制流图（CFG）

    Args:
        function_name: 函数名称
        format: 输出格式 ("dot", "json")
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 控制流图数据

    Example:
        >>> await get_control_flow_graph("main", format="dot", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "main",
            "cfg": "digraph CFG { ... }",
            "format": "dot"
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Getting CFG for function: {function_name} (project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        # 构建查询
        if format == "dot":
            query = f'{cpg_prefix}.method.name("{function_name}").dotCfg.l'
        else:
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .controlStructure
               .map(cs => Map(
                   "type" -> cs.controlStructureType,
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            '''

        # 执行查询（不自动添加.toJson，因为dotCfg返回的是字符串）
        result = await server_state.query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "")
            response = {
                "success": True,
                "function": function_name,
                "cfg": stdout,
                "format": format,
            }
            if project_name:
                response["project"] = project_name
            return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error getting CFG: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_dominators(
    function_name: str, format: str = "dot", project_name: str | None = None
) -> dict:
    """
    获取函数的支配树

    Args:
        function_name: 函数名称
        format: 输出格式 ("dot", "json")
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 支配树数据

    Example:
        >>> await get_dominators("main", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "main",
            "dominators": "digraph DOM { ... }"
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Getting dominators for function: {function_name} (project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        query = f'{cpg_prefix}.method.name("{function_name}").dotDom.l'
        result = await server_state.query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "")
            response = {
                "success": True,
                "function": function_name,
                "dominators": stdout,
                "format": format,
            }
            if project_name:
                response["project"] = project_name
            return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error getting dominators: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_control_structures(
    function_name: str, project_name: str | None = None
) -> dict:
    """
    分析函数中的控制结构

    Args:
        function_name: 函数名称
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 控制结构列表

    Example:
        >>> await analyze_control_structures("main", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "function": "main",
            "structures": [
                {"type": "IF", "code": "if (x > 0)", "line": 10},
                {"type": "FOR", "code": "for (i = 0; i < n; i++)", "line": 15}
            ],
            "count": 2
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Analyzing control structures in: {function_name} (project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        query = f'''
        {cpg_prefix}.method.name("{function_name}")
           .controlStructure
           .map(cs => Map(
               "type" -> cs.controlStructureType,
               "code" -> cs.code,
               "line" -> cs.lineNumber.getOrElse(-1),
               "file" -> cs.file.name.headOption.getOrElse("unknown")
           ))
        '''

        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            from joern_mcp.utils.response_parser import parse_joern_response

            stdout = result.get("stdout", "")
            try:
                structures = parse_joern_response(stdout)
                if not isinstance(structures, list):
                    structures = [structures] if structures else []

                response = {
                    "success": True,
                    "function": function_name,
                    "structures": structures,
                    "count": len(structures),
                }
                if project_name:
                    response["project"] = project_name
                return response
            except (ValueError, Exception):
                # 解析失败，返回原始输出供调试
                response = {
                    "success": True,
                    "function": function_name,
                    "raw_output": stdout,
                }
                if project_name:
                    response["project"] = project_name
                return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error analyzing control structures: {e}")
        return {"success": False, "error": str(e)}
