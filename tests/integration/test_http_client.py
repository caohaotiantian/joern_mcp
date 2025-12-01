"""HTTP客户端功能测试"""

import pytest

from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerManager


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestHTTPClient:
    """测试HTTP客户端功能"""

    @pytest.mark.asyncio
    async def test_http_client_basic_query(self):
        """测试HTTP客户端基础查询"""
        from joern_mcp.utils.port_utils import find_free_port

        # 使用HTTP客户端
        port = find_free_port()
        server = JoernServerManager(host="localhost", port=port, use_http_client=True)

        try:
            await server.start(timeout=180)

            # 执行简单查询
            result = await server.execute_query_async("1 + 1")

            # 验证结果
            assert isinstance(result, dict), f"应该返回dict，实际: {type(result)}"
            # HTTP客户端应该返回纯JSON
            print(f"Result: {result}")

        finally:
            await server.stop()

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="cpgqls-client在pytest-asyncio环境下有event loop冲突问题"
    )
    async def test_cpgqls_client_basic_query(self):
        """测试cpgqls客户端基础查询（对比）"""
        from joern_mcp.utils.port_utils import find_free_port

        # 使用cpgqls客户端
        port = find_free_port()
        server = JoernServerManager(host="localhost", port=port, use_http_client=False)

        try:
            await server.start(timeout=180)

            # 执行简单查询
            result = await server.execute_query_async("1 + 1")

            # 验证结果
            assert isinstance(result, dict), f"应该返回dict，实际: {type(result)}"
            print(f"Result: {result}")

        finally:
            await server.stop()

