#!/usr/bin/env python3
"""
缓冲区溢出漏洞检测脚本

该脚本专门用于检测 C/C++ 代码中的缓冲区溢出漏洞。
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

# 危险函数列表
DANGEROUS_FUNCTIONS = [
    ("strcpy", "使用不安全的字符串复制，建议使用 strncpy 或 strlcpy"),
    ("strcat", "使用不安全的字符串连接，建议使用 strncat 或 strlcat"),
    ("sprintf", "使用不安全的格式化输出，建议使用 snprintf"),
    ("gets", "极度危险，永远不应使用，建议使用 fgets"),
    ("scanf", "没有长度限制的输入，建议指定最大宽度"),
    ("vsprintf", "使用不安全的格式化输出，建议使用 vsnprintf"),
]


async def analyze_buffer_overflow(source_path: str, project_name: str = "buffer_overflow_scan"):
    """
    分析代码中的缓冲区溢出漏洞

    Args:
        source_path: 源代码路径
        project_name: 项目名称
    """
    port = find_free_port()
    print(f"🚀 启动 Joern 服务器 (端口: {port})...")

    server = JoernServerManager(port=port)

    try:
        await server.start()
        print("✅ Joern 服务器已启动")

        await asyncio.sleep(2)

        # 导入代码
        print(f"\n📂 导入代码: {source_path}")
        result = await server.import_code(source_path, project_name)

        if not result.get("success"):
            print(f"❌ 代码导入失败: {result.get('stderr', 'Unknown error')}")
            return

        print("✅ 代码导入成功")

        executor = QueryExecutor(server)
        taint_service = TaintAnalysisService(executor)

        # 1. 使用污点分析规则检测
        print("\n🔍 执行污点分析检测...")
        rule = get_rule_by_name("Buffer Overflow")

        print(f"   规则: {rule.name}")
        print(f"   严重程度: {rule.severity}")
        print(f"   CWE: {rule.cwe_id}")

        taint_result = await taint_service.analyze_with_rule(rule, max_flows=20)

        taint_vulns = []
        if taint_result.get("success"):
            taint_vulns = taint_result.get("vulnerabilities", [])

        # 2. 检查危险函数调用
        print("\n🔍 检查危险函数调用...")
        dangerous_calls = []

        for func_name, recommendation in DANGEROUS_FUNCTIONS:
            query = f'''
            cpg.call.name("{func_name}")
               .map(c => Map(
                   "function" -> c.name,
                   "code" -> c.code,
                   "file" -> c.file.name.headOption.getOrElse("unknown"),
                   "line" -> c.lineNumber.getOrElse(-1),
                   "method" -> c.method.name
               ))
            '''

            result = await executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                import json
                import re

                # 清理输出
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_output = ansi_escape.sub('', stdout).strip()

                try:
                    calls = json.loads(clean_output)
                    if isinstance(calls, str):
                        calls = json.loads(calls)

                    if calls:
                        for call in (calls if isinstance(calls, list) else [calls]):
                            call["recommendation"] = recommendation
                            dangerous_calls.append(call)
                except json.JSONDecodeError:
                    pass

        # 输出结果
        total_issues = len(taint_vulns) + len(dangerous_calls)

        if total_issues > 0:
            print(f"\n🚨 发现 {total_issues} 个潜在缓冲区溢出问题!")
            print("=" * 60)

            # 输出污点分析结果
            if taint_vulns:
                print(f"\n📌 污点分析发现 {len(taint_vulns)} 个数据流漏洞:")
                print("-" * 60)

                for i, vuln in enumerate(taint_vulns, 1):
                    print(f"\n漏洞 #{i}")

                    source = vuln.get("source", {})
                    sink = vuln.get("sink", {})

                    print(f"  源: {source.get('code', 'N/A')} ({source.get('file', 'unknown')}:{source.get('line', -1)})")
                    print(f"  汇: {sink.get('code', 'N/A')} ({sink.get('file', 'unknown')}:{sink.get('line', -1)})")

            # 输出危险函数调用
            if dangerous_calls:
                print(f"\n📌 危险函数调用 {len(dangerous_calls)} 处:")
                print("-" * 60)

                for i, call in enumerate(dangerous_calls, 1):
                    print(f"\n问题 #{i}")
                    print(f"  函数: {call.get('function', 'unknown')}")
                    print(f"  代码: {call.get('code', 'N/A')}")
                    print(f"  位置: {call.get('file', 'unknown')}:{call.get('line', -1)}")
                    print(f"  所在方法: {call.get('method', 'unknown')}")
                    print(f"  💡 建议: {call.get('recommendation', 'N/A')}")

            print("\n" + "=" * 60)
            print("通用修复建议:")
            print("1. 使用带长度限制的安全函数 (strncpy, snprintf 等)")
            print("2. 始终检查缓冲区边界")
            print("3. 使用静态分析工具定期扫描")
            print("4. 启用编译器保护选项 (-fstack-protector)")
            print("=" * 60)
        else:
            print("\n✅ 未发现缓冲区溢出漏洞")

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
        print("用法: python analyze_buffer_overflow.py <源代码路径> [项目名称]")
        print()
        print("示例:")
        print("  python analyze_buffer_overflow.py ./vulnerable_c")
        print("  python analyze_buffer_overflow.py /path/to/project my_project")
        sys.exit(1)

    source_path = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else "buffer_overflow_scan"

    if not Path(source_path).exists():
        print(f"❌ 路径不存在: {source_path}")
        sys.exit(1)

    asyncio.run(analyze_buffer_overflow(str(Path(source_path).resolve()), project_name))


if __name__ == "__main__":
    main()

