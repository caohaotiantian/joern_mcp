"""集成测试配置"""

import pytest
import asyncio
import random
from pathlib import Path
from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerManager


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


@pytest.fixture(scope="function")
def joern_port():
    """为每个测试生成不同的端口"""
    return random.randint(8100, 8999)


@pytest.fixture(scope="function")
async def joern_server(joern_port):
    """创建并管理Joern Server"""
    if not JoernManager().validate_installation():
        pytest.skip("Joern not installed")

    server = JoernServerManager(host="localhost", port=joern_port)

    try:
        await server.start(timeout=60)  # 增加超时时间
        yield server
    finally:
        await server.stop()
        await asyncio.sleep(1)  # 等待端口释放
