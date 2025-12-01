"""
测试Joern Server Manager (Mock版本)

使用Mock测试server.py中的逻辑，避免真实启动Joern
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerError, JoernServerManager


class TestJoernServerManagerMock:
    """使用Mock测试JoernServerManager"""

    def test_init(self):
        """测试初始化"""
        with patch("shutil.which", return_value="/usr/local/bin/joern"):
            with patch.object(Path, "exists", return_value=True):
                manager = JoernServerManager(host="localhost", port=9999)
                assert manager.host == "localhost"
                assert manager.port == 9999
                assert manager.endpoint == "localhost:9999"

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        with patch("shutil.which", return_value="/usr/local/bin/joern"):
            with patch.object(Path, "exists", return_value=True):
                manager = JoernServerManager()
                assert manager.host is not None
                assert manager.port is not None

    @pytest.mark.asyncio
    async def test_start_with_port_occupied(self):
        """测试端口被占用时启动失败"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
            patch("joern_mcp.joern.server.is_port_available", return_value=False),
        ):
            manager = JoernServerManager(port=8080)

            with pytest.raises(JoernServerError, match="Port.*already in use"):
                await manager.start()

    @pytest.mark.asyncio
    async def test_start_command_building(self):
        """测试启动命令构建"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            joern_manager = JoernManager()
            manager = JoernServerManager(
                host="0.0.0.0", port=9999, joern_manager=joern_manager
            )

            # Mock create_subprocess_exec
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.stdout = None
            mock_process.stderr = None

            with (
                patch(
                    "asyncio.create_subprocess_exec", return_value=mock_process
                ) as mock_exec,
                patch("joern_mcp.joern.server.is_port_available", return_value=True),
                patch.object(manager, "_wait_for_ready", return_value=None),
            ):
                await manager.start()

                # 验证命令
                call_args = mock_exec.call_args[0]
                assert "--server" in call_args
                assert "--server-host" in call_args
                assert "0.0.0.0" in call_args
                assert "--server-port" in call_args

    @pytest.mark.asyncio
    async def test_start_with_auth(self):
        """测试启用认证的启动"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            joern_manager = JoernManager()
            manager = JoernServerManager(joern_manager=joern_manager, port=9998)

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.stdout = None
            mock_process.stderr = None

            with (
                patch(
                    "asyncio.create_subprocess_exec", return_value=mock_process
                ) as mock_exec,
                patch("joern_mcp.joern.server.is_port_available", return_value=True),
                patch.object(manager, "_wait_for_ready", return_value=None),
            ):
                await manager.start(username="test_user", password="test_pass")

                # 验证认证参数
                call_args = mock_exec.call_args[0]
                assert "--server-auth-username" in call_args
                assert "test_user" in call_args

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """测试停止未运行的服务器"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()
            # 不应该抛出异常
            await manager.stop()

    @pytest.mark.asyncio
    async def test_is_running(self):
        """测试服务器运行状态检查"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            # 未启动时
            assert not manager.is_running()

            # Mock一个运行中的进程
            mock_process = MagicMock()
            mock_process.returncode = None
            manager.process = mock_process

            assert manager.is_running()

            # Mock已退出的进程
            mock_process.returncode = 0
            assert not manager.is_running()

    @pytest.mark.asyncio
    async def test_execute_query_sync(self):
        """测试同步查询执行"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            # Mock client
            mock_client = MagicMock()
            mock_client.execute = MagicMock(
                return_value={"response": '["result"]', "success": True}
            )
            manager.client = mock_client

            result = manager.execute_query("test_query")

            assert result["success"] is True
            assert mock_client.execute.called

    @pytest.mark.asyncio
    async def test_execute_query_without_client(self):
        """测试未初始化client时的查询"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()
            manager.client = None

            with pytest.raises(JoernServerError, match="Server not started"):
                manager.execute_query("test")

    @pytest.mark.asyncio
    async def test_execute_query_async(self):
        """测试异步查询执行"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            mock_client = MagicMock()
            mock_client.execute = MagicMock(
                return_value={"response": '["async_result"]', "success": True}
            )
            manager.client = mock_client

            result = await manager.execute_query_async("async_query")

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_running(self):
        """测试运行中服务器的健康检查"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            # Mock运行中的进程
            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.poll = MagicMock(return_value=None)
            manager.process = mock_process

            # Mock client可用（返回正确的字典）
            mock_client = MagicMock()
            mock_client.execute = MagicMock(return_value={"success": True})
            manager.client = mock_client

            is_healthy = await manager.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_running(self):
        """测试未运行服务器的健康检查"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()
            manager.process = None

            is_healthy = await manager.health_check()
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_import_code_mock(self):
        """测试代码导入（Mock）"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            # Mock client
            mock_client = MagicMock()
            mock_client.execute = MagicMock(
                return_value={"response": "true", "success": True}
            )
            manager.client = mock_client

            # Mock import_code_query
            with patch(
                "joern_mcp.joern.server.import_code_query", return_value="import_query"
            ):
                result = await manager.import_code("/path/to/code", "test_project")

                assert result["success"] is True
                assert mock_client.execute.called


class TestJoernServerErrorHandling:
    """测试Joern Server错误处理"""

    @pytest.mark.asyncio
    async def test_start_subprocess_failure(self):
        """测试subprocess启动失败"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager(port=9997)

            with (
                patch("joern_mcp.joern.server.is_port_available", return_value=True),
                patch(
                    "asyncio.create_subprocess_exec",
                    side_effect=Exception("Failed to start"),
                ),
                pytest.raises(JoernServerError, match="Failed to start"),
            ):
                await manager.start()

    @pytest.mark.asyncio
    async def test_execute_query_client_error(self):
        """测试client执行查询出错"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            mock_client = MagicMock()
            mock_client.execute = MagicMock(side_effect=Exception("Client error"))
            manager.client = mock_client

            with pytest.raises(JoernServerError, match="Query failed"):
                manager.execute_query("test")

    @pytest.mark.asyncio
    async def test_import_code_failure(self):
        """测试代码导入失败"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/joern"),
            patch.object(Path, "exists", return_value=True),
        ):
            manager = JoernServerManager()

            mock_client = MagicMock()
            mock_client.execute = MagicMock(
                return_value={
                    "response": "false",
                    "success": False,
                    "error": "Import failed",
                }
            )
            manager.client = mock_client

            with patch(
                "joern_mcp.joern.server.import_code_query", return_value="import_query"
            ):
                result = await manager.import_code("/path", "project")
                assert result["success"] is False
