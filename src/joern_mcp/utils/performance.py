"""
性能优化工具

提供高级缓存、性能监控、查询优化等功能
"""

import asyncio
import json
import time
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from cachetools import LRUCache, TTLCache
from loguru import logger


@dataclass
class PerformanceMetrics:
    """性能指标"""

    # 查询统计
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    # 时间统计
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0

    # 缓存统计
    cache_hits: int = 0
    cache_misses: int = 0

    # 并发统计
    current_concurrent: int = 0
    max_concurrent: int = 0

    # 查询时间分布 (P50, P95, P99)
    query_times: list = field(default_factory=list)

    def record_query(self, duration: float, success: bool = True, cached: bool = False):
        """记录一次查询"""
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1

        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.query_times.append(duration)

        # 只保留最近1000条记录
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

    def get_avg_time(self) -> float:
        """获取平均响应时间"""
        if self.total_queries == 0:
            return 0.0
        return self.total_time / self.total_queries

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total * 100

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries * 100

    def get_percentile(self, percentile: int) -> float:
        """获取百分位数（P50, P95, P99）"""
        if not self.query_times:
            return 0.0
        sorted_times = sorted(self.query_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "avg_time": round(self.get_avg_time(), 3),
            "min_time": round(self.min_time, 3)
            if self.min_time != float("inf")
            else 0.0,
            "max_time": round(self.max_time, 3),
            "p50": round(self.get_percentile(50), 3),
            "p95": round(self.get_percentile(95), 3),
            "p99": round(self.get_percentile(99), 3),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
            "success_rate": round(self.get_success_rate(), 2),
            "current_concurrent": self.current_concurrent,
            "max_concurrent": self.max_concurrent,
        }


class HybridCache:
    """
    混合缓存：LRU + TTL

    - 热数据使用LRU策略（快速访问）
    - 冷数据使用TTL策略（自动过期）
    - 支持缓存压缩（大结果）
    """

    def __init__(
        self,
        hot_size: int = 100,
        cold_size: int = 1000,
        ttl: int = 3600,
        compress_threshold: int = 10240,  # 10KB
    ):
        self.hot_cache = LRUCache(maxsize=hot_size)
        self.cold_cache = TTLCache(maxsize=cold_size, ttl=ttl)
        self.compress_threshold = compress_threshold

        # 访问统计
        self.access_count: dict[str, int] = defaultdict(int)
        self.promotion_threshold = 3  # 访问3次后提升到热缓存

        # 缓存统计
        self.stats = {
            "hot_hits": 0,
            "cold_hits": 0,
            "misses": 0,
            "promotions": 0,
            "compressed": 0,
        }

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        # 先查热缓存
        if key in self.hot_cache:
            self.stats["hot_hits"] += 1
            self.access_count[key] += 1
            return self._decompress(self.hot_cache[key])

        # 再查冷缓存
        if key in self.cold_cache:
            self.stats["cold_hits"] += 1
            self.access_count[key] += 1
            value = self.cold_cache[key]

            # 访问次数达到阈值，提升到热缓存
            if self.access_count[key] >= self.promotion_threshold:
                self.hot_cache[key] = value
                del self.cold_cache[key]
                self.stats["promotions"] += 1
                logger.debug(f"Cache key promoted to hot: {key}")

            return self._decompress(value)

        # 缓存未命中
        self.stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, hot: bool = False):
        """设置缓存"""
        # 压缩大结果
        compressed_value = self._compress(value)

        if hot:
            self.hot_cache[key] = compressed_value
        else:
            self.cold_cache[key] = compressed_value

        self.access_count[key] = 0

    def _compress(self, value: Any) -> Any:
        """压缩值（如果需要）"""
        # 尝试序列化
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value).encode()

            # 如果大于阈值，进行压缩
            if len(serialized) > self.compress_threshold:
                compressed = zlib.compress(serialized, level=6)
                self.stats["compressed"] += 1
                return {"_compressed": True, "data": compressed}

        return value

    def _decompress(self, value: Any) -> Any:
        """解压缩值"""
        if isinstance(value, dict) and value.get("_compressed"):
            decompressed = zlib.decompress(value["data"])
            return json.loads(decompressed.decode())
        return value

    def clear(self):
        """清空缓存"""
        self.hot_cache.clear()
        self.cold_cache.clear()
        self.access_count.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total_hits = self.stats["hot_hits"] + self.stats["cold_hits"]
        total_requests = total_hits + self.stats["misses"]

        return {
            **self.stats,
            "hot_size": len(self.hot_cache),
            "cold_size": len(self.cold_cache),
            "total_size": len(self.hot_cache) + len(self.cold_cache),
            "hit_rate": round(total_hits / total_requests * 100, 2)
            if total_requests > 0
            else 0.0,
        }


class AdaptiveSemaphore:
    """
    自适应信号量

    根据系统负载和查询性能动态调整并发数
    """

    def __init__(
        self,
        min_concurrent: int = 5,
        max_concurrent: int = 20,
        target_response_time: float = 1.0,  # 目标响应时间（秒）
    ):
        self.min_concurrent = min_concurrent
        self.max_concurrent = max_concurrent
        self.current_limit = min_concurrent
        self.target_response_time = target_response_time

        self.semaphore = asyncio.Semaphore(self.current_limit)
        self.lock = asyncio.Lock()

        # 性能监控
        self.recent_times: list = []
        self.adjustment_interval = 10  # 每10次查询评估一次
        self.query_count = 0

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()

    async def adjust(self, response_time: float):
        """根据响应时间调整并发限制"""
        self.recent_times.append(response_time)
        self.query_count += 1

        # 每N次查询评估一次
        if self.query_count % self.adjustment_interval != 0:
            return

        # 计算平均响应时间
        avg_time = sum(self.recent_times) / len(self.recent_times)
        self.recent_times = []  # 清空

        async with self.lock:
            old_limit = self.current_limit

            # 响应时间过长，减少并发
            if avg_time > self.target_response_time * 1.5:
                new_limit = max(self.min_concurrent, self.current_limit - 2)
            # 响应时间很快，增加并发
            elif avg_time < self.target_response_time * 0.5:
                new_limit = min(self.max_concurrent, self.current_limit + 2)
            else:
                new_limit = self.current_limit

            if new_limit != old_limit:
                self.current_limit = new_limit
                # 重新创建信号量
                self.semaphore = asyncio.Semaphore(self.current_limit)
                logger.info(f"Adjusted concurrent limit: {old_limit} -> {new_limit}")

    def get_current_limit(self) -> int:
        """获取当前并发限制"""
        return self.current_limit


class QueryComplexityAnalyzer:
    """查询复杂度分析器"""

    @staticmethod
    def analyze(query: str) -> dict:
        """
        分析查询复杂度

        返回：
        - complexity: 1-10 (1最简单，10最复杂)
        - estimated_time: 预估执行时间（秒）
        - priority: 优先级（1-5，5最高）
        """
        complexity = 1

        # 1. 查询长度
        length_score = min(len(query) // 100, 3)
        complexity += length_score

        # 2. 嵌套深度（括号层数）
        max_depth = 0
        current_depth = 0
        for char in query:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1
        complexity += min(max_depth, 3)

        # 3. 特殊操作
        expensive_ops = ["repeat", "flows", "reachableBy", "sinks", "sources"]
        for op in expensive_ops:
            if op in query:
                complexity += 1

        complexity = min(complexity, 10)

        # 预估时间（简单线性模型）
        estimated_time = complexity * 0.5

        # 优先级（复杂度越低优先级越高）
        priority = 6 - (complexity // 2)

        return {
            "complexity": complexity,
            "estimated_time": estimated_time,
            "priority": max(1, min(5, priority)),
            "length": len(query),
            "nesting_depth": max_depth,
        }


class SlowQueryLogger:
    """慢查询日志"""

    def __init__(self, threshold: float = 5.0):
        self.threshold = threshold
        self.slow_queries: list = []
        self.max_records = 100

    def log(self, query: str, duration: float, **kwargs):
        """记录慢查询"""
        if duration >= self.threshold:
            record = {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "duration": round(duration, 3),
                "timestamp": time.time(),
                **kwargs,
            }
            self.slow_queries.append(record)

            # 保持列表大小
            if len(self.slow_queries) > self.max_records:
                self.slow_queries = self.slow_queries[-self.max_records :]

            logger.warning(f"Slow query detected: {duration:.2f}s - {query[:100]}")

    def get_slow_queries(self, limit: int = 10) -> list:
        """获取最近的慢查询"""
        return self.slow_queries[-limit:]

    def clear(self):
        """清空慢查询记录"""
        self.slow_queries.clear()


# 全局性能监控实例
_global_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """获取全局性能指标"""
    return _global_metrics


def reset_metrics():
    """重置性能指标"""
    global _global_metrics
    _global_metrics = PerformanceMetrics()
