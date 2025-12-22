"""代码查询MCP工具

提供代码搜索和函数分析功能：
- get_function_code: 获取函数源代码
- list_functions: 列出所有函数
- search_code: 搜索代码模式

多项目支持：
- 所有查询工具要求指定 project_name 参数
- 使用 list_projects 查看可用项目
- 使用 parse_project 导入新项目
"""

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.project_utils import get_safe_cpg_prefix
from joern_mcp.utils.response_parser import safe_parse_joern_response


@mcp.tool()
async def get_function_code(
    project_name: str, function_name: str, file_filter: str | None = None
) -> dict:
    """
    获取指定函数的源代码

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_name: 函数名称（支持正则表达式）
        file_filter: 文件路径过滤（可选，正则表达式）

    Returns:
        dict: 函数信息，包含源代码、位置等

    Example:
        >>> await get_function_code("webapp", "buffer_overflow")
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

    logger.info(f"Getting function code: {function_name} (project: {project_name})")

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(
            server_state.query_executor, project_name
        )
        if error:
            return {"success": False, "error": error}

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

            # 确保每个函数都是字典格式（处理多重编码问题）
            parsed_functions = []
            for func in functions:
                if isinstance(func, dict):
                    parsed_functions.append(func)
                elif isinstance(func, str):
                    # 尝试解析字符串为 JSON
                    import json

                    try:
                        parsed = json.loads(func)
                        if isinstance(parsed, dict):
                            parsed_functions.append(parsed)
                        elif isinstance(parsed, list):
                            parsed_functions.extend(parsed)
                        else:
                            parsed_functions.append({"code": str(parsed)})
                    except json.JSONDecodeError:
                        parsed_functions.append({"code": func})

            return {
                "success": True,
                "project": project_name,
                "functions": parsed_functions,
                "count": len(parsed_functions),
            }
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error getting function code: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_functions(
    project_name: str, name_filter: str | None = None, limit: int = 100
) -> dict:
    """
    列出所有函数

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        name_filter: 名称过滤（正则表达式，可选）
        limit: 返回数量限制（默认100）

    Returns:
        dict: 函数列表，每个函数包含名称、文件名和行号

    Example:
        >>> await list_functions("webapp", limit=5)
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

    logger.info(
        f"Listing functions (filter: {name_filter}, limit: {limit}, project: {project_name})"
    )

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(
            server_state.query_executor, project_name
        )
        if error:
            return {"success": False, "error": error}

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

            return {
                "success": True,
                "project": project_name,
                "functions": functions,
                "count": len(functions),
            }
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error listing functions: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_code(project_name: str, pattern: str, scope: str = "all") -> dict:
    """
    搜索代码

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        pattern: 搜索模式（正则表达式）
        scope: 搜索范围
            - "all": 搜索调用和标识符（默认）
            - "methods": 搜索方法/函数名
            - "calls": 搜索函数调用
            - "identifiers": 搜索标识符/变量名
            - "literals": 搜索字面量

    Returns:
        dict: 匹配结果，包含代码、类型、文件和行号

    Example:
        >>> await search_code("webapp", "strcpy", scope="calls")
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

    logger.info(f"Searching code: {pattern} in {scope} (project: {project_name})")

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(
            server_state.query_executor, project_name
        )
        if error:
            return {"success": False, "error": error}

        # 根据scope构建查询
        if scope == "methods":
            # 搜索方法名
            query = f"""{cpg_prefix}.method.name(".*{pattern}.*").take(50).map(n => Map(
                "code" -> n.name,
                "type" -> "METHOD",
                "file" -> n.filename,
                "line" -> n.lineNumber.getOrElse(-1)
            ))"""
        elif scope == "calls":
            # 搜索函数调用
            query = f"""{cpg_prefix}.call.name(".*{pattern}.*").take(50).map(n => Map(
                "code" -> n.code,
                "type" -> "CALL",
                "file" -> n.file.name.headOption.getOrElse("unknown"),
                "line" -> n.lineNumber.getOrElse(-1)
            ))"""
        elif scope == "identifiers":
            # 搜索标识符
            query = f"""{cpg_prefix}.identifier.name(".*{pattern}.*").take(50).map(n => Map(
                "code" -> n.code,
                "type" -> "IDENTIFIER",
                "file" -> n.file.name.headOption.getOrElse("unknown"),
                "line" -> n.lineNumber.getOrElse(-1)
            ))"""
        elif scope == "literals":
            # 搜索字面量
            query = f"""{cpg_prefix}.literal.code(".*{pattern}.*").take(50).map(n => Map(
                "code" -> n.code,
                "type" -> "LITERAL",
                "file" -> n.file.name.headOption.getOrElse("unknown"),
                "line" -> n.lineNumber.getOrElse(-1)
            ))"""
        else:  # all - 搜索调用和标识符
            # 使用 call 和 identifier 的组合来搜索
            query = f"""{cpg_prefix}.call.code(".*{pattern}.*").take(25).map(n => Map(
                "code" -> n.code,
                "type" -> "CALL",
                "file" -> n.file.name.headOption.getOrElse("unknown"),
                "line" -> n.lineNumber.getOrElse(-1)
            )) ++ {cpg_prefix}.identifier.name(".*{pattern}.*").take(25).map(n => Map(
                "code" -> n.code,
                "type" -> "IDENTIFIER",
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

            return {
                "success": True,
                "project": project_name,
                "matches": matches,
                "count": len(matches),
                "scope": scope,
            }
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error searching code: {e}")
        return {"success": False, "error": str(e)}
