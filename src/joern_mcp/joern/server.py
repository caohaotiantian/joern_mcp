"""Joern Server管理"""

import asyncio

from cpgqls_client import CPGQLSClient, import_code_query
from loguru import logger

from joern_mcp.config import settings
from joern_mcp.joern.manager import JoernManager
from joern_mcp.utils.port_utils import is_port_available


class JoernServerError(Exception):
    """Joern Server错误"""

    pass


class JoernServerManager:
    """Joern Server生命周期管理"""

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
        self.client: CPGQLSClient | None = None
        self.auth_credentials: tuple[str, str] | None = None

    async def start(
        self,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> None:
        """启动Joern Server"""
        if self.process:
            logger.warning("Joern server already running")
            return

        # 检查端口是否可用
        if not is_port_available(self.port, self.host):
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

        # 初始化客户端
        self.client = CPGQLSClient(
            self.endpoint, auth_credentials=self.auth_credentials
        )
        logger.info("Joern client initialized")

    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self.process is not None and self.process.returncode is None

    async def _wait_for_ready(self, timeout: int = 30) -> None:
        """等待服务器就绪

        使用简单的TCP连接测试来检查端口是否可达
        """
        logger.info(f"Waiting for server to be ready (timeout: {timeout}s)")
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                # 尝试建立TCP连接来检查端口是否可达
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                result = sock.connect_ex((self.host, self.port))
                sock.close()

                if result == 0:
                    # 端口可达，服务器已启动
                    logger.info(f"Server port {self.port} is accepting connections")
                    return
            except Exception as e:
                logger.debug(f"Waiting for server: {e}")

                # 检查超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    # 获取进程输出用于调试
                    if self.process:
                        try:
                            stdout_data = (
                                await asyncio.wait_for(
                                    self.process.stdout.read(1024), timeout=0.5
                                )
                                if self.process.stdout
                                else b""
                            )
                            stderr_data = (
                                await asyncio.wait_for(
                                    self.process.stderr.read(1024), timeout=0.5
                                )
                                if self.process.stderr
                                else b""
                            )
                            logger.error(f"Server stdout: {stdout_data.decode()}")
                            logger.error(f"Server stderr: {stderr_data.decode()}")
                        except Exception:  # noqa: S110
                            pass
                    raise TimeoutError(
                        f"Joern server failed to start within {timeout}s"
                    ) from None

                # 检查进程是否已退出
                if self.process and self.process.returncode is not None:
                    stderr = (
                        await self.process.stderr.read() if self.process.stderr else b""
                    )
                    raise JoernServerError(
                        f"Server process exited: {stderr.decode()}"
                    ) from None

                await asyncio.sleep(1.0)  # 增加等待间隔

    async def stop(self) -> None:
        """停止Joern Server"""
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
        """健康检查"""
        if not self.client:
            return False

        try:
            result = self.client.execute("1 + 1")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def execute_query(self, query: str) -> dict:
        """执行查询（同步）"""
        if not self.client:
            raise JoernServerError("Server not started") from None

        logger.debug(f"Executing query: {query[:100]}...")
        try:
            result = self.client.execute(query)
            logger.debug(f"Query completed: success={result.get('success')}")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise JoernServerError(f"Query failed: {e}") from None

    async def execute_query_async(self, query: str) -> dict:
        """执行查询（异步）- 在已有event loop中使用"""
        import concurrent.futures

        if not self.client:
            raise JoernServerError("Server not started") from None

        logger.debug(f"Executing query (async): {query[:100]}...")

        # 在线程池中运行同步的execute_query
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                result = await loop.run_in_executor(executor, self.execute_query, query)
                return result
            except Exception as e:
                logger.error(f"Async query execution failed: {e}")
                raise JoernServerError(f"Query failed: {e}") from None

    async def import_code(self, source_path: str, project_name: str) -> dict:
        """导入代码生成CPG"""
        logger.info(f"Importing code from {source_path} as {project_name}")
        query = import_code_query(source_path, project_name)
        result = self.execute_query(query)

        if result.get("success"):
            logger.info(f"Code imported successfully: {project_name}")
        else:
            logger.error(f"Code import failed: {result.get('stderr')}")

        return result
