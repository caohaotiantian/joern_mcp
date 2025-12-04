"""结果导出MCP工具

提供分析结果导出功能：
- export_cpg: 导出 CPG 到文件
- export_analysis_results: 导出分析结果

Note:
    export_cpg 会导出当前活动项目的 CPG。
    如需导出特定项目，请先使用 switch_project 切换到该项目。
"""

from pathlib import Path
from typing import Any

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state


@mcp.tool()
async def export_cpg(project_name: str, output_path: str, format: str = "bin") -> dict:
    """
    导出CPG到文件

    Args:
        project_name: 项目名称（用于记录，实际导出当前活动项目的 CPG）
        output_path: 输出文件路径
        format: 导出格式 ("bin", "json", "dot")

    Returns:
        dict: 导出结果

    Example:
        >>> await export_cpg("my-project", "/tmp/cpg.bin", "bin")
        {
            "success": true,
            "project": "my-project",
            "output_path": "/tmp/cpg.bin",
            "format": "bin"
        }

    Note:
        此函数导出当前活动项目的 CPG。
        如需导出特定项目，请先使用 switch_project 切换到该项目。
    """
    if not server_state.query_executor:
        return {"success": False, "error": "Query executor not initialized"}

    logger.info(f"Exporting CPG for project: {project_name}")

    try:
        # 验证输出路径
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 构建导出查询
        if format == "bin":
            query = f'save("{str(output_file)}")'
        elif format == "json":
            query = f'cpg.toJson |> "{str(output_file)}"'
        elif format == "dot":
            query = f'cpg.toDot |> "{str(output_file)}"'
        else:
            return {"success": False, "error": f"Unsupported format: {format}"}

        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            return {
                "success": True,
                "project": project_name,
                "output_path": str(output_file),
                "format": format,
                "message": "CPG exported successfully",
            }
        else:
            return {"success": False, "error": result.get("stderr", "Export failed")}

    except Exception as e:
        logger.exception(f"Error exporting CPG: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def export_analysis_results(
    results: dict[str, Any], output_path: str, format: str = "json"
) -> dict:
    """
    导出分析结果到文件

    Args:
        results: 分析结果数据
        output_path: 输出文件路径
        format: 导出格式 ("json", "markdown", "csv")

    Returns:
        dict: 导出结果

    Example:
        >>> await export_analysis_results(
        ...     {"vulnerabilities": [...]},
        ...     "/tmp/report.json",
        ...     "json"
        ... )
        {
            "success": True,
            "output_path": "/tmp/report.json",
            "format": "json"
        }
    """
    logger.info(f"Exporting analysis results to: {output_path}")

    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            # JSON格式
            import orjson

            content = orjson.dumps(results, option=orjson.OPT_INDENT_2)
            output_file.write_bytes(content)

        elif format == "markdown":
            # Markdown格式
            md_content = _format_as_markdown(results)
            output_file.write_text(md_content, encoding="utf-8")

        elif format == "csv":
            # CSV格式
            csv_content = _format_as_csv(results)
            output_file.write_text(csv_content, encoding="utf-8")

        else:
            return {"success": False, "error": f"Unsupported format: {format}"}

        return {
            "success": True,
            "output_path": str(output_file),
            "format": format,
            "size_bytes": output_file.stat().st_size,
        }

    except Exception as e:
        logger.exception(f"Error exporting results: {e}")
        return {"success": False, "error": str(e)}


def _format_as_markdown(results: dict[str, Any]) -> str:
    """格式化为Markdown"""
    lines = ["# 代码分析报告\n"]

    if "vulnerabilities" in results:
        lines.append("## 发现的漏洞\n")
        for i, vuln in enumerate(results["vulnerabilities"], 1):
            lines.append(f"### {i}. {vuln.get('vulnerability', 'Unknown')}")
            lines.append(f"- **严重程度**: {vuln.get('severity', 'Unknown')}")
            lines.append(f"- **CWE**: {vuln.get('cwe_id', 'N/A')}")

            if "source" in vuln:
                src = vuln["source"]
                lines.append(f"- **源**: {src.get('file', '')}:{src.get('line', '')}")
                lines.append(f"  - 代码: `{src.get('code', '')}`")

            if "sink" in vuln:
                sink = vuln["sink"]
                lines.append(f"- **汇**: {sink.get('file', '')}:{sink.get('line', '')}")
                lines.append(f"  - 代码: `{sink.get('code', '')}`")

            lines.append("")

    if "summary" in results:
        lines.append("## 统计摘要\n")
        for severity, count in results["summary"].items():
            lines.append(f"- **{severity}**: {count}")
        lines.append("")

    return "\n".join(lines)


def _format_as_csv(results: dict[str, Any]) -> str:
    """格式化为CSV"""
    lines = [
        "Type,Severity,CWE,Source_File,Source_Line,Source_Code,Sink_File,Sink_Line,Sink_Code"
    ]

    if "vulnerabilities" in results:
        for vuln in results["vulnerabilities"]:
            row = [
                vuln.get("vulnerability", ""),
                vuln.get("severity", ""),
                vuln.get("cwe_id", ""),
                vuln.get("source", {}).get("file", ""),
                str(vuln.get("source", {}).get("line", "")),
                vuln.get("source", {}).get("code", "").replace('"', '""'),
                vuln.get("sink", {}).get("file", ""),
                str(vuln.get("sink", {}).get("line", "")),
                vuln.get("sink", {}).get("code", "").replace('"', '""'),
            ]
            lines.append(",".join(f'"{v}"' for v in row))

    return "\n".join(lines)
