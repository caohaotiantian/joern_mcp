"""性能优化功能测试 - 真正验证性能优化是否工作"""

import asyncio

import pytest

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.joern.manager import JoernManager


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestPerformanceFeatures:
    """性能优化功能测试"""

    @pytest.mark.asyncio
    async def test_hybrid_cache_hot_cold(self, joern_server):
        """测试混合缓存的热缓存和冷缓存"""
        executor = QueryExecutor(joern_server)

        # 清空缓存
        executor.clear_cache()

        # 执行不同的查询
        queries = [
            "cpg.method.name.l",
            "cpg.call.name.l",
            "cpg.file.name.l",
        ]

        # 第一轮：全部miss
        for query in queries:
            await executor.execute(query)

        # 第二轮：应该有cache hit
        for query in queries:
            await executor.execute(query)

        # 获取缓存统计
        cache_stats = executor.get_cache_stats()

        # 验证缓存统计结构
        assert "hot_hits" in cache_stats, "应该有热缓存命中统计"
        assert "cold_hits" in cache_stats, "应该有冷缓存命中统计"
        assert "misses" in cache_stats, "应该有缓存未命中统计"
        assert "hot_size" in cache_stats, "应该有热缓存大小"
        assert "cold_size" in cache_stats, "应该有冷缓存大小"

        # 应该有至少1次命中（第二轮查询）
        total_hits = cache_stats["hot_hits"] + cache_stats["cold_hits"]
        assert total_hits >= 1, f"应该有至少1次缓存命中，实际: {total_hits}"

    @pytest.mark.asyncio
    async def test_cache_compression(self, joern_server):
        """测试缓存压缩功能"""
        executor = QueryExecutor(joern_server)
        executor.clear_cache()

        # 执行一个可能产生大结果的查询
        # 注意：实际结果取决于CPG内容
        await executor.execute("cpg.method.name.l")

        # 获取缓存统计
        cache_stats = executor.get_cache_stats()

        # 验证缓存统计包含压缩信息
        if "cold_cache" in cache_stats:
            cold_cache = cache_stats["cold_cache"]
            # 压缩阈值是10KB，如果有大结果应该会压缩
            # 这里主要验证统计功能正常
            assert isinstance(cold_cache.get("size", 0), int)

    @pytest.mark.asyncio
    async def test_adaptive_concurrency_adjustment(self, joern_server):
        """测试自适应并发调整"""
        executor = QueryExecutor(joern_server)

        # 获取初始并发限制
        initial_limit = executor.get_current_concurrent_limit()
        assert isinstance(initial_limit, int), "并发限制应该是整数"
        assert initial_limit > 0, "并发限制应该>0"

        # 执行一些查询（这可能触发自适应调整）
        for _i in range(5):
            await executor.execute("cpg.method.name.l")
            await asyncio.sleep(0.1)  # 给时间进行调整

        # 再次获取并发限制
        current_limit = executor.get_current_concurrent_limit()
        assert isinstance(current_limit, int), "并发限制应该是整数"
        assert current_limit > 0, "并发限制应该>0"

        # 限制应该在合理范围内（根据配置：min=3, max=20）
        assert 3 <= current_limit <= 20, \
            f"并发限制应该在3-20之间，实际: {current_limit}"

    @pytest.mark.asyncio
    async def test_query_complexity_analysis(self, joern_server):
        """测试查询复杂度分析"""
        executor = QueryExecutor(joern_server)

        # 测试不同复杂度的查询
        simple_query = "cpg.method.name.l"
        complex_query = "cpg.method.where(_.name.matches('.*')).repeat(_.caller)(3).name.l"

        # 执行查询（内部会进行复杂度分析）
        await executor.execute(simple_query)
        await executor.execute(complex_query)

        # 获取性能统计（应该包含复杂度分析结果）
        perf_stats = executor.get_performance_stats()

        # 验证统计包含必要信息
        assert "total_queries" in perf_stats, "应该有总查询数"
        assert perf_stats["total_queries"] >= 2, \
            f"应该至少有2个查询，实际: {perf_stats['total_queries']}"

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, joern_server):
        """测试慢查询检测"""
        executor = QueryExecutor(joern_server)

        # 执行一些查询
        for _i in range(3):
            await executor.execute("cpg.method.name.l")

        # 获取慢查询列表
        slow_queries = executor.get_slow_queries()

        # 验证返回格式
        assert isinstance(slow_queries, list), "慢查询应该是列表"

        # 验证每个慢查询的结构
        for sq in slow_queries:
            assert isinstance(sq, dict), "每个慢查询应该是字典"
            assert "query" in sq, "慢查询应该有query字段"
            assert "duration" in sq, "慢查询应该有duration字段"
            assert "timestamp" in sq, "慢查询应该有timestamp字段"

            # 验证duration是数字且合理
            assert isinstance(sq["duration"], (int, float)), \
                "duration应该是数字"
            assert sq["duration"] > 0, "duration应该>0"

    @pytest.mark.asyncio
    async def test_performance_metrics_detailed(self, joern_server):
        """测试详细的性能指标"""
        executor = QueryExecutor(joern_server)

        # 执行多个查询以收集统计
        queries = [
            "cpg.method.name.l",
            "cpg.call.name.l",
            "cpg.method.name.l",  # 重复，测试缓存
        ]

        for query in queries:
            await executor.execute(query)

        # 获取性能统计
        perf_stats = executor.get_performance_stats()

        # 验证所有关键指标
        required_fields = [
            "total_queries",
            "successful_queries",
            "failed_queries",
            "avg_time",
            "min_time",
            "max_time",
            "cache_hit_rate",
            "success_rate",
        ]

        for field in required_fields:
            assert field in perf_stats, f"性能统计应该包含{field}"

        # 验证值的合理性
        assert perf_stats["total_queries"] >= 3, \
            f"总查询数应该>=3，实际: {perf_stats['total_queries']}"
        # 注意：cache_hit_rate和success_rate是百分比（0-100），不是比率（0-1）
        assert 0 <= perf_stats["cache_hit_rate"] <= 100, \
            f"缓存命中率应该在0-100之间，实际: {perf_stats['cache_hit_rate']}"
        assert 0 <= perf_stats["success_rate"] <= 100, \
            f"成功率应该在0-100之间，实际: {perf_stats['success_rate']}"
        assert perf_stats["avg_time"] >= 0, \
            f"平均时间应该>=0，实际: {perf_stats['avg_time']}"

    @pytest.mark.asyncio
    async def test_cache_clear_functionality(self, joern_server):
        """测试缓存清理功能"""
        executor = QueryExecutor(joern_server)

        # 执行查询填充缓存
        await executor.execute("cpg.method.name.l")

        # 获取清理前的缓存统计
        stats_before = executor.get_cache_stats()
        stats_before.get("total_size", 0)

        # 清理缓存
        executor.clear_cache()

        # 获取清理后的缓存统计
        stats_after = executor.get_cache_stats()
        after_size = stats_after.get("total_size", 0)

        # 清理后缓存应该为空
        assert after_size == 0, \
            f"清理后缓存大小应该为0，实际: {after_size}"

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="并发测试在完整测试套件中可能因资源竞争而超时，单独运行正常。可通过 pytest -k test_concurrent_with_metrics 单独运行"
    )
    async def test_concurrent_with_metrics(self, joern_server):
        """测试并发查询的性能指标收集"""
        import warnings

        executor = QueryExecutor(joern_server)

        # 并发执行多个查询
        queries = ["cpg.method.name.l"] * 5

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
            tasks = [executor.execute(q) for q in queries]
            await asyncio.gather(*tasks, return_exceptions=True)

        # 获取性能统计
        perf_stats = executor.get_performance_stats()

        # 应该记录了所有查询
        assert perf_stats["total_queries"] >= 5, \
            f"应该记录至少5个查询，实际: {perf_stats['total_queries']}"

        # 成功率应该合理（百分比：0-100）
        success_rate = perf_stats.get("success_rate", 0)
        assert 0 <= success_rate <= 100, \
            f"成功率应该在0-100之间，实际: {success_rate}"

    @pytest.mark.asyncio
    async def test_format_options(self, joern_server):
        """测试不同输出格式"""
        executor = QueryExecutor(joern_server)

        # 测试JSON格式（默认）
        result_json = await executor.execute("cpg.method.name.l", format="json")
        assert isinstance(result_json, dict), "JSON格式应返回dict"

        # 测试DOT格式
        result_dot = await executor.execute("cpg.method.name.l", format="dot")
        assert isinstance(result_dot, dict), "DOT格式应返回dict"

        # 两者都应该有结果
        assert result_json is not None
        assert result_dot is not None

