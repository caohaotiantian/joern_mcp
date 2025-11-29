"""
tests/test_tools/test_dataflow.py

测试数据流工具
"""
import pytest
import json
from unittest.mock import AsyncMock
from joern_mcp.services.dataflow import DataFlowService


class TestDataFlowTools:
    """测试数据流工具逻辑"""

    @pytest.mark.asyncio
    async def test_track_dataflow_logic(self, mock_query_executor):
        """测试追踪数据流"""
        service = DataFlowService(mock_query_executor)
        
        # Mock数据流结果 - 返回JSON格式的stdout
        flows_data = [
            {
                "path": ["gets", "buffer", "strcpy", "system"],
                "source_line": 10,
                "sink_line": 15
            }
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(flows_data)
            }
        )
        
        result = await service.track_dataflow("gets", "system", max_flows=10)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_analyze_variable_flow(self, mock_query_executor):
        """测试分析变量流"""
        service = DataFlowService(mock_query_executor)
        
        flow_data = [
            {"variable": "buffer", "uses": ["line10", "line15", "line20"]}
        ]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(flow_data)
            }
        )
        
        result = await service.analyze_variable_flow("buffer")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_find_data_dependencies(self, mock_query_executor):
        """测试查找数据依赖"""
        service = DataFlowService(mock_query_executor)
        
        deps_data = [
            {"statement": "x = y + z", "dependencies": ["y", "z"]}
        ]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(deps_data)
            }
        )
        
        result = await service.find_data_dependencies("main")
        
        assert result["success"] is True


class TestDataFlowEdgeCases:
    """测试数据流边界情况"""

    @pytest.mark.asyncio
    async def test_track_dataflow_no_flows(self, mock_query_executor):
        """测试没有数据流的情况"""
        service = DataFlowService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "[]"
            }
        )
        
        result = await service.track_dataflow("safe_input", "safe_output")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_track_dataflow_complex_path(self, mock_query_executor):
        """测试复杂数据流路径"""
        service = DataFlowService(mock_query_executor)
        
        # 复杂的数据流路径
        flows = [
            {
                "path": ["source", "var1", "func1", "var2", "func2", "sink"],
                "source_line": 5,
                "sink_line": 50
            }
        ]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(flows)
            }
        )
        
        result = await service.track_dataflow("source", "sink", max_flows=5)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_max_flows_limit(self, mock_query_executor):
        """测试最大流数限制"""
        service = DataFlowService(mock_query_executor)
        
        # 返回达到限制的流
        flows = [{"path": [f"node{i}"] * 3} for i in range(5)]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(flows)
            }
        )
        
        result = await service.track_dataflow("src", "sink", max_flows=5)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_query_failure(self, mock_query_executor):
        """测试查询失败的情况"""
        service = DataFlowService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": False,
                "stderr": "Query error"
            }
        )
        
        result = await service.track_dataflow("src", "sink")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_variable_flow_empty(self, mock_query_executor):
        """测试变量流为空"""
        service = DataFlowService(mock_query_executor)
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "[]"
            }
        )
        
        result = await service.analyze_variable_flow("unused_var")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_find_data_dependencies_complex(self, mock_query_executor):
        """测试复杂数据依赖"""
        service = DataFlowService(mock_query_executor)
        
        deps_data = [
            {"statement": "result = func(a, b, c)", "dependencies": ["a", "b", "c", "func"]}
        ]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(deps_data)
            }
        )
        
        result = await service.find_data_dependencies("complex_function")
        
        assert result["success"] is True
