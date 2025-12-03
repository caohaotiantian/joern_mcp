"""集成测试配置"""

import asyncio
import contextlib
import socket
from pathlib import Path

import pytest
from loguru import logger

from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerManager


def find_free_port(
    start_port: int = 20000, end_port: int = 30000, max_attempts: int = 100
) -> int:
    """查找一个可用的端口

    Args:
        start_port: 起始端口
        end_port: 结束端口
        max_attempts: 最大尝试次数

    Returns:
        可用的端口号

    Raises:
        RuntimeError: 如果找不到可用端口
    """
    import random

    for _ in range(max_attempts):
        port = random.randint(start_port, end_port)

        # 检查端口是否可用
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                # 尝试绑定端口
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("localhost", port))
                logger.info(f"Found free port: {port}")
                return port
            except OSError:
                # 端口被占用，继续尝试
                continue

    raise RuntimeError(f"Could not find free port after {max_attempts} attempts")


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return False
        except OSError:
            return True


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def sample_c_code(test_data_dir):
    """示例C代码"""
    code_dir = test_data_dir / "sample_c"
    code_dir.mkdir(parents=True, exist_ok=True)

    # 创建示例C文件
    sample_file = code_dir / "vulnerable.c"
    sample_file.write_text("""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[100];
    strcpy(buffer, input);  // Buffer overflow
    system(buffer);         // Command injection
}

void safe_function(char *input) {
    char buffer[100];
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\\0';
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0;
}
""")

    return code_dir


@pytest.fixture(scope="session")
def sample_java_code(test_data_dir):
    """示例Java代码"""
    code_dir = test_data_dir / "sample_java"
    code_dir.mkdir(parents=True, exist_ok=True)

    # 创建示例Java文件
    sample_file = code_dir / "Vulnerable.java"
    sample_file.write_text("""
import java.sql.*;

public class Vulnerable {
    public void sqlInjection(String userInput) {
        String query = "SELECT * FROM users WHERE name = '" + userInput + "'";
        // SQL Injection vulnerability
        executeQuery(query);
    }

    public void safeQuery(String userInput) {
        String query = "SELECT * FROM users WHERE name = ?";
        // Use PreparedStatement - safe
        executePreparedQuery(query, userInput);
    }

    private void executeQuery(String query) {
        // Execute SQL query
    }

    private void executePreparedQuery(String query, String param) {
        // Execute prepared statement
    }
}
""")

    return code_dir


@pytest.fixture(scope="session")
async def joern_server(event_loop):
    """Session级别的Joern Server - 所有测试共享

    这样可以：
    1. 减少启动次数，加快测试速度
    2. 避免端口冲突
    3. 确保端口正确释放
    """
    if not JoernManager().validate_installation():
        pytest.skip("Joern not installed")

    # 查找可用端口
    max_retries = 3
    server = None

    for attempt in range(max_retries):
        try:
            port = find_free_port()
            logger.info(f"🔧 Attempt {attempt + 1}/{max_retries}: Using port {port}")

            # 使用HTTP客户端与Joern Server交互
            server = JoernServerManager(host="localhost", port=port)

            # 尝试启动服务器（增加超时到180秒）
            logger.info("⏳ Starting Joern Server (this may take 1-3 minutes)...")
            logger.info("💡 Tip: Check another terminal with: ps aux | grep joern")
            await server.start(timeout=180)
            logger.success(f"✅ Joern server started successfully on port {port}")

            # 启动成功，跳出循环
            break

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")

            # 清理失败的server
            if server and server.process:
                with contextlib.suppress(Exception):
                    await server.stop()

            # 如果不是最后一次尝试，继续
            if attempt < max_retries - 1:
                logger.info("Retrying with different port...")
                await asyncio.sleep(2)
            else:
                # 最后一次尝试也失败了
                logger.error("All attempts to start Joern server failed")
                pytest.skip(
                    f"Could not start Joern server after {max_retries} attempts: {e}"
                )

    # 提供服务器给所有测试
    try:
        yield server
    finally:
        # 清理：停止服务器
        if server:
            logger.info("🧹 Stopping Joern server...")
            try:
                await server.stop()
                logger.success("✅ Joern server stopped")
            except Exception as e:
                logger.warning(f"⚠️  Error stopping server: {e}")

            # 等待端口完全释放
            await asyncio.sleep(2)

            # 验证端口已释放
            if not is_port_in_use(server.port):
                logger.success(f"✅ Port {server.port} released successfully")
            else:
                logger.warning(f"⚠️  Port {server.port} still in use after stop")


@pytest.fixture(scope="function", autouse=True)
async def ensure_joern_server_health(joern_server):
    """在每个测试前确保Joern server健康

    如果server崩溃，尝试重启
    """
    if not joern_server:
        pytest.skip("Joern server not available")

    # 检查server是否仍在运行
    if not joern_server.is_running():
        logger.warning("⚠️  Joern server appears to be stopped, attempting restart...")
        try:
            await joern_server.start(timeout=180)
            logger.success("✅ Joern server restarted successfully")
        except Exception as e:
            logger.error(f"❌ Failed to restart Joern server: {e}")
            pytest.skip(f"Joern server unavailable: {e}")

    # 执行测试
    yield

    # 测试后不需要特殊处理（session级别的fixture会负责清理）
