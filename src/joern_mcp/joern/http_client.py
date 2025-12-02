"""
Joern HTTP+WebSocket客户端 - 直接与Joern Server交互

Joern Server工作模式（参考cpgqls-client实现）：
1. WebSocket连接: ws://host:port/connect
2. POST查询: http://host:port/query -> 返回UUID
3. WebSocket等待完成通知
4. GET结果: http://host:port/result/{uuid}

替代cpgqls-client，避免:
1. Event loop冲突（run_until_complete）
2. 控制台输出解析（ANSI颜色码）
3. 同步阻塞调用
"""

import asyncio
import time
from typing import Any

import requests  # 使用同步requests，与cpgqls-client一致
import websockets
from loguru import logger

# 全局信号量：限制并发WebSocket连接数，避免资源竞争
_connection_semaphore: asyncio.Semaphore | None = None
_MAX_CONCURRENT_CONNECTIONS = 5  # 最大并发连接数（支持4-5个并发查询）


def _get_semaphore() -> asyncio.Semaphore:
    """获取或创建连接信号量（延迟初始化，避免事件循环问题）"""
    global _connection_semaphore
    if _connection_semaphore is None:
        _connection_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_CONNECTIONS)
    return _connection_semaphore


class JoernHTTPClient:
    """通过HTTP+WebSocket与Joern Server交互的客户端"""

    CPGQLS_MSG_CONNECTED = "connected"

    def __init__(
        self,
        endpoint: str,
        auth: tuple[str, str] | None = None,
        timeout: float = 3600.0,
    ):
        """
        初始化Joern HTTP客户端

        Args:
            endpoint: Joern Server地址，格式为"host:port"
            auth: 认证凭据(username, password)，可选
            timeout: 请求超时时间（秒）
        """
        self.endpoint = endpoint.rstrip("/")
        self.auth = auth
        self.timeout = timeout

        logger.info(f"Joern HTTP client initialized for http://{endpoint}")

    def _connect_endpoint(self) -> str:
        """WebSocket连接端点"""
        return f"ws://{self.endpoint}/connect"

    def _post_query_endpoint(self) -> str:
        """POST查询端点"""
        return f"http://{self.endpoint}/query"

    def _get_result_endpoint(self, uuid: str) -> str:
        """GET结果端点"""
        return f"http://{self.endpoint}/result/{uuid}"

    async def execute(self, query: str) -> dict[str, Any]:
        """
        执行CPGQL查询（完全异步）

        Args:
            query: CPGQL查询字符串

        Returns:
            查询结果（纯JSON，无ANSI颜色码）

        Raises:
            Exception: 连接或查询失败
        """
        # 使用信号量限制并发连接数，避免资源竞争
        semaphore = _get_semaphore()

        async with semaphore:
            return await self._execute_internal(query)

    async def _execute_internal(self, query: str) -> dict[str, Any]:
        """内部执行方法（在信号量保护下调用）"""
        try:
            # 1. 建立WebSocket连接
            connect_endpoint = self._connect_endpoint()
            logger.debug(f"连接WebSocket: {connect_endpoint}")

            async with websockets.connect(connect_endpoint, ping_interval=None) as ws_conn:
                logger.debug("WebSocket连接成功，等待确认消息...")
                # 等待连接确认消息
                connected_msg = await ws_conn.recv()
                logger.debug(f"收到消息: {connected_msg}")

                if connected_msg != self.CPGQLS_MSG_CONNECTED:
                    raise Exception(
                        f"Unexpected first message on websocket: {connected_msg}"
                    )
                logger.debug("WebSocket连接已确认")

                # 2. POST查询（使用同步requests，与cpgqls-client一致）
                post_endpoint = self._post_query_endpoint()
                logger.debug(f"POST查询到: {post_endpoint}")

                post_res = requests.post(
                    post_endpoint,
                    json={"query": query},
                    auth=self.auth,
                    timeout=self.timeout,
                )
                logger.debug(f"POST响应状态: {post_res.status_code}")

                # 检查认证
                if post_res.status_code == 401:
                    raise Exception("Basic authentication failed")
                elif post_res.status_code != 200:
                    raise Exception(
                        f"Could not post query: HTTP {post_res.status_code}, body: {post_res.text}"
                    )

                # 获取查询UUID
                query_uuid = post_res.json()["uuid"]
                logger.debug(f"查询已提交，UUID: {query_uuid}")

                # 3. 等待WebSocket完成通知（必须等到我们提交的查询完成）
                logger.debug(f"等待查询 {query_uuid} 的完成通知（超时: {self.timeout}s）...")

                # 循环等待，直到收到我们查询的UUID
                start_time = time.time()
                while True:
                    remaining_timeout = self.timeout - (time.time() - start_time)
                    if remaining_timeout <= 0:
                        raise asyncio.TimeoutError(f"等待查询 {query_uuid} 完成超时")

                    completion_msg = await asyncio.wait_for(
                        ws_conn.recv(),
                        timeout=remaining_timeout
                    )
                    logger.debug(f"收到完成通知: {completion_msg}")

                    # 检查是否是我们的查询完成
                    if completion_msg == query_uuid:
                        logger.debug(f"查询 {query_uuid} 已完成")
                        break
                    else:
                        # 收到其他查询的通知，继续等待
                        logger.debug(f"收到其他查询的通知 {completion_msg}，继续等待 {query_uuid}")

                # 4. GET查询结果（同步requests）
                result_endpoint = self._get_result_endpoint(query_uuid)
                logger.debug(f"GET结果从: {result_endpoint}")

                get_res = requests.get(
                    result_endpoint,
                    auth=self.auth,
                    timeout=self.timeout,
                )
                logger.debug(f"GET响应状态: {get_res.status_code}")

                # 检查结果获取
                if get_res.status_code == 401:
                    raise Exception("Basic authentication failed")
                elif get_res.status_code != 200:
                    raise Exception(
                        f"Could not retrieve result: HTTP {get_res.status_code}, body: {get_res.text}"
                    )

                # 获取Joern Server的原始响应
                raw_result = get_res.json()
                logger.debug(f"查询成功完成: {query[:50]}...")

                # 检查Joern Server的错误响应
                if "err" in raw_result:
                    # Joern Server返回错误
                    error_msg = raw_result["err"]
                    logger.error(f"Joern Server error: {error_msg}")
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Joern Error: {error_msg}",
                    }

                # Joern Server返回格式: {"success": true, "uuid": "...", "stdout": "..."}
                # cpgqls-client返回格式: {"success": True, "stdout": "...", "stderr": ""}
                # 提取stdout字段（Scala REPL输出）
                stdout_content = raw_result.get("stdout", "")

                return {
                    "success": True,
                    "stdout": stdout_content,
                    "stderr": "",
                }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            # 返回错误格式与cpgqls-client一致
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution Error: {e}",
            }

    async def import_code(self, path: str, project_name: str) -> dict[str, Any]:
        """
        导入代码到Joern

        Args:
            path: 代码路径
            project_name: 项目名称

        Returns:
            导入结果（格式与cpgqls-client一致）
        """
        # 使用importCode查询
        query = f'importCode(inputPath="{path}", projectName="{project_name}")'
        logger.info(f"Importing code: {path} as {project_name}")
        # execute已经返回统一格式，直接返回即可
        return await self.execute(query)

    async def workspace(self) -> dict[str, Any]:
        """
        获取workspace信息

        Returns:
            Workspace信息（格式与cpgqls-client一致）
        """
        # execute已经返回统一格式，直接返回即可
        return await self.execute("workspace")

    async def close(self) -> None:
        """关闭客户端（HTTP客户端无需显式关闭）"""
        logger.debug("HTTP client closed")

    def __repr__(self) -> str:
        return f"JoernHTTPClient(endpoint={self.endpoint})"

