"""
tests/test_services/test_dataflow_extended.py

扩展的数据流服务测试
"""

import json
from unittest.mock import AsyncMock

import pytest

from joern_mcp.services.dataflow import DataFlowService


class TestDataFlowServiceExtended:
    """扩展的数据流服务测试"""

    @pytest.mark.asyncio
    async def test_track_dataflow_json_decode_error(self, mock_query_executor):
        """测试track_dataflow JSON解析失败"""
        service = DataFlowService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "invalid json"}
        )

        result = await service.track_dataflow("source", "sink")

        assert result["success"] is True
        assert "raw_output" in result

    @pytest.mark.asyncio
    async def test_analyze_variable_flow_json_error(self, mock_query_executor):
        """测试analyze_variable_flow JSON解析失败"""
        service = DataFlowService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "bad json"}
        )

        result = await service.analyze_variable_flow("var")

        assert result["success"] is True
        assert "raw_output" in result

    @pytest.mark.asyncio
    async def test_find_data_dependencies_json_error(self, mock_query_executor):
        """测试find_data_dependencies JSON解析失败"""
        service = DataFlowService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "not json"}
        )

        result = await service.find_data_dependencies("func")

        assert result["success"] is True
        assert "raw_output" in result

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_query_executor):
        """测试异常处理"""
        service = DataFlowService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(side_effect=Exception("Test error"))

        result = await service.track_dataflow("src", "sink")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_failure(self, mock_query_executor):
        """测试查询失败"""
        service = DataFlowService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Error"}
        )

        result = await service.track_dataflow("src", "sink")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_max_flows_parameter(self, mock_query_executor):
        """测试max_flows参数"""
        service = DataFlowService(mock_query_executor)

        flows = [{"path": [f"node{i}"]} for i in range(20)]

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(flows)}
        )

        # 测试不同的max_flows值
        result1 = await service.track_dataflow("src", "sink", max_flows=5)
        assert result1["success"] is True

        result2 = await service.track_dataflow("src", "sink", max_flows=20)
        assert result2["success"] is True
