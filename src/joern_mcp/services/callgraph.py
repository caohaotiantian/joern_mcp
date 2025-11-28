"""调用图分析服务"""
import json
from typing import List, Dict, Optional, Set
from loguru import logger
from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.joern.templates import QueryTemplates


class CallGraphService:
    """调用图分析服务"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    async def get_callers(
        self,
        function_name: str,
        depth: int = 1
    ) -> Dict:
        """
        获取函数的调用者
        
        Args:
            function_name: 函数名称
            depth: 调用深度（默认1层）
            
        Returns:
            dict: 调用者列表
        """
        logger.info(f"Getting callers for function: {function_name}")
        
        try:
            if depth == 1:
                # 使用预定义模板
                query = QueryTemplates.build("GET_CALLERS", name=function_name)
            else:
                # 多层调用
                query = f'''
                cpg.method.name("{function_name}")
                   .repeat(_.caller)(_.times({depth}))
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "signature" -> m.signature,
                       "filename" -> m.filename,
                       "lineNumber" -> m.lineNumber.getOrElse(-1)
                   ))
                '''
            
            result = await self.executor.execute(query)
            
            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    callers = json.loads(stdout)
                    return {
                        "success": True,
                        "function": function_name,
                        "depth": depth,
                        "callers": callers if isinstance(callers, list) else [callers],
                        "count": len(callers) if isinstance(callers, list) else 1
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
            logger.exception(f"Error getting callers: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_callees(
        self,
        function_name: str,
        depth: int = 1
    ) -> Dict:
        """
        获取函数调用的其他函数
        
        Args:
            function_name: 函数名称
            depth: 调用深度（默认1层）
            
        Returns:
            dict: 被调用函数列表
        """
        logger.info(f"Getting callees for function: {function_name}")
        
        try:
            if depth == 1:
                query = QueryTemplates.build("GET_CALLEES", name=function_name)
            else:
                query = f'''
                cpg.method.name("{function_name}")
                   .repeat(_.callee)(_.times({depth}))
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "signature" -> m.signature,
                       "filename" -> m.filename,
                       "lineNumber" -> m.lineNumber.getOrElse(-1)
                   ))
                '''
            
            result = await self.executor.execute(query)
            
            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    callees = json.loads(stdout)
                    return {
                        "success": True,
                        "function": function_name,
                        "depth": depth,
                        "callees": callees if isinstance(callees, list) else [callees],
                        "count": len(callees) if isinstance(callees, list) else 1
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
            logger.exception(f"Error getting callees: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_call_chain(
        self,
        function_name: str,
        max_depth: int = 5,
        direction: str = "up"
    ) -> Dict:
        """
        获取函数的调用链
        
        Args:
            function_name: 函数名称
            max_depth: 最大深度
            direction: 方向 (up=调用者链, down=被调用者链)
            
        Returns:
            dict: 调用链
        """
        logger.info(f"Getting call chain for function: {function_name}, direction: {direction}")
        
        try:
            if direction == "up":
                # 向上追踪调用者
                query = f'''
                cpg.method.name("{function_name}")
                   .repeat(_.caller)(_.times({max_depth}))
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "filename" -> m.filename,
                       "depth" -> "unknown"
                   ))
                '''
            else:
                # 向下追踪被调用者
                query = f'''
                cpg.method.name("{function_name}")
                   .repeat(_.callee)(_.times({max_depth}))
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "filename" -> m.filename,
                       "depth" -> "unknown"
                   ))
                '''
            
            result = await self.executor.execute(query)
            
            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    chain = json.loads(stdout)
                    return {
                        "success": True,
                        "function": function_name,
                        "direction": direction,
                        "max_depth": max_depth,
                        "chain": chain if isinstance(chain, list) else [chain],
                        "count": len(chain) if isinstance(chain, list) else 1
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
            logger.exception(f"Error getting call chain: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_call_graph(
        self,
        function_name: str,
        include_callers: bool = True,
        include_callees: bool = True,
        depth: int = 2
    ) -> Dict:
        """
        获取函数的完整调用图
        
        Args:
            function_name: 函数名称
            include_callers: 是否包含调用者
            include_callees: 是否包含被调用者
            depth: 深度
            
        Returns:
            dict: 调用图数据
        """
        logger.info(f"Building call graph for function: {function_name}")
        
        graph = {
            "success": True,
            "function": function_name,
            "nodes": [],
            "edges": []
        }
        
        try:
            # 获取调用者
            if include_callers:
                callers_result = await self.get_callers(function_name, depth)
                if callers_result.get("success"):
                    callers = callers_result.get("callers", [])
                    for caller in callers:
                        if isinstance(caller, dict):
                            graph["nodes"].append({
                                "id": caller.get("name", "unknown"),
                                "type": "caller",
                                "filename": caller.get("filename", ""),
                                "lineNumber": caller.get("lineNumber", -1)
                            })
                            graph["edges"].append({
                                "from": caller.get("name", "unknown"),
                                "to": function_name,
                                "type": "calls"
                            })
            
            # 添加目标函数
            graph["nodes"].append({
                "id": function_name,
                "type": "target",
                "filename": "",
                "lineNumber": -1
            })
            
            # 获取被调用者
            if include_callees:
                callees_result = await self.get_callees(function_name, depth)
                if callees_result.get("success"):
                    callees = callees_result.get("callees", [])
                    for callee in callees:
                        if isinstance(callee, dict):
                            graph["nodes"].append({
                                "id": callee.get("name", "unknown"),
                                "type": "callee",
                                "filename": callee.get("filename", ""),
                                "lineNumber": callee.get("lineNumber", -1)
                            })
                            graph["edges"].append({
                                "from": function_name,
                                "to": callee.get("name", "unknown"),
                                "type": "calls"
                            })
            
            # 去重节点
            seen = set()
            unique_nodes = []
            for node in graph["nodes"]:
                node_id = node["id"]
                if node_id not in seen:
                    seen.add(node_id)
                    unique_nodes.append(node)
            graph["nodes"] = unique_nodes
            
            graph["node_count"] = len(graph["nodes"])
            graph["edge_count"] = len(graph["edges"])
            
            return graph
            
        except Exception as e:
            logger.exception(f"Error building call graph: {e}")
            return {
                "success": False,
                "error": str(e)
            }

