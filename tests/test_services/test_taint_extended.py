"""
tests/test_services/test_taint_extended.py

扩展的污点分析服务测试
"""
import pytest
import json
from unittest.mock import AsyncMock
from joern_mcp.services.taint import TaintAnalysisService
from joern_mcp.models.taint_rules import get_rule_by_name


class TestTaintAnalysisServiceExtended:
    """扩展的污点分析服务测试"""

    @pytest.mark.asyncio
    async def test_analyze_with_rule_json_error(self, mock_query_executor):
        """测试analyze_with_rule JSON解析失败"""
        service = TaintAnalysisService(mock_query_executor)
        rule = get_rule_by_name("Command Injection")
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "invalid json"
            }
        )
        
        result = await service.analyze_with_rule(rule)
        
        assert result["success"] is True
        assert "raw_output" in result

    @pytest.mark.asyncio
    async def test_find_vulnerabilities_json_error(self, mock_query_executor):
        """测试find_vulnerabilities JSON解析失败"""
        service = TaintAnalysisService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "bad json"
            }
        )
        
        result = await service.find_vulnerabilities()
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_check_specific_flow_json_error(self, mock_query_executor):
        """测试check_specific_flow JSON解析失败"""
        service = TaintAnalysisService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "not json"
            }
        )
        
        result = await service.check_specific_flow("src", "sink")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_query_executor):
        """测试异常处理"""
        service = TaintAnalysisService(mock_query_executor)
        rule = get_rule_by_name("SQL Injection")
        
        mock_query_executor.execute = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        result = await service.analyze_with_rule(rule)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_failure_with_rule(self, mock_query_executor):
        """测试查询失败"""
        service = TaintAnalysisService(mock_query_executor)
        rule = get_rule_by_name("Network Data Injection")
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": False,
                "stderr": "Error"
            }
        )
        
        result = await service.analyze_with_rule(rule)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_max_flows_parameter(self, mock_query_executor):
        """测试max_flows参数"""
        service = TaintAnalysisService(mock_query_executor)
        rule = get_rule_by_name("Path Traversal")
        
        vuln_data = [{"source": "input", "sink": "file"} for _ in range(15)]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(vuln_data)
            }
        )
        
        result = await service.analyze_with_rule(rule, max_flows=15)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_all_vulnerability_rules(self, mock_query_executor):
        """测试所有漏洞规则"""
        from joern_mcp.models.taint_rules import VULNERABILITY_RULES
        
        service = TaintAnalysisService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "[]"
            }
        )
        
        # 测试每个规则都可以使用
        for rule in VULNERABILITY_RULES:
            result = await service.analyze_with_rule(rule, max_flows=5)
            assert result["success"] is True

