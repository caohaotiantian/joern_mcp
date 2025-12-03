"""
E2E测试的fixture配置

提供测试所需的环境和数据
"""

import asyncio

import pytest

from joern_mcp.joern.server import JoernServerManager
from joern_mcp.utils.port_utils import find_free_port


@pytest.fixture(scope="session")
def joern_server():
    """启动Joern服务器供E2E测试使用（session级别）"""
    port = find_free_port(start_port=35000, end_port=35100)
    manager = JoernServerManager(port=port)

    # 启动服务器
    async def start_server():
        await manager.start()
        return manager

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    manager = loop.run_until_complete(start_server())

    yield manager

    # 清理
    async def stop_server():
        await manager.stop()

    loop.run_until_complete(stop_server())
    loop.close()


@pytest.fixture
def sample_c_code(tmp_path):
    """创建示例C代码用于测试"""
    code_dir = tmp_path / "sample_code"
    code_dir.mkdir()

    # 创建一个简单的C程序
    main_c = code_dir / "main.c"
    main_c.write_text(
        """
#include <stdio.h>
#include <string.h>

void unsafe_strcpy(char *dest, char *src) {
    strcpy(dest, src);  // 不安全的strcpy
}

void safe_function(char *data) {
    printf("Safe: %s\\n", data);
}

int process_input(char *input) {
    char buffer[100];
    unsafe_strcpy(buffer, input);
    safe_function(buffer);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        process_input(argv[1]);
    }
    return 0;
}
"""
    )

    return code_dir


@pytest.fixture
def sample_java_code(tmp_path):
    """创建示例Java代码用于测试"""
    code_dir = tmp_path / "sample_java"
    code_dir.mkdir()

    # 创建一个简单的Java程序
    main_java = code_dir / "Main.java"
    main_java.write_text(
        """
public class Main {
    public static void unsafeMethod(String input) {
        System.out.println(input);
    }

    public static void caller1() {
        unsafeMethod("test");
    }

    public static void caller2() {
        caller1();
    }

    public static void main(String[] args) {
        caller2();
    }
}
"""
    )

    return code_dir
