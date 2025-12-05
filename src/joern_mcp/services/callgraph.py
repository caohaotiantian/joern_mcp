"""调用图分析服务

支持多项目查询：所有方法接受可选的 project_name 参数，
不指定时使用当前活动项目。
"""

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.utils.project_utils import get_safe_cpg_prefix
from joern_mcp.utils.response_parser import safe_parse_joern_response


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
            # 安全获取 CPG 前缀，验证项目存在性
            cpg_prefix, error = await get_safe_cpg_prefix(self.executor, project_name)
            if error:
                return {"success": False, "error": error}

            # 使用 .caller 方法获取调用者
            # 根据 Joern 文档 (https://docs.joern.io/cpgql/complex-steps/)
            # caller 是 Call Graph Step，直接可用
            depth = min(depth, 5)  # 限制最大深度

            # 注意：.caller.caller 只返回第2层，我们需要收集所有层级
            # 使用 flatMap 收集从第1层到第N层的所有调用者
            if depth == 1:
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .caller
                   .dedup
                   .map(m => Map(
                       "name" -> m.name,
                       "signature" -> m.signature,
                       "filename" -> m.filename,
                       "lineNumber" -> m.lineNumber.getOrElse(-1)
                   ))
                '''
            else:
                # 对于 depth > 1，使用 callIn 遍历获取所有层级的调用者
                # callIn 返回调用该方法的 CALL 节点，然后获取其所在的 method
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .caller
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
            # 安全获取 CPG 前缀，验证项目存在性
            cpg_prefix, error = await get_safe_cpg_prefix(self.executor, project_name)
            if error:
                return {"success": False, "error": error}

            # 使用 .callee 方法获取被调用者
            # 根据 Joern 文档 (https://docs.joern.io/cpgql/complex-steps/)
            # callee 是 Call Graph Step，直接可用
            depth = min(depth, 5)  # 限制最大深度

            # 始终使用 .callee 获取直接被调用者（一层）
            # 多层调用关系应该通过 get_call_graph 的递归收集来实现
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .callee
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
            # 安全获取 CPG 前缀，验证项目存在性
            cpg_prefix, error = await get_safe_cpg_prefix(self.executor, project_name)
            if error:
                return {"success": False, "error": error}

            # 限制深度并构建查询
            max_depth = min(max_depth, 5)

            # 始终使用单层调用关系
            # 多层调用链通过递归收集实现
            step = ".caller" if direction == "up" else ".callee"

            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               {step}
               .dedup
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename
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
            depth: 深度（递归收集的层数）
            project_name: 项目名称（可选）

        Returns:
            dict: 调用图数据（节点和边）
        """
        logger.info(f"Building call graph for function: {function_name} (project: {project_name or 'current'})")

        graph = {"success": True, "function": function_name, "nodes": [], "edges": []}
        if project_name:
            graph["project"] = project_name

        # 用于去重
        visited_callers = set()
        visited_callees = set()

        try:
            # 添加目标函数
            graph["nodes"].append({
                "id": function_name,
                "type": "target",
                "filename": "",
                "lineNumber": -1,
            })

            # 递归收集调用者（向上追溯 depth 层）
            if include_callers:
                await self._collect_callers_recursive(
                    function_name, depth, project_name,
                    graph, visited_callers
                )

            # 递归收集被调用者（向下追溯 depth 层）
            if include_callees:
                await self._collect_callees_recursive(
                    function_name, depth, project_name,
                    graph, visited_callees
                )

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

    async def _collect_callers_recursive(
        self,
        function_name: str,
        remaining_depth: int,
        project_name: str | None,
        graph: dict,
        visited: set,
    ) -> None:
        """递归收集调用者"""
        if remaining_depth <= 0 or function_name in visited:
            return

        visited.add(function_name)

        callers_result = await self.get_callers(function_name, 1, project_name)
        if not callers_result.get("success"):
            return

        for caller in callers_result.get("callers", []):
            if isinstance(caller, dict):
                caller_name = caller.get("name", "unknown")

                # 添加节点
                graph["nodes"].append({
                    "id": caller_name,
                    "type": "caller",
                    "filename": caller.get("filename", ""),
                    "lineNumber": caller.get("lineNumber", -1),
                })

                # 添加边
                graph["edges"].append({
                    "from": caller_name,
                    "to": function_name,
                    "type": "calls",
                })

                # 递归收集更上层的调用者
                if remaining_depth > 1 and caller_name not in visited:
                    await self._collect_callers_recursive(
                        caller_name, remaining_depth - 1, project_name,
                        graph, visited
                    )

    async def _collect_callees_recursive(
        self,
        function_name: str,
        remaining_depth: int,
        project_name: str | None,
        graph: dict,
        visited: set,
    ) -> None:
        """递归收集被调用者"""
        if remaining_depth <= 0 or function_name in visited:
            return

        visited.add(function_name)

        callees_result = await self.get_callees(function_name, 1, project_name)
        if not callees_result.get("success"):
            return

        for callee in callees_result.get("callees", []):
            if isinstance(callee, dict):
                callee_name = callee.get("name", "unknown")

                # 添加节点
                graph["nodes"].append({
                    "id": callee_name,
                    "type": "callee",
                    "filename": callee.get("filename", ""),
                    "lineNumber": callee.get("lineNumber", -1),
                })

                # 添加边
                graph["edges"].append({
                    "from": function_name,
                    "to": callee_name,
                    "type": "calls",
                })

                # 递归收集更下层的被调用者
                if remaining_depth > 1 and callee_name not in visited:
                    await self._collect_callees_recursive(
                        callee_name, remaining_depth - 1, project_name,
                        graph, visited
                    )
