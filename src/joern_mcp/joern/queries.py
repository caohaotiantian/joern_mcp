"""Joern 查询辅助函数

参考官方实现: https://github.com/joernio/cpgqls-client-python/blob/master/cpgqls_client/queries.py

提供常用的 Joern 查询构建函数，避免在代码中重复构建查询字符串。
"""


def import_code_query(
    path: str, project_name: str | None = None, language: str | None = None
) -> str:
    """构建 importCode 查询

    Args:
        path: 代码路径
        project_name: 项目名称（可选）
        language: 编程语言（可选）

    Returns:
        importCode 查询字符串

    Example:
        >>> import_code_query("/path/to/code", "my-project", "c")
        'importCode(inputPath="/path/to/code", projectName="my-project", language="c")'
    """
    if not path:
        raise ValueError("An importCode query requires a project path")

    if project_name and language:
        return f'importCode(inputPath="{path}", projectName="{project_name}", language="{language}")'
    if project_name:
        return f'importCode(inputPath="{path}", projectName="{project_name}")'
    return f'importCode("{path}")'


def open_query(project_name: str) -> str:
    """构建 open 查询（切换/打开项目）

    Args:
        project_name: 项目名称

    Returns:
        open 查询字符串
    """
    return f'open("{project_name}")'


def close_query(project_name: str) -> str:
    """构建 close 查询（关闭项目）

    Args:
        project_name: 项目名称

    Returns:
        close 查询字符串
    """
    return f'close("{project_name}")'


def delete_query(project_name: str) -> str:
    """构建 delete 查询（删除项目）

    Args:
        project_name: 项目名称

    Returns:
        delete 查询字符串
    """
    return f'delete("{project_name}")'


def workspace_query() -> str:
    """构建 workspace 查询"""
    return "workspace"


def project_query() -> str:
    """构建 project 查询（获取当前项目）"""
    return "project"


def help_query() -> str:
    """构建 help 查询"""
    return "help"


# ===== 扩展查询（官方未提供，但常用）=====


def list_projects_query() -> str:
    """列出所有项目

    Returns:
        查询字符串，返回项目名称和路径列表（JSON 格式）
    """
    return 'workspace.projects.map(p => Map("name" -> p.name, "path" -> p.inputPath))'


def cpg_root_query() -> str:
    """获取当前 CPG 的根路径"""
    return 'cpg.metaData.root.headOption.getOrElse("")'


def method_count_query() -> str:
    """获取方法数量"""
    return "cpg.method.size"


def file_count_query() -> str:
    """获取文件数量"""
    return "cpg.file.size"


def list_methods_query(limit: int = 100, name_filter: str | None = None) -> str:
    """列出方法

    Args:
        limit: 返回数量限制
        name_filter: 名称过滤（正则表达式）

    Returns:
        查询字符串
    """
    if name_filter:
        return f"""cpg.method.name(".*{name_filter}.*")
           .take({limit})
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))"""
    return f"""cpg.method
           .take({limit})
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))"""


def get_function_query(function_name: str) -> str:
    """获取函数详情

    Args:
        function_name: 函数名称

    Returns:
        查询字符串
    """
    return f'''cpg.method.name("{function_name}")
           .map(m => Map(
               "name" -> m.name,
               "signature" -> m.signature,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1),
               "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
               "code" -> m.code
           ))'''


def get_callers_query(function_name: str) -> str:
    """获取函数调用者

    使用 .callIn 获取调用节点，而非 .caller 获取方法定义。
    .callIn 返回调用当前方法的 Call 节点，包含调用点的位置信息。
    .caller 返回调用者的方法定义，但缺少具体调用位置。

    参考: https://docs.joern.io/cpgql/calls/

    Args:
        function_name: 函数名称
        depth: 调用深度（保留参数，当前只支持1层）

    Returns:
        查询字符串
    """
    # 注意：depth 参数保留但当前只支持单层调用
    # 多层调用应通过递归方式实现
    return f'''cpg.method.name("{function_name}")
           .callIn
           .map(c => Map(
               "name" -> c.method.name,
               "methodFullName" -> c.method.fullName,
               "signature" -> c.method.signature,
               "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
               "lineNumber" -> c.lineNumber.getOrElse(-1),
               "code" -> c.code
           ))
           .dedup'''


def get_callees_query(function_name: str) -> str:
    """获取函数调用的其他函数

    使用 .call 获取调用节点，而非 .callee 获取方法定义。
    .call 返回函数内的所有调用点，包含调用位置信息（文件名、行号、代码）。
    .callee 返回被调用方法的定义，但外部库函数通常没有完整定义信息。

    参考: https://docs.joern.io/cpgql/calls/

    Args:
        function_name: 函数名称
        depth: 调用深度（保留参数，当前只支持1层）

    Returns:
        查询字符串
    """
    # 注意：depth 参数保留但当前只支持单层调用
    # 多层调用应通过递归方式实现
    return f'''cpg.method.name("{function_name}")
           .call
           .filterNot(_.name == "<operator>.*")
           .map(c => Map(
               "name" -> c.name,
               "methodFullName" -> c.methodFullName,
               "signature" -> c.signature,
               "filename" -> c.file.name.headOption.getOrElse("<unknown>"),
               "lineNumber" -> c.lineNumber.getOrElse(-1),
               "code" -> c.code
           ))
           .dedup'''


def get_cfg_query(function_name: str) -> str:
    """获取控制流图（DOT 格式）

    Args:
        function_name: 函数名称

    Returns:
        查询字符串
    """
    return f'cpg.method.name("{function_name}").dotCfg.head'


def get_dominators_query(function_name: str) -> str:
    """获取支配树（DOT 格式）

    Args:
        function_name: 函数名称

    Returns:
        查询字符串
    """
    return f'cpg.method.name("{function_name}").dotDom.head'


def search_code_query(pattern: str, scope: str = "all", limit: int = 50) -> str:
    """搜索代码

    Args:
        pattern: 搜索模式（正则表达式）
        scope: 搜索范围 (all, methods, calls, identifiers)
        limit: 返回数量限制

    Returns:
        查询字符串
    """
    if scope == "methods":
        base = f'cpg.method.name(".*{pattern}.*")'
    elif scope == "calls":
        base = f'cpg.call.name(".*{pattern}.*")'
    elif scope == "identifiers":
        base = f'cpg.identifier.name(".*{pattern}.*")'
    else:
        base = f'cpg.all.code(".*{pattern}.*")'

    return f"""{base}.take({limit}).map(n => Map(
            "code" -> n.code,
            "type" -> n.label,
            "file" -> n.file.name.headOption.getOrElse("unknown"),
            "line" -> n.lineNumber.getOrElse(-1)
        ))"""
