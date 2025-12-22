"""批量操作MCP工具

提供批量分析功能：
- batch_query: 批量执行查询
- batch_function_analysis: 批量分析函数

多项目支持：batch_function_analysis 要求指定 project_name 参数。
batch_query 执行原始查询，用户需在查询中自行指定项目前缀。
"""

import asyncio

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.project_utils import get_safe_cpg_prefix


@mcp.tool()
async def batch_query(queries: list[str], timeout: int = 300) -> dict:
    """
    批量执行多个查询

    Args:
        queries: 查询列表（Scala查询语句）
        timeout: 每个查询的超时时间（秒）

    Returns:
        dict: 批量查询结果

    Example:
        >>> await batch_query([
        ...     'workspace.project("myproject").get.cpg.get.method.name',
        ...     'workspace.project("myproject").get.cpg.get.call.name'
        ... ])
        {
            "success": true,
            "results": [...],
            "total": 2,
            "succeeded": 2,
            "failed": 0
        }

    Note:
        查询使用原始 Scala 语法，返回 JSON 格式。
        必须在查询中指定项目：workspace.project("name").get.cpg.get.method.name
        避免使用 .l 以防止输出截断（默认截断为 1000 字符）
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if len(queries) > 20:
        return {"success": False, "error": "Maximum 20 queries allowed in batch"}

    logger.info(f"Executing batch query with {len(queries)} queries")

    results = []
    succeeded = 0
    failed = 0

    try:
        # 并发执行所有查询
        tasks = [
            server_state.query_executor.execute(query, timeout=timeout)
            for query in queries
        ]

        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(query_results):
            if isinstance(result, Exception):
                results.append(
                    {"query_index": i, "success": False, "error": str(result)}
                )
                failed += 1
            elif result.get("success"):
                results.append(
                    {
                        "query_index": i,
                        "success": True,
                        "result": result.get("stdout", ""),
                    }
                )
                succeeded += 1
            else:
                results.append(
                    {
                        "query_index": i,
                        "success": False,
                        "error": result.get("stderr", "Unknown error"),
                    }
                )
                failed += 1

        return {
            "success": True,
            "results": results,
            "total": len(queries),
            "succeeded": succeeded,
            "failed": failed,
        }

    except Exception as e:
        logger.exception(f"Error in batch query: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def batch_function_analysis(project_name: str, function_names: list[str]) -> dict:
    """
    批量分析多个函数

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        function_names: 函数名称列表

    Returns:
        dict: 批量分析结果

    Example:
        >>> await batch_function_analysis("webapp", ["main", "init"])
        {
            "success": true,
            "project": "webapp",
            "analyses": {
                "main": {"name": "main", "signature": "...", ...},
                "init": {...}
            },
            "count": 2,
            "analyzed": 2
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if len(function_names) > 10:
        return {"success": False, "error": "Maximum 10 functions allowed in batch"}

    logger.info(
        f"Batch analyzing {len(function_names)} functions (project: {project_name})"
    )

    try:
        # 安全获取 CPG 前缀，验证项目存在性
        cpg_prefix, error = await get_safe_cpg_prefix(
            server_state.query_executor, project_name
        )
        if error:
            return {"success": False, "error": error}

        analyses = {}

        for func_name in function_names:
            # 获取函数信息
            query = f'''
            {cpg_prefix}.method.name("{func_name}")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code,
                   "parameterCount" -> m.parameter.size
               ))
            '''

            result = await server_state.query_executor.execute(query)

            if result.get("success"):
                from joern_mcp.utils.response_parser import parse_joern_response

                stdout = result.get("stdout", "")
                try:
                    func_data = parse_joern_response(stdout)
                    if isinstance(func_data, list) and func_data:
                        analyses[func_name] = func_data[0]
                    elif isinstance(func_data, dict) and func_data:
                        analyses[func_name] = func_data
                    else:
                        # 空结果但解析成功
                        analyses[func_name] = None
                except (ValueError, Exception) as e:
                    # 解析失败，保留错误上下文
                    analyses[func_name] = {
                        "error": f"Failed to parse result: {e}",
                        "raw_output": stdout[:200],
                    }
            else:
                analyses[func_name] = {"error": result.get("stderr", "Query failed")}

        return {
            "success": True,
            "project": project_name,
            "analyses": analyses,
            "count": len(function_names),
            "analyzed": sum(1 for v in analyses.values() if v and "error" not in v),
        }

    except Exception as e:
        logger.exception(f"Error in batch function analysis: {e}")
        return {"success": False, "error": str(e)}
