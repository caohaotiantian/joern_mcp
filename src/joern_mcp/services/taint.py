"""污点分析服务

识别和追踪安全漏洞：
- analyze_with_rule: 使用特定规则进行污点分析
- find_vulnerabilities: 查找代码中的漏洞
- check_specific_flow: 检查自定义的污点流
"""

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.models.taint_rules import (
    VULNERABILITY_RULES,
    TaintRule,
    get_rule_by_name,
    get_rules_by_severity,
    list_all_rules,
)
from joern_mcp.utils.response_parser import safe_parse_joern_response


class TaintAnalysisService:
    """污点分析服务"""

    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor

    async def analyze_with_rule(self, rule: TaintRule, max_flows: int = 10) -> dict:
        """
        使用特定规则进行污点分析

        Args:
            rule: 污点规则
            max_flows: 最大流数量

        Returns:
            dict: 分析结果

        Example:
            >>> result = await service.analyze_with_rule(command_injection_rule)
            {
                "success": True,
                "rule": "Command Injection",
                "severity": "CRITICAL",
                "cwe_id": "CWE-78",
                "vulnerabilities": [
                    {
                        "vulnerability": "Command Injection",
                        "source": {"code": "input", "file": "main.c", "line": 5},
                        "sink": {"code": "system(cmd)", "file": "main.c", "line": 20}
                    }
                ],
                "count": 1
            }
        """
        logger.info(f"Running taint analysis with rule: {rule.name}")

        try:
            source_pattern = "|".join(rule.sources)
            sink_pattern = "|".join(rule.sinks)

            query = f'''
            {{
              val sources = cpg.method.name("({source_pattern})").parameter
              val sinks = cpg.call.name("({sink_pattern})").argument

              sinks.reachableByFlows(sources).take({max_flows}).map {{ path =>
                val sourceNode = path.elements.head
                val sinkNode = path.elements.last
                Map(
                  "vulnerability" -> "{rule.name}",
                  "severity" -> "{rule.severity}",
                  "cwe_id" -> "{rule.cwe_id}",
                  "description" -> "{rule.description}",
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
                  "pathLength" -> path.elements.size
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
                    "rule": rule.name,
                    "severity": rule.severity,
                    "cwe_id": rule.cwe_id,
                    "vulnerabilities": flows,
                    "count": len(flows),
                }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error in taint analysis: {e}")
            return {"success": False, "error": str(e)}

    async def find_vulnerabilities(
        self,
        rule_name: str | None = None,
        severity: str | None = None,
        max_flows: int = 10,
    ) -> dict:
        """
        查找漏洞

        Args:
            rule_name: 规则名称（可选）
            severity: 严重程度过滤（可选：CRITICAL, HIGH, MEDIUM, LOW）
            max_flows: 每个规则的最大流数量

        Returns:
            dict: 漏洞列表

        Example:
            >>> result = await service.find_vulnerabilities(severity="CRITICAL")
            {
                "success": True,
                "vulnerabilities": [...],
                "total_count": 5,
                "summary": {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 0, "LOW": 0},
                "rules_checked": 6
            }
        """
        logger.info(
            f"Finding vulnerabilities (rule: {rule_name}, severity: {severity})"
        )

        try:
            if rule_name:
                rules = [get_rule_by_name(rule_name)]
            elif severity:
                rules = get_rules_by_severity(severity)
            else:
                rules = VULNERABILITY_RULES

            all_vulnerabilities = []
            summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

            for rule in rules:
                result = await self.analyze_with_rule(rule, max_flows)

                if result.get("success") and result.get("vulnerabilities"):
                    vulns = result["vulnerabilities"]
                    all_vulnerabilities.extend(vulns)
                    summary[rule.severity] += len(vulns)

            return {
                "success": True,
                "vulnerabilities": all_vulnerabilities,
                "total_count": len(all_vulnerabilities),
                "summary": summary,
                "rules_checked": len(rules),
            }

        except Exception as e:
            logger.exception(f"Error finding vulnerabilities: {e}")
            return {"success": False, "error": str(e)}

    async def check_specific_flow(
        self, source_pattern: str, sink_pattern: str, max_flows: int = 10
    ) -> dict:
        """
        检查特定的污点流

        Args:
            source_pattern: 源模式（正则表达式，如 "gets|scanf"）
            sink_pattern: 汇模式（正则表达式，如 "system|exec"）
            max_flows: 最大流数量

        Returns:
            dict: 污点流信息

        Example:
            >>> result = await service.check_specific_flow("gets", "system")
            {
                "success": True,
                "source_pattern": "gets",
                "sink_pattern": "system",
                "flows": [
                    {
                        "source": {"code": "input", "file": "main.c", "line": 5},
                        "sink": {"code": "system(cmd)", "file": "main.c", "line": 20},
                        "pathLength": 4,
                        "path": [...]
                    }
                ],
                "count": 1
            }
        """
        logger.info(f"Checking taint flow: {source_pattern} -> {sink_pattern}")

        try:
            query = f"""
            {{
              val sources = cpg.method.name("({source_pattern})").parameter
              val sinks = cpg.call.name("({sink_pattern})").argument

              sinks.reachableByFlows(sources).take({max_flows}).map {{ path =>
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
            """

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                flows = safe_parse_joern_response(stdout, default=[])

                if not isinstance(flows, list):
                    flows = [flows] if flows else []

                return {
                    "success": True,
                    "source_pattern": source_pattern,
                    "sink_pattern": sink_pattern,
                    "flows": flows,
                    "count": len(flows),
                }
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error checking taint flow: {e}")
            return {"success": False, "error": str(e)}

    def list_rules(self) -> dict:
        """
        列出所有可用的规则

        Returns:
            dict: 规则列表

        Example:
            >>> result = service.list_rules()
            {
                "success": True,
                "rules": [
                    {"name": "Command Injection", "severity": "CRITICAL", "cwe_id": "CWE-78"},
                    {"name": "SQL Injection", "severity": "CRITICAL", "cwe_id": "CWE-89"},
                    ...
                ],
                "count": 6
            }
        """
        return {
            "success": True,
            "rules": list_all_rules(),
            "count": len(VULNERABILITY_RULES),
        }

    def get_rule_details(self, rule_name: str) -> dict:
        """
        获取规则详情

        Args:
            rule_name: 规则名称

        Returns:
            dict: 规则详细信息

        Example:
            >>> result = service.get_rule_details("Command Injection")
            {
                "success": True,
                "rule": {
                    "name": "Command Injection",
                    "description": "Untrusted data flows to command execution",
                    "severity": "CRITICAL",
                    "cwe_id": "CWE-78",
                    "sources": ["gets", "scanf", "argv"],
                    "sinks": ["system", "exec", "popen"],
                    "source_count": 3,
                    "sink_count": 3
                }
            }
        """
        try:
            rule = get_rule_by_name(rule_name)
            return {
                "success": True,
                "rule": {
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "cwe_id": rule.cwe_id,
                    "sources": rule.sources,
                    "sinks": rule.sinks,
                    "source_count": len(rule.sources),
                    "sink_count": len(rule.sinks),
                },
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
