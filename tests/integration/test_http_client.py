"""HTTP客户端功能测试

所有与Joern Server的交互都使用HTTP+WebSocket方式。
"""

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
        server = JoernServerManager(host="localhost", port=port)

        try:
            await server.start(timeout=180)

            # 执行简单查询
            result = await server.execute_query_async("1 + 1")

            # 验证结果
            assert isinstance(result, dict), f"应该返回dict，实际: {type(result)}"
            assert result.get("success"), f"查询应该成功: {result}"
            print(f"Result: {result}")

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_http_client_import_code(self):
        """测试HTTP客户端导入代码"""
        import tempfile
        from pathlib import Path

        from joern_mcp.utils.port_utils import find_free_port

        port = find_free_port()
        server = JoernServerManager(host="localhost", port=port)

        try:
            await server.start(timeout=180)

            # 创建临时C代码文件
            with tempfile.TemporaryDirectory() as tmpdir:
                code_file = Path(tmpdir) / "test.c"
                code_file.write_text("int main() { return 0; }")

                # 导入代码
                result = await server.import_code(str(tmpdir), "test-project")

                assert isinstance(result, dict), f"应该返回dict，实际: {type(result)}"
                assert result.get("success"), f"导入应该成功: {result}"

        finally:
            await server.stop()
