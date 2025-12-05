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

import re
from pathlib import Path

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state
from joern_mcp.utils.response_parser import safe_parse_joern_response


def _parse_int_from_output(stdout: str) -> int:
    """从 Joern 输出中解析整数值

    Joern 返回的格式可能包括：
    - 直接数字: "123"
    - Scala REPL 格式: "val res1: Int = 123"
    - 带类型: "res1: Int = 123"

    Args:
        stdout: Joern 输出

    Returns:
        解析出的整数，解析失败返回 0
    """
    if not stdout:
        return 0

    clean = stdout.strip()

    # 尝试直接解析数字
    if clean.isdigit():
        return int(clean)

    # 尝试从 "val res1: Int = 123" 格式提取
    # 或 "res1: Int = 123" 格式
    match = re.search(r'=\s*(\d+)', clean)
    if match:
        return int(match.group(1))

    # 尝试查找任何数字
    numbers = re.findall(r'\b(\d+)\b', clean)
    if numbers:
        # 返回最后一个数字（通常是结果值）
        return int(numbers[-1])

    return 0


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

        # 获取项目统计信息 - 分开查询更可靠
        method_count = 0
        file_count = 0

        # 获取方法数量
        method_query = "cpg.method.size"
        method_result = await server_state.joern_server.execute_query_async(method_query)
        if method_result.get("success"):
            method_stdout = method_result.get("stdout", "").strip()
            method_count = _parse_int_from_output(method_stdout)

        # 获取文件数量
        file_query = "cpg.file.size"
        file_result = await server_state.joern_server.execute_query_async(file_query)
        if file_result.get("success"):
            file_stdout = file_result.get("stdout", "").strip()
            file_count = _parse_int_from_output(file_stdout)

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
async def delete_project(project_name: str, permanent: bool = True) -> dict:
    """
    删除指定项目的CPG

    Args:
        project_name: 要删除的项目名称
        permanent: 是否永久删除（包括磁盘数据）
                   True: 使用 delete() 彻底删除
                   False: 使用 close() 仅关闭项目

    Returns:
        dict: 删除结果

    Example:
        >>> await delete_project("my-app")
        {"success": True, "message": "Project deleted permanently"}

    Note:
        - permanent=True（默认）: 使用 Joern 的 delete() 命令，
          彻底删除项目及其在磁盘上的数据
        - permanent=False: 使用 Joern 的 close() 命令，
          仅关闭项目，数据保留在 workspace 中
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        if permanent:
            # 使用 delete 命令彻底删除项目（包括磁盘数据）
            query = f'delete("{project_name}")'
            action = "deleted permanently"
        else:
            # 使用 close 命令仅关闭项目
            query = f'close("{project_name}")'
            action = "closed"

        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            logger.info(f"Project {project_name} {action}")
            return {
                "success": True,
                "project_name": project_name,
                "message": f"Project {action} successfully",
                "permanent": permanent,
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", f"Failed to {action.split()[0]} project"),
            }

    except Exception as e:
        logger.exception(f"Error deleting project: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def cleanup_inactive_projects(keep_active: bool = True) -> dict:
    """
    清理所有非活跃项目

    这个工具用于批量删除 workspace 中的非活跃项目，
    释放磁盘空间并保持 workspace 整洁。

    Args:
        keep_active: 是否保留当前活跃项目（默认 True）

    Returns:
        dict: 清理结果，包含删除的项目列表

    Example:
        >>> await cleanup_inactive_projects()
        {
            "success": true,
            "deleted": ["old-project-1", "old-project-2"],
            "kept": ["current-project"],
            "deleted_count": 2
        }

    Warning:
        此操作不可逆！删除的项目数据将永久丢失。
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        # 首先获取当前活动项目
        root_query = "cpg.metaData.root.headOption.getOrElse(\"\")"
        root_result = await server_state.joern_server.execute_query_async(root_query)
        current_root = ""
        if root_result.get("success"):
            current_root = safe_parse_joern_response(
                root_result.get("stdout", ""), default=""
            )

        # 获取所有项目
        projects_query = 'workspace.projects.map(p => s"${p.name}:::${p.inputPath}").l'
        projects_result = await server_state.joern_server.execute_query_async(projects_query)

        if not projects_result.get("success"):
            return {
                "success": False,
                "error": projects_result.get("stderr", "Failed to list projects"),
            }

        raw_projects = safe_parse_joern_response(
            projects_result.get("stdout", ""), default=[]
        )

        if not isinstance(raw_projects, list):
            raw_projects = [raw_projects] if raw_projects else []

        deleted = []
        kept = []
        errors = []

        for p_str in raw_projects:
            if not isinstance(p_str, str) or ":::" not in p_str:
                continue

            parts = p_str.split(":::", 1)
            if len(parts) != 2:
                continue

            name = parts[0]
            input_path = parts[1]
            is_active = input_path == current_root

            if is_active and keep_active:
                kept.append(name)
                continue

            # 删除非活跃项目
            delete_query = f'delete("{name}")'
            delete_result = await server_state.joern_server.execute_query_async(delete_query)

            if delete_result.get("success"):
                deleted.append(name)
                logger.info(f"Deleted inactive project: {name}")
            else:
                errors.append({
                    "name": name,
                    "error": delete_result.get("stderr", "Unknown error"),
                })
                logger.warning(f"Failed to delete project {name}: {delete_result.get('stderr')}")

        return {
            "success": True,
            "deleted": deleted,
            "kept": kept,
            "deleted_count": len(deleted),
            "kept_count": len(kept),
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.exception(f"Error cleaning up projects: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def close_project(project_name: str) -> dict:
    """
    关闭指定项目（不删除数据）

    与 delete_project 不同，close_project 只是关闭项目，
    数据仍然保留在 workspace 中，可以稍后重新打开。

    Args:
        project_name: 要关闭的项目名称

    Returns:
        dict: 关闭结果

    Example:
        >>> await close_project("my-app")
        {"success": True, "message": "Project closed"}

    Note:
        使用 switch_project 或 parse_project 可以重新打开已关闭的项目。
    """
    if not server_state.joern_server:
        return {"success": False, "error": "Joern server not initialized"}

    try:
        query = f'close("{project_name}")'
        result = await server_state.joern_server.execute_query_async(query)

        if result.get("success"):
            logger.info(f"Project {project_name} closed")
            return {
                "success": True,
                "project_name": project_name,
                "message": "Project closed successfully",
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to close project"),
            }

    except Exception as e:
        logger.exception(f"Error closing project: {e}")
        return {"success": False, "error": str(e)}
