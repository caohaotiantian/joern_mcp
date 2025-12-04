"""
tests/test_services/test_callgraph_extended.py

扩展的调用图服务测试
"""

import json
from unittest.mock import AsyncMock

import pytest

from joern_mcp.services.callgraph import CallGraphService


class TestCallGraphServiceExtended:
    """扩展的调用图服务测试"""

    @pytest.mark.asyncio
    async def test_get_callers_json_decode_error(self, mock_query_executor):
        """测试get_callers JSON解析失败 - 返回空列表"""
        service = CallGraphService(mock_query_executor)

        # Mock返回无效JSON
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "invalid json {{"}
        )

        result = await service.get_callers("test_func")

        # 解析失败时返回空列表（使用safe_parse_joern_response的默认值）
        assert result["success"] is True
        assert result["callers"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_callees_json_decode_error(self, mock_query_executor):
        """测试get_callees JSON解析失败 - 返回空列表"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "not valid json"}
        )

        result = await service.get_callees("test_func")

        # 解析失败时返回空列表
        assert result["success"] is True
        assert result["callees"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_call_chain_json_decode_error(self, mock_query_executor):
        """测试get_call_chain JSON解析失败 - 返回空列表"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "bad json"}
        )

        result = await service.get_call_chain("func_a")

        # 解析失败时返回空列表
        assert result["success"] is True
        assert result["chain"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_call_graph(self, mock_query_executor):
        """测试获取调用图"""
        service = CallGraphService(mock_query_executor)

        # Mock调用图数据
        graph_data = {
            "nodes": [
                {"name": "main", "type": "function"},
                {"name": "helper", "type": "function"},
            ],
            "edges": [{"from": "main", "to": "helper"}],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(graph_data)}
        )

        result = await service.get_call_graph("main", depth=2)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_call_graph_with_options(self, mock_query_executor):
        """测试带选项的调用图"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps({"nodes": [], "edges": []}),
            }
        )

        # 测试不同选项组合
        result1 = await service.get_call_graph(
            "test", include_callers=True, include_callees=False
        )
        assert result1["success"] is True

        result2 = await service.get_call_graph(
            "test", include_callers=False, include_callees=True
        )
        assert result2["success"] is True

        result3 = await service.get_call_graph(
            "test", include_callers=False, include_callees=False
        )
        assert result3["success"] is True

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_query_executor):
        """测试异常处理"""
        service = CallGraphService(mock_query_executor)

        # Mock抛出异常
        mock_query_executor.execute = AsyncMock(side_effect=Exception("Test exception"))

        result = await service.get_callers("test")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_failure(self, mock_query_executor):
        """测试查询失败"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Query failed"}
        )

        result = await service.get_callers("test")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_callees_multi_depth(self, mock_query_executor):
        """测试多层深度的callees"""
        service = CallGraphService(mock_query_executor)

        callees_data = [{"name": f"func_{i}", "filename": "test.c"} for i in range(10)]

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(callees_data)}
        )

        result = await service.get_callees("main", depth=5)

        assert result["success"] is True
        assert len(result["callees"]) == 10
