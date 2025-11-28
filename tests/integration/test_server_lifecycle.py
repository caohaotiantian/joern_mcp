"""测试MCP Server生命周期"""

import pytest
import asyncio
from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.executor import QueryExecutor


@pytest.mark.integration
class TestServerLifecycle:
    """测试服务器生命周期"""

    def test_joern_manager_initialization(self):
        """测试Joern管理器初始化"""
        manager = JoernManager()

        # 验证基本功能
        assert manager.joern_path is not None
        assert manager.validate_installation()

    @pytest.mark.asyncio
    async def test_joern_server_lifecycle(self, joern_server):
        """测试Joern Server生命周期"""
        # 验证服务器运行
        assert await joern_server.is_running()
        assert joern_server.client is not None

        # 验证可以执行查询
        executor = QueryExecutor(joern_server)
        result = await executor.execute("cpg.method.name.l")
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_executor_initialization(self, joern_server):
        """测试查询执行器初始化"""
        executor = QueryExecutor(joern_server)

        # 验证缓存
        assert executor.cache is not None
        assert executor.query_semaphore is not None

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, joern_server):
        """测试并发查询"""
        executor = QueryExecutor(joern_server)

        # 创建多个并发查询
        queries = ["cpg.method.name.l", "cpg.call.name.l", "cpg.file.name.l"]

        tasks = [executor.execute(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证大部分查询成功
        success_count = sum(1 for r in results if isinstance(r, dict) and r is not None)
        assert success_count >= 2  # 至少2个成功
