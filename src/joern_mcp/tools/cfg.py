"""控制流分析MCP工具

提供控制流分析功能：
- get_control_flow_graph: 获取控制流图
- get_dominators: 获取支配树/支配关系
- analyze_control_structures: 分析控制结构

多项目支持：所有工具要求指定 project_name 参数。
"""

import re

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.project_utils import get_safe_cpg_prefix


def _clean_dot_string(stdout: str) -> str:
    """清理 DOT 格式字符串

    处理 Joern 返回的 DOT 字符串，移除多余的引号和转义字符。
    """
    result = stdout.strip()

    # 移除 Scala REPL 输出前缀（如 "val res0: String = "）
    if result.startswith("val "):
        match = re.search(r'=\s*(.+)', result, re.DOTALL)
        if match:
            result = match.group(1).strip()

    # 移除多层首尾双引号 (如 '""digraph...""')
    while result.startswith('""') and result.endswith('""') and len(result) > 4:
        result = result[2:-2]

    # 移除单层首尾引号
    if result.startswith('"') and result.endswith('"') and len(result) > 2:
        result = result[1:-1]

    # 处理转义字符
    result = result.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')

    return result


@mcp.tool()
async def get_control_flow_graph(
    project_name: str, function_name: str, format: str = "dot"
) -> dict:
    """
    获取函数的控制流图（CFG）

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_name: 函数名称
        format: 输出格式 ("dot", "json")

    Returns:
        dict: 控制流图数据

    Example:
        >>> await get_control_flow_graph("webapp", "main", format="dot")
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

    logger.info(f"Getting CFG for function: {function_name} (project: {project_name})")

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(server_state.query_executor, project_name)
        if error:
            return {"success": False, "error": error}

        # 构建查询
        if format == "dot":
            # dotCfg 返回 List[String]，使用 headOption.getOrElse("") 安全获取
            query = f'{cpg_prefix}.method.name("{function_name}").dotCfg.headOption.getOrElse("")'
        else:
            # JSON 格式：返回控制结构信息
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .ast.isControlStructure
               .map(cs => Map(
                   "type" -> cs.controlStructureType,
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            '''

        # 执行查询
        result = await server_state.query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "")
            cfg = _clean_dot_string(stdout) if format == "dot" else stdout

            return {
                "success": True,
                "project": project_name,
                "function": function_name,
                "cfg": cfg,
                "format": format,
            }
        else:
            return {"success": False, "error": result.get("stderr", "Query failed")}

    except Exception as e:
        logger.exception(f"Error getting CFG: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_dominators(
    project_name: str, function_name: str, format: str = "dot"
) -> dict:
    """
    获取函数的控制依赖图（CDG）

    注意：由于 Joern 版本兼容性问题，此工具返回控制依赖图（CDG）
    而不是传统的支配树。CDG 展示了控制流依赖关系。

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_name: 函数名称
        format: 输出格式 ("dot", "json")

    Returns:
        dict: 控制依赖图数据

    Example:
        >>> await get_dominators("webapp", "main")
        {
            "success": true,
            "project": "webapp",
            "function": "main",
            "dominators": "digraph CDG { ... }"
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Getting control dependency graph for function: {function_name} (project: {project_name})")

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(server_state.query_executor, project_name)
        if error:
            return {"success": False, "error": error}

        if format == "dot":
            # 使用 dotCdg（控制依赖图）替代 dotDom（支配树）
            # dotCdg 在大多数 Joern 版本中都可用
            query = f'{cpg_prefix}.method.name("{function_name}").dotCdg.headOption.getOrElse("")'
        else:
            # JSON 格式：返回控制依赖关系
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .ast
               .map(n => Map(
                   "id" -> n.id,
                   "label" -> n.label,
                   "code" -> n.code.take(50),
                   "line" -> n.lineNumber.getOrElse(-1)
               )).take(50)
            '''

        result = await server_state.query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "")
            dominators = _clean_dot_string(stdout) if format == "dot" else stdout

            return {
                "success": True,
                "project": project_name,
                "function": function_name,
                "dominators": dominators,
                "format": format,
                "note": "This returns Control Dependency Graph (CDG) for better compatibility",
            }
        else:
            stderr = result.get("stderr", "Query failed")
            # 如果 dotCdg 也不可用，提供有用的错误信息
            if "not a member" in stderr:
                return {
                    "success": False,
                    "error": "Control dependency graph not available. Try using get_control_flow_graph instead.",
                }
            return {"success": False, "error": stderr}

    except Exception as e:
        logger.exception(f"Error getting control dependency graph: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_control_structures(
    project_name: str, function_name: str
) -> dict:
    """
    分析函数中的控制结构

    根据 Joern CPGQL 文档，使用多种策略获取控制结构：
    1. 直接使用 cpg.controlStructure（全局）
    2. 使用 method.ast.isControlStructure（方法内）
    3. 使用 filter 筛选 CONTROL_STRUCTURE 标签

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_name: 函数名称

    Returns:
        dict: 控制结构列表

    Example:
        >>> await analyze_control_structures("webapp", "main")
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

    Reference:
        https://docs.joern.io/cpgql/calls/
        https://docs.joern.io/cpgql/node-type-steps/
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Analyzing control structures in: {function_name} (project: {project_name})")

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(server_state.query_executor, project_name)
        if error:
            return {"success": False, "error": error}

        # 策略列表：按可靠性顺序尝试不同的查询方式
        # 使用最简单直接的属性访问，避免类型问题
        queries = [
            # 策略1: 使用 cpg.controlStructure + parserTypeName
            f'''
            {cpg_prefix}.controlStructure
               .where(_.method.name("{function_name}"))
               .map(cs => Map(
                   "type" -> cs.parserTypeName,
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            ''',
            # 策略2: 使用 method.controlStructure（直接遍历方法的控制结构）
            f'''
            {cpg_prefix}.method.name("{function_name}")
               .controlStructure
               .map(cs => Map(
                   "type" -> cs.parserTypeName,
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            ''',
            # 策略3: 使用 ast + label 过滤，只返回 code 和 line
            f'''
            {cpg_prefix}.method.name("{function_name}")
               .ast.filter(_.label == "CONTROL_STRUCTURE")
               .map(cs => Map(
                   "type" -> "CONTROL_STRUCTURE",
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            ''',
        ]

        from joern_mcp.utils.response_parser import safe_parse_joern_response

        # 依次尝试每个查询策略
        for i, query in enumerate(queries):
            result = await server_state.query_executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                structures = safe_parse_joern_response(stdout, default=[])

                if not isinstance(structures, list):
                    structures = [structures] if structures else []

                # 如果获取到结果，返回
                if structures:
                    logger.debug(f"Control structures found using strategy {i + 1}")
                    return {
                        "success": True,
                        "project": project_name,
                        "function": function_name,
                        "structures": structures,
                        "count": len(structures),
                    }
                # 结果为空但查询成功，继续尝试下一个策略
                logger.debug(f"Strategy {i + 1} returned empty result, trying next...")
            else:
                stderr = result.get("stderr", "")
                logger.debug(f"Strategy {i + 1} failed: {stderr[:100]}")

        # 所有策略都没找到控制结构，可能函数确实没有控制结构
        # 返回空列表而不是错误
        return {
            "success": True,
            "project": project_name,
            "function": function_name,
            "structures": [],
            "count": 0,
            "note": "No control structures found. This is normal for simple functions without if/for/while statements.",
        }

    except Exception as e:
        logger.exception(f"Error analyzing control structures: {e}")
        return {"success": False, "error": str(e)}
