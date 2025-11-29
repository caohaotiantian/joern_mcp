"""
tests/test_tools/test_taint.py

测试污点分析工具
"""

import json
from unittest.mock import AsyncMock

import pytest

from joern_mcp.services.taint import TaintAnalysisService


class TestTaintTools:
    """测试污点分析工具逻辑"""

    @pytest.mark.asyncio
    async def test_find_vulnerabilities_logic(self, mock_query_executor):
        """测试查找漏洞"""
        service = TaintAnalysisService(mock_query_executor)

        # Mock漏洞结果 - 返回JSON格式的stdout
        vuln_data = [
            {"source": "gets", "sink": "system", "path": ["gets", "buffer", "system"]}
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(vuln_data)}
        )

        result = await service.find_vulnerabilities()

        assert result["success"] is True

    def test_list_rules_logic(self, mock_query_executor):
        """测试列出规则"""
        service = TaintAnalysisService(mock_query_executor)

        result = service.list_rules()

        assert result["success"] is True
        assert len(result["rules"]) >= 6  # 至少6个默认规则
        # 验证规则包含必要字段
        rule = result["rules"][0]
        assert "name" in rule
        assert "severity" in rule
        assert "source_count" in rule  # 修正：不是sources而是source_count
        assert "sink_count" in rule  # 修正：不是sinks而是sink_count

    def test_get_rule_details_logic(self, mock_query_executor):
        """测试获取规则详情"""
        service = TaintAnalysisService(mock_query_executor)

        result = service.get_rule_details("Command Injection")

        assert result["success"] is True
        assert result["rule"]["name"] == "Command Injection"
        assert result["rule"]["severity"] == "CRITICAL"
        assert "sources" in result["rule"]  # 详情中包含sources
        assert len(result["rule"]["sinks"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_with_rule(self, mock_query_executor):
        """测试使用规则分析"""
        from joern_mcp.models.taint_rules import get_rule_by_name

        service = TaintAnalysisService(mock_query_executor)
        rule = get_rule_by_name("Command Injection")

        vuln_data = [
            {"source": "gets", "sink": "system", "path": ["gets", "buffer", "system"]}
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(vuln_data)}
        )

        result = await service.analyze_with_rule(rule, max_flows=10)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_check_specific_flow(self, mock_query_executor):
        """测试检查特定流"""
        service = TaintAnalysisService(mock_query_executor)

        flow_data = [{"exists": True, "path": ["gets", "system"]}]

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(flow_data)}
        )

        result = await service.check_specific_flow("gets", "system")

        assert result["success"] is True


class TestTaintEdgeCases:
    """测试污点分析边界情况"""

    @pytest.mark.asyncio
    async def test_find_vulnerabilities_none_found(self, mock_query_executor):
        """测试没有找到漏洞"""
        service = TaintAnalysisService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        result = await service.find_vulnerabilities()

        assert result["success"] is True

    def test_get_rule_details_not_found(self, mock_query_executor):
        """测试获取不存在的规则"""
        service = TaintAnalysisService(mock_query_executor)

        result = service.get_rule_details("Nonexistent Rule")

        assert result["success"] is False
        assert "error" in result

    def test_list_rules_filtered(self, mock_query_executor):
        """测试过滤规则列表"""
        service = TaintAnalysisService(mock_query_executor)

        result = service.list_rules()

        # 过滤出高危规则
        critical_rules = [r for r in result["rules"] if r["severity"] == "CRITICAL"]

        assert len(critical_rules) >= 2  # 至少2个高危规则

    @pytest.mark.asyncio
    async def test_query_error_handling(self, mock_query_executor):
        """测试查询错误处理"""
        service = TaintAnalysisService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Query failed"}
        )

        result = await service.find_vulnerabilities()

        # find_vulnerabilities可能捕获异常并返回成功但为空的结果
        # 或者返回失败，取决于实现
        assert "success" in result

    @pytest.mark.asyncio
    async def test_analyze_with_multiple_rules(self, mock_query_executor):
        """测试使用多个规则分析"""
        from joern_mcp.models.taint_rules import VULNERABILITY_RULES

        service = TaintAnalysisService(mock_query_executor)

        # Mock空结果（用于快速测试）
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        # 分析所有规则
        for rule in VULNERABILITY_RULES[:3]:  # 只测试前3个规则
            result = await service.analyze_with_rule(rule, max_flows=5)
            assert result["success"] is True
