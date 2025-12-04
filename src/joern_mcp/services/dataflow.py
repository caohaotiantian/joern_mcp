"""数据流分析服务

追踪程序中的数据流向：
- track_dataflow: 从源到汇的数据流追踪
- analyze_variable_flow: 分析变量的数据流
- find_data_dependencies: 查找数据依赖关系
"""

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.utils.response_parser import safe_parse_joern_response


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
            source_method: 源方法名称（如 "gets", "scanf"）
            sink_method: 汇方法名称（如 "strcpy", "system"）
            max_flows: 最大流数量

        Returns:
            dict: 数据流信息

        Example:
            >>> result = await service.track_dataflow("gets", "strcpy", max_flows=5)
            {
                "success": True,
                "source_method": "gets",
                "sink_method": "strcpy",
                "flows": [
                    {
                        "source": {"code": "buf", "file": "main.c", "line": 10},
                        "sink": {"code": "strcpy(dst, buf)", "file": "main.c", "line": 15},
                        "pathLength": 3,
                        "path": [...]
                    }
                ],
                "count": 1
            }
        """
        logger.info(f"Tracking dataflow from {source_method} to {sink_method}")

        try:
            query = f'''
            {{
              val source = cpg.method.name("{source_method}").parameter
              val sink = cpg.call.name("{sink_method}").argument

              sink.reachableByFlows(source).take({max_flows}).map {{ path =>
                val sourceNode = path.elements.head
                val sinkNode = path.elements.last
                Map(
                  "source" -> Map(
                      "code" -> sourceNode.code,
                      "file" -> sourceNode.file.name.headOption.getOrElse("unknown"),
                      "line" -> sourceNode.lineNumber.getOrElse(-1)
                  ),
                  "sink" -> Map(
                      "code" -> sinkNode.code,
                      "file" -> sinkNode.file.name.headOption.getOrElse("unknown"),
                      "line" -> sinkNode.lineNumber.getOrElse(-1)
                  ),
                  "pathLength" -> path.elements.size,
                  "path" -> path.elements.take(20).map(e => Map(
                      "type" -> e.label,
                      "code" -> e.code,
                      "line" -> e.lineNumber.getOrElse(-1)
                  ))
                )
              }}
            }}
            '''

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                flows = safe_parse_joern_response(stdout, default=[])

                if not isinstance(flows, list):
                    flows = [flows] if flows else []

                return {
                    "success": True,
                    "source_method": source_method,
                    "sink_method": sink_method,
                    "flows": flows,
                    "count": len(flows),
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
            variable_name: 变量名称（如 "user_input", "buffer"）
            sink_method: 目标汇方法（可选，如 "system", "exec"）
            max_flows: 最大流数量

        Returns:
            dict: 变量流信息

        Example:
            >>> result = await service.analyze_variable_flow("cmd", sink_method="system")
            {
                "success": True,
                "variable": "cmd",
                "sink_method": "system",
                "flows": [
                    {
                        "variable": "cmd",
                        "source": {"code": "cmd", "file": "main.c", "line": 5},
                        "sink": {"code": "system(cmd)", "file": "main.c", "line": 10},
                        "pathLength": 4
                    }
                ],
                "count": 1
            }
        """
        logger.info(f"Analyzing variable flow: {variable_name}")

        try:
            if sink_method:
                query = f'''
                {{
                  val source = cpg.identifier.name("{variable_name}")
                  val sink = cpg.call.name("{sink_method}").argument

                  sink.reachableByFlows(source).take({max_flows}).map {{ path =>
                    Map(
                      "variable" -> "{variable_name}",
                      "source" -> Map(
                          "code" -> path.elements.head.code,
                          "file" -> path.elements.head.file.name.headOption.getOrElse("unknown"),
                          "line" -> path.elements.head.lineNumber.getOrElse(-1)
                      ),
                      "sink" -> Map(
                          "code" -> path.elements.last.code,
                          "method" -> "{sink_method}",
                          "file" -> path.elements.last.file.name.headOption.getOrElse("unknown"),
                          "line" -> path.elements.last.lineNumber.getOrElse(-1)
                      ),
                      "pathLength" -> path.elements.size
                    )
                  }}
                }}
                '''
            else:
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
                flows = safe_parse_joern_response(stdout, default=[])

                if not isinstance(flows, list):
                    flows = [flows] if flows else []

                return {
                    "success": True,
                    "variable": variable_name,
                    "sink_method": sink_method,
                    "flows": flows,
                    "count": len(flows),
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

        Example:
            >>> result = await service.find_data_dependencies("process_input", "buffer")
            {
                "success": True,
                "function": "process_input",
                "variable": "buffer",
                "dependencies": [
                    {
                        "variable": "buffer",
                        "code": "buffer",
                        "type": "char*",
                        "file": "input.c",
                        "line": 25
                    }
                ],
                "count": 1
            }
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
                   .dedupBy(_.name)
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
                dependencies = safe_parse_joern_response(stdout, default=[])

                if not isinstance(dependencies, list):
                    dependencies = [dependencies] if dependencies else []

                return {
                    "success": True,
                    "function": function_name,
                    "variable": variable_name,
                    "dependencies": dependencies,
                    "count": len(dependencies),
                }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error finding data dependencies: {e}")
            return {"success": False, "error": str(e)}
