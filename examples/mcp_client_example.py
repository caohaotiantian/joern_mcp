#!/usr/bin/env python3
"""
MCP 客户端使用示例

此脚本演示如何通过 MCP 协议与 Joern MCP Server 交互，
完成从 CPG 构建到漏洞检测的完整流程。

使用方法：
    # 方式一：使用 streamable-http 传输（需要先启动服务器）
    python -m joern_mcp &  # 先启动服务器
    python examples/mcp_client_example.py http

    # 方式二：使用 stdio 传输（自动启动服务器）
    python examples/mcp_client_example.py stdio
"""

import asyncio
import json
import sys
from pathlib import Path


async def run_with_http_transport():
    """通过 HTTP 传输连接 MCP 服务器"""
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        print("❌ 请安装 mcp 包: pip install mcp")
        return

    server_url = "http://localhost:8000/mcp"

    print(f"🔌 连接到 MCP 服务器: {server_url}")

    try:
        async with (
            streamablehttp_client(server_url) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            await run_analysis(session)
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   请确保服务器已启动: python -m joern_mcp")


async def run_with_stdio_transport():
    """通过 stdio 传输连接 MCP 服务器（自动启动）"""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("❌ 请安装 mcp 包: pip install mcp")
        return

    # 项目根目录
    project_root = Path(__file__).parent.parent

    print("🚀 启动 MCP 服务器（stdio 模式）...")

    server_params = {
        "command": "python",
        "args": ["-m", "joern_mcp"],
        "cwd": str(project_root),
    }

    async with (
        stdio_client(**server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await run_analysis(session)


async def run_analysis(session):
    """执行完整的分析流程"""
    print("\n" + "=" * 60)
    print("         Joern MCP 客户端示例")
    print("=" * 60)

    # 1. 健康检查
    print("\n📋 步骤 1: 健康检查")
    print("-" * 40)
    result = await session.call_tool("health_check", {})
    print_result(result)

    # 2. 列出可用工具
    print("\n📋 步骤 2: 列出可用工具")
    print("-" * 40)
    tools = await session.list_tools()
    print(f"可用工具数量: {len(tools.tools)}")
    for tool in tools.tools[:10]:  # 只显示前10个
        print(f"  - {tool.name}: {tool.description[:50]}...")
    if len(tools.tools) > 10:
        print(f"  ... 还有 {len(tools.tools) - 10} 个工具")

    # 3. 解析示例项目
    print("\n📋 步骤 3: 解析示例项目（构建 CPG）")
    print("-" * 40)

    # 使用示例漏洞代码
    example_path = Path(__file__).parent / "vulnerable_c"
    if not example_path.exists():
        print(f"⚠️ 示例项目不存在: {example_path}")
        print("   跳过解析步骤")
    else:
        result = await session.call_tool(
            "parse_project",
            {
                "source_path": str(example_path.absolute()),
                "project_name": "mcp_demo",
            },
        )
        print_result(result)

        # 等待 CPG 构建完成
        await asyncio.sleep(2)

        # 4. 列出函数
        print("\n📋 步骤 4: 列出项目中的函数")
        print("-" * 40)
        result = await session.call_tool("list_functions", {"limit": 20})
        print_result(result)

        # 5. 搜索危险函数
        print("\n📋 步骤 5: 搜索危险函数调用")
        print("-" * 40)
        result = await session.call_tool(
            "search_code", {"pattern": "strcpy|gets|system", "scope": "calls"}
        )
        print_result(result)

        # 6. 漏洞检测
        print("\n📋 步骤 6: 执行漏洞检测")
        print("-" * 40)
        result = await session.call_tool(
            "find_vulnerabilities", {"severity": "CRITICAL", "max_flows": 5}
        )
        print_result(result)

        # 7. 列出漏洞规则
        print("\n📋 步骤 7: 查看可用的漏洞检测规则")
        print("-" * 40)
        result = await session.call_tool("list_vulnerability_rules", {})
        print_result(result)

        # 8. 检查特定污点流
        print("\n📋 步骤 8: 检查用户输入到系统命令的污点流")
        print("-" * 40)
        result = await session.call_tool(
            "check_taint_flow",
            {"source_pattern": "gets|scanf|fgets", "sink_pattern": "system|exec|popen"},
        )
        print_result(result)

        # 9. 获取特定函数代码
        print("\n📋 步骤 9: 获取 main 函数代码")
        print("-" * 40)
        result = await session.call_tool("get_function_code", {"function_name": "main"})
        print_result(result)

        # 10. 执行自定义查询
        print("\n📋 步骤 10: 执行自定义 CPGQL 查询")
        print("-" * 40)
        result = await session.call_tool(
            "execute_query", {"query": "cpg.method.name.take(5).l", "format": "json"}
        )
        print_result(result)

    print("\n" + "=" * 60)
    print("         分析完成!")
    print("=" * 60)


def print_result(result):
    """格式化打印结果"""
    if hasattr(result, "content"):
        for content in result.content:
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                    if len(content.text) > 500:
                        print("... (输出已截断)")
                except json.JSONDecodeError:
                    print(content.text[:500])
    else:
        print(result)


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        print("使用 HTTP 传输模式")
        asyncio.run(run_with_http_transport())
    else:
        print("使用 stdio 传输模式（默认）")
        print("提示: 使用 'python mcp_client_example.py http' 切换到 HTTP 模式")
        asyncio.run(run_with_stdio_transport())


if __name__ == "__main__":
    main()
