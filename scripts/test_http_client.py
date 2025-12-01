"""测试HTTP客户端与Joern Server的交互"""

import asyncio
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from joern_mcp.joern.http_client import JoernHTTPClient
from joern_mcp.joern.manager import JoernManager
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.utils.port_utils import find_free_port


async def test_http_client():
    """测试HTTP客户端"""
    port = find_free_port(start_port=20000, end_port=20100)
    logger.info(f"使用端口: {port}")

    # 启动Joern Server
    server = JoernServerManager(host="localhost", port=port, use_http_client=True)

    try:
        logger.info("🚀 启动Joern Server...")
        await server.start(timeout=180)
        logger.success(f"✅ Server启动成功: {server.endpoint}")

        # 测试1: 简单查询
        logger.info("\n=== 测试1: 简单算术查询 ===")
        result = await server.execute_query_async("1 + 1")
        logger.info(f"查询结果: {result}")

        # 测试2: CPG查询（需要先导入代码）
        logger.info("\n=== 测试2: 导入测试代码 ===")
        test_code = Path(__file__).parent.parent / "tests/integration/test_data/sample_c"
        if test_code.exists():
            import_result = await server.import_code(str(test_code), "http_test")
            logger.info(f"导入结果: {import_result.get('success', False)}")

            # 测试3: 查询方法
            logger.info("\n=== 测试3: 查询方法列表 ===")
            methods_result = await server.execute_query_async("cpg.method.name.l")
            logger.info(f"方法查询结果类型: {type(methods_result)}")
            logger.info(f"方法查询结果: {methods_result}")

            # 测试4: 查询具体方法
            logger.info("\n=== 测试4: 查询main函数 ===")
            main_result = await server.execute_query_async('cpg.method.name("main").code.l')
            logger.info(f"main函数查询结果: {main_result}")
        else:
            logger.warning(f"测试代码不存在: {test_code}")

        logger.success("\n✅ 所有测试通过!")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        logger.info("\n🛑 停止Server...")
        await server.stop()
        logger.info("✅ Server已停止")


async def test_raw_http_client():
    """直接测试JoernHTTPClient"""
    port = find_free_port(start_port=20100, end_port=20200)
    logger.info(f"使用端口: {port}")

    # 手动启动Joern Server
    import subprocess

    manager = JoernManager()
    cmd = [
        str(manager.joern_path),
        "--server",
        "--server-host",
        "localhost",
        "--server-port",
        str(port),
    ]

    logger.info("🚀 启动Joern Server进程...")
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        # 等待server启动
        logger.info("⏳ 等待Server启动...")
        await asyncio.sleep(30)  # 增加到30秒
        
        # 检查进程状态
        if process.returncode is not None:
            logger.error(f"❌ Server进程已退出，返回码: {process.returncode}")
            stdout, stderr = await process.communicate()
            logger.error(f"STDOUT: {stdout.decode() if stdout else 'N/A'}")
            logger.error(f"STDERR: {stderr.decode() if stderr else 'N/A'}")
            return
        
        logger.info(f"✅ Server进程运行中 (PID: {process.pid})")

        # 创建HTTP客户端
        client = JoernHTTPClient(endpoint=f"localhost:{port}", timeout=60.0)

        # 测试查询
        logger.info("\n=== 测试HTTP客户端查询 ===")
        result = await client.execute("1 + 1")
        logger.info(f"查询结果: {result}")
        logger.info(f"结果类型: {type(result)}")
        logger.info(f"结果键: {result.keys() if isinstance(result, dict) else 'N/A'}")

        if isinstance(result, dict):
            if result.get("success") is False:
                logger.error(f"查询失败: {result.get('error')}")
            else:
                logger.success("✅ 查询成功!")
                logger.info(f"返回数据: {result}")
        else:
            logger.warning(f"意外的结果格式: {result}")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        logger.info("\n🛑 停止Server进程...")
        process.terminate()
        await process.wait()
        logger.info("✅ Server进程已停止")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("HTTP客户端测试")
    logger.info("=" * 60)

    # 选择测试模式
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--raw":
        logger.info("使用模式: 直接测试JoernHTTPClient")
        await test_raw_http_client()
    else:
        logger.info("使用模式: 通过JoernServerManager测试")
        await test_http_client()


if __name__ == "__main__":
    asyncio.run(main())

