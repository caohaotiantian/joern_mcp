#!/usr/bin/env python3
"""
性能基准测试工具

测试查询性能、缓存效率、并发能力等
"""

import asyncio
import json

# 添加项目路径
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor
from joern_mcp.joern.manager import JoernManager, JoernNotFoundError
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.utils.performance import get_metrics, reset_metrics

# 测试查询集
TEST_QUERIES = [
    # 简单查询
    "cpg.method.name.l",
    "cpg.method.signature.l",
    "cpg.method.isExternal(false).name.l",
    # 中等复杂度查询
    'cpg.method.name("main").parameter.name.l',
    'cpg.call.methodFullName(".*printf.*").l',
    "cpg.method.where(_.parameter.size > 3).name.l",
    # 复杂查询
    'cpg.method.name(".*exec.*").caller.name.l',
    "cpg.method.where(_.isPublic).callIn.method.name.l",
]


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.server = None
        self.executor = None
        self.results = []

    async def setup(self):
        """初始化测试环境"""
        logger.info("Setting up test environment...")

        try:
            manager = JoernManager()
            self.server = JoernServerManager(joern_manager=manager, port=19999)
            await self.server.start(timeout=120)
            self.executor = OptimizedQueryExecutor(self.server)

            logger.info("Test environment ready")
        except JoernNotFoundError:
            logger.error("Joern not found! Please install Joern first.")
            raise
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    async def teardown(self):
        """清理测试环境"""
        logger.info("Cleaning up...")
        if self.server:
            await self.server.stop()

    async def test_single_query_performance(self):
        """测试单查询性能"""
        logger.info("=" * 60)
        logger.info("Test 1: Single Query Performance")
        logger.info("=" * 60)

        results = []

        for query in TEST_QUERIES:
            logger.info(f"\nTesting query: {query[:60]}...")

            # 测试3次取平均
            times = []
            for i in range(3):
                start = time.time()
                try:
                    await self.executor.execute(query, use_cache=False)
                    duration = time.time() - start
                    times.append(duration)
                    logger.info(f"  Run {i + 1}: {duration:.3f}s")
                except Exception as e:
                    logger.error(f"  Run {i + 1} failed: {e}")

            if times:
                avg_time = sum(times) / len(times)
                results.append(
                    {
                        "query": query,
                        "avg_time": avg_time,
                        "min_time": min(times),
                        "max_time": max(times),
                    }
                )
                logger.info(f"  Average: {avg_time:.3f}s")

        self.results.append({"test": "single_query_performance", "results": results})

        return results

    async def test_cache_performance(self):
        """测试缓存性能"""
        logger.info("=" * 60)
        logger.info("Test 2: Cache Performance")
        logger.info("=" * 60)

        query = TEST_QUERIES[0]

        # 第一次查询（缓存未命中）
        logger.info("\nFirst query (cache miss)...")
        start = time.time()
        await self.executor.execute(query, use_cache=True)
        first_time = time.time() - start
        logger.info(f"  Time: {first_time:.3f}s")

        # 第二次查询（缓存命中）
        logger.info("\nSecond query (cache hit)...")
        start = time.time()
        await self.executor.execute(query, use_cache=True)
        second_time = time.time() - start
        logger.info(f"  Time: {second_time:.3f}s")

        # 计算加速比
        speedup = first_time / second_time if second_time > 0 else 0
        logger.info(f"\nCache speedup: {speedup:.1f}x")

        cache_stats = self.executor.get_cache_stats()
        logger.info(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")

        self.results.append(
            {
                "test": "cache_performance",
                "first_time": first_time,
                "second_time": second_time,
                "speedup": speedup,
                "cache_stats": cache_stats,
            }
        )

    async def test_concurrent_performance(self):
        """测试并发性能"""
        logger.info("=" * 60)
        logger.info("Test 3: Concurrent Performance")
        logger.info("=" * 60)

        query = TEST_QUERIES[1]
        concurrent_levels = [1, 5, 10, 20]

        results = []

        for concurrent in concurrent_levels:
            logger.info(f"\nTesting {concurrent} concurrent queries...")

            start = time.time()
            tasks = [
                self.executor.execute(query, use_cache=False) for _ in range(concurrent)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start

            qps = concurrent / duration if duration > 0 else 0
            logger.info(f"  Time: {duration:.3f}s")
            logger.info(f"  QPS: {qps:.2f}")

            results.append({"concurrent": concurrent, "duration": duration, "qps": qps})

        self.results.append({"test": "concurrent_performance", "results": results})

    async def test_adaptive_concurrency(self):
        """测试自适应并发"""
        logger.info("=" * 60)
        logger.info("Test 4: Adaptive Concurrency")
        logger.info("=" * 60)

        # 发送一系列查询，观察并发限制的调整
        logger.info("\nSending queries to trigger adaptation...")

        initial_limit = self.executor.get_current_concurrent_limit()
        logger.info(f"Initial concurrent limit: {initial_limit}")

        # 发送快速查询
        for _i in range(20):
            await self.executor.execute(TEST_QUERIES[0])

        final_limit = self.executor.get_current_concurrent_limit()
        logger.info(f"Final concurrent limit: {final_limit}")

        self.results.append(
            {
                "test": "adaptive_concurrency",
                "initial_limit": initial_limit,
                "final_limit": final_limit,
                "adjustment": final_limit - initial_limit,
            }
        )

    async def test_slow_query_detection(self):
        """测试慢查询检测"""
        logger.info("=" * 60)
        logger.info("Test 5: Slow Query Detection")
        logger.info("=" * 60)

        # 执行一个复杂查询
        complex_query = TEST_QUERIES[-1]
        logger.info(f"\nExecuting complex query: {complex_query[:60]}...")

        start = time.time()
        await self.executor.execute(complex_query)
        duration = time.time() - start

        logger.info(f"  Time: {duration:.3f}s")

        # 获取慢查询列表
        slow_queries = self.executor.get_slow_queries(limit=5)
        logger.info(f"\nSlow queries detected: {len(slow_queries)}")

        for sq in slow_queries[:3]:
            logger.info(f"  - {sq['query'][:50]}... ({sq['duration']:.2f}s)")

        self.results.append(
            {
                "test": "slow_query_detection",
                "slow_query_count": len(slow_queries),
                "slowest_queries": slow_queries[:3],
            }
        )

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("Starting Performance Benchmark Tests")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        try:
            await self.setup()

            # 重置指标
            reset_metrics()

            # 运行测试
            await self.test_single_query_performance()
            await self.test_cache_performance()
            await self.test_concurrent_performance()
            await self.test_adaptive_concurrency()
            await self.test_slow_query_detection()

            # 获取总体性能指标
            metrics = get_metrics()
            logger.info("\n" + "=" * 60)
            logger.info("Overall Performance Metrics")
            logger.info("=" * 60)
            logger.info(json.dumps(metrics.to_dict(), indent=2))

            # 保存结果
            self.save_results()

        finally:
            await self.teardown()

    def save_results(self):
        """保存测试结果"""
        output_dir = Path(__file__).parent.parent / "benchmark_results"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"benchmark_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nResults saved to: {output_file}")


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
