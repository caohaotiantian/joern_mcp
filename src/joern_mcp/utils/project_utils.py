"""项目操作辅助函数

提供多项目管理的安全辅助函数：
- 验证项目存在性
- 安全获取项目 CPG
- 构建安全的查询前缀
"""

from loguru import logger


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
            # 解析布尔值结果
            if "true" in stdout.lower():
                return True, None
            else:
                return False, f"Project '{project_name}' not found in workspace"
        else:
            return False, f"Failed to check project: {result.get('stderr', 'Unknown error')}"
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

        # 检查项目是否有 CPG
        query = f'workspace.project("{project_name}").flatMap(_.cpg).isDefined'
        result = await query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            if "true" in stdout.lower():
                return True, None
            else:
                return False, f"Project '{project_name}' has no CPG loaded. Use switch_project to load it first."
        else:
            return False, f"Failed to check CPG: {result.get('stderr', 'Unknown error')}"
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
    query_executor, project_name: str | None
) -> tuple[str | None, str | None]:
    """安全地获取 CPG 访问前缀

    此函数会先验证项目存在性，然后返回前缀。

    Args:
        query_executor: 查询执行器
        project_name: 项目名称（可选）

    Returns:
        tuple: (前缀, 错误消息)
            - (prefix, None) 如果成功
            - (None, error_message) 如果失败
    """
    if not project_name:
        return "cpg", None

    # 验证项目和 CPG
    has_cpg, error = await validate_project_has_cpg(query_executor, project_name)
    if not has_cpg:
        return None, error

    return f'workspace.project("{project_name}").get.cpg.get', None

