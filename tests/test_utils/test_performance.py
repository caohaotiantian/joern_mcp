"""
测试性能优化工具

完整测试performance.py中的所有类和功能
"""

import asyncio

import pytest

from joern_mcp.utils.performance import (
    AdaptiveSemaphore,
    HybridCache,
    PerformanceMetrics,
    QueryComplexityAnalyzer,
    SlowQueryLogger,
    get_metrics,
    reset_metrics,
)


class TestPerformanceMetrics:
    """测试性能指标类"""

    def test_initial_state(self):
        """测试初始状态"""
        metrics = PerformanceMetrics()
        assert metrics.total_queries == 0
        assert metrics.successful_queries == 0
        assert metrics.failed_queries == 0
        assert metrics.get_avg_time() == 0.0

    def test_record_query_success(self):
        """测试记录成功查询"""
        metrics = PerformanceMetrics()
        metrics.record_query(1.5, success=True, cached=False)

        assert metrics.total_queries == 1
        assert metrics.successful_queries == 1
        assert metrics.get_avg_time() == 1.5

    def test_record_query_failure(self):
        """测试记录失败查询"""
        metrics = PerformanceMetrics()
        metrics.record_query(0.5, success=False, cached=False)

        assert metrics.total_queries == 1
        assert metrics.failed_queries == 1

    def test_cache_stats(self):
        """测试缓存统计"""
        metrics = PerformanceMetrics()
        metrics.record_query(1.0, success=True, cached=True)
        metrics.record_query(1.0, success=True, cached=False)

        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.get_cache_hit_rate() == 50.0

    def test_percentile_calculation(self):
        """测试百分位计算"""
        metrics = PerformanceMetrics()

        # 记录多个查询时间
        for i in range(100):
            metrics.record_query(i / 100.0, success=True, cached=False)

        p50 = metrics.get_percentile(50)
        p95 = metrics.get_percentile(95)
        p99 = metrics.get_percentile(99)

        assert p50 < p95 < p99

    def test_min_max_time(self):
        """测试最小/最大时间"""
        metrics = PerformanceMetrics()
        metrics.record_query(1.0, success=True, cached=False)
        metrics.record_query(5.0, success=True, cached=False)
        metrics.record_query(0.5, success=True, cached=False)

        assert metrics.min_time == 0.5
        assert metrics.max_time == 5.0

    def test_to_dict(self):
        """测试转换为字典"""
        metrics = PerformanceMetrics()
        metrics.record_query(1.0, success=True, cached=True)

        result = metrics.to_dict()
        assert "total_queries" in result
        assert "avg_time" in result
        assert "p50" in result
        assert "cache_hit_rate" in result

    def test_query_times_limit(self):
        """测试查询时间列表限制"""
        metrics = PerformanceMetrics()

        # 记录超过1000个
        for _i in range(1200):
            metrics.record_query(0.1, success=True, cached=False)

        # 应该只保留最近1000个
        assert len(metrics.query_times) == 1000


class TestHybridCache:
    """测试混合缓存类"""

    def test_basic_get_set(self):
        """测试基本的get/set"""
        cache = HybridCache(hot_size=10, cold_size=100)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = HybridCache()
        assert cache.get("nonexistent") is None

    def test_hot_cache_promotion(self):
        """测试热缓存提升"""
        cache = HybridCache(hot_size=10, cold_size=100)

        # 设置到冷缓存
        cache.set("key1", "value1", hot=False)

        # 多次访问以触发提升
        for _ in range(5):
            cache.get("key1")

        stats = cache.get_stats()
        assert stats["promotions"] > 0

    def test_compression(self):
        """测试数据压缩"""
        cache = HybridCache(compress_threshold=100)  # 100字节阈值

        # 大数据（应该被压缩）
        large_data = [{"key": f"value{i}" * 100} for i in range(100)]
        cache.set("large", large_data)

        # 取回数据
        retrieved = cache.get("large")
        assert retrieved == large_data

        # 检查压缩统计
        stats = cache.get_stats()
        assert stats["compressed"] > 0

    def test_hot_vs_cold_cache(self):
        """测试热缓存和冷缓存"""
        cache = HybridCache(hot_size=5, cold_size=20)

        # 添加到热缓存
        cache.set("hot1", "value1", hot=True)

        # 添加到冷缓存
        cache.set("cold1", "value1", hot=False)

        # 获取统计
        stats = cache.get_stats()
        assert stats["hot_size"] > 0
        assert stats["cold_size"] > 0

    def test_cache_clear(self):
        """测试清空缓存"""
        cache = HybridCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_hit_rate_calculation(self):
        """测试命中率计算"""
        cache = HybridCache()

        cache.set("key1", "value1")

        cache.get("key1")  # 命中
        cache.get("key2")  # 未命中
        cache.get("key1")  # 命中

        stats = cache.get_stats()
        # 2次命中，1次未命中 = 66.67%
        assert 60 < stats["hit_rate"] < 70

    def test_dict_compression(self):
        """测试字典数据压缩"""
        cache = HybridCache(compress_threshold=50)

        small_dict = {"a": "b"}
        large_dict = {f"key{i}": f"value{i}" * 100 for i in range(10)}

        cache.set("small", small_dict)
        cache.set("large", large_dict)

        assert cache.get("small") == small_dict
        assert cache.get("large") == large_dict

    def test_list_compression(self):
        """测试列表数据压缩"""
        cache = HybridCache(compress_threshold=50)

        large_list = [f"item{i}" * 100 for i in range(10)]
        cache.set("list", large_list)

        assert cache.get("list") == large_list


class TestAdaptiveSemaphore:
    """测试自适应信号量类"""

    @pytest.mark.asyncio
    async def test_basic_usage(self):
        """测试基本使用"""
        sem = AdaptiveSemaphore(min_concurrent=2, max_concurrent=10)

        async with sem:
            assert True  # 成功获取

    @pytest.mark.asyncio
    async def test_concurrency_control(self):
        """测试并发控制"""
        sem = AdaptiveSemaphore(min_concurrent=2, max_concurrent=5)

        concurrent_count = 0
        max_concurrent = 0

        async def task():
            nonlocal concurrent_count, max_concurrent
            async with sem:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                await asyncio.sleep(0.01)
                concurrent_count -= 1

        # 启动10个任务
        await asyncio.gather(*[task() for _ in range(10)])

        # 最大并发数不应超过初始限制
        assert max_concurrent <= sem.get_current_limit()

    @pytest.mark.asyncio
    async def test_adjustment_on_fast_response(self):
        """测试快速响应时的调整"""
        sem = AdaptiveSemaphore(
            min_concurrent=5, max_concurrent=20, target_response_time=1.0
        )

        initial_limit = sem.get_current_limit()

        # 执行快速查询（应该增加并发）
        for _i in range(15):
            await sem.adjust(0.1)  # 很快的响应时间

        # 并发限制可能增加
        final_limit = sem.get_current_limit()
        assert final_limit >= initial_limit

    @pytest.mark.asyncio
    async def test_adjustment_on_slow_response(self):
        """测试慢响应时的调整"""
        sem = AdaptiveSemaphore(
            min_concurrent=10, max_concurrent=20, target_response_time=1.0
        )

        initial_limit = sem.get_current_limit()

        # 执行慢查询（应该减少并发）
        for _i in range(15):
            await sem.adjust(5.0)  # 很慢的响应时间

        # 并发限制可能减少
        final_limit = sem.get_current_limit()
        assert final_limit <= initial_limit

    @pytest.mark.asyncio
    async def test_min_max_limits(self):
        """测试最小/最大限制"""
        sem = AdaptiveSemaphore(min_concurrent=3, max_concurrent=10)

        # 模拟极快的响应（尝试增加到最大）
        for _i in range(50):
            await sem.adjust(0.01)

        assert sem.get_current_limit() <= 10

        # 模拟极慢的响应（尝试减少到最小）
        sem2 = AdaptiveSemaphore(min_concurrent=3, max_concurrent=10)
        for _i in range(50):
            await sem2.adjust(10.0)

        assert sem2.get_current_limit() >= 3


class TestQueryComplexityAnalyzer:
    """测试查询复杂度分析器"""

    def test_simple_query(self):
        """测试简单查询"""
        analyzer = QueryComplexityAnalyzer()
        result = analyzer.analyze("cpg.method.name.l")

        assert result["complexity"] >= 1
        assert result["estimated_time"] > 0
        assert result["priority"] > 0

    def test_complex_query(self):
        """测试复杂查询"""
        analyzer = QueryComplexityAnalyzer()
        complex_query = """
        cpg.method.name("main")
            .repeat(_.caller)(10)
            .where(_.reachableBy(cpg.call))
            .dedup
        """

        result = analyzer.analyze(complex_query)

        # 复杂查询应该有更高的复杂度
        assert result["complexity"] > 3

    def test_nested_query(self):
        """测试嵌套查询"""
        analyzer = QueryComplexityAnalyzer()
        nested_query = "((((cpg.method))))"

        result = analyzer.analyze(nested_query)

        # 嵌套深度应该影响复杂度
        assert result["nesting_depth"] > 0

    def test_expensive_operations(self):
        """测试expensive操作"""
        analyzer = QueryComplexityAnalyzer()

        # 包含多个expensive操作
        query = "cpg.method.repeat(_.caller).flows.reachableBy(sources).sinks"

        result = analyzer.analyze(query)

        # 应该有较高复杂度
        assert result["complexity"] > 5

    def test_priority_calculation(self):
        """测试优先级计算"""
        analyzer = QueryComplexityAnalyzer()

        simple = analyzer.analyze("cpg.method.name.l")
        complex = analyzer.analyze("cpg.method.repeat(_.caller)(10).flows.l")

        # 简单查询应该有更高优先级
        assert simple["priority"] >= complex["priority"]

    def test_long_query(self):
        """测试长查询"""
        analyzer = QueryComplexityAnalyzer()
        long_query = "cpg.method.name.l" * 50

        result = analyzer.analyze(long_query)

        # 长度应该影响复杂度
        assert result["length"] > 100
        assert result["complexity"] > 1


class TestSlowQueryLogger:
    """测试慢查询日志器"""

    def test_log_slow_query(self):
        """测试记录慢查询"""
        logger = SlowQueryLogger(threshold=2.0)

        # 记录一个慢查询
        logger.log("slow_query", 3.0, complexity=7)

        slow_queries = logger.get_slow_queries(limit=10)
        assert len(slow_queries) == 1
        assert slow_queries[0]["duration"] == 3.0

    def test_threshold(self):
        """测试阈值过滤"""
        logger = SlowQueryLogger(threshold=5.0)

        # 快查询不应该被记录
        logger.log("fast_query", 1.0)

        slow_queries = logger.get_slow_queries()
        assert len(slow_queries) == 0

        # 慢查询应该被记录
        logger.log("slow_query", 6.0)

        slow_queries = logger.get_slow_queries()
        assert len(slow_queries) == 1

    def test_max_records(self):
        """测试最大记录数限制"""
        logger = SlowQueryLogger(threshold=1.0)
        logger.max_records = 10

        # 记录超过max_records的慢查询
        for i in range(20):
            logger.log(f"query{i}", 2.0)

        slow_queries = logger.get_slow_queries(limit=100)
        # 应该只保留最近10条
        assert len(slow_queries) == 10

    def test_query_truncation(self):
        """测试查询截断"""
        logger = SlowQueryLogger(threshold=1.0)

        long_query = "x" * 500
        logger.log(long_query, 2.0)

        slow_queries = logger.get_slow_queries()
        # 查询应该被截断到200字符 + "..."
        assert len(slow_queries[0]["query"]) <= 203

    def test_get_slow_queries_limit(self):
        """测试获取慢查询的limit参数"""
        logger = SlowQueryLogger(threshold=1.0)

        for i in range(10):
            logger.log(f"query{i}", 2.0)

        # 获取前5条
        queries = logger.get_slow_queries(limit=5)
        assert len(queries) == 5

    def test_clear(self):
        """测试清空慢查询"""
        logger = SlowQueryLogger(threshold=1.0)

        logger.log("query1", 2.0)
        logger.log("query2", 3.0)

        logger.clear()

        slow_queries = logger.get_slow_queries()
        assert len(slow_queries) == 0

    def test_additional_metadata(self):
        """测试额外元数据"""
        logger = SlowQueryLogger(threshold=1.0)

        logger.log("query", 2.0, complexity=8, cached=False, user="test")

        queries = logger.get_slow_queries()
        assert queries[0]["complexity"] == 8
        assert queries[0]["cached"] is False
        assert queries[0]["user"] == "test"


class TestGlobalMetrics:
    """测试全局指标函数"""

    def test_get_metrics(self):
        """测试获取全局指标"""
        reset_metrics()

        metrics = get_metrics()
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_queries == 0

    def test_reset_metrics(self):
        """测试重置指标"""
        metrics = get_metrics()
        metrics.record_query(1.0, success=True, cached=False)

        reset_metrics()

        new_metrics = get_metrics()
        assert new_metrics.total_queries == 0

    def test_global_metrics_singleton(self):
        """测试全局指标单例"""
        metrics1 = get_metrics()
        metrics1.record_query(1.0, success=True, cached=False)

        metrics2 = get_metrics()
        # 应该是同一个实例
        assert metrics2.total_queries == 1
