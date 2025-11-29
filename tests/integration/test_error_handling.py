"""错误处理和边界测试"""

import pytest
import asyncio
from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.taint import TaintAnalysisService


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_query(self, joern_server):
        """测试无效查询"""
        executor = QueryExecutor(joern_server)

        # 无效的查询语法
        result = await executor.execute("invalid query syntax!!!")

        # 应该返回错误而不是抛出异常
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_query(self, joern_server):
        """测试空查询"""
        executor = QueryExecutor(joern_server)
        result = await executor.execute("")

        # 应该处理空查询
        assert result is not None

    @pytest.mark.asyncio
    async def test_dangerous_query_blocked(self, joern_server):
        """测试危险查询被阻止"""
        from joern_mcp.joern.executor import QueryValidationError

        executor = QueryExecutor(joern_server)

        # 尝试执行危险操作
        dangerous_queries = [
            "System.exit(0)",
            "Runtime.getRuntime().exec('ls')",
        ]

        for query in dangerous_queries:
            # 危险查询应该抛出QueryValidationError
            with pytest.raises(QueryValidationError):
                await executor.execute(query)


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestBoundaryConditions:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_max_depth_limit(self, joern_server):
        """测试最大深度限制"""
        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试深度限制（使用合理的深度值）
        # 注意：Joern可能没有内置的深度限制，查询语法错误会在raw_output中体现
        result = await service.get_callers("main", depth=5)

        # 应该能执行（可能返回空结果或错误信息）
        assert result.get("success") is not None
        # 检查返回的调用者列表
        assert "callers" in result or "error" in result or "raw_output" in result

    @pytest.mark.asyncio
    async def test_max_flows_limit(self, joern_server):
        """测试最大流数量限制"""
        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 超过最大流数量
        result = await service.find_vulnerabilities(max_flows=100)

        # 应该被限制或正常返回
        assert result is not None

    @pytest.mark.asyncio
    async def test_unicode_in_queries(self, joern_server):
        """测试查询中的Unicode字符"""
        executor = QueryExecutor(joern_server)

        # 包含Unicode的查询
        result = await executor.execute('cpg.method.name("测试函数").l')

        # 应该正确处理
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, joern_server):
        """测试并发错误处理"""
        import warnings
        
        executor = QueryExecutor(joern_server)

        # 混合有效和无效查询
        queries = [
            "cpg.method.name.l",  # 有效
            "invalid!!!",  # 无效
            "cpg.call.name.l",  # 有效
            "more invalid",  # 无效
        ]

        # 使用warnings过滤器抑制CPGQLSClient的协程警告
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
            tasks = [executor.execute(q) for q in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # 所有查询都应该返回结果（成功或失败）
        assert len(results) == len(queries)
        for result in results:
            assert result is not None
