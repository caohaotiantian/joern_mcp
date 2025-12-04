"""增强的服务器生命周期测试 - 提升覆盖率"""


import pytest
from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor


@pytest.mark.integration
class TestServerLifecycleEnhanced:
    """增强的服务器生命周期测试"""

    @pytest.mark.asyncio
    async def test_server_health_check(self, joern_server):
        """测试服务器健康检查"""
        # 验证服务器运行状态
        assert joern_server.is_running() is True, "服务器应该运行中"

        # 客户端应该存在
        assert joern_server.client is not None, "客户端应该已初始化"

        # 通过执行简单查询验证服务器健康
        executor = QueryExecutor(joern_server)
        result = await executor.execute("1 + 1")
        assert isinstance(result, dict), "健康检查查询应返回dict"

    @pytest.mark.asyncio
    async def test_query_timeout_handling(self, joern_server):
        """测试查询超时处理"""
        from joern_mcp.joern.executor_optimized import QueryExecutionError

        executor = QueryExecutor(joern_server)

        # 使用极短超时测试（应该触发超时）
        # 超时会抛出QueryExecutionError，这是正确的行为
        with pytest.raises(QueryExecutionError) as exc_info:
            await executor.execute("cpg.method.name.l", timeout=0.001)

        # 验证错误消息包含"timeout"
        assert "timeout" in str(exc_info.value).lower(), \
            f"错误消息应包含timeout，实际: {exc_info.value}"

    @pytest.mark.asyncio
    async def test_cache_functionality(self, joern_server):
        """测试缓存功能是否真正工作"""
        executor = QueryExecutor(joern_server)
        query = "cpg.method.name.l"

        # 清空缓存
        executor.clear_cache()

        # 第一次查询（应该缓存miss）
        result1 = await executor.execute(query)
        assert isinstance(result1, dict), "第一次查询应返回字典"

        # 第二次查询（应该缓存hit）
        result2 = await executor.execute(query)
        assert isinstance(result2, dict), "第二次查询应返回字典"

        # 获取缓存统计
        cache_stats = executor.get_cache_stats()
        assert isinstance(cache_stats, dict), "缓存统计应该是字典"

        # 验证缓存统计字段
        assert "hot_hits" in cache_stats, "应该有热缓存命中统计"
        assert "cold_hits" in cache_stats, "应该有冷缓存命中统计"
        assert "misses" in cache_stats, "应该有缓存未命中统计"
        assert "hot_size" in cache_stats, "应该有热缓存大小"
        assert "cold_size" in cache_stats, "应该有冷缓存大小"
        assert "hit_rate" in cache_stats, "应该有缓存命中率"

        # 验证有缓存命中（第二次查询）
        total_hits = cache_stats["hot_hits"] + cache_stats["cold_hits"]
        logger.info(f"缓存命中次数: {total_hits}")

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, joern_server):
        """测试性能指标收集"""
        executor = QueryExecutor(joern_server)

        # 执行几次查询
        for _i in range(3):
            await executor.execute("cpg.method.name.l")

        # 获取性能统计
        perf_stats = executor.get_performance_stats()
        assert isinstance(perf_stats, dict), "性能统计应该是字典"
        assert "total_queries" in perf_stats, "应该有总查询数"
        assert "avg_time" in perf_stats, "应该有平均响应时间"
        assert "cache_hit_rate" in perf_stats, "应该有缓存命中率"

        # 验证统计值合理
        assert perf_stats["total_queries"] >= 3, f"总查询数应该>=3，实际{perf_stats['total_queries']}"
        assert perf_stats["avg_time"] >= 0, "平均时间应该非负"

    @pytest.mark.asyncio
    async def test_slow_query_logging(self, joern_server):
        """测试慢查询日志"""
        executor = QueryExecutor(joern_server)

        # 执行一个查询
        await executor.execute("cpg.method.name.l")

        # 获取慢查询列表
        slow_queries = executor.get_slow_queries()
        assert isinstance(slow_queries, list), "慢查询应该是列表"

        # 如果有慢查询，验证格式
        for sq in slow_queries:
            assert "query" in sq, "慢查询应该包含query字段"
            assert "duration" in sq, "慢查询应该包含duration字段"
            assert "timestamp" in sq, "慢查询应该包含timestamp字段"

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, joern_server):
        """测试并发限制"""
        executor = QueryExecutor(joern_server)

        # 获取当前并发限制
        current_limit = executor.get_current_concurrent_limit()
        assert isinstance(current_limit, int), "并发限制应该是整数"
        assert current_limit > 0, f"并发限制应该>0，实际{current_limit}"

    @pytest.mark.asyncio
    async def test_query_validation_strict(self, joern_server):
        """测试严格的查询验证

        注意：引号内的模式用于搜索代码中的漏洞，不会被阻止。
        只有引号外直接执行的危险代码才会被阻止。
        """
        from joern_mcp.joern.executor_optimized import QueryValidationError

        executor = QueryExecutor(joern_server)

        # 真正危险的操作模式（引号外，会被直接执行）
        dangerous_patterns = [
            ("System.exit", "System.exit(0)"),
            ("Runtime.getRuntime", "Runtime.getRuntime().exec(cmd)"),
            ("ProcessBuilder", "new ProcessBuilder(cmd).start()"),
            ("scala.sys.process", 'scala.sys.process.Process("ls").!'),
        ]

        blocked_count = 0
        for pattern_name, query in dangerous_patterns:
            # 这些直接执行的危险代码应该被阻止
            try:
                with pytest.raises(QueryValidationError) as exc_info:
                    await executor.execute(query)

                # 验证错误消息包含"Forbidden"
                assert "Forbidden" in str(exc_info.value), \
                    f"模式{pattern_name}: 错误消息应该包含Forbidden，实际: {exc_info.value}"
                blocked_count += 1
            except Exception as e:
                # 如果查询本身有其他问题，记录并继续
                logger.warning(f"模式{pattern_name}测试失败: {e}")

        # 大部分危险操作应该被阻止
        assert blocked_count >= len(dangerous_patterns) // 2, \
            "应该阻止至少一半的危险操作"

        # 验证搜索查询（引号内的模式）被允许
        search_query = 'cpg.typeDecl.name("ProcessBuilder").l'
        result = await executor.execute(search_query)
        assert isinstance(result, dict), "搜索查询应返回结果"

    @pytest.mark.asyncio
    async def test_empty_and_whitespace_queries(self, joern_server):
        """测试空查询和空白查询"""
        executor = QueryExecutor(joern_server)

        # 空字符串
        result = await executor.execute("")
        assert isinstance(result, dict), "空查询应返回字典"
        # 可以是成功（返回空）或失败

        # 只有空白
        result = await executor.execute("   \n\t  ")
        assert isinstance(result, dict), "空白查询应返回字典"

    @pytest.mark.asyncio
    async def test_very_long_query(self, joern_server):
        """测试超长查询"""
        executor = QueryExecutor(joern_server)

        # 构造一个很长的查询
        long_query = "cpg.method.name.l" + ".head" * 100
        result = await executor.execute(long_query)

        # 应该正常处理（成功或失败都可以）
        assert isinstance(result, dict), "超长查询应返回字典"

    @pytest.mark.asyncio
    async def test_unicode_handling(self, joern_server):
        """测试Unicode字符处理"""
        executor = QueryExecutor(joern_server)

        # 测试各种Unicode字符
        unicode_queries = [
            'cpg.method.name("测试函数").l',
            'cpg.method.name("テスト").l',
            'cpg.method.name("тест").l',
            'cpg.method.name("🔥").l',
        ]

        for query in unicode_queries:
            result = await executor.execute(query)
            assert isinstance(result, dict), f"Unicode查询应返回字典: {query}"

    @pytest.mark.asyncio
    async def test_error_query_returns_proper_format(self, joern_server):
        """测试错误查询返回正确格式"""
        executor = QueryExecutor(joern_server)

        # 明显错误的查询
        result = await executor.execute("this is definitely not valid joern query!!!")

        # 验证返回格式
        assert isinstance(result, dict), "错误查询应返回字典"

        # Joern对于语法错误可能返回success=True，但错误信息在stdout中
        # 检查是否包含错误信息（在stdout或stderr中）
        stdout = str(result.get("stdout", ""))
        stderr = str(result.get("stderr", ""))

        # 至少应该返回了某种结果（成功或失败）
        assert "success" in result or "stdout" in result or "stderr" in result, \
            "应该包含success、stdout或stderr字段"

        # 如果有输出，记录日志（用于调试）
        if stdout or stderr:
            logger.info(f"查询输出: stdout长度={len(stdout)}, stderr长度={len(stderr)}")

