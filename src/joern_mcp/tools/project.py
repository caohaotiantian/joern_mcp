"""项目管理MCP工具"""

import asyncio
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
        # 导入代码
        result = await asyncio.to_thread(
            server_state.joern_server.import_code, str(path.absolute()), project_name
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
        dict: 项目列表

    Example:
        >>> await list_projects()
        {
            "success": True,
            "projects": ["project1", "project2"],
            "count": 2
        }
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # 执行workspace查询
        from cpgqls_client import workspace_query

        query = workspace_query()
        result = server_state.joern_server.execute_query(query)

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
        # Joern的close命令
        query = f'close("{project_name}")'
        result = server_state.joern_server.execute_query(query)

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
