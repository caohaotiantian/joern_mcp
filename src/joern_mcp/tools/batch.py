"""批量操作MCP工具"""

import asyncio
from typing import List, Dict
from loguru import logger
from joern_mcp.mcp_server import mcp, server_state


@mcp.tool()
async def batch_query(queries: List[str], timeout: int = 300) -> dict:
    """
    批量执行多个查询

    Args:
        queries: 查询列表（Scala查询语句）
        timeout: 每个查询的超时时间（秒）

    Returns:
        dict: 批量查询结果

    Example:
        >>> await batch_query([
        ...     "cpg.method.name.l",
        ...     "cpg.call.name.l"
        ... ])
        {
            "success": True,
            "results": [...],
            "total": 2,
            "succeeded": 2,
            "failed": 0
        }
    """
    if not ServerState.query_executor:
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
            ServerState.query_executor.execute(query, timeout=timeout)
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
async def batch_function_analysis(function_names: List[str]) -> dict:
    """
    批量分析多个函数

    Args:
        function_names: 函数名称列表

    Returns:
        dict: 批量分析结果

    Example:
        >>> await batch_function_analysis(["main", "init", "cleanup"])
        {
            "success": True,
            "analyses": {
                "main": {"code": "...", "callers": [...], ...},
                "init": {...},
                "cleanup": {...}
            },
            "count": 3
        }
    """
    if not ServerState.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if len(function_names) > 10:
        return {"success": False, "error": "Maximum 10 functions allowed in batch"}

    logger.info(f"Batch analyzing {len(function_names)} functions")

    analyses = {}

    try:
        for func_name in function_names:
            # 获取函数信息
            query = f'''
            cpg.method.name("{func_name}")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code,
                   "parameterCount" -> m.parameter.size,
                   "complexity" -> m.cyclomatic Complexity.getOrElse(-1)
               ))
            '''

            result = await ServerState.query_executor.execute(query)

            if result.get("success"):
                import json

                try:
                    func_data = json.loads(result.get("stdout", "[]"))
                    analyses[func_name] = func_data[0] if func_data else None
                except json.JSONDecodeError:
                    analyses[func_name] = {"error": "Failed to parse result"}
            else:
                analyses[func_name] = {"error": result.get("stderr", "Query failed")}

        return {
            "success": True,
            "analyses": analyses,
            "count": len(function_names),
            "analyzed": sum(1 for v in analyses.values() if v and "error" not in v),
        }

    except Exception as e:
        logger.exception(f"Error in batch function analysis: {e}")
        return {"success": False, "error": str(e)}
