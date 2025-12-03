#!/usr/bin/env python3
"""
命令注入漏洞检测脚本

该脚本专门用于检测 C/C++ 代码中的命令注入漏洞。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from joern_mcp.joern.executor import QueryExecutor  # noqa: E402
from joern_mcp.joern.server import JoernServerManager  # noqa: E402
from joern_mcp.models.taint_rules import get_rule_by_name  # noqa: E402
from joern_mcp.services.taint import TaintAnalysisService  # noqa: E402
from joern_mcp.utils.port_utils import find_free_port  # noqa: E402


async def analyze_command_injection(source_path: str, project_name: str = "cmd_injection_scan"):
    """
    分析代码中的命令注入漏洞

    Args:
        source_path: 源代码路径
        project_name: 项目名称
    """
    # 查找可用端口
    port = find_free_port()
    print(f"🚀 启动 Joern 服务器 (端口: {port})...")

    server = JoernServerManager(port=port)

    try:
        await server.start()
        print("✅ Joern 服务器已启动")

        # 等待服务器完全就绪
        await asyncio.sleep(2)

        # 导入代码
        print(f"\n📂 导入代码: {source_path}")
        result = await server.import_code(source_path, project_name)

        if not result.get("success"):
            print(f"❌ 代码导入失败: {result.get('stderr', 'Unknown error')}")
            return

        print("✅ 代码导入成功")

        # 初始化服务
        executor = QueryExecutor(server)
        taint_service = TaintAnalysisService(executor)

        # 获取命令注入规则
        print("\n🔍 检测命令注入漏洞...")
        rule = get_rule_by_name("Command Injection")

        print(f"   规则: {rule.name}")
        print(f"   严重程度: {rule.severity}")
        print(f"   CWE: {rule.cwe_id}")
        print(f"   源函数: {', '.join(rule.sources[:5])}...")
        print(f"   汇函数: {', '.join(rule.sinks[:5])}...")

        # 执行分析
        result = await taint_service.analyze_with_rule(rule, max_flows=20)

        if result.get("success"):
            vulns = result.get("vulnerabilities", [])

            if vulns:
                print(f"\n🚨 发现 {len(vulns)} 个命令注入漏洞!")
                print("-" * 60)

                for i, vuln in enumerate(vulns, 1):
                    print(f"\n漏洞 #{i}")
                    print(f"  类型: {vuln.get('vulnerability', 'Command Injection')}")
                    print(f"  严重程度: {vuln.get('severity', rule.severity)}")

                    source = vuln.get("source", {})
                    sink = vuln.get("sink", {})

                    print("  源位置:")
                    print(f"    文件: {source.get('file', 'unknown')}")
                    print(f"    行号: {source.get('line', -1)}")
                    print(f"    代码: {source.get('code', 'N/A')}")

                    print("  汇位置:")
                    print(f"    文件: {sink.get('file', 'unknown')}")
                    print(f"    行号: {sink.get('line', -1)}")
                    print(f"    代码: {sink.get('code', 'N/A')}")

                    print(f"  路径长度: {vuln.get('pathLength', 'N/A')}")

                print("\n" + "=" * 60)
                print("修复建议:")
                print("1. 避免直接使用用户输入构造系统命令")
                print("2. 使用白名单验证用户输入")
                print("3. 使用参数化的命令执行方式")
                print("4. 对用户输入进行转义处理")
                print("=" * 60)
            else:
                print("\n✅ 未发现命令注入漏洞")
        else:
            print(f"\n❌ 分析失败: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n🛑 停止 Joern 服务器...")
        await server.stop()
        print("✅ 服务器已停止")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_command_injection.py <源代码路径> [项目名称]")
        print()
        print("示例:")
        print("  python analyze_command_injection.py ./vulnerable_c")
        print("  python analyze_command_injection.py /path/to/project my_project")
        sys.exit(1)

    source_path = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else "cmd_injection_scan"

    # 验证路径
    if not Path(source_path).exists():
        print(f"❌ 路径不存在: {source_path}")
        sys.exit(1)

    # 运行分析
    asyncio.run(analyze_command_injection(str(Path(source_path).resolve()), project_name))


if __name__ == "__main__":
    main()

