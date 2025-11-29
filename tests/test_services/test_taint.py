"""测试污点分析服务"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from joern_mcp.models.taint_rules import (
    VULNERABILITY_RULES,
    get_rule_by_name,
    list_all_rules,
)
from joern_mcp.services.taint import TaintAnalysisService


def test_taint_rules():
    """测试污点规则定义"""
    # 检查规则数量
    assert len(VULNERABILITY_RULES) >= 5

    # 检查命令注入规则
    cmd_injection = get_rule_by_name("Command Injection")
    assert cmd_injection.severity == "CRITICAL"
    assert cmd_injection.cwe_id == "CWE-78"
    assert len(cmd_injection.sources) > 0
    assert len(cmd_injection.sinks) > 0


def test_list_all_rules():
    """测试列出所有规则"""
    rules = list_all_rules()
    assert len(rules) >= 5

    # 检查规则格式
    for rule in rules:
        assert "name" in rule
        assert "severity" in rule
        assert "cwe_id" in rule


@pytest.mark.asyncio
async def test_analyze_with_rule():
    """测试使用规则进行污点分析"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "vulnerability": "Command Injection",
            "severity": "CRITICAL",
            "cwe_id": "CWE-78",
            "source": {"code": "gets(buf)", "method": "main", "file": "main.c", "line": 10},
            "sink": {"code": "system(cmd)", "method": "exec", "file": "main.c", "line": 20},
            "pathLength": 5
        }]""",
        }
    )

    service = TaintAnalysisService(mock_executor)
    rule = get_rule_by_name("Command Injection")
    result = await service.analyze_with_rule(rule)

    assert result["success"] is True
    assert result["rule"] == "Command Injection"
    assert result["severity"] == "CRITICAL"
    assert len(result["vulnerabilities"]) >= 1


@pytest.mark.asyncio
async def test_find_vulnerabilities():
    """测试查找漏洞"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "vulnerability": "SQL Injection",
            "severity": "CRITICAL",
            "source": {"code": "getParameter(\"id\")", "method": "doGet", "file": "Servlet.java", "line": 15},
            "sink": {"code": "executeQuery(sql)", "method": "query", "file": "Servlet.java", "line": 25},
            "pathLength": 3
        }]""",
        }
    )

    service = TaintAnalysisService(mock_executor)
    result = await service.find_vulnerabilities(severity="CRITICAL")

    assert result["success"] is True
    assert "vulnerabilities" in result
    assert "summary" in result
    assert result["summary"]["CRITICAL"] >= 0


@pytest.mark.asyncio
async def test_find_vulnerabilities_by_rule_name():
    """测试按规则名称查找漏洞"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={"success": True, "stdout": "[]"})

    service = TaintAnalysisService(mock_executor)
    result = await service.find_vulnerabilities(rule_name="Command Injection")

    assert result["success"] is True
    assert result["rules_checked"] == 1


@pytest.mark.asyncio
async def test_check_specific_flow():
    """测试检查特定污点流"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "source": {"code": "gets(buf)", "method": "main", "file": "main.c", "line": 10},
            "sink": {"code": "system(cmd)", "method": "main", "file": "main.c", "line": 20},
            "pathLength": 5,
            "path": []
        }]""",
        }
    )

    service = TaintAnalysisService(mock_executor)
    result = await service.check_specific_flow("gets", "system")

    assert result["success"] is True
    assert result["source_pattern"] == "gets"
    assert result["sink_pattern"] == "system"
    assert len(result["flows"]) >= 1


@pytest.mark.asyncio
async def test_check_specific_flow_no_results():
    """测试检查污点流无结果"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={"success": True, "stdout": "[]"})

    service = TaintAnalysisService(mock_executor)
    result = await service.check_specific_flow("safe_func", "safe_sink")

    assert result["success"] is True
    assert result["count"] == 0
    assert len(result["flows"]) == 0


def test_list_rules():
    """测试列出规则"""
    mock_executor = MagicMock()
    service = TaintAnalysisService(mock_executor)

    result = service.list_rules()

    assert result["success"] is True
    assert len(result["rules"]) >= 5
    assert result["count"] >= 5


def test_get_rule_details():
    """测试获取规则详情"""
    mock_executor = MagicMock()
    service = TaintAnalysisService(mock_executor)

    result = service.get_rule_details("Command Injection")

    assert result["success"] is True
    assert result["rule"]["name"] == "Command Injection"
    assert result["rule"]["severity"] == "CRITICAL"
    assert len(result["rule"]["sources"]) > 0


def test_get_rule_details_not_found():
    """测试获取不存在的规则"""
    mock_executor = MagicMock()
    service = TaintAnalysisService(mock_executor)

    result = service.get_rule_details("NonExistent Rule")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_analyze_query_failed():
    """测试查询失败"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={"success": False, "stderr": "Query error"}
    )

    service = TaintAnalysisService(mock_executor)
    rule = get_rule_by_name("Command Injection")
    result = await service.analyze_with_rule(rule)

    assert result["success"] is False
    assert "error" in result
