"""调用图分析服务

支持多项目查询：所有方法接受可选的 project_name 参数，
不指定时使用当前活动项目。
"""

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.joern.templates import QueryTemplates
from joern_mcp.utils.response_parser import safe_parse_joern_response


def _get_cpg_prefix(project_name: str | None) -> str:
    """获取 CPG 访问前缀

    workspace.project() 返回 Option[Project]，需要先 .get 获取 Project，
    然后 Project.cpg 返回 Option[Cpg]，再 .get 获取 Cpg。
    """
    if project_name:
        return f'workspace.project("{project_name}").get.cpg.get'
    return "cpg"


class CallGraphService:
    """调用图分析服务

    提供函数调用关系分析：
    - 获取调用者 (callers)
    - 获取被调用者 (callees)
    - 调用链追踪
    - 完整调用图构建

    所有方法支持 project_name 参数指定项目范围。
    """

    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor

    async def get_callers(
        self, function_name: str, depth: int = 1, project_name: str | None = None
    ) -> dict:
        """
        获取函数的调用者

        Args:
            function_name: 函数名称
            depth: 调用深度（默认1层）
            project_name: 项目名称（可选）

        Returns:
            dict: 调用者列表
        """
        logger.info(f"Getting callers for function: {function_name} (project: {project_name or 'current'})")

        try:
            cpg_prefix = _get_cpg_prefix(project_name)

            if depth == 1 and not project_name:
                query = QueryTemplates.build("GET_CALLERS", name=function_name)
            else:
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .repeat(_.caller)(_.maxDepth({depth}))
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
                callers = safe_parse_joern_response(stdout, default=[])

                if not isinstance(callers, list):
                    callers = [callers] if callers else []

                response = {
                    "success": True,
                    "function": function_name,
                    "depth": depth,
                    "callers": callers,
                    "count": len(callers),
                }
                if project_name:
                    response["project"] = project_name
                return response
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error getting callers: {e}")
            return {"success": False, "error": str(e)}

    async def get_callees(
        self, function_name: str, depth: int = 1, project_name: str | None = None
    ) -> dict:
        """
        获取函数调用的其他函数

        Args:
            function_name: 函数名称
            depth: 调用深度（默认1层）
            project_name: 项目名称（可选）

        Returns:
            dict: 被调用函数列表
        """
        logger.info(f"Getting callees for function: {function_name} (project: {project_name or 'current'})")

        try:
            cpg_prefix = _get_cpg_prefix(project_name)

            if depth == 1 and not project_name:
                query = QueryTemplates.build("GET_CALLEES", name=function_name)
            else:
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .repeat(_.callee)(_.maxDepth({depth}))
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
                callees = safe_parse_joern_response(stdout, default=[])

                if not isinstance(callees, list):
                    callees = [callees] if callees else []

                response = {
                    "success": True,
                    "function": function_name,
                    "depth": depth,
                    "callees": callees,
                    "count": len(callees),
                }
                if project_name:
                    response["project"] = project_name
                return response
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error getting callees: {e}")
            return {"success": False, "error": str(e)}

    async def get_call_chain(
        self,
        function_name: str,
        max_depth: int = 5,
        direction: str = "up",
        project_name: str | None = None,
    ) -> dict:
        """
        获取函数的调用链

        Args:
            function_name: 函数名称
            max_depth: 最大深度
            direction: 方向 (up=调用者链, down=被调用者链)
            project_name: 项目名称（可选）

        Returns:
            dict: 调用链
        """
        logger.info(
            f"Getting call chain for function: {function_name}, direction: {direction} "
            f"(project: {project_name or 'current'})"
        )

        try:
            cpg_prefix = _get_cpg_prefix(project_name)

            if direction == "up":
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .repeat(_.caller)(_.maxDepth({max_depth}))
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "filename" -> m.filename,
                       "depth" -> "unknown"
                   ))
                '''
            else:
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .repeat(_.callee)(_.maxDepth({max_depth}))
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
                chain = safe_parse_joern_response(stdout, default=[])

                if not isinstance(chain, list):
                    chain = [chain] if chain else []

                response = {
                    "success": True,
                    "function": function_name,
                    "direction": direction,
                    "max_depth": max_depth,
                    "chain": chain,
                    "count": len(chain),
                }
                if project_name:
                    response["project"] = project_name
                return response
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error getting call chain: {e}")
            return {"success": False, "error": str(e)}

    async def get_call_graph(
        self,
        function_name: str,
        include_callers: bool = True,
        include_callees: bool = True,
        depth: int = 2,
        project_name: str | None = None,
    ) -> dict:
        """
        获取函数的完整调用图

        Args:
            function_name: 函数名称
            include_callers: 是否包含调用者
            include_callees: 是否包含被调用者
            depth: 深度
            project_name: 项目名称（可选）

        Returns:
            dict: 调用图数据（节点和边）
        """
        logger.info(f"Building call graph for function: {function_name} (project: {project_name or 'current'})")

        graph = {"success": True, "function": function_name, "nodes": [], "edges": []}
        if project_name:
            graph["project"] = project_name

        try:
            # 获取调用者
            if include_callers:
                callers_result = await self.get_callers(function_name, depth, project_name)
                if callers_result.get("success"):
                    for caller in callers_result.get("callers", []):
                        if isinstance(caller, dict):
                            graph["nodes"].append({
                                "id": caller.get("name", "unknown"),
                                "type": "caller",
                                "filename": caller.get("filename", ""),
                                "lineNumber": caller.get("lineNumber", -1),
                            })
                            graph["edges"].append({
                                "from": caller.get("name", "unknown"),
                                "to": function_name,
                                "type": "calls",
                            })

            # 添加目标函数
            graph["nodes"].append({
                "id": function_name,
                "type": "target",
                "filename": "",
                "lineNumber": -1,
            })

            # 获取被调用者
            if include_callees:
                callees_result = await self.get_callees(function_name, depth, project_name)
                if callees_result.get("success"):
                    for callee in callees_result.get("callees", []):
                        if isinstance(callee, dict):
                            graph["nodes"].append({
                                "id": callee.get("name", "unknown"),
                                "type": "callee",
                                "filename": callee.get("filename", ""),
                                "lineNumber": callee.get("lineNumber", -1),
                            })
                            graph["edges"].append({
                                "from": function_name,
                                "to": callee.get("name", "unknown"),
                                "type": "calls",
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
            return {"success": False, "error": str(e)}
