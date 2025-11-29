"""
优化的查询执行器

集成了高级缓存、性能监控、查询优化等功能
"""

import asyncio
import hashlib
import re
import time

from loguru import logger

from joern_mcp.config import settings
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.utils.performance import (
    AdaptiveSemaphore,
    HybridCache,
    QueryComplexityAnalyzer,
    SlowQueryLogger,
    get_metrics,
)


class QueryExecutionError(Exception):
    """查询执行错误"""

    pass


class QueryValidationError(Exception):
    """查询验证错误"""

    pass


class OptimizedQueryExecutor:
    """
    优化的查询执行引擎

    特性：
    - 混合缓存（LRU + TTL）
    - 自适应并发控制
    - 查询复杂度分析
    - 慢查询监控
    - 性能指标收集
    """

    def __init__(self, server_manager: JoernServerManager) -> None:
        self.server_manager = server_manager

        # 高级缓存
        self.cache = HybridCache(
            hot_size=100,
            cold_size=settings.query_cache_size,
            ttl=settings.query_cache_ttl,
            compress_threshold=10240,  # 10KB
        )

        # 自适应并发控制
        self.semaphore = AdaptiveSemaphore(
            min_concurrent=settings.max_concurrent_queries,
            max_concurrent=settings.max_concurrent_queries * 4,
            target_response_time=1.0,
        )

        # 查询分析器
        self.complexity_analyzer = QueryComplexityAnalyzer()

        # 慢查询日志
        self.slow_query_logger = SlowQueryLogger(threshold=5.0)

        # 禁止的查询模式
        self.forbidden_patterns = [
            r"System\.exit",
            r"Runtime\.getRuntime",
            r"ProcessBuilder",
            r"File\.delete",
            r"Files\.delete",
            r"scala\.sys\.process",
        ]

        # 性能指标
        self.metrics = get_metrics()

    async def execute(
        self,
        query: str,
        format: str = "json",
        timeout: int | None = None,
        use_cache: bool = True,
        priority: int | None = None,  # noqa: ARG002 - Reserved for future use
    ) -> dict:
        """
        执行查询

        Args:
            query: Scala查询语句
            format: 输出格式 (json, dot等)
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存
            priority: 查询优先级（1-5，5最高）

        Returns:
            查询结果字典
        """
        start_time = time.time()
        cached = False

        try:
            # 1. 验证查询
            is_valid, error_msg = self._validate_query(query)
            if not is_valid:
                logger.warning(f"Query validation failed: {error_msg}")
                raise QueryValidationError(error_msg)

            # 2. 分析查询复杂度
            complexity_info = self.complexity_analyzer.analyze(query)
            logger.debug(f"Query complexity: {complexity_info['complexity']}/10")

            # 3. 确保查询返回正确格式
            query = self._format_query(query, format)

            # 4. 检查缓存
            cache_key = self._get_cache_key(query)
            if use_cache:
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.debug("Cache hit")
                    cached = True
                    duration = time.time() - start_time
                    self.metrics.record_query(duration, success=True, cached=True)
                    return cached_result

            # 5. 执行查询（自适应并发控制）
            async with self.semaphore:
                self.metrics.current_concurrent += 1
                self.metrics.max_concurrent = max(
                    self.metrics.max_concurrent, self.metrics.current_concurrent
                )

                try:
                    timeout_val = timeout or settings.query_timeout

                    # 根据复杂度调整超时
                    if complexity_info["complexity"] >= 7:
                        timeout_val = int(timeout_val * 1.5)

                    # 优先使用异步方法
                    if hasattr(self.server_manager, "execute_query_async"):
                        result = await asyncio.wait_for(
                            self.server_manager.execute_query_async(query),
                            timeout=timeout_val,
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(self.server_manager.execute_query, query),
                            timeout=timeout_val,
                        )
                finally:
                    self.metrics.current_concurrent -= 1

            # 6. 处理结果
            if not result.get("success"):
                stderr = result.get("stderr", "Unknown error")
                logger.error(f"Query failed: {stderr}")
                raise QueryExecutionError(stderr) from None

            # 7. 缓存结果
            if use_cache:
                # 简单查询放入热缓存，复杂查询放入冷缓存
                hot = complexity_info["complexity"] <= 3
                self.cache.set(cache_key, result, hot=hot)

            # 8. 性能记录
            duration = time.time() - start_time
            self.metrics.record_query(duration, success=True, cached=False)

            # 9. 调整并发限制
            await self.semaphore.adjust(duration)

            # 10. 慢查询日志
            self.slow_query_logger.log(
                query, duration, complexity=complexity_info["complexity"], cached=cached
            )

            logger.debug(f"Query completed in {duration:.2f}s")
            return result

        except QueryValidationError:
            duration = time.time() - start_time
            self.metrics.record_query(duration, success=False, cached=False)
            raise
        except QueryExecutionError:
            duration = time.time() - start_time
            self.metrics.record_query(duration, success=False, cached=False)
            raise
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.metrics.record_query(duration, success=False, cached=False)
            logger.error(f"Query timeout after {timeout or settings.query_timeout}s")
            raise QueryExecutionError("Query timeout") from None
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_query(duration, success=False, cached=False)
            logger.exception(f"Query execution failed: {e}")
            raise QueryExecutionError(str(e)) from None

    def _validate_query(self, query: str) -> tuple[bool, str]:
        """验证查询安全性"""
        # 检查长度
        if len(query) > 10000:
            return False, "Query too long (max 10000 characters)"

        # 检查禁止的模式
        for pattern in self.forbidden_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Forbidden operation: {pattern}"

        return True, ""

    def _format_query(self, query: str, format: str) -> str:
        """格式化查询以返回指定格式"""
        query = query.strip()

        if format == "json":
            if not query.endswith(".toJson"):
                if "\n" in query or query.count(";") > 0:
                    query = f"({query}).toJson"
                else:
                    query = f"{query}.toJson"
        elif format == "dot" and not query.endswith(".toDot"):
            query = f"{query}.toDot"

        return query

    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("Query cache cleared")

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return self.cache.get_stats()

    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        return self.metrics.to_dict()

    def get_slow_queries(self, limit: int = 10) -> list:
        """获取慢查询列表"""
        return self.slow_query_logger.get_slow_queries(limit)

    def get_current_concurrent_limit(self) -> int:
        """获取当前并发限制"""
        return self.semaphore.get_current_limit()


# 兼容性：保留原有的QueryExecutor类名
QueryExecutor = OptimizedQueryExecutor
