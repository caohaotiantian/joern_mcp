"""污点分析服务"""

import json

from loguru import logger

from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.models.taint_rules import (
    VULNERABILITY_RULES,
    TaintRule,
    get_rule_by_name,
    get_rules_by_severity,
    list_all_rules,
)


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
        """
        logger.info(f"Running taint analysis with rule: {rule.name}")

        try:
            # 构建污点分析查询
            source_pattern = "|".join(rule.sources)
            sink_pattern = "|".join(rule.sinks)

            query = f'''
            val sources = cpg.method.name("({source_pattern})").parameter
            val sinks = cpg.call.name("({sink_pattern})").argument

            sinks.reachableBy(sources).flows.take({max_flows}).map(flow => Map(
                "vulnerability" -> "{rule.name}",
                "severity" -> "{rule.severity}",
                "cwe_id" -> "{rule.cwe_id}",
                "description" -> "{rule.description}",
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
                "pathLength" -> flow.elements.size
            ))
            '''

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    flows = json.loads(stdout)
                    return {
                        "success": True,
                        "rule": rule.name,
                        "severity": rule.severity,
                        "cwe_id": rule.cwe_id,
                        "vulnerabilities": flows
                        if isinstance(flows, list)
                        else [flows]
                        if flows
                        else [],
                        "count": len(flows)
                        if isinstance(flows, list)
                        else (1 if flows else 0),
                    }
                except json.JSONDecodeError:
                    return {"success": True, "rule": rule.name, "raw_output": stdout}
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
        """
        logger.info(
            f"Finding vulnerabilities (rule: {rule_name}, severity: {severity})"
        )

        try:
            # 确定要使用的规则
            if rule_name:
                rules = [get_rule_by_name(rule_name)]
            elif severity:
                rules = get_rules_by_severity(severity)
            else:
                rules = VULNERABILITY_RULES

            all_vulnerabilities = []
            summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

            # 对每个规则进行分析
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
            source_pattern: 源模式（正则表达式）
            sink_pattern: 汇模式（正则表达式）
            max_flows: 最大流数量

        Returns:
            dict: 污点流信息
        """
        logger.info(f"Checking taint flow: {source_pattern} -> {sink_pattern}")

        try:
            query = f"""
            val sources = cpg.method.name("({source_pattern})").parameter
            val sinks = cpg.call.name("({sink_pattern})").argument

            sinks.reachableBy(sources).flows.take({max_flows}).map(flow => Map(
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
            """

            result = await self.executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                try:
                    flows = json.loads(stdout)
                    return {
                        "success": True,
                        "source_pattern": source_pattern,
                        "sink_pattern": sink_pattern,
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
                    return {"success": True, "raw_output": stdout}
            else:
                return {"success": False, "error": result.get("stderr", "Query failed")}

        except Exception as e:
            logger.exception(f"Error checking taint flow: {e}")
            return {"success": False, "error": str(e)}

    def list_rules(self) -> dict:
        """列出所有可用的规则"""
        return {
            "success": True,
            "rules": list_all_rules(),
            "count": len(VULNERABILITY_RULES),
        }

    def get_rule_details(self, rule_name: str) -> dict:
        """获取规则详情"""
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
