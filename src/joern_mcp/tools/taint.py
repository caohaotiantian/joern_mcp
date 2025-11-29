"""污点分析MCP工具"""



from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.services.taint import TaintAnalysisService


@mcp.tool()
async def find_vulnerabilities(
    rule_name: str | None = None, severity: str | None = None, max_flows: int = 10
) -> dict:
    """
    查找代码中的安全漏洞

    Args:
        rule_name: 规则名称（可选，如"Command Injection", "SQL Injection"）
        severity: 严重程度过滤（可选：CRITICAL, HIGH, MEDIUM, LOW）
        max_flows: 每个规则的最大流数量（默认10，最大50）

    Returns:
        dict: 漏洞列表和统计信息

    Example:
        >>> await find_vulnerabilities(severity="CRITICAL")
        {
            "success": True,
            "vulnerabilities": [...],
            "total_count": 5,
            "summary": {"CRITICAL": 3, "HIGH": 2, ...}
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
    return await service.find_vulnerabilities(rule_name, severity, max_flows)


@mcp.tool()
async def check_taint_flow(
    source_pattern: str, sink_pattern: str, max_flows: int = 10
) -> dict:
    """
    检查特定的污点流

    Args:
        source_pattern: 源模式（正则表达式，如"gets|scanf"）
        sink_pattern: 汇模式（正则表达式，如"system|exec"）
        max_flows: 最大流数量（默认10，最大50）

    Returns:
        dict: 污点流信息

    Example:
        >>> await check_taint_flow("gets", "system")
        {
            "success": True,
            "flows": [...],
            "count": 3
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    if max_flows < 1 or max_flows > 50:
        return {"success": False, "error": "Max flows must be between 1 and 50"}

    service = TaintAnalysisService(server_state.query_executor)
    return await service.check_specific_flow(source_pattern, sink_pattern, max_flows)


@mcp.tool()
async def list_vulnerability_rules() -> dict:
    """
    列出所有可用的漏洞检测规则

    Returns:
        dict: 规则列表

    Example:
        >>> await list_vulnerability_rules()
        {
            "success": True,
            "rules": [
                {
                    "name": "Command Injection",
                    "severity": "CRITICAL",
                    "cwe_id": "CWE-78",
                    ...
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
        rule_name: 规则名称

    Returns:
        dict: 规则详细信息

    Example:
        >>> await get_rule_details("Command Injection")
        {
            "success": True,
            "rule": {
                "name": "Command Injection",
                "description": "...",
                "severity": "CRITICAL",
                "sources": [...],
                "sinks": [...]
            }
        }
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    service = TaintAnalysisService(server_state.query_executor)
    return service.get_rule_details(rule_name)
