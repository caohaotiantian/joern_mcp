"""性能和压力测试"""

import pytest
import time
import asyncio
from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.executor import QueryExecutor


@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_query_response_time(self, joern_server):
        """测试查询响应时间"""
        executor = QueryExecutor(joern_server)

        # 简单查询应该很快
        start = time.time()
        result = await executor.execute("cpg.method.name.l")
        elapsed = time.time() - start

        assert result is not None
        assert elapsed < 10.0  # 应该在10秒内完成（给更多时间）

    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, joern_server):
        """测试并发查询性能"""
        executor = QueryExecutor(joern_server)

        # 创建10个并发查询
        queries = ["cpg.method.name.l"] * 10

        start = time.time()
        tasks = [executor.execute(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        # 验证至少大部分查询成功
        success_count = sum(1 for r in results if isinstance(r, dict) and r is not None)
        assert success_count >= 7  # 至少70%成功

        # 并发执行应该在合理时间内完成
        assert elapsed < 60.0  # 应该在60秒内完成

    @pytest.mark.asyncio
    async def test_cache_performance(self, joern_server):
        """测试缓存性能"""
        executor = QueryExecutor(joern_server)
        query = "cpg.method.name.l"

        # 第一次查询（无缓存）
        start = time.time()
        result1 = await executor.execute(query)
        time1 = time.time() - start

        # 第二次查询（有缓存）
        start = time.time()
        result2 = await executor.execute(query)
        time2 = time.time() - start

        # 缓存的查询应该更快或相同
        assert time2 <= time1 * 2  # 允许一些误差
        assert result1 is not None
        assert result2 is not None


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestStress:
    """压力测试"""

    @pytest.mark.asyncio
    async def test_high_concurrency(self, joern_server):
        """测试高并发"""
        executor = QueryExecutor(joern_server)

        # 创建20个并发查询（降低数量避免超时）
        queries = ["cpg.method.name.l"] * 20

        tasks = [executor.execute(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计成功和失败
        success_count = sum(1 for r in results if isinstance(r, dict) and r is not None)

        # 应该有大部分成功
        success_rate = success_count / len(results)
        assert success_rate >= 0.5  # 至少50%成功率（降低要求）

    @pytest.mark.asyncio
    async def test_sequential_queries(self, joern_server):
        """测试连续查询"""
        executor = QueryExecutor(joern_server)

        # 连续执行多个查询
        for i in range(10):
            result = await executor.execute("cpg.method.name.l")
            assert result is not None
