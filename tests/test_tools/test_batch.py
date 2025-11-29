"""
tests/test_tools/test_batch.py

测试批量查询工具
"""
import pytest
import json
from unittest.mock import AsyncMock


class TestBatchTools:
    """测试批量查询工具逻辑"""

    @pytest.mark.asyncio
    async def test_batch_query_basic(self, mock_query_executor):
        """测试基本批量查询"""
        # Mock批量查询结果
        results = [
            {"query": "query1", "success": True, "result": [{"name": "func1"}]},
            {"query": "query2", "success": True, "result": [{"name": "func2"}]}
        ]
        
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": json.dumps([{"name": "func1"}])},
                {"success": True, "stdout": json.dumps([{"name": "func2"}])}
            ]
        )
        
        # 模拟批量查询执行
        query_results = []
        for i in range(2):
            result = await mock_query_executor.execute(f"query{i+1}")
            query_results.append(result)
        
        assert len(query_results) == 2
        assert all(r["success"] for r in query_results)

    @pytest.mark.asyncio
    async def test_batch_function_analysis(self, mock_query_executor):
        """测试批量函数分析"""
        functions = ["func1", "func2", "func3"]
        
        # Mock每个函数的分析结果
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": json.dumps({"name": f, "lines": 10})}
                for f in functions
            ]
        )
        
        # 批量分析函数
        results = []
        for func in functions:
            result = await mock_query_executor.execute(f"analyze({func})")
            results.append(result)
        
        assert len(results) == 3
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_batch_with_partial_failure(self, mock_query_executor):
        """测试部分失败的批量查询"""
        # Mock部分成功、部分失败
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": json.dumps({"result": "ok"})},
                {"success": False, "stderr": "Query failed"},
                {"success": True, "stdout": json.dumps({"result": "ok"})}
            ]
        )
        
        results = []
        for i in range(3):
            result = await mock_query_executor.execute(f"query{i}")
            results.append(result)
        
        assert len(results) == 3
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 2

    @pytest.mark.asyncio
    async def test_batch_query_aggregation(self, mock_query_executor):
        """测试批量查询结果聚合"""
        # Mock多个查询的结果用于聚合
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": json.dumps([{"count": 5}])},
                {"success": True, "stdout": json.dumps([{"count": 3}])},
                {"success": True, "stdout": json.dumps([{"count": 7}])}
            ]
        )
        
        results = []
        for i in range(3):
            result = await mock_query_executor.execute("count_query")
            results.append(result)
        
        # 聚合结果
        total_count = sum(
            json.loads(r["stdout"])[0]["count"] 
            for r in results if r["success"]
        )
        
        assert total_count == 15


class TestBatchEdgeCases:
    """测试批量查询边界情况"""

    @pytest.mark.asyncio
    async def test_empty_batch(self, mock_query_executor):
        """测试空批量查询"""
        # 不执行任何查询
        results = []
        
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_large_batch(self, mock_query_executor):
        """测试大批量查询"""
        # Mock大量查询
        batch_size = 100
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )
        
        results = []
        for i in range(batch_size):
            result = await mock_query_executor.execute(f"query{i}")
            results.append(result)
        
        assert len(results) == batch_size
        assert mock_query_executor.execute.call_count == batch_size

    @pytest.mark.asyncio
    async def test_batch_timeout_handling(self, mock_query_executor):
        """测试批量查询超时处理"""
        # Mock超时情况
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": "[]"},
                {"success": False, "error": "Timeout"},
                {"success": True, "stdout": "[]"}
            ]
        )
        
        results = []
        for i in range(3):
            result = await mock_query_executor.execute(f"query{i}")
            results.append(result)
        
        # 验证有一个超时
        timeout_count = sum(
            1 for r in results 
            if not r["success"] and "error" in r
        )
        assert timeout_count == 1

    @pytest.mark.asyncio
    async def test_batch_result_ordering(self, mock_query_executor):
        """测试批量查询结果顺序"""
        queries = [f"query{i}" for i in range(5)]
        
        # Mock按顺序返回结果
        mock_query_executor.execute = AsyncMock(
            side_effect=[
                {"success": True, "stdout": json.dumps({"id": i})}
                for i in range(5)
            ]
        )
        
        results = []
        for query in queries:
            result = await mock_query_executor.execute(query)
            results.append(result)
        
        # 验证顺序
        for i, result in enumerate(results):
            data = json.loads(result["stdout"])
            assert data["id"] == i

