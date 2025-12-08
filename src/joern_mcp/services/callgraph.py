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
            dict: 调用者列表，包含调用点的位置信息
        """
        logger.info(f"Getting callers for function: {function_name} (project: {project_name or 'current'})")

        try:
            # 安全获取 CPG 前缀，验证项目存在性
            cpg_prefix, error = await get_safe_cpg_prefix(self.executor, project_name)
            if error:
                return {"success": False, "error": error}

            depth = min(depth, 5)  # 限制最大深度

            # 使用 .callIn 获取调用节点（Call），而非 .caller 获取方法定义
            # .callIn 返回调用当前方法的 Call 节点，包含调用点的位置信息
            # .caller 返回调用者的方法定义，但缺少具体调用位置
            # 参考: https://docs.joern.io/cpgql/calls/
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .callIn
               .map(c => Map(
                   "name" -> c.method.name,
                   "methodFullName" -> c.method.fullName,
                   "signature" -> c.method.signature,
                   "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
                   "lineNumber" -> c.lineNumber.getOrElse(-1),
                   "code" -> c.code
               ))
               .dedup
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
            dict: 被调用函数列表，包含调用点的位置信息
        """
        logger.info(f"Getting callees for function: {function_name} (project: {project_name or 'current'})")

        try:
            # 安全获取 CPG 前缀，验证项目存在性
            cpg_prefix, error = await get_safe_cpg_prefix(self.executor, project_name)
            if error:
                return {"success": False, "error": error}

            depth = min(depth, 5)  # 限制最大深度

            # 使用 .call 获取调用节点，而非 .callee 获取方法定义
            # .call 返回函数内的所有调用节点（Call），包含调用点的位置信息
            # .callee 返回被调用方法的定义（Method），外部库函数通常没有完整定义
            # 参考: https://docs.joern.io/cpgql/calls/
            query = f'''
            {cpg_prefix}.method.name("{function_name}")
               .call
               .filterNot(_.name == "<operator>.*")
               .map(c => Map(
                   "name" -> c.name,
                   "methodFullName" -> c.methodFullName,
                   "signature" -> c.signature,
                   "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
                   "lineNumber" -> c.lineNumber.getOrElse(-1),
                   "code" -> c.code
               ))
               .dedup
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

            # 向上追溯使用 .callIn（获取调用节点，包含位置信息）
            # 向下追溯使用 .call（获取调用节点，包含位置信息）
            if direction == "up":
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .callIn
                   .map(c => Map(
                       "name" -> c.method.name,
                       "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
                       "lineNumber" -> c.lineNumber.getOrElse(-1)
                   ))
                   .dedup
                '''
            else:
                # 向下追溯使用 .call 获取调用点信息
                query = f'''
                {cpg_prefix}.method.name("{function_name}")
                   .call
                   .filterNot(_.name == "<operator>.*")
                   .map(c => Map(
                       "name" -> c.name,
                       "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
                       "lineNumber" -> c.lineNumber.getOrElse(-1)
                   ))
                   .dedup
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

                # 添加节点（包含完整的调用信息）
                graph["nodes"].append({
                    "id": caller_name,
                    "type": "caller",
                    "methodFullName": caller.get("methodFullName", ""),
                    "signature": caller.get("signature", ""),
                    "filename": caller.get("filename", ""),
                    "lineNumber": caller.get("lineNumber", -1),
                    "code": caller.get("code", ""),
                })

                # 添加边（包含调用位置信息）
                graph["edges"].append({
                    "from": caller_name,
                    "to": function_name,
                    "type": "calls",
                    "lineNumber": caller.get("lineNumber", -1),
                    "code": caller.get("code", ""),
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

                # 添加节点（包含完整的调用信息）
                graph["nodes"].append({
                    "id": callee_name,
                    "type": "callee",
                    "methodFullName": callee.get("methodFullName", ""),
                    "signature": callee.get("signature", ""),
                    "filename": callee.get("filename", ""),
                    "lineNumber": callee.get("lineNumber", -1),
                    "code": callee.get("code", ""),
                })

                # 添加边（包含调用位置信息）
                graph["edges"].append({
                    "from": function_name,
                    "to": callee_name,
                    "type": "calls",
                    "lineNumber": callee.get("lineNumber", -1),
                    "code": callee.get("code", ""),
                })

                # 递归收集更下层的被调用者
                if remaining_depth > 1 and callee_name not in visited:
                    await self._collect_callees_recursive(
                        callee_name, remaining_depth - 1, project_name,
                        graph, visited
                    )
