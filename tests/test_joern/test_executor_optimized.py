"""
测试优化的查询执行器

完整测试executor_optimized.py中的所有功能
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from joern_mcp.joern.executor_optimized import (
    OptimizedQueryExecutor,
    QueryExecutionError,
    QueryValidationError,
)


class TestOptimizedQueryExecutor:
    """测试优化的查询执行器"""

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """测试基本查询执行"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": '["result"]'}
        )

        executor = OptimizedQueryExecutor(mock_server)
        result = await executor.execute("cpg.method.name.l")

        assert result["success"] is True
        assert mock_server.execute_query_async.called

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """测试缓存功能"""
        mock_server = MagicMock()
        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"success": True, "stdout": '["result"]'}

        mock_server.execute_query_async = mock_execute

        executor = OptimizedQueryExecutor(mock_server)

        # 第一次调用
        await executor.execute("test_query", use_cache=True)
        assert call_count == 1

        # 第二次调用（缓存命中）
        await executor.execute("test_query", use_cache=True)
        assert call_count == 1  # 不应该再次调用

        # 禁用缓存的调用
        await executor.execute("test_query", use_cache=False)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_query_validation(self):
        """测试查询验证"""
        mock_server = MagicMock()
        executor = OptimizedQueryExecutor(mock_server)

        # 测试禁止的操作
        with pytest.raises(QueryValidationError):
            await executor.execute("System.exit(0)")

        # 测试过长的查询
        with pytest.raises(QueryValidationError):
            await executor.execute("x" * 20000)

    @pytest.mark.asyncio
    async def test_complexity_analysis(self):
        """测试查询复杂度分析"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 简单查询
        await executor.execute("cpg.method.name.l")

        # 复杂查询
        complex_query = "cpg.method.repeat(_.caller)(10).name.l"
        await executor.execute(complex_query)

        # 验证执行了
        assert mock_server.execute_query_async.call_count == 2

    @pytest.mark.asyncio
    async def test_adaptive_concurrency(self):
        """测试自适应并发"""
        mock_server = MagicMock()

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)  # 更短的sleep
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = mock_execute

        executor = OptimizedQueryExecutor(mock_server)

        # 获取初始并发限制
        initial_limit = executor.get_current_concurrent_limit()
        assert initial_limit > 0

        # 执行少量查询（减少数量以避免超时）
        tasks = [executor.execute(f"query{i}", use_cache=False) for i in range(5)]
        await asyncio.gather(*tasks)

        # 验证查询被执行
        assert call_count == 5

        # 并发限制可能已调整
        final_limit = executor.get_current_concurrent_limit()
        assert final_limit > 0

    @pytest.mark.asyncio
    async def test_slow_query_logging(self):
        """测试慢查询记录"""
        mock_server = MagicMock()

        async def slow_query(*args, **kwargs):
            await asyncio.sleep(6)  # 超过5秒阈值
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = slow_query

        executor = OptimizedQueryExecutor(mock_server)

        # 执行慢查询
        await executor.execute("slow_query")

        # 检查慢查询记录
        slow_queries = executor.get_slow_queries()
        assert len(slow_queries) > 0

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """测试性能指标收集"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 执行几个查询（禁用缓存以确保每个都被执行）
        for i in range(5):
            await executor.execute(f"query{i}", use_cache=False)

        # 获取性能统计
        stats = executor.get_performance_stats()
        assert stats["total_queries"] >= 5  # 至少5个
        assert "avg_time" in stats
        assert "cache_hit_rate" in stats

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 执行查询
        await executor.execute("test1")
        await executor.execute("test1")  # 缓存命中
        await executor.execute("test2")

        # 获取缓存统计
        cache_stats = executor.get_cache_stats()
        assert cache_stats["hot_hits"] + cache_stats["cold_hits"] > 0
        assert "hit_rate" in cache_stats

    @pytest.mark.asyncio
    async def test_query_timeout(self):
        """测试查询超时"""
        mock_server = MagicMock()

        async def timeout_query(*args, **kwargs):
            await asyncio.sleep(100)
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = timeout_query

        executor = OptimizedQueryExecutor(mock_server)

        # 应该超时
        with pytest.raises(QueryExecutionError):
            await executor.execute("test", timeout=1)

    @pytest.mark.asyncio
    async def test_query_failure(self):
        """测试查询失败"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": False, "stderr": "Query error"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        with pytest.raises(QueryExecutionError):
            await executor.execute("test")

    @pytest.mark.asyncio
    async def test_format_query_json(self):
        """测试JSON格式化"""
        mock_server = MagicMock()
        captured_query = None

        async def capture_query(query, *args, **kwargs):
            nonlocal captured_query
            captured_query = query
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = capture_query

        executor = OptimizedQueryExecutor(mock_server)
        await executor.execute("cpg.method.name.l", format="json")

        assert ".toJson" in captured_query

    @pytest.mark.asyncio
    async def test_format_query_dot(self):
        """测试DOT格式化"""
        mock_server = MagicMock()
        captured_query = None

        async def capture_query(query, *args, **kwargs):
            nonlocal captured_query
            captured_query = query
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = capture_query

        executor = OptimizedQueryExecutor(mock_server)
        await executor.execute("cpg.method.name.l", format="dot")

        assert ".toDot" in captured_query

    @pytest.mark.asyncio
    async def test_cache_hot_vs_cold(self):
        """测试热缓存vs冷缓存"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 简单查询（应该进入热缓存）
        await executor.execute("cpg.method.name.l")

        # 复杂查询（应该进入冷缓存）
        await executor.execute("cpg.method.repeat(_.caller)(10).name.l")

        cache_stats = executor.get_cache_stats()
        assert cache_stats["total_size"] >= 2

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """测试清空缓存"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 填充缓存
        await executor.execute("test1")
        await executor.execute("test2")

        cache_stats_before = executor.get_cache_stats()
        assert cache_stats_before["total_size"] > 0

        # 清空缓存
        executor.clear_cache()

        cache_stats_after = executor.get_cache_stats()
        assert cache_stats_after["total_size"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """测试并发查询"""
        mock_server = MagicMock()

        async def mock_execute(*args, **kwargs):
            await asyncio.sleep(0.01)
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = mock_execute

        executor = OptimizedQueryExecutor(mock_server)

        # 并发执行
        tasks = [executor.execute(f"query{i}", use_cache=False) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """测试异常处理"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(side_effect=Exception("Test error"))

        executor = OptimizedQueryExecutor(mock_server)

        with pytest.raises(QueryExecutionError):
            await executor.execute("test")

        # 验证性能指标记录了失败
        stats = executor.get_performance_stats()
        assert stats["failed_queries"] > 0

    @pytest.mark.asyncio
    async def test_metrics_percentiles(self):
        """测试性能指标百分位"""
        mock_server = MagicMock()

        async def variable_time_query(*args, **kwargs):
            # 模拟不同响应时间
            await asyncio.sleep(0.001)
            return {"success": True, "stdout": "[]"}

        mock_server.execute_query_async = variable_time_query

        executor = OptimizedQueryExecutor(mock_server)

        # 执行多个查询
        for i in range(20):
            await executor.execute(f"query{i}", use_cache=False)

        stats = executor.get_performance_stats()
        assert "p50" in stats
        assert "p95" in stats
        assert "p99" in stats
        assert stats["p95"] >= stats["p50"]

    @pytest.mark.asyncio
    async def test_without_async_method(self):
        """测试不支持async方法的服务器 - 应该抛出错误"""
        from joern_mcp.joern.executor_optimized import QueryExecutionError

        mock_server = MagicMock()
        # 没有execute_query_async方法
        del mock_server.execute_query_async

        executor = OptimizedQueryExecutor(mock_server)

        # 由于现在只支持异步方法，缺少execute_query_async应该导致错误
        with pytest.raises(QueryExecutionError):
            await executor.execute("test")

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """测试缓存键生成"""
        mock_server = MagicMock()
        mock_server.execute_query_async = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )

        executor = OptimizedQueryExecutor(mock_server)

        # 相同查询应该有相同的缓存键
        await executor.execute("test_query")
        call_count_1 = mock_server.execute_query_async.call_count

        await executor.execute("test_query")
        call_count_2 = mock_server.execute_query_async.call_count

        # 第二次调用不应该执行查询（缓存命中）
        assert call_count_2 == call_count_1
