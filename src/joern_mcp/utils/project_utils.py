"""项目操作辅助函数

提供多项目管理的安全辅助函数：
- 验证项目存在性
- 安全获取项目 CPG
- 构建安全的查询前缀
"""

import re

from loguru import logger


def _parse_boolean_result(stdout: str) -> bool | None:
    """解析 Joern 返回的布尔值结果

    Joern 返回格式可能是：
    - "true" 或 "false"
    - "val res0: Boolean = true"
    - "res0: Boolean = false"

    Args:
        stdout: Joern 输出

    Returns:
        True, False, 或 None（无法解析）
    """
    if not stdout:
        return None

    clean = stdout.strip().lower()

    # 直接是 true/false
    if clean == "true":
        return True
    if clean == "false":
        return False

    # 从 "val res0: Boolean = true" 格式提取
    match = re.search(r'=\s*(true|false)', clean)
    if match:
        return match.group(1) == "true"

    # 检查是否包含 true/false（最后的手段）
    if "true" in clean and "false" not in clean:
        return True
    if "false" in clean and "true" not in clean:
        return False

    return None


async def list_available_projects(query_executor) -> list[str]:
    """列出所有可用的项目名称

    Args:
        query_executor: 查询执行器

    Returns:
        项目名称列表
    """
    try:
        query = 'workspace.projects.map(_.name).l'
        result = await query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            # 解析 List("name1", "name2") 格式
            list_match = re.search(r'List\s*\((.*)\)', stdout, re.DOTALL)
            if list_match:
                content = list_match.group(1)
                # 提取引号内的字符串
                names = re.findall(r'"([^"]*)"', content)
                return names
        return []
    except Exception as e:
        logger.debug(f"Failed to list projects: {e}")
        return []


async def validate_project_exists(query_executor, project_name: str) -> tuple[bool, str | None]:
    """验证项目是否存在

    Args:
        query_executor: 查询执行器
        project_name: 项目名称

    Returns:
        tuple: (存在, 错误消息)
            - (True, None) 如果项目存在
            - (False, error_message) 如果项目不存在
    """
    try:
        query = f'workspace.project("{project_name}").isDefined'
        result = await query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            is_defined = _parse_boolean_result(stdout)

            if is_defined is True:
                return True, None
            elif is_defined is False:
                # 获取可用项目列表，提供更好的错误提示
                available = await list_available_projects(query_executor)
                if available:
                    return False, (
                        f"Project '{project_name}' not found in workspace. "
                        f"Available projects: {', '.join(available)}"
                    )
                else:
                    return False, (
                        f"Project '{project_name}' not found in workspace. "
                        f"No projects available. Use parse_project to import a project first."
                    )
            else:
                # 无法解析结果，记录警告
                logger.warning(f"Cannot parse isDefined result: {stdout}")
                return False, f"Cannot determine if project '{project_name}' exists. Raw output: {stdout[:100]}"
        else:
            stderr = result.get("stderr", "Unknown error")
            # 检查是否是编译错误（项目不存在导致的）
            if "Not Found Error" in stderr or "not a member" in stderr:
                return False, f"Project '{project_name}' not found in workspace"
            return False, f"Failed to check project: {stderr}"
    except Exception as e:
        logger.exception(f"Error validating project: {e}")
        return False, str(e)


async def validate_project_has_cpg(query_executor, project_name: str) -> tuple[bool, str | None]:
    """验证项目是否已加载 CPG

    Args:
        query_executor: 查询执行器
        project_name: 项目名称

    Returns:
        tuple: (有CPG, 错误消息)
    """
    try:
        # 先检查项目是否存在
        exists, error = await validate_project_exists(query_executor, project_name)
        if not exists:
            return False, error

        # 简化验证：直接尝试一个简单的 CPG 查询
        # 如果查询成功，说明 CPG 已加载；如果失败，说明 CPG 未加载
        # 使用 method.size 因为它快速且可靠
        query = f'workspace.project("{project_name}").get.cpg.get.method.size'
        result = await query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            # 如果输出包含数字（包括 0），说明 CPG 已加载
            if re.search(r'\d+', stdout):
                return True, None
            # 如果输出不包含数字但查询成功，可能是空 CPG（仍然算已加载）
            logger.debug(f"CPG query returned non-numeric: {stdout}")
            return True, None

        # 查询失败，检查具体错误
        stderr = result.get("stderr", "")

        # "None.get" 错误表示 Option 为空（项目或 CPG 不存在）
        if "None.get" in stderr or "NoSuchElementException" in stderr:
            # 项目存在但 CPG 未加载，尝试加载它
            # 注意：不要返回错误，而是直接尝试用 open 加载
            logger.info(f"CPG for project '{project_name}' not loaded, attempting to load...")

            # 使用 open 命令加载 CPG
            open_query = f'open("{project_name}")'
            open_result = await query_executor.execute(open_query, format="raw")

            if open_result.get("success"):
                # 再次验证 CPG 是否加载成功
                verify_result = await query_executor.execute(query, format="raw")
                if verify_result.get("success"):
                    stdout = verify_result.get("stdout", "").strip()
                    if re.search(r'\d+', stdout):
                        logger.info(f"Successfully loaded CPG for project '{project_name}'")
                        return True, None

            # 加载失败
            return False, (
                f"Project '{project_name}' exists but CPG could not be loaded. "
                f"Try using switch_project('{project_name}') first."
            )

        # 其他错误
        return False, f"Failed to access CPG for project '{project_name}': {stderr[:200]}"

    except Exception as e:
        logger.exception(f"Error validating CPG: {e}")
        return False, str(e)


def get_cpg_prefix(project_name: str | None) -> str:
    """获取 CPG 访问前缀

    Args:
        project_name: 项目名称（可选）

    Returns:
        str: CPG 访问语句前缀

    Note:
        workspace.project() 返回 Option[Project]，需要先 .get 获取 Project，
        然后 Project.cpg 返回 Option[Cpg]，再 .get 获取 Cpg。

        调用方应该在使用此前缀之前先调用 validate_project_has_cpg() 验证项目存在性。
    """
    if project_name:
        return f'workspace.project("{project_name}").get.cpg.get'
    return "cpg"


async def get_safe_cpg_prefix(
    query_executor, project_name: str
) -> tuple[str | None, str | None]:
    """安全地获取 CPG 访问前缀

    此函数会先验证项目存在性，然后返回前缀。

    Args:
        query_executor: 查询执行器
        project_name: 项目名称（必填）

    Returns:
        tuple: (前缀, 错误消息)
            - (prefix, None) 如果成功
            - (None, error_message) 如果失败
    """
    if not project_name:
        return None, "project_name is required. Use list_projects to see available projects."

    # 验证项目和 CPG
    has_cpg, error = await validate_project_has_cpg(query_executor, project_name)
    if not has_cpg:
        return None, error

    return f'workspace.project("{project_name}").get.cpg.get', None

