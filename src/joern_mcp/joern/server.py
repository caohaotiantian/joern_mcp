"""Joern Server管理

统一使用HTTP+WebSocket方式与Joern Server交互，
不再使用cpgqls-client的同步方法，避免event loop冲突。
"""

import asyncio

from loguru import logger

from joern_mcp.config import settings
from joern_mcp.joern.http_client import JoernHTTPClient
from joern_mcp.joern.manager import JoernManager
from joern_mcp.utils.port_utils import (
    find_free_port,
    get_port_info,
    is_port_available,
)


class JoernServerError(Exception):
    """Joern Server错误"""

    pass


class JoernServerManager:
    """Joern Server生命周期管理

    使用HTTP+WebSocket方式与Joern Server交互，
    完全异步，不会阻塞event loop。
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        joern_manager: JoernManager | None = None,
    ) -> None:
        self.host = host or settings.joern_server_host
        self.port = port or settings.joern_server_port
        self.endpoint = f"{self.host}:{self.port}"
        self.joern_manager = joern_manager or JoernManager()

        self.process: asyncio.subprocess.Process | None = None
        self.client: JoernHTTPClient | None = None
        self.auth_credentials: tuple[str, str] | None = None

    async def start(
        self,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 30,
        auto_select_port: bool = True,
    ) -> None:
        """启动Joern Server

        Args:
            username: 认证用户名
            password: 认证密码
            timeout: 启动超时时间（秒）
            auto_select_port: 端口被占用时是否自动选择新端口
        """
        if self.process:
            logger.warning("Joern server already running")
            return

        # 检查端口是否可用
        if not is_port_available(self.port, self.host):
            # 获取占用端口的进程信息
            port_info = get_port_info(self.port)

            if port_info:
                logger.warning(
                    f"Port {self.port} is already in use by: "
                    f"{port_info.get('command', 'unknown')} (PID: {port_info.get('pid', 'unknown')})"
                )

                # 检查是否是已有的 Joern 进程
                command = port_info.get("command", "").lower()
                if "joern" in command or "java" in command:
                    logger.info(
                        f"Detected existing Joern/Java process on port {self.port}. "
                        f"Attempting to connect to existing server..."
                    )
                    # 尝试连接到已有的服务器
                    if await self._try_connect_existing(timeout):
                        logger.info("Successfully connected to existing Joern server")
                        return

            if auto_select_port:
                # 自动选择一个空闲端口
                try:
                    new_port = find_free_port(start_port=8081, end_port=9000)
                    logger.info(
                        f"Port {self.port} is in use, auto-selected port {new_port}"
                    )
                    self.port = new_port
                    self.endpoint = f"{self.host}:{self.port}"
                except RuntimeError as e:
                    raise JoernServerError(
                        f"Port {self.port} is already in use and no free port available: {e}"
                    ) from None
            else:
                raise JoernServerError(
                    f"Port {self.port} is already in use. "
                    f"Please choose a different port or stop the process using this port."
                )

        logger.info(f"Starting Joern server at {self.endpoint}")

        # 构建命令
        cmd = [
            str(self.joern_manager.joern_path),
            "--server",
            "--server-host",
            self.host,
            "--server-port",
            str(self.port),
        ]

        # 添加认证
        username = username or settings.joern_server_username
        password = password or settings.joern_server_password

        if username and password:
            cmd.extend(
                ["--server-auth-username", username, "--server-auth-password", password]
            )
            self.auth_credentials = (username, password)
            logger.info("Authentication enabled")

        # 启动进程
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Joern server process started (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start Joern server: {e}")
            raise JoernServerError(f"Failed to start server: {e}") from None

        # 等待服务器就绪
        try:
            await self._wait_for_ready(timeout)
            logger.info("Joern server is ready")
        except TimeoutError as e:
            await self.stop()
            raise e

        # 初始化HTTP客户端（统一使用HTTP+WebSocket方式）
        self.client = JoernHTTPClient(
            endpoint=self.endpoint,
            auth=self.auth_credentials,
            timeout=settings.query_timeout,
        )
        logger.info("Joern HTTP client initialized")

    async def _try_connect_existing(self, timeout: int = 10) -> bool:
        """尝试连接到已有的 Joern 服务器

        Args:
            timeout: 连接超时时间（秒）

        Returns:
            True 如果成功连接，False 如果失败
        """
        import requests

        try:
            # 尝试使用同步端点验证服务器
            sync_endpoint = f"http://{self.host}:{self.port}/query-sync"
            logger.debug(f"Trying to connect to existing server at {sync_endpoint}")

            response = requests.post(
                sync_endpoint,
                json={"query": "1 + 1"},
                auth=self.auth_credentials,
                timeout=timeout,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("stdout") and "2" in result.get("stdout", ""):
                    # 服务器响应正确，初始化客户端
                    self.client = JoernHTTPClient(
                        endpoint=self.endpoint,
                        auth=self.auth_credentials,
                        timeout=settings.query_timeout,
                    )
                    # 标记为外部管理的服务器（不由我们启动）
                    self._external_server = True
                    logger.info(
                        f"Connected to existing Joern server at {self.endpoint}"
                    )
                    return True

            logger.debug(f"Server at {self.endpoint} did not respond correctly")
            return False

        except Exception as e:
            logger.debug(f"Failed to connect to existing server: {e}")
            return False

    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        # 如果是外部服务器，检查客户端是否存在
        if getattr(self, "_external_server", False):
            return self.client is not None
        return self.process is not None and self.process.returncode is None

    async def _wait_for_ready(self, timeout: int = 30) -> None:
        """等待服务器就绪

        分两阶段验证：
        1. TCP端口可达
        2. 同步查询端点 /query-sync 可用（比 WebSocket 更可靠）

        参考: https://docs.joern.io/server/
        """
        import socket

        import requests

        logger.info(f"Waiting for server to be ready (timeout: {timeout}s)")
        start_time = asyncio.get_event_loop().time()

        # 阶段1: 等待端口可达
        port_ready = False
        while not port_ready:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                result = sock.connect_ex((self.host, self.port))
                sock.close()

                if result == 0:
                    port_ready = True
                    logger.info(f"Server port {self.port} is accepting connections")
            except Exception as e:
                logger.debug(f"Waiting for port: {e}")

            if not port_ready:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    await self._log_process_output()
                    raise TimeoutError(
                        f"Joern server port not available within {timeout}s"
                    ) from None

                if self.process and self.process.returncode is not None:
                    stderr = (
                        await self.process.stderr.read() if self.process.stderr else b""
                    )
                    raise JoernServerError(
                        f"Server process exited: {stderr.decode()}"
                    ) from None

                await asyncio.sleep(0.5)

        # 阶段2: 验证同步查询端点可用（比 WebSocket 更可靠）
        sync_endpoint = f"http://{self.host}:{self.port}/query-sync"
        logger.info(f"Verifying sync query endpoint: {sync_endpoint}")

        api_ready = False
        while not api_ready:
            try:
                # 使用简单查询测试 API 是否就绪
                response = requests.post(
                    sync_endpoint,
                    json={"query": "1 + 1"},
                    auth=self.auth_credentials,
                    timeout=5.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("stdout") and "2" in result.get("stdout", ""):
                        api_ready = True
                        logger.info("Joern API endpoint verified successfully")
            except Exception as e:
                logger.debug(f"API not ready yet: {e}")

            if not api_ready:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    await self._log_process_output()
                    raise TimeoutError(
                        f"Joern server API not ready within {timeout}s. "
                        f"Check if Joern supports HTTP server mode (--server flag)."
                    ) from None

                if self.process and self.process.returncode is not None:
                    stderr = (
                        await self.process.stderr.read() if self.process.stderr else b""
                    )
                    raise JoernServerError(
                        f"Server process exited: {stderr.decode()}"
                    ) from None

                await asyncio.sleep(1.0)

    async def _log_process_output(self) -> None:
        """记录进程输出用于调试"""
        if not self.process:
            return
        try:
            stdout_data = (
                await asyncio.wait_for(self.process.stdout.read(2048), timeout=0.5)
                if self.process.stdout
                else b""
            )
            stderr_data = (
                await asyncio.wait_for(self.process.stderr.read(2048), timeout=0.5)
                if self.process.stderr
                else b""
            )
            if stdout_data:
                logger.error(f"Server stdout: {stdout_data.decode()}")
            if stderr_data:
                logger.error(f"Server stderr: {stderr_data.decode()}")
        except Exception:  # noqa: S110
            pass

    async def stop(self) -> None:
        """停止Joern Server"""
        # 如果是连接到外部服务器，只清理客户端，不尝试停止进程
        if getattr(self, "_external_server", False):
            logger.info("Disconnecting from external Joern server (not stopping it)")
            self.client = None
            self._external_server = False
            return

        if not self.process:
            logger.warning("Joern server not running")
            return

        logger.info("Stopping Joern server")
        saved_port = self.port

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=10)
            logger.info("Joern server stopped gracefully")
        except asyncio.TimeoutError:
            logger.warning("Server did not stop gracefully, killing...")
            self.process.kill()
            await self.process.wait()
            logger.info("Joern server killed")
        finally:
            self.process = None
            self.client = None

            # 等待端口释放
            await asyncio.sleep(1)

            # 验证端口已释放
            if is_port_available(saved_port, self.host):
                logger.success(f"Port {saved_port} released successfully")
            else:
                logger.warning(
                    f"Port {saved_port} still in use after server stop. "
                    f"It may take a few seconds to release."
                )

    async def restart(self) -> None:
        """重启Joern Server"""
        logger.info("Restarting Joern server")
        await self.stop()
        await self.start()

    async def health_check(self) -> bool:
        """健康检查（异步）

        优先使用同步端点 /query-sync 进行检查，
        这个端点更简单可靠，不需要 WebSocket 连接。
        """
        if not self.client:
            return False

        try:
            # 使用同步端点进行健康检查（更可靠）
            result = await self.client.execute("1 + 1", use_sync_endpoint=True)
            if result.get("success"):
                # 验证结果是否正确
                stdout = result.get("stdout", "")
                return "2" in stdout
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def execute_query_async(self, query: str) -> dict:
        """执行查询（异步）

        使用HTTP+WebSocket方式与Joern Server交互，
        完全异步，不会阻塞event loop。
        """
        if not self.client:
            raise JoernServerError("Server not started") from None

        logger.debug(f"Executing query (async): {query[:100]}...")

        try:
            result = await self.client.execute(query)
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise JoernServerError(f"Query failed: {e}") from None

    async def import_code(self, source_path: str, project_name: str) -> dict:
        """导入代码生成CPG"""
        logger.info(f"Importing code from {source_path} as {project_name}")

        # 构建importCode查询（不再依赖cpgqls_client）
        query = f'importCode(inputPath="{source_path}", projectName="{project_name}")'

        result = await self.execute_query_async(query)

        if result.get("success"):
            logger.info(f"Code imported successfully: {project_name}")
        else:
            logger.error(f"Code import failed: {result.get('stderr')}")

        return result
