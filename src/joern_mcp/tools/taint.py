"""污点分析MCP工具

提供安全漏洞检测功能：
- find_vulnerabilities: 查找安全漏洞
- check_taint_flow: 检查自定义污点流
- list_vulnerability_rules: 列出检测规则
- get_rule_details: 获取规则详情

多项目支持：find_vulnerabilities 和 check_taint_flow 要求指定 project_name 参数。
"""

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.services.taint import TaintAnalysisService


@mcp.tool()
async def find_vulnerabilities(
    project_name: str,
    rule_name: str | None = None,
    severity: str | None = None,
    max_flows: int = 10,
) -> dict:
    """
    查找代码中的安全漏洞

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        rule_name: 规则名称（可选，如"Command Injection", "SQL Injection"）
        severity: 严重程度过滤（可选：CRITICAL, HIGH, MEDIUM, LOW）
        max_flows: 每个规则的最大流数量（默认10，最大50）

    Returns:
        dict: 漏洞列表和统计信息

    Example:
        >>> await find_vulnerabilities("webapp", severity="CRITICAL")
        {
            "success": true,
            "project": "webapp",
            "vulnerabilities": [...],
            "total_count": 1,
            "summary": {"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "rules_checked": 6
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_flows < 1 or max_flows > 50:
        return {"success": False, "error": "Max flows must be between 1 and 50"}

    if severity and severity not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        return {
            "success": False,
            "error": "Severity must be one of: CRITICAL, HIGH, MEDIUM, LOW",
        }

    service = TaintAnalysisService(server_state.query_executor)
    return await service.find_vulnerabilities(
        rule_name, severity, max_flows, project_name
    )


@mcp.tool()
async def check_taint_flow(
    project_name: str,
    source_pattern: str,
    sink_pattern: str,
    max_flows: int = 10,
) -> dict:
    """
    检查特定的污点流

    Args:
        project_name: 项目名称（必填，使用 list_projects 查看可用项目）
        source_pattern: 源模式（正则表达式，如"gets|scanf"）
        sink_pattern: 汇模式（正则表达式，如"system|exec"）
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 污点流信息

    Example:
        >>> await check_taint_flow("webapp", "gets", "system")
        {
            "success": true,
            "project": "webapp",
            "flows": [...],
            "count": 3
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_flows < 1 or max_flows > 50:
        return {"success": False, "error": "Max flows must be between 1 and 50"}

    service = TaintAnalysisService(server_state.query_executor)
    return await service.check_specific_flow(
        source_pattern, sink_pattern, max_flows, project_name
    )


@mcp.tool()
async def list_vulnerability_rules() -> dict:
    """
    列出所有可用的漏洞检测规则

    Returns:
        dict: 规则列表

    Example:
        >>> await list_vulnerability_rules()
        {
            "success": true,
            "rules": [
                {
                    "name": "Command Injection",
                    "description": "用户输入未经验证直接传递到命令执行函数",
                    "severity": "CRITICAL",
                    "cwe_id": "CWE-78",
                    "source_count": 18,
                    "sink_count": 13
                },
                {
                    "name": "SQL Injection",
                    "description": "用户输入未经验证直接用于SQL查询",
                    "severity": "CRITICAL",
                    "cwe_id": "CWE-89",
                    "source_count": 18,
                    "sink_count": 8
                }
            ],
            "count": 6
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    service = TaintAnalysisService(server_state.query_executor)
    return service.list_rules()


@mcp.tool()
async def get_rule_details(rule_name: str) -> dict:
    """
    获取特定规则的详细信息

    Args:
        rule_name: 规则名称（如 "Command Injection", "SQL Injection" 等）

    Returns:
        dict: 规则详细信息

    Example:
        >>> await get_rule_details("Command Injection")
        {
            "success": true,
            "rule": {
                "name": "Command Injection",
                "description": "用户输入未经验证直接传递到命令执行函数",
                "severity": "CRITICAL",
                "cwe_id": "CWE-78",
                "sources": ["gets", "scanf", "fgets", "argv", "getenv"],
                "sinks": ["system", "exec", "popen", "Runtime.exec"],
                "source_count": 18,
                "sink_count": 13
            }
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    service = TaintAnalysisService(server_state.query_executor)
    return service.get_rule_details(rule_name)
