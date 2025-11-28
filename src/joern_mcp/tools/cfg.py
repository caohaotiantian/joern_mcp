"""控制流分析MCP工具"""
from typing import Optional
from loguru import logger
from joern_mcp.mcp_server import mcp, ServerState


@mcp.tool()
async def get_control_flow_graph(
    function_name: str,
    format: str = "dot"
) -> dict:
    """
    获取函数的控制流图（CFG）
    
    Args:
        function_name: 函数名称
        format: 输出格式 ("dot", "json")
    
    Returns:
        dict: 控制流图数据
    
    Example:
        >>> await get_control_flow_graph("main", format="dot")
        {
            "success": True,
            "function": "main",
            "cfg": "digraph CFG { ... }",
            "format": "dot"
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Getting CFG for function: {function_name}")
    
    try:
        # 构建查询
        if format == "dot":
            query = f'cpg.method.name("{function_name}").dotCfg.l'
        else:
            query = f'''
            cpg.method.name("{function_name}")
               .controlStructure
               .map(cs => Map(
                   "type" -> cs.controlStructureType,
                   "code" -> cs.code,
                   "line" -> cs.lineNumber.getOrElse(-1)
               ))
            '''
        
        # 执行查询（不自动添加.toJson，因为dotCfg返回的是字符串）
        result = await ServerState.query_executor.execute(query, format="raw")
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            return {
                "success": True,
                "function": function_name,
                "cfg": stdout,
                "format": format
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error getting CFG: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_dominators(
    function_name: str,
    format: str = "dot"
) -> dict:
    """
    获取函数的支配树
    
    Args:
        function_name: 函数名称
        format: 输出格式 ("dot", "json")
    
    Returns:
        dict: 支配树数据
    
    Example:
        >>> await get_dominators("main")
        {
            "success": True,
            "function": "main",
            "dominators": "digraph DOM { ... }"
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Getting dominators for function: {function_name}")
    
    try:
        query = f'cpg.method.name("{function_name}").dotDom.l'
        result = await ServerState.query_executor.execute(query, format="raw")
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            return {
                "success": True,
                "function": function_name,
                "dominators": stdout,
                "format": format
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error getting dominators: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def analyze_control_structures(
    function_name: str
) -> dict:
    """
    分析函数中的控制结构
    
    Args:
        function_name: 函数名称
    
    Returns:
        dict: 控制结构列表
    
    Example:
        >>> await analyze_control_structures("main")
        {
            "success": True,
            "function": "main",
            "structures": [
                {"type": "IF", "code": "if (x > 0)", "line": 10},
                {"type": "FOR", "code": "for (i = 0; i < n; i++)", "line": 15}
            ],
            "count": 2
        }
    """
    if not ServerState.query_executor:
        return {
            "success": False,
            "error": "Query executor not initialized"
        }
    
    logger.info(f"Analyzing control structures in: {function_name}")
    
    try:
        query = f'''
        cpg.method.name("{function_name}")
           .controlStructure
           .map(cs => Map(
               "type" -> cs.controlStructureType,
               "code" -> cs.code,
               "line" -> cs.lineNumber.getOrElse(-1),
               "file" -> cs.file.name.headOption.getOrElse("unknown")
           ))
        '''
        
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            import json
            stdout = result.get("stdout", "")
            try:
                structures = json.loads(stdout)
                return {
                    "success": True,
                    "function": function_name,
                    "structures": structures if isinstance(structures, list) else [structures] if structures else [],
                    "count": len(structures) if isinstance(structures, list) else (1 if structures else 0)
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "function": function_name,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error analyzing control structures: {e}")
        return {
            "success": False,
            "error": str(e)
        }

