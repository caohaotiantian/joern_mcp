#!/usr/bin/env python3
"""
Joern MCP Server 演示脚本

本脚本展示如何使用Joern MCP Server进行代码安全分析。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")


def print_result(result: dict, indent: int = 0):
    """格式化打印结果"""
    prefix = "  " * indent
    if result.get("success"):
        print(f"{prefix}✅ 成功")
    else:
        print(f"{prefix}❌ 失败: {result.get('error', 'Unknown')}")
        return

    # 打印主要字段
    for key, value in result.items():
        if key in ["success", "raw_output"]:
            continue
        if isinstance(value, list):
            print(f"{prefix}  {key}: ({len(value)} 项)")
            for i, item in enumerate(value[:5]):  # 最多显示5项
                if isinstance(item, dict):
                    print(f"{prefix}    [{i}] {item.get('name', item)}")
                else:
                    print(f"{prefix}    [{i}] {item}")
            if len(value) > 5:
                print(f"{prefix}    ... 还有 {len(value) - 5} 项")
        elif isinstance(value, dict):
            print(f"{prefix}  {key}: {value}")
        else:
            print(f"{prefix}  {key}: {value}")


async def demo_project_management(server: JoernServerManager, code_path: str):
    """演示项目管理功能"""
    print_section("📂 项目管理演示")

    print("1. 解析项目...")
    result = await server.import_code(code_path, "demo-vulnerable-c")
    if result.get("success"):
        print("   ✅ 项目解析成功")
    else:
        print(f"   ❌ 解析失败: {result.get('stderr')}")
        return False

    print("\n2. 验证项目已加载...")
    executor = OptimizedQueryExecutor(server)
    verify = await executor.execute("cpg.method.name.l")
    if verify.get("success"):
        print("   ✅ CPG已加载，可以开始分析")

    return True


async def demo_callgraph_analysis(executor: OptimizedQueryExecutor):
    """演示调用图分析"""
    print_section("📞 调用图分析演示")

    service = CallGraphService(executor)

    # 1. 获取函数调用者
    print("1. 查找调用 buffer_overflow 的函数:")
    callers = await service.get_callers("buffer_overflow", depth=3)
    print_result(callers, indent=1)

    # 2. 获取函数被调用者
    print("\n2. 查找 main 调用的函数:")
    callees = await service.get_callees("main", depth=1)
    print_result(callees, indent=1)

    # 3. 获取调用链
    print("\n3. 追踪 buffer_overflow 的调用链 (向上):")
    chain = await service.get_call_chain("buffer_overflow", max_depth=5, direction="up")
    print_result(chain, indent=1)

    # 4. 获取调用图
    print("\n4. 生成 handle_request 的调用图:")
    graph = await service.get_call_graph("handle_request", depth=2)
    if graph.get("success"):
        print(f"   节点数: {graph.get('node_count', 0)}")
        print(f"   边数: {graph.get('edge_count', 0)}")


async def demo_dataflow_analysis(executor: OptimizedQueryExecutor):
    """演示数据流分析"""
    print_section("🌊 数据流分析演示")

    service = DataFlowService(executor)

    # 1. 追踪数据流
    print("1. 追踪从 gets 到 strcpy 的数据流:")
    flow1 = await service.track_dataflow("gets", "strcpy", max_flows=5)
    print_result(flow1, indent=1)

    # 2. 分析变量流向
    print("\n2. 分析 buffer 变量的数据流:")
    flow2 = await service.analyze_variable_flow("buffer", sink_method="printf")
    print_result(flow2, indent=1)

    # 3. 查找数据依赖
    print("\n3. 查找 main 函数的数据依赖:")
    deps = await service.find_data_dependencies("main")
    print_result(deps, indent=1)


async def demo_vulnerability_detection(executor: OptimizedQueryExecutor):
    """演示漏洞检测"""
    print_section("🛡️ 漏洞检测演示")

    service = TaintAnalysisService(executor)

    # 1. 列出所有规则
    print("1. 可用的漏洞检测规则:")
    rules = service.list_rules()
    for rule in rules.get("rules", []):
        print(f"   - {rule['name']} ({rule['severity']})")

    # 2. 检测所有漏洞
    print("\n2. 扫描所有漏洞:")
    all_vulns = await service.find_vulnerabilities(max_flows=5)
    if all_vulns.get("success"):
        print(f"   发现 {all_vulns.get('total_count', 0)} 个潜在漏洞")
        summary = all_vulns.get("summary", {})
        for severity, count in summary.items():
            print(f"   - {severity}: {count} 个")

    # 3. 只检测严重漏洞
    print("\n3. 检测严重漏洞 (CRITICAL):")
    critical = await service.find_vulnerabilities(severity="CRITICAL", max_flows=3)
    print_result(critical, indent=1)

    # 4. 自定义污点检查
    print("\n4. 自定义检查: gets -> system:")
    custom = await service.check_specific_flow("gets", "system", max_flows=3)
    print_result(custom, indent=1)

    # 5. 检查格式化字符串
    print("\n5. 检查格式化字符串漏洞:")
    fmt = await service.check_specific_flow("gets|scanf|argv", "printf|sprintf", max_flows=3)
    print_result(fmt, indent=1)


async def demo_custom_query(executor: OptimizedQueryExecutor):
    """演示自定义查询"""
    print_section("⚙️ 自定义查询演示")

    # 1. 获取所有方法
    print("1. 获取所有函数名:")
    result1 = await executor.execute("cpg.method.name.l")
    if result1.get("success"):
        stdout = result1.get("stdout", "[]")
        print(f"   结果: {stdout[:200]}...")

    # 2. 查找危险函数调用
    print("\n2. 查找所有 strcpy 调用:")
    result2 = await executor.execute('cpg.call.name("strcpy").code.l')
    if result2.get("success"):
        print(f"   结果: {result2.get('stdout', '[]')}")

    # 3. 查找带有用户输入的函数
    print("\n3. 查找使用 gets 的函数:")
    result3 = await executor.execute('cpg.call.name("gets").method.name.l')
    if result3.get("success"):
        print(f"   结果: {result3.get('stdout', '[]')}")


async def main():
    """主演示函数"""
    print("\n" + "🔒" * 30)
    print("     Joern MCP Server 演示")
    print("🔒" * 30 + "\n")

    # 获取示例代码路径
    demo_dir = Path(__file__).parent
    code_path = str(demo_dir / "vulnerable_c")

    print(f"示例代码路径: {code_path}")

    # 启动Joern服务器（使用随机端口避免冲突）
    import random
    port = random.randint(20000, 30000)
    print(f"\n启动Joern服务器（端口: {port}）...")
    server = JoernServerManager(host="localhost", port=port)

    try:
        await server.start(timeout=120)
        print(f"✅ Joern服务器已启动: {server.endpoint}")

        # 等待服务器完全初始化
        print("等待服务器完全初始化...")
        await asyncio.sleep(3)

        # 1. 项目管理
        if not await demo_project_management(server, code_path):
            print("❌ 项目加载失败，退出演示")
            return

        # 创建查询执行器
        executor = OptimizedQueryExecutor(server)

        # 2. 调用图分析
        await demo_callgraph_analysis(executor)

        # 3. 数据流分析
        await demo_dataflow_analysis(executor)

        # 4. 漏洞检测
        await demo_vulnerability_detection(executor)

        # 5. 自定义查询
        await demo_custom_query(executor)

        # 总结
        print_section("📊 演示总结")
        print("本演示展示了Joern MCP Server的核心功能:")
        print("  ✅ 项目解析和CPG生成")
        print("  ✅ 函数调用图分析")
        print("  ✅ 数据流追踪")
        print("  ✅ 自动漏洞检测")
        print("  ✅ 自定义CPGQL查询")
        print("\n更多信息请参考文档: docs/USER_GUIDE.md")

    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        raise
    finally:
        # 停止服务器
        print("\n停止Joern服务器...")
        await server.stop()
        print("✅ 服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())

