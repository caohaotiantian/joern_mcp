"""
tests/test_tools/test_callgraph.py

测试调用图工具
"""

import json
from unittest.mock import AsyncMock

import pytest

from joern_mcp.services.callgraph import CallGraphService


class TestCallGraphTools:
    """测试调用图工具逻辑"""

    @pytest.mark.asyncio
    async def test_get_callers_logic(self, mock_query_executor):
        """测试获取调用者"""
        service = CallGraphService(mock_query_executor)

        # Mock查询结果 - 返回JSON格式的stdout
        callers_data = [
            {
                "name": "caller1",
                "filename": "test.c",
                "signature": "void()",
                "lineNumber": 10,
            },
            {
                "name": "caller2",
                "filename": "test.c",
                "signature": "int()",
                "lineNumber": 20,
            },
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(callers_data)}
        )

        result = await service.get_callers("main", depth=1, project_name="test")

        assert result["success"] is True
        assert result["function"] == "main"
        assert len(result["callers"]) == 2

    @pytest.mark.asyncio
    async def test_get_callees_logic(self, mock_query_executor):
        """测试获取被调用者"""
        service = CallGraphService(mock_query_executor)

        # Mock查询结果 - 返回JSON格式的stdout
        callees_data = [
            {
                "name": "helper",
                "filename": "test.c",
                "signature": "void()",
                "lineNumber": 30,
            },
            {
                "name": "printf",
                "filename": "libc.so",
                "signature": "int()",
                "lineNumber": -1,
            },
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(callees_data)}
        )

        result = await service.get_callees("main", depth=1, project_name="test")

        assert result["success"] is True
        assert result["function"] == "main"
        assert len(result["callees"]) == 2

    @pytest.mark.asyncio
    async def test_get_call_chain_logic(self, mock_query_executor):
        """测试获取调用链"""
        service = CallGraphService(mock_query_executor)

        # Mock调用链结果
        chain_data = [
            {"name": "main", "filename": "test.c"},
            {"name": "vulnerable_function", "filename": "test.c"},
            {"name": "strcpy", "filename": "libc.so"},
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(chain_data)}
        )

        # get_call_chain(function_name, max_depth, direction, project_name)
        result = await service.get_call_chain(
            function_name="main", max_depth=5, direction="down", project_name="test"
        )

        assert result["success"] is True


class TestCallGraphEdgeCases:
    """测试调用图边界情况"""

    @pytest.mark.asyncio
    async def test_get_callers_no_results(self, mock_query_executor):
        """测试没有调用者的情况"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        result = await service.get_callers("isolated_function", project_name="test")

        assert result["success"] is True
        assert len(result["callers"]) == 0

    @pytest.mark.asyncio
    async def test_get_callees_depth_zero(self, mock_query_executor):
        """测试深度为0的情况"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        result = await service.get_callees("main", depth=0, project_name="test")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_call_chain_no_path(self, mock_query_executor):
        """测试找不到调用路径"""
        service = CallGraphService(mock_query_executor)

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        # 正确的调用方式：function_name, max_depth, direction
        result = await service.get_call_chain(
            "func_a", max_depth=5, direction="up", project_name="test"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_callers_large_depth(self, mock_query_executor):
        """测试大深度调用者查询"""
        service = CallGraphService(mock_query_executor)

        # 大深度可能返回很多结果
        callers = [
            {
                "name": f"caller{i}",
                "filename": "test.c",
                "signature": "void()",
                "lineNumber": i,
            }
            for i in range(100)
        ]

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(callers)}
        )

        result = await service.get_callers("main", depth=10, project_name="test")

        assert result["success"] is True
        assert len(result["callers"]) == 100

    @pytest.mark.asyncio
    async def test_call_chain_circular_reference(self, mock_query_executor):
        """测试循环引用的调用链"""
        service = CallGraphService(mock_query_executor)

        # Mock循环引用的路径
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(
                    [
                        {"name": "func_a", "filename": "test.c"},
                        {"name": "func_b", "filename": "test.c"},
                    ]
                ),
            }
        )

        # 正确的调用方式
        result = await service.get_call_chain(
            "func_a", max_depth=5, direction="up", project_name="test"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_function_not_found(self, mock_query_executor):
        """测试函数不存在"""
        service = CallGraphService(mock_query_executor)

        # 查询失败的情况
        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Function not found"}
        )

        result = await service.get_callers("nonexistent_function", project_name="test")

        assert result["success"] is False
        assert "error" in result
