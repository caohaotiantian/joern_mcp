"""
性能监控和管理工具

提供查询性能统计、缓存管理、慢查询分析等功能
"""

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state


@mcp.tool()
async def get_performance_stats() -> dict:
    """
    获取性能统计信息

    Returns:
        dict: 性能指标，包括：
            - total_queries: 总查询数
            - avg_time: 平均响应时间
            - p50/p95/p99: 响应时间百分位
            - cache_hit_rate: 缓存命中率
            - success_rate: 成功率
            - current_concurrent: 当前并发数
    """
    try:
        if not server_state.query_executor:
            return {"error": "Query executor not initialized"}

        # 获取性能统计
        stats = server_state.query_executor.get_performance_stats()

        # 获取缓存统计
        cache_stats = server_state.query_executor.get_cache_stats()

        # 获取并发限制
        concurrent_limit = server_state.query_executor.get_current_concurrent_limit()

        return {
            "success": True,
            "performance": stats,
            "cache": cache_stats,
            "concurrent_limit": concurrent_limit,
        }

    except Exception as e:
        logger.exception(f"Error getting performance stats: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_cache_stats() -> dict:
    """
    获取缓存统计信息

    Returns:
        dict: 缓存统计，包括：
            - hot_size: 热缓存大小
            - cold_size: 冷缓存大小
            - hit_rate: 命中率
            - compressed: 压缩条目数
    """
    try:
        if not server_state.query_executor:
            return {"error": "Query executor not initialized"}

        stats = server_state.query_executor.get_cache_stats()

        return {"success": True, **stats}

    except Exception as e:
        logger.exception(f"Error getting cache stats: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def clear_query_cache() -> dict:
    """
    清空查询缓存

    Returns:
        dict: 操作结果
    """
    try:
        if not server_state.query_executor:
            return {"error": "Query executor not initialized"}

        server_state.query_executor.clear_cache()

        logger.info("Query cache cleared")
        return {"success": True, "message": "Cache cleared successfully"}

    except Exception as e:
        logger.exception(f"Error clearing cache: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_slow_queries(limit: int = 10) -> dict:
    """
    获取慢查询列表

    Args:
        limit: 返回数量限制（默认10）

    Returns:
        dict: 慢查询列表，包含：
            - query: 查询语句（截断）
            - duration: 执行时间
            - complexity: 复杂度
            - timestamp: 时间戳
    """
    try:
        if not server_state.query_executor:
            return {"error": "Query executor not initialized"}

        slow_queries = server_state.query_executor.get_slow_queries(limit)

        return {
            "success": True,
            "slow_queries": slow_queries,
            "count": len(slow_queries),
        }

    except Exception as e:
        logger.exception(f"Error getting slow queries: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_system_health() -> dict:
    """
    获取系统健康状态

    Returns:
        dict: 系统健康信息，包括：
            - joern_server_running: Joern服务器状态
            - cache_health: 缓存健康度
            - performance_grade: 性能评级（A-F）
    """
    try:
        health = {"success": True}

        # Joern服务器状态
        if server_state.joern_server:
            health["joern_server_running"] = server_state.joern_server.is_running()
        else:
            health["joern_server_running"] = False

        # 性能指标
        if server_state.query_executor:
            stats = server_state.query_executor.get_performance_stats()

            # 缓存健康度
            cache_hit_rate = stats.get("cache_hit_rate", 0)
            if cache_hit_rate >= 70:
                cache_health = "Excellent"
            elif cache_hit_rate >= 50:
                cache_health = "Good"
            elif cache_hit_rate >= 30:
                cache_health = "Fair"
            else:
                cache_health = "Poor"

            health["cache_health"] = cache_health
            health["cache_hit_rate"] = cache_hit_rate

            # 性能评级
            avg_time = stats.get("avg_time", 0)
            success_rate = stats.get("success_rate", 0)

            if avg_time < 1.0 and success_rate > 95:
                grade = "A"
            elif avg_time < 2.0 and success_rate > 90:
                grade = "B"
            elif avg_time < 3.0 and success_rate > 85:
                grade = "C"
            elif avg_time < 5.0 and success_rate > 80:
                grade = "D"
            else:
                grade = "F"

            health["performance_grade"] = grade
            health["avg_response_time"] = avg_time
            health["success_rate"] = success_rate

        return health

    except Exception as e:
        logger.exception(f"Error getting system health: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def optimize_performance() -> dict:
    """
    执行性能优化建议

    分析当前性能状况并提供优化建议

    Returns:
        dict: 优化建议列表
    """
    try:
        recommendations = []

        if not server_state.query_executor:
            return {"error": "Query executor not initialized"}

        # 获取统计信息
        perf_stats = server_state.query_executor.get_performance_stats()
        cache_stats = server_state.query_executor.get_cache_stats()

        # 分析缓存命中率
        cache_hit_rate = perf_stats.get("cache_hit_rate", 0)
        if cache_hit_rate < 50:
            recommendations.append(
                {
                    "type": "cache",
                    "priority": "high",
                    "issue": f"Low cache hit rate ({cache_hit_rate:.1f}%)",
                    "recommendation": "Consider increasing cache size or TTL",
                }
            )

        # 分析响应时间
        avg_time = perf_stats.get("avg_time", 0)
        p95 = perf_stats.get("p95", 0)
        if avg_time > 3.0:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "high",
                    "issue": f"High average response time ({avg_time:.2f}s)",
                    "recommendation": "Optimize queries or increase concurrent limit",
                }
            )

        if p95 > 10.0:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "medium",
                    "issue": f"High P95 response time ({p95:.2f}s)",
                    "recommendation": "Check slow queries and optimize them",
                }
            )

        # 分析成功率
        success_rate = perf_stats.get("success_rate", 0)
        if success_rate < 90:
            recommendations.append(
                {
                    "type": "reliability",
                    "priority": "critical",
                    "issue": f"Low success rate ({success_rate:.1f}%)",
                    "recommendation": "Investigate failing queries and increase timeout",
                }
            )

        # 分析缓存压缩
        compressed = cache_stats.get("compressed", 0)
        total_size = cache_stats.get("total_size", 0)
        if total_size > 0 and compressed / total_size < 0.1:
            recommendations.append(
                {
                    "type": "memory",
                    "priority": "low",
                    "issue": "Few cached items are compressed",
                    "recommendation": "Lower compression threshold to save memory",
                }
            )

        return {
            "success": True,
            "recommendations": recommendations,
            "count": len(recommendations),
        }

    except Exception as e:
        logger.exception(f"Error analyzing performance: {e}")
        return {"success": False, "error": str(e)}
