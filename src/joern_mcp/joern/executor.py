"""查询执行器"""

import hashlib
import asyncio
import re
from typing import Dict, Optional, Tuple
from cachetools import TTLCache
from loguru import logger
from joern_mcp.config import settings
from joern_mcp.joern.server import JoernServerManager


class QueryExecutionError(Exception):
    """查询执行错误"""

    pass


class QueryValidationError(Exception):
    """查询验证错误"""

    pass


class QueryExecutor:
    """查询执行引擎"""

    def __init__(self, server_manager: JoernServerManager) -> None:
        self.server_manager = server_manager
        self.cache: TTLCache = TTLCache(
            maxsize=settings.query_cache_size, ttl=settings.query_cache_ttl
        )
        self.query_semaphore = asyncio.Semaphore(settings.max_concurrent_queries)

        # 禁止的查询模式
        self.forbidden_patterns = [
            r"System\.exit",
            r"Runtime\.getRuntime",
            r"ProcessBuilder",
            r"File\.delete",
            r"Files\.delete",
            r"scala\.sys\.process",
        ]

    async def execute(
        self,
        query: str,
        format: str = "json",
        timeout: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict:
        """
        执行查询

        Args:
            query: Scala查询语句
            format: 输出格式 (json, dot等)
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存

        Returns:
            查询结果字典
        """
        # 1. 验证查询
        is_valid, error_msg = self._validate_query(query)
        if not is_valid:
            logger.warning(f"Query validation failed: {error_msg}")
            raise QueryValidationError(error_msg)

        # 2. 确保查询返回正确格式
        query = self._format_query(query, format)

        # 3. 检查缓存
        cache_key = self._get_cache_key(query)
        if use_cache and cache_key in self.cache:
            logger.debug("Cache hit")
            return self.cache[cache_key]

        # 4. 执行查询（并发控制）
        async with self.query_semaphore:
            try:
                timeout = timeout or settings.query_timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.server_manager.execute_query, query),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"Query timeout after {timeout}s")
                raise QueryExecutionError(f"Query timeout after {timeout}s")
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise QueryExecutionError(str(e))

        # 5. 处理结果
        if not result.get("success"):
            stderr = result.get("stderr", "Unknown error")
            logger.error(f"Query failed: {stderr}")
            raise QueryExecutionError(stderr)

        # 6. 缓存结果
        if use_cache:
            self.cache[cache_key] = result

        logger.debug("Query completed successfully")
        return result

    def _validate_query(self, query: str) -> Tuple[bool, str]:
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
                # 如果查询是一个语句块，需要用括号包裹
                if "\n" in query or query.count(";") > 0:
                    query = f"({query}).toJson"
                else:
                    query = f"{query}.toJson"
        elif format == "dot":
            if not query.endswith(".toDot"):
                query = f"{query}.toDot"

        return query

    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("Query cache cleared")
