"""项目管理MCP工具

提供 CPG 项目管理功能：
- parse_project: 解析代码生成 CPG
- list_projects: 列出已解析的项目
- switch_project: 切换当前活动项目
- get_current_project: 获取当前活动项目
- delete_project: 删除项目

多项目支持：
- Joern 支持同时加载多个项目到 workspace
- 使用 switch_project 切换当前活动项目
- 所有查询默认针对当前活动项目，也可指定 project_name 参数

所有与 Joern Server 的交互都通过异步 HTTP+WebSocket 方式进行。
"""

from pathlib import Path

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.response_parser import safe_parse_joern_response


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
async def switch_project(project_name: str) -> dict:
    """
    切换当前活动项目

    在 Joern 中，所有不指定项目的查询都针对"当前活动项目"。
    使用此工具切换到指定项目后，后续查询将默认针对该项目。

    Args:
        project_name: 要切换到的项目名称

    Returns:
        dict: 切换结果

    Example:
        >>> await switch_project("my-webapp")
        {
            "success": true,
            "project_name": "my-webapp",
            "message": "Switched to project: my-webapp"
        }

    Note:
        - 项目必须先通过 parse_project 导入
        - 使用 list_projects 查看可用项目
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    logger.info(f"Switching to project: {project_name}")

    try:
        # Joern 的 open 命令切换当前项目
        query = f'open("{project_name}")'
        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            logger.info(f"Switched to project: {project_name}")
            return {
                "success": True,
                "project_name": project_name,
                "message": f"Switched to project: {project_name}",
            }
        else:
            error_msg = result.get("stderr", "Failed to switch project")
            logger.error(f"Failed to switch project: {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        logger.exception(f"Error switching project: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_current_project() -> dict:
    """
    获取当前活动项目信息

    Returns:
        dict: 当前项目信息，包含名称和统计数据

    Example:
        >>> await get_current_project()
        {
            "success": true,
            "project": {
                "name": "my-webapp",
                "inputPath": "/path/to/source",
                "methodCount": 150,
                "fileCount": 25
            }
        }
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # 使用更简单的查询获取当前项目信息
        # 先获取当前 CPG 的 root 路径
        root_query = "cpg.metaData.root.headOption.getOrElse(\"\")"
        root_result = await server_state.joern_server.execute_query_async(root_query)

        if not root_result.get("success"):
            return {
                "success": False,
                "error": "No active project. Use parse_project to import a project first.",
            }

        current_root = safe_parse_joern_response(
            root_result.get("stdout", ""), default=""
        )

        if not current_root:
            return {
                "success": False,
                "error": "No active project. Use parse_project to import a project first.",
            }

        # 获取项目统计信息
        stats_query = """
        {
            val methods = cpg.method.size
            val files = cpg.file.size
            s"${methods},${files}"
        }
        """
        stats_result = await server_state.joern_server.execute_query_async(stats_query)

        method_count = 0
        file_count = 0

        if stats_result.get("success"):
            stats_str = safe_parse_joern_response(
                stats_result.get("stdout", ""), default=""
            )
            if isinstance(stats_str, str) and "," in stats_str:
                parts = stats_str.split(",")
                try:
                    method_count = int(parts[0])
                    file_count = int(parts[1])
                except (ValueError, IndexError):
                    pass

        # 查找匹配的项目名称
        projects_query = 'workspace.projects.map(p => s"${p.name}:::${p.inputPath}").l'
        projects_result = await server_state.joern_server.execute_query_async(
            projects_query
        )

        project_name = "unknown"
        input_path = current_root

        if projects_result.get("success"):
            projects = safe_parse_joern_response(
                projects_result.get("stdout", ""), default=[]
            )
            for p_str in projects:
                if isinstance(p_str, str) and ":::" in p_str:
                    parts = p_str.split(":::", 1)
                    if len(parts) == 2 and parts[1] == current_root:
                        project_name = parts[0]
                        input_path = parts[1]
                        break

        return {
            "success": True,
            "project": {
                "name": project_name,
                "inputPath": input_path,
                "methodCount": method_count,
                "fileCount": file_count,
            },
        }

    except Exception as e:
        logger.exception(f"Error getting current project: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_projects() -> dict:
    """
    列出所有已解析的项目

    Returns:
        dict: 项目列表和详细信息

    Example:
        >>> await list_projects()
        {
            "success": true,
            "projects": [
                {
                    "name": "webapp",
                    "inputPath": "/path/to/webapp",
                    "isActive": true
                },
                {
                    "name": "library",
                    "inputPath": "/path/to/library",
                    "isActive": false
                }
            ],
            "count": 2,
            "activeProject": "webapp"
        }

    Note:
        - isActive 表示该项目是否为当前活动项目
        - 使用 switch_project 切换活动项目
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # 首先获取当前活动 CPG 的路径
        root_query = "cpg.metaData.root.headOption.getOrElse(\"\")"
        root_result = await server_state.joern_server.execute_query_async(root_query)
        current_root = ""
        if root_result.get("success"):
            current_root = safe_parse_joern_response(
                root_result.get("stdout", ""), default=""
            )

        # 获取项目列表（使用简单格式避免复杂 Scala 语法）
        query = 'workspace.projects.map(p => s"${p.name}:::${p.inputPath}").l'
        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            stdout = result.get("stdout", "")
            raw_projects = safe_parse_joern_response(stdout, default=[])

            if not isinstance(raw_projects, list):
                raw_projects = [raw_projects] if raw_projects else []

            # 解析项目列表
            projects = []
            active_project = None

            for p_str in raw_projects:
                if isinstance(p_str, str) and ":::" in p_str:
                    parts = p_str.split(":::", 1)
                    if len(parts) == 2:
                        name = parts[0]
                        input_path = parts[1]
                        is_active = input_path == current_root

                        projects.append(
                            {
                                "name": name,
                                "inputPath": input_path,
                                "isActive": is_active,
                            }
                        )

                        if is_active:
                            active_project = name

            logger.info(f"Found {len(projects)} projects, active: {active_project}")
            return {
                "success": True,
                "projects": projects,
                "count": len(projects),
                "activeProject": active_project,
            }
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
