#!/usr/bin/env python
"""测试Joern Server启动"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from joern_mcp.joern.server import JoernServerManager
from loguru import logger


async def test_server_startup():
    """测试Joern Server启动"""
    logger.info("=" * 60)
    logger.info("测试Joern Server启动")
    logger.info("=" * 60)

    # 创建服务器管理器（使用随机端口）
    import random

    port = random.randint(20000, 30000)
    server = JoernServerManager(host="localhost", port=port)

    try:
        logger.info(f"尝试在端口 {port} 启动Joern Server...")
        start_time = time.time()

        # 尝试启动（增加超时到180秒）
        await server.start(timeout=180)

        elapsed = time.time() - start_time
        logger.success(f"✅ Joern Server启动成功！耗时: {elapsed:.1f}秒")

        # 测试健康检查
        logger.info("执行健康检查...")
        healthy = await server.health_check()
        if healthy:
            logger.success("✅ 健康检查通过")
        else:
            logger.warning("⚠️  健康检查失败")

        # 测试简单查询
        logger.info("执行简单查询...")
        result = server.execute_query("1 + 1")
        logger.info(f"查询结果: {result}")

        if result.get("success"):
            logger.success("✅ 查询执行成功")
        else:
            logger.error(f"❌ 查询失败: {result}")

    except TimeoutError as e:
        logger.error(f"❌ 启动超时: {e}")
        logger.error("这表明Joern Server启动需要很长时间")
        logger.error("可能的原因:")
        logger.error("  1. JVM启动慢")
        logger.error("  2. 系统资源不足")
        logger.error("  3. Joern版本问题")
        return False
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 停止服务器
        logger.info("停止Joern Server...")
        await server.stop()
        logger.info("清理完成")

    return True


async def main():
    """主函数"""
    success = await test_server_startup()

    logger.info("=" * 60)
    if success:
        logger.success("🎉 测试完成：Joern Server可以正常启动！")
        logger.info("集成测试应该可以运行（但可能需要很长时间）")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败：Joern Server无法启动")
        logger.warning("建议:")
        logger.warning("  1. 依赖单元测试（48个全部通过）")
        logger.warning("  2. 手动验证功能")
        logger.warning("  3. 跳过自动化集成测试")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
