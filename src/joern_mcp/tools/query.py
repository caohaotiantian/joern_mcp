"""代码查询MCP工具

提供代码搜索和函数分析功能：
- get_function_code: 获取函数源代码
- list_functions: 列出所有函数
- search_code: 搜索代码模式

多项目支持：
- 所有查询工具支持可选的 project_name 参数
- 不指定 project_name 时，查询当前活动项目
- 指定 project_name 时，仅在该项目范围内查询
"""

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.response_parser import safe_parse_joern_response


def _get_cpg_prefix(project_name: str | None) -> str:
    """
    获取 CPG 访问前缀

    Args:
        project_name: 项目名称（可选）

    Returns:
        str: CPG 访问语句前缀
             - None: 使用 "cpg" (当前活动项目)
             - 指定项目: 使用 workspace.project("name").cpg.get
    """
    if project_name:
        return f'workspace.project("{project_name}").cpg.get'
    return "cpg"


@mcp.tool()
async def get_function_code(
    function_name: str, file_filter: str | None = None, project_name: str | None = None
) -> dict:
    """
    获取指定函数的源代码

    Args:
        function_name: 函数名称（支持正则表达式）
        file_filter: 文件路径过滤（可选，正则表达式）
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 函数信息，包含源代码、位置等

    Example:
        >>> await get_function_code("buffer_overflow", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "functions": [
                {
                    "name": "buffer_overflow",
                    "signature": "void(char*)",
                    "filename": "vulnerable.c",
                    "lineNumber": 25,
                    "lineNumberEnd": 30,
                    "code": "void buffer_overflow(char *input) {...}"
                }
            ],
            "count": 1
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Getting function code: {function_name} (project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        # 构建查询
        if file_filter:
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .filename(".*{file_filter}.*")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code
               ))
            '''
        else:
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code
               ))
            '''

        # 执行查询
        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            stdout = result.get("stdout", "")
            functions = safe_parse_joern_response(stdout, default=[])

            if not isinstance(functions, list):
                functions = [functions] if functions else []

            response = {
                "success": True,
                "functions": functions,
                "count": len(functions),
            }
            if project_name:
                response["project"] = project_name
            return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error getting function code: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_functions(
    name_filter: str | None = None, limit: int = 100, project_name: str | None = None
) -> dict:
    """
    列出所有函数

    Args:
        name_filter: 名称过滤（正则表达式，可选）
        limit: 返回数量限制（默认100）
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 函数列表，每个函数包含名称、文件名和行号

    Example:
        >>> await list_functions(limit=5, project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "functions": [
                {"name": "command_injection", "filename": "vulnerable.c", "lineNumber": 15},
                {"name": "buffer_overflow", "filename": "vulnerable.c", "lineNumber": 25},
                {"name": "format_string", "filename": "vulnerable.c", "lineNumber": 35}
            ],
            "count": 3
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Listing functions (filter: {name_filter}, limit: {limit}, project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        # 构建查询
        if name_filter:
            query = f"""
            {cpg_prefix}.method.name(".*{name_filter}.*")
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            """
        else:
            query = f"""
            {cpg_prefix}.method
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            """

        # 执行查询
        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            stdout = result.get("stdout", "")
            functions = safe_parse_joern_response(stdout, default=[])

            if not isinstance(functions, list):
                functions = [functions] if functions else []

            response = {
                "success": True,
                "functions": functions,
                "count": len(functions),
            }
            if project_name:
                response["project"] = project_name
            return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error listing functions: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_code(
    pattern: str, scope: str = "all", project_name: str | None = None
) -> dict:
    """
    搜索代码

    Args:
        pattern: 搜索模式（正则表达式）
        scope: 搜索范围 (all, methods, calls, identifiers)
        project_name: 项目名称（可选，不指定则使用当前活动项目）

    Returns:
        dict: 匹配结果，包含代码、类型、文件和行号

    Example:
        >>> await search_code("strcpy", scope="calls", project_name="webapp")
        {
            "success": true,
            "project": "webapp",
            "matches": [
                {
                    "code": "strcpy(buffer, input)",
                    "type": "CALL",
                    "file": "vulnerable.c",
                    "line": 28
                }
            ],
            "count": 1,
            "scope": "calls"
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Searching code: {pattern} in {scope} (project: {project_name or 'current'})")

    try:
        cpg_prefix = _get_cpg_prefix(project_name)

        # 根据scope构建查询
        if scope == "methods":
            query = f'{cpg_prefix}.method.name(".*{pattern}.*")'
        elif scope == "calls":
            query = f'{cpg_prefix}.call.name(".*{pattern}.*")'
        elif scope == "identifiers":
            query = f'{cpg_prefix}.identifier.name(".*{pattern}.*")'
        else:  # all
            query = f'{cpg_prefix}.all.code(".*{pattern}.*")'

        query += """.take(50).map(n => Map(
            "code" -> n.code,
            "type" -> n.label,
            "file" -> n.file.name.headOption.getOrElse("unknown"),
            "line" -> n.lineNumber.getOrElse(-1)
        ))"""

        # 执行查询
        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            stdout = result.get("stdout", "")
            matches = safe_parse_joern_response(stdout, default=[])

            if not isinstance(matches, list):
                matches = [matches] if matches else []

            response = {
                "success": True,
                "matches": matches,
                "count": len(matches),
                "scope": scope,
            }
            if project_name:
                response["project"] = project_name
            return response
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error searching code: {e}")
        return {"success": False, "error": str(e)}
