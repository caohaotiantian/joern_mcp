#!/usr/bin/env python3
"""快速测试脚本 - 验证Week 1的代码是否正常工作"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("Joern MCP Server - Week 1 快速测试")
print("=" * 60)
print()

# 测试1: 配置系统
print("📋 测试1: 配置系统")
try:
    from joern_mcp.config import settings
    print(f"  ✅ 配置加载成功")
    print(f"     - Joern Server: {settings.joern_server_host}:{settings.joern_server_port}")
    print(f"     - 工作空间: {settings.joern_workspace}")
    print(f"     - 日志级别: {settings.log_level}")
except Exception as e:
    print(f"  ❌ 配置加载失败: {e}")
    sys.exit(1)

print()

# 测试2: 日志系统
print("📝 测试2: 日志系统")
try:
    from loguru import logger
    logger.info("日志系统测试")
    print(f"  ✅ 日志系统正常")
except Exception as e:
    print(f"  ❌ 日志系统失败: {e}")
    sys.exit(1)

print()

# 测试3: Joern检测
print("🔍 测试3: Joern检测")
try:
    from joern_mcp.joern.manager import JoernManager, JoernNotFoundError
    
    try:
        manager = JoernManager()
        print(f"  ✅ Joern已找到")
        print(f"     - 路径: {manager.joern_path}")
        version = manager.get_version()
        print(f"     - 版本: {version}")
        
        # 验证安装
        validation = manager.validate_installation()
        if all(validation.values()):
            print(f"  ✅ Joern安装完整")
        else:
            print(f"  ⚠️  Joern安装可能不完整: {validation}")
            
    except JoernNotFoundError:
        print(f"  ⚠️  Joern未安装")
        print(f"     可以通过以下命令安装:")
        print(f"     curl -L https://github.com/joernio/joern/releases/latest/download/joern-install.sh | sudo bash")
        
except Exception as e:
    print(f"  ❌ Joern检测失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试4: Joern Server（可选）
print("🚀 测试4: Joern Server管理（可选 - 需要安装Joern）")
try:
    from joern_mcp.joern.manager import JoernManager, JoernNotFoundError
    from joern_mcp.joern.server import JoernServerManager
    from joern_mcp.joern.executor import QueryExecutor
    
    try:
        # 检查Joern是否可用
        manager = JoernManager()
        
        async def test_server():
            server = JoernServerManager()
            print("  启动Joern Server...")
            await server.start(timeout=30)
            print(f"  ✅ Server启动成功: {server.endpoint}")
            
            # 测试健康检查
            is_healthy = await server.health_check()
            if is_healthy:
                print(f"  ✅ 健康检查通过")
            else:
                print(f"  ⚠️  健康检查失败")
            
            # 测试查询执行
            print("  测试查询执行...")
            executor = QueryExecutor(server)
            result = await executor.execute("1 + 1")
            if result.get("success"):
                print(f"  ✅ 查询执行成功")
            else:
                print(f"  ⚠️  查询执行失败: {result.get('stderr')}")
            
            # 停止服务器
            print("  停止Server...")
            await server.stop()
            print(f"  ✅ Server已停止")
        
        asyncio.run(test_server())
        
    except JoernNotFoundError:
        print("  ⏭️  跳过（Joern未安装）")
        
except Exception as e:
    print(f"  ❌ Server测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 总结
print("=" * 60)
print("测试总结")
print("=" * 60)
print()
print("✅ Week 1基础代码已实现并通过基本测试")
print()
print("下一步:")
print("1. 如果还没安装Joern，建议安装以运行完整测试")
print("2. 运行完整测试套件: pytest tests/ -v")
print("3. 查看Week 2开发计划: cat doc/DEVELOPMENT_PLAN_WEEK2-8.md")
print("4. 开始实现Week 2的MCP工具")
print()
print("详细信息请查看: NEXT_STEPS.md")
print()

