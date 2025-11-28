"""代码查询MCP工具"""
import json
from typing import Optional
from loguru import logger
from joern_mcp.mcp_server import mcp, ServerState


@mcp.tool()
async def get_function_code(
    function_name: str,
    file_filter: Optional[str] = None
) -> dict:
    """
    获取指定函数的源代码
    
    Args:
        function_name: 函数名称（支持正则表达式）
        file_filter: 文件路径过滤（可选，正则表达式）
    
    Returns:
        dict: 函数信息，包含源代码、位置等
    
    Example:
        >>> await get_function_code("main")
        {
            "success": True,
            "functions": [{
                "name": "main",
                "signature": "int main()",
                "filename": "main.c",
                "lineNumber": 10,
                "code": "int main() { ... }"
            }],
            "count": 1
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Getting function code: {function_name}")
    
    try:
        # 构建查询
        if file_filter:
            query = f'''
            cpg.method.name("{function_name}")
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
            cpg.method.name("{function_name}")
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
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            # 解析JSON结果
            stdout = result.get("stdout", "")
            try:
                functions = json.loads(stdout)
                return {
                    "success": True,
                    "functions": functions if isinstance(functions, list) else [functions],
                    "count": len(functions) if isinstance(functions, list) else 1
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error getting function code: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def list_functions(
    name_filter: Optional[str] = None,
    limit: int = 100
) -> dict:
    """
    列出所有函数
    
    Args:
        name_filter: 名称过滤（正则表达式，可选）
        limit: 返回数量限制（默认100）
    
    Returns:
        dict: 函数列表
    
    Example:
        >>> await list_functions(name_filter=".*main.*", limit=10)
        {
            "success": True,
            "functions": ["main", "main_helper"],
            "count": 2
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Listing functions (filter: {name_filter}, limit: {limit})")
    
    try:
        # 构建查询
        if name_filter:
            query = f'''
            cpg.method.name(".*{name_filter}.*")
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            '''
        else:
            query = f'''
            cpg.method
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            '''
        
        # 执行查询
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            try:
                functions = json.loads(stdout)
                return {
                    "success": True,
                    "functions": functions,
                    "count": len(functions) if isinstance(functions, list) else 1
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error listing functions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_code(
    pattern: str,
    scope: str = "all"
) -> dict:
    """
    搜索代码
    
    Args:
        pattern: 搜索模式（正则表达式）
        scope: 搜索范围 (all, methods, calls, identifiers)
    
    Returns:
        dict: 匹配结果
    
    Example:
        >>> await search_code("strcpy", scope="calls")
        {
            "success": True,
            "matches": [{
                "code": "strcpy(dst, src)",
                "filename": "main.c",
                "lineNumber": 25
            }],
            "count": 1
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Searching code: {pattern} in {scope}")
    
    try:
        # 根据scope构建查询
        if scope == "methods":
            query = f'cpg.method.name(".*{pattern}.*")'
        elif scope == "calls":
            query = f'cpg.call.name(".*{pattern}.*")'
        elif scope == "identifiers":
            query = f'cpg.identifier.name(".*{pattern}.*")'
        else:  # all
            query = f'cpg.all.code(".*{pattern}.*")'
        
        query += '''.take(50).map(n => Map(
            "code" -> n.code,
            "type" -> n.label,
            "file" -> n.file.name.headOption.getOrElse("unknown"),
            "line" -> n.lineNumber.getOrElse(-1)
        ))'''
        
        # 执行查询
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            try:
                matches = json.loads(stdout)
                return {
                    "success": True,
                    "matches": matches,
                    "count": len(matches) if isinstance(matches, list) else 1,
                    "scope": scope
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error searching code: {e}")
        return {
            "success": False,
            "error": str(e)
        }

