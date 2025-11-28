"""Joern Server管理"""
import asyncio
from typing import Optional, Tuple, Dict
import httpx
from loguru import logger
from cpgqls_client import CPGQLSClient, import_code_query
from joern_mcp.config import settings
from joern_mcp.joern.manager import JoernManager


class JoernServerError(Exception):
    """Joern Server错误"""
    pass


class JoernServerManager:
    """Joern Server生命周期管理"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        joern_manager: Optional[JoernManager] = None
    ) -> None:
        self.host = host or settings.joern_server_host
        self.port = port or settings.joern_server_port
        self.endpoint = f"{self.host}:{self.port}"
        self.joern_manager = joern_manager or JoernManager()
        
        self.process: Optional[asyncio.subprocess.Process] = None
        self.client: Optional[CPGQLSClient] = None
        self.auth_credentials: Optional[Tuple[str, str]] = None
    
    async def start(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ) -> None:
        """启动Joern Server"""
        if self.process:
            logger.warning("Joern server already running")
            return
        
        logger.info(f"Starting Joern server at {self.endpoint}")
        
        # 构建命令
        cmd = [
            str(self.joern_manager.joern_path),
            "--server",
            "--server-host", self.host,
            "--server-port", str(self.port)
        ]
        
        # 添加认证
        username = username or settings.joern_server_username
        password = password or settings.joern_server_password
        
        if username and password:
            cmd.extend([
                "--server-auth-username", username,
                "--server-auth-password", password
            ])
            self.auth_credentials = (username, password)
            logger.info("Authentication enabled")
        
        # 启动进程
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Joern server process started (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start Joern server: {e}")
            raise JoernServerError(f"Failed to start server: {e}")
        
        # 等待服务器就绪
        try:
            await self._wait_for_ready(timeout)
            logger.info("Joern server is ready")
        except TimeoutError as e:
            await self.stop()
            raise e
        
        # 初始化客户端
        self.client = CPGQLSClient(
            self.endpoint,
            auth_credentials=self.auth_credentials
        )
        logger.info("Joern client initialized")
    
    async def _wait_for_ready(self, timeout: int = 30) -> None:
        """等待服务器就绪"""
        logger.info(f"Waiting for server to be ready (timeout: {timeout}s)")
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"http://{self.endpoint}/",
                        timeout=2.0
                    )
                    # 服务器返回任何响应都表示已启动
                    if response.status_code in [200, 404]:
                        return
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                except Exception as e:
                    logger.debug(f"Waiting for server: {e}")
                
                # 检查超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Joern server failed to start within {timeout}s")
                
                # 检查进程是否已退出
                if self.process and self.process.returncode is not None:
                    stderr = await self.process.stderr.read() if self.process.stderr else b""
                    raise JoernServerError(f"Server process exited: {stderr.decode()}")
                
                await asyncio.sleep(0.5)
    
    async def stop(self) -> None:
        """停止Joern Server"""
        if not self.process:
            logger.warning("Joern server not running")
            return
        
        logger.info("Stopping Joern server")
        
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
    
    def execute_query(self, query: str) -> Dict:
        """执行查询（同步）"""
        if not self.client:
            raise JoernServerError("Server not started")
        
        logger.debug(f"Executing query: {query[:100]}...")
        try:
            result = self.client.execute(query)
            logger.debug(f"Query completed: success={result.get('success')}")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise JoernServerError(f"Query failed: {e}")
    
    async def import_code(
        self,
        source_path: str,
        project_name: str
    ) -> Dict:
        """导入代码生成CPG"""
        logger.info(f"Importing code from {source_path} as {project_name}")
        query = import_code_query(source_path, project_name)
        result = self.execute_query(query)
        
        if result.get("success"):
            logger.info(f"Code imported successfully: {project_name}")
        else:
            logger.error(f"Code import failed: {result.get('stderr')}")
        
        return result

