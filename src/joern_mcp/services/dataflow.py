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
            # 使用代码块包裹val定义，避免表达式中的语法错误
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

                # 移除ANSI颜色码
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_output = ansi_escape.sub('', stdout).strip()

                try:
                    # 尝试直接解析JSON
                    flows = json.loads(clean_output)
                    # 处理双重编码
                    if isinstance(flows, str):
                        flows = json.loads(flows)
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
                    # 尝试从Scala REPL输出提取JSON
                    match = re.search(r'=\s*(.+)$', clean_output)
                    if match:
                        try:
                            json_str = match.group(1).strip()
                            flows = json.loads(json_str)
                            if isinstance(flows, str):
                                flows = json.loads(flows)
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
                        except (json.JSONDecodeError, AttributeError):
                            pass

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
                # 追踪到特定汇（使用代码块避免val/def在表达式中的问题）
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

                # 移除ANSI颜色码
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_output = ansi_escape.sub('', stdout).strip()

                try:
                    # 尝试直接解析JSON
                    flows = json.loads(clean_output)
                    # 处理双重编码
                    if isinstance(flows, str):
                        flows = json.loads(flows)
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
                    # 尝试从Scala REPL输出提取JSON
                    match = re.search(r'=\s*(.+)$', clean_output)
                    if match:
                        try:
                            json_str = match.group(1).strip()
                            flows = json.loads(json_str)
                            # 双重解码
                            if isinstance(flows, str):
                                flows = json.loads(flows)
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
                        except (json.JSONDecodeError, AttributeError):
                            pass

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

                # 移除ANSI颜色码
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_output = ansi_escape.sub('', stdout).strip()

                try:
                    # 尝试直接解析JSON
                    dependencies = json.loads(clean_output)
                    # 处理双重编码
                    if isinstance(dependencies, str):
                        dependencies = json.loads(dependencies)
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
                    # 尝试从Scala REPL输出提取JSON
                    match = re.search(r'=\s*(.+)$', clean_output)
                    if match:
                        try:
                            json_str = match.group(1).strip()
                            dependencies = json.loads(json_str)
                            if isinstance(dependencies, str):
                                dependencies = json.loads(dependencies)
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
                        except (json.JSONDecodeError, AttributeError):
                            pass

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
