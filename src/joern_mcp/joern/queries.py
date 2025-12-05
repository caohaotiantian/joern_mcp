"""Joern 查询辅助函数

参考官方实现: https://github.com/joernio/cpgqls-client-python/blob/master/cpgqls_client/queries.py

提供常用的 Joern 查询构建函数，避免在代码中重复构建查询字符串。
"""


def import_code_query(path: str, project_name: str | None = None, language: str | None = None) -> str:
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
        查询字符串，返回项目名称和路径列表
    """
    return 'workspace.projects.map(p => s"${p.name}:::${p.inputPath}").l'


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
        return f'''cpg.method.name(".*{name_filter}.*")
           .take({limit})
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))'''
    return f'''cpg.method
           .take({limit})
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))'''


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


def get_callers_query(function_name: str, depth: int = 1) -> str:
    """获取函数调用者

    根据 Joern 文档 (https://docs.joern.io/cpgql/complex-steps/)
    使用 .caller 链式调用获取调用者

    Args:
        function_name: 函数名称
        depth: 调用深度（最大 5）

    Returns:
        查询字符串
    """
    depth = min(depth, 5)  # 限制最大深度
    caller_chain = ".caller" * depth
    return f'''cpg.method.name("{function_name}")
           {caller_chain}
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))'''


def get_callees_query(function_name: str, depth: int = 1) -> str:
    """获取函数被调用者

    根据 Joern 文档 (https://docs.joern.io/cpgql/complex-steps/)
    使用 .callee 链式调用获取被调用者

    Args:
        function_name: 函数名称
        depth: 调用深度（最大 5）

    Returns:
        查询字符串
    """
    depth = min(depth, 5)  # 限制最大深度
    callee_chain = ".callee" * depth
    return f'''cpg.method.name("{function_name}")
           {callee_chain}
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))'''


def get_cfg_query(function_name: str) -> str:
    """获取控制流图（DOT 格式）

    Args:
        function_name: 函数名称

    Returns:
        查询字符串
    """
    return f'cpg.method.name("{function_name}").dotCfg.l'


def get_dominators_query(function_name: str) -> str:
    """获取支配树（DOT 格式）

    Args:
        function_name: 函数名称

    Returns:
        查询字符串
    """
    return f'cpg.method.name("{function_name}").dotDom.l'


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

    return f'''{base}.take({limit}).map(n => Map(
            "code" -> n.code,
            "type" -> n.label,
            "file" -> n.file.name.headOption.getOrElse("unknown"),
            "line" -> n.lineNumber.getOrElse(-1)
        ))'''

