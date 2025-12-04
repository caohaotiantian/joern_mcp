"""项目管理MCP工具

提供 CPG 项目管理功能：
- parse_project: 解析代码生成 CPG
- list_projects: 列出已解析的项目
- delete_project: 删除项目

所有与 Joern Server 的交互都通过异步 HTTP+WebSocket 方式进行。
Joern Server 返回 JSON 格式：{"success": true, "uuid": "...", "stdout": "查询结果"}
stdout 字段包含查询的实际输出（已清理 ANSI 颜色码）。
"""

from pathlib import Path

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state


@mcp.tool()
async def parse_project(
    source_path: str, project_name: str | None = None, language: str = "auto"
) -> dict:
    """
    解析代码项目生成CPG

    Args:
        source_path: 源代码路径（绝对路径或相对路径）
        project_name: 项目名称（可选，默认使用目录名）
        language: 编程语言 (auto, c, java, javascript, python, kotlin)

    Returns:
        dict: 解析结果，包含项目ID和状态

    Example:
        >>> await parse_project("/path/to/project", "my-app", "java")
        {
            "success": True,
            "project_name": "my-app",
            "message": "Project parsed successfully"
        }
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    logger.info(f"Parsing project: {source_path}")

    # 验证路径
    path = Path(source_path)
    if not path.exists():
        return {"success": False, "error": f"Path does not exist: {source_path}"}

    # 生成项目名称
    if not project_name:
        project_name = path.name

    try:
        # 导入代码（使用异步方法）
        result = await server_state.joern_server.import_code(
            str(path.absolute()), project_name
        )

        if result.get("success"):
            logger.info(f"Project {project_name} parsed successfully")
            return {
                "success": True,
                "project_name": project_name,
                "source_path": str(path.absolute()),
                "language": language,
                "message": "Project parsed successfully",
                "output": result.get("stdout", ""),
            }
        else:
            logger.error(f"Failed to parse project: {result.get('stderr')}")
            return {"success": False, "error": result.get("stderr", "Unknown error")}

    except Exception as e:
        logger.exception(f"Error parsing project: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_projects() -> dict:
    """
    列出所有已解析的项目

    Returns:
        dict: 工作空间信息

    Example:
        >>> await list_projects()
        {
            "success": True,
            "workspace_info": "WorkspaceManager(<project1>, <project2>)",
            "raw_output": {...}
        }

    Note:
        workspace_info 包含 Joern 工作空间的文本表示。
        如需结构化项目列表，请使用 project://list 资源。
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # 执行workspace查询（使用异步方法）
        query = "workspace"
        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            # 解析workspace输出
            stdout = result.get("stdout", "")
            logger.info(f"Workspace query result: {stdout}")
            return {"success": True, "workspace_info": stdout, "raw_output": result}
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to get workspace"),
            }

    except Exception as e:
        logger.exception(f"Error listing projects: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_project(project_name: str) -> dict:
    """
    删除指定项目的CPG

    Args:
        project_name: 要删除的项目名称

    Returns:
        dict: 删除结果

    Example:
        >>> await delete_project("my-app")
        {"success": True, "message": "Project deleted"}
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # Joern的close命令（使用异步方法）
        query = f'close("{project_name}")'
        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            logger.info(f"Project {project_name} deleted")
            return {
                "success": True,
                "project_name": project_name,
                "message": "Project deleted successfully",
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to delete project"),
            }

    except Exception as e:
        logger.exception(f"Error deleting project: {e}")
        return {"success": False, "error": str(e)}
