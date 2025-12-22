#!/usr/bin/env python3
"""
综合安全扫描脚本

该脚本执行全面的安全扫描，检测多种类型的漏洞。
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from joern_mcp.joern.executor import QueryExecutor  # noqa: E402
from joern_mcp.joern.server import JoernServerManager  # noqa: E402
from joern_mcp.services.callgraph import CallGraphService  # noqa: E402
from joern_mcp.services.dataflow import DataFlowService  # noqa: E402
from joern_mcp.services.taint import TaintAnalysisService  # noqa: E402
from joern_mcp.utils.port_utils import find_free_port  # noqa: E402


async def comprehensive_scan(source_path: str, project_name: str = "security_scan"):
    """
    执行综合安全扫描

    Args:
        source_path: 源代码路径
        project_name: 项目名称
    """
    start_time = datetime.now()
    port = find_free_port()

    print("=" * 70)
    print("                    🛡️  综合安全扫描报告")
    print("=" * 70)
    print(f"扫描时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标路径: {source_path}")
    print(f"项目名称: {project_name}")
    print("=" * 70)

    server = JoernServerManager(port=port)

    try:
        # 启动服务器
        print("\n🚀 初始化扫描环境...")
        await server.start()
        await asyncio.sleep(2)

        # 导入代码
        print("📂 导入代码...")
        result = await server.import_code(source_path, project_name)

        if not result.get("success"):
            print(f"❌ 代码导入失败: {result.get('stderr', 'Unknown error')}")
            return

        print("✅ 代码导入成功")

        # 初始化服务
        executor = QueryExecutor(server)
        taint_service = TaintAnalysisService(executor)
        callgraph_service = CallGraphService(executor)
        # DataFlowService 可用于更深入的数据流分析（当前扫描未使用）
        _ = DataFlowService(executor)

        # 收集统计信息
        stats = {
            "total_vulnerabilities": 0,
            "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "by_type": {},
            "dangerous_functions": 0,
            "risky_data_flows": 0,
        }

        all_findings = []

        # 1. 执行污点分析
        print("\n" + "-" * 70)
        print("📋 阶段 1: 污点分析")
        print("-" * 70)

        vuln_result = await taint_service.find_vulnerabilities(max_flows=15)

        if vuln_result.get("success"):
            vulns = vuln_result.get("vulnerabilities", [])
            stats["total_vulnerabilities"] = len(vulns)
            stats["by_severity"] = vuln_result.get("summary", stats["by_severity"])

            print(f"✅ 扫描完成，检查了 {vuln_result.get('rules_checked', 0)} 条规则")

            for vuln in vulns:
                vuln_type = vuln.get("vulnerability", "Unknown")
                stats["by_type"][vuln_type] = stats["by_type"].get(vuln_type, 0) + 1
                all_findings.append(
                    {
                        "category": "污点分析",
                        "type": vuln_type,
                        "severity": vuln.get("severity", "UNKNOWN"),
                        "cwe_id": vuln.get("cwe_id", "N/A"),
                        "source": vuln.get("source", {}),
                        "sink": vuln.get("sink", {}),
                    }
                )

        # 2. 检查危险函数
        print("\n" + "-" * 70)
        print("📋 阶段 2: 危险函数检查")
        print("-" * 70)

        dangerous_funcs = [
            ("gets", "CRITICAL", "CWE-120"),
            ("strcpy", "HIGH", "CWE-120"),
            ("strcat", "HIGH", "CWE-120"),
            ("sprintf", "HIGH", "CWE-120"),
            ("scanf", "MEDIUM", "CWE-120"),
            ("system", "HIGH", "CWE-78"),
            ("popen", "HIGH", "CWE-78"),
        ]

        for func_name, severity, cwe in dangerous_funcs:
            query = f'''
            cpg.call.name("{func_name}")
               .map(c => Map(
                   "code" -> c.code,
                   "file" -> c.file.name.headOption.getOrElse("unknown"),
                   "line" -> c.lineNumber.getOrElse(-1)
               ))
            '''

            result = await executor.execute(query)

            if result.get("success"):
                stdout = result.get("stdout", "")
                import re

                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                clean_output = ansi_escape.sub("", stdout).strip()

                try:
                    calls = json.loads(clean_output)
                    if isinstance(calls, str):
                        calls = json.loads(calls)

                    if calls:
                        call_list = calls if isinstance(calls, list) else [calls]
                        stats["dangerous_functions"] += len(call_list)

                        for call in call_list:
                            all_findings.append(
                                {
                                    "category": "危险函数",
                                    "type": f"使用 {func_name}",
                                    "severity": severity,
                                    "cwe_id": cwe,
                                    "location": {
                                        "file": call.get("file", "unknown"),
                                        "line": call.get("line", -1),
                                        "code": call.get("code", "N/A"),
                                    },
                                }
                            )
                except json.JSONDecodeError:
                    pass

        print(f"✅ 检查了 {len(dangerous_funcs)} 个危险函数")

        # 3. 关键函数调用链分析
        print("\n" + "-" * 70)
        print("📋 阶段 3: 敏感函数调用链分析")
        print("-" * 70)

        sensitive_sinks = ["system", "exec", "popen", "strcpy"]

        for sink in sensitive_sinks:
            result = await callgraph_service.get_callers(sink, depth=3)

            if result.get("success"):
                callers = result.get("callers", [])
                if callers:
                    print(f"   {sink}: 被 {len(callers)} 个函数调用")

        print("✅ 调用链分析完成")

        # 输出报告
        print("\n" + "=" * 70)
        print("                         📊 扫描结果摘要")
        print("=" * 70)

        total_findings = stats["total_vulnerabilities"] + stats["dangerous_functions"]

        print(f"\n📌 总计发现: {total_findings} 个安全问题")
        print(f"   - 污点分析漏洞: {stats['total_vulnerabilities']}")
        print(f"   - 危险函数调用: {stats['dangerous_functions']}")

        print("\n📌 按严重程度分类:")
        print(f"   🔴 CRITICAL: {stats['by_severity'].get('CRITICAL', 0)}")
        print(f"   🟠 HIGH:     {stats['by_severity'].get('HIGH', 0)}")
        print(f"   🟡 MEDIUM:   {stats['by_severity'].get('MEDIUM', 0)}")
        print(f"   🟢 LOW:      {stats['by_severity'].get('LOW', 0)}")

        if stats["by_type"]:
            print("\n📌 按漏洞类型分类:")
            for vuln_type, count in sorted(
                stats["by_type"].items(), key=lambda x: -x[1]
            ):
                print(f"   - {vuln_type}: {count}")

        # 输出详细发现
        if all_findings:
            print("\n" + "=" * 70)
            print("                         📋 详细发现列表")
            print("=" * 70)

            # 按严重程度排序
            severity_order = {
                "CRITICAL": 0,
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
                "UNKNOWN": 4,
            }
            sorted_findings = sorted(
                all_findings,
                key=lambda x: severity_order.get(x.get("severity", "UNKNOWN"), 4),
            )

            for _i, finding in enumerate(sorted_findings[:20], 1):  # 只显示前 20 个
                severity = finding.get("severity", "UNKNOWN")
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                }.get(severity, "⚪")

                print(
                    f"\n{severity_icon} [{severity}] {finding.get('type', 'Unknown')}"
                )
                print(f"   分类: {finding.get('category', 'N/A')}")
                print(f"   CWE: {finding.get('cwe_id', 'N/A')}")

                if "source" in finding and "sink" in finding:
                    source = finding["source"]
                    sink = finding["sink"]
                    print(
                        f"   源: {source.get('code', 'N/A')} ({source.get('file', 'unknown')}:{source.get('line', -1)})"
                    )
                    print(
                        f"   汇: {sink.get('code', 'N/A')} ({sink.get('file', 'unknown')}:{sink.get('line', -1)})"
                    )
                elif "location" in finding:
                    loc = finding["location"]
                    print(
                        f"   位置: {loc.get('file', 'unknown')}:{loc.get('line', -1)}"
                    )
                    print(f"   代码: {loc.get('code', 'N/A')}")

            if len(all_findings) > 20:
                print(f"\n... 还有 {len(all_findings) - 20} 个发现未显示")

        # 扫描耗时
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 70)
        print(f"扫描完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration:.2f} 秒")
        print("=" * 70)

        # 保存报告
        report_file = Path(source_path).parent / f"security_report_{project_name}.json"
        report = {
            "scan_time": start_time.isoformat(),
            "source_path": source_path,
            "project_name": project_name,
            "duration_seconds": duration,
            "statistics": stats,
            "findings": all_findings,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存至: {report_file}")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n🛑 清理扫描环境...")
        await server.stop()
        print("✅ 完成")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("综合安全扫描工具")
        print()
        print("用法: python analyze_all_vulnerabilities.py <源代码路径> [项目名称]")
        print()
        print("示例:")
        print("  python analyze_all_vulnerabilities.py ./vulnerable_c")
        print("  python analyze_all_vulnerabilities.py /path/to/project my_project")
        print()
        print("支持的漏洞类型:")
        print("  - 命令注入 (Command Injection)")
        print("  - SQL 注入 (SQL Injection)")
        print("  - 路径遍历 (Path Traversal)")
        print("  - 跨站脚本 (XSS)")
        print("  - 缓冲区溢出 (Buffer Overflow)")
        print("  - 格式化字符串 (Format String)")
        sys.exit(1)

    source_path = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else "security_scan"

    if not Path(source_path).exists():
        print(f"❌ 路径不存在: {source_path}")
        sys.exit(1)

    asyncio.run(comprehensive_scan(str(Path(source_path).resolve()), project_name))


if __name__ == "__main__":
    main()
