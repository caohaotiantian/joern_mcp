"""数据流分析服务"""

import json

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor


class DataFlowService:
    """数据流分析服务"""

    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor

    async def track_dataflow(
        self, source_method: str, sink_method: str, max_flows: int = 10
    ) -> dict:
        """
        追踪从源方法到汇方法的数据流

        Args:
            source_method: 源方法名称
            sink_method: 汇方法名称
            max_flows: 最大流数量

        Returns:
            dict: 数据流信息
        """
        logger.info(f"Tracking dataflow from {source_method} to {sink_method}")

        try:
            # 使用正确的Joern查询语法（不使用def关键字）
            query = f'''
            val source = cpg.method.name("{source_method}").parameter
            val sink = cpg.call.name("{sink_method}").argument

            sink.reachableBy(source).flows.take({max_flows}).map(flow => Map(
                "source" -> Map(
                    "code" -> flow.source.code,
                    "method" -> flow.source.method.name,
                    "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                    "line" -> flow.source.lineNumber.getOrElse(-1)
                ),
                "sink" -> Map(
                    "code" -> flow.sink.code,
                    "method" -> flow.sink.method.name,
                    "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                    "line" -> flow.sink.lineNumber.getOrElse(-1)
                ),
                "pathLength" -> flow.elements.size,
                "path" -> flow.elements.take(20).map(e => Map(
                    "type" -> e.label,
                    "code" -> e.code,
                    "line" -> e.lineNumber.getOrElse(-1)
                ))
            ))
            '''

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    flows = json.loads(stdout)
                    return {
                        "success": True,
                        "source_method": source_method,
                        "sink_method": sink_method,
                        "flows": flows
                        if isinstance(flows, list)
                        else [flows]
                        if flows
                        else [],
                        "count": len(flows)
                        if isinstance(flows, list)
                        else (1 if flows else 0),
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "source_method": source_method,
                        "sink_method": sink_method,
                        "raw_output": stdout,
                    }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error tracking dataflow: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_variable_flow(
        self, variable_name: str, sink_method: str | None = None, max_flows: int = 10
    ) -> dict:
        """
        分析变量的数据流

        Args:
            variable_name: 变量名称
            sink_method: 目标汇方法（可选）
            max_flows: 最大流数量

        Returns:
            dict: 变量流信息
        """
        logger.info(f"Analyzing variable flow: {variable_name}")

        try:
            if sink_method:
                # 追踪到特定汇
                query = f'''
                val source = cpg.identifier.name("{variable_name}")
                val sink = cpg.call.name("{sink_method}").argument

                sink.reachableBy(source).flows.take({max_flows}).map(flow => Map(
                    "variable" -> "{variable_name}",
                    "source" -> Map(
                        "code" -> flow.source.code,
                        "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                        "line" -> flow.source.lineNumber.getOrElse(-1)
                    ),
                    "sink" -> Map(
                        "code" -> flow.sink.code,
                        "method" -> "{sink_method}",
                        "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                        "line" -> flow.sink.lineNumber.getOrElse(-1)
                    ),
                    "pathLength" -> flow.elements.size
                ))
                '''
            else:
                # 查找所有使用该变量的地方
                query = f'''
                cpg.identifier.name("{variable_name}")
                   .take({max_flows})
                   .map(i => Map(
                       "variable" -> "{variable_name}",
                       "code" -> i.code,
                       "type" -> i.typeFullName,
                       "method" -> i.method.name,
                       "file" -> i.file.name.headOption.getOrElse("unknown"),
                       "line" -> i.lineNumber.getOrElse(-1)
                   ))
                '''

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    flows = json.loads(stdout)
                    return {
                        "success": True,
                        "variable": variable_name,
                        "sink_method": sink_method,
                        "flows": flows
                        if isinstance(flows, list)
                        else [flows]
                        if flows
                        else [],
                        "count": len(flows)
                        if isinstance(flows, list)
                        else (1 if flows else 0),
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "variable": variable_name,
                        "raw_output": stdout,
                    }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error analyzing variable flow: {e}")
            return {"success": False, "error": str(e)}

    async def find_data_dependencies(
        self, function_name: str, variable_name: str | None = None
    ) -> dict:
        """
        查找函数中的数据依赖关系

        Args:
            function_name: 函数名称
            variable_name: 变量名称（可选，如果指定则只查找该变量）

        Returns:
            dict: 数据依赖信息
        """
        logger.info(f"Finding data dependencies in function: {function_name}")

        try:
            if variable_name:
                query = f'''
                cpg.method.name("{function_name}")
                   .ast.isIdentifier.name("{variable_name}")
                   .map(i => Map(
                       "variable" -> i.name,
                       "code" -> i.code,
                       "method" -> i.method.name,
                       "file" -> i.file.name.headOption.getOrElse("unknown"),
                       "line" -> i.lineNumber.getOrElse(-1),
                       "type" -> i.typeFullName
                   ))
                '''
            else:
                query = f'''
                cpg.method.name("{function_name}")
                   .ast.isIdentifier
                   .dedup.by(_.name)
                   .take(50)
                   .map(i => Map(
                       "variable" -> i.name,
                       "code" -> i.code,
                       "type" -> i.typeFullName,
                       "file" -> i.file.name.headOption.getOrElse("unknown"),
                       "line" -> i.lineNumber.getOrElse(-1)
                   ))
                '''

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    dependencies = json.loads(stdout)
                    return {
                        "success": True,
                        "function": function_name,
                        "variable": variable_name,
                        "dependencies": dependencies
                        if isinstance(dependencies, list)
                        else [dependencies]
                        if dependencies
                        else [],
                        "count": len(dependencies)
                        if isinstance(dependencies, list)
                        else (1 if dependencies else 0),
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "function": function_name,
                        "raw_output": stdout,
                    }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error finding data dependencies: {e}")
            return {"success": False, "error": str(e)}
