# Joern MCP Server 开发计划（第2-8周）

## 第二周：MCP基础设施和项目管理工具

### Day 6-7: FastMCP集成

#### 任务 2.1: MCP服务器基础

**目标**: 搭建FastMCP服务器框架

**文件**: `src/joern_mcp/server.py`

**代码**:
```python
"""MCP服务器主入口"""
import asyncio
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from loguru import logger
from joern_mcp.config import settings
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor


# 全局状态
class ServerState:
    joern_server: JoernServerManager = None
    query_executor: QueryExecutor = None


@asynccontextmanager
async def lifespan(app: FastMCP):
    """应用生命周期管理"""
    logger.info("Starting Joern MCP Server...")
    
    # 启动Joern Server
    ServerState.joern_server = JoernServerManager()
    await ServerState.joern_server.start()
    
    # 初始化查询执行器
    ServerState.query_executor = QueryExecutor(ServerState.joern_server)
    
    logger.info("Joern MCP Server started successfully")
    
    yield
    
    # 清理
    logger.info("Stopping Joern MCP Server...")
    await ServerState.joern_server.stop()
    logger.info("Joern MCP Server stopped")


# 创建MCP应用
mcp = FastMCP(
    "Joern Code Analysis",
    lifespan=lifespan
)


# 健康检查端点
@mcp.tool()
async def health_check() -> dict:
    """检查服务器健康状态"""
    is_healthy = await ServerState.joern_server.health_check()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "joern_endpoint": ServerState.joern_server.endpoint
    }


def main():
    """主函数"""
    import sys
    logger.info("Starting Joern MCP Server")
    logger.info(f"Joern Server: {settings.joern_server_host}:{settings.joern_server_port}")
    
    # 运行MCP服务器
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**测试**: `tests/test_server.py`
```python
import pytest
from joern_mcp.server import mcp, ServerState


@pytest.mark.asyncio
async def test_server_initialization():
    """测试服务器初始化"""
    # 这个测试需要在集成测试环境中运行
    pass


def test_health_check_tool_registered():
    """测试健康检查工具已注册"""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "health_check" in tool_names
```

**验收标准**:
```bash
pytest tests/test_server.py -v

# 运行服务器（不会退出，Ctrl+C停止）
python -m joern_mcp.server
```

**时间**: 4小时

---

#### 任务 2.2: 项目管理工具 - 解析项目

**目标**: 实现项目解析和CPG生成

**文件**: `src/joern_mcp/tools/project.py`

**代码**:
```python
"""项目管理MCP工具"""
import json
from pathlib import Path
from typing import Optional
from loguru import logger
from joern_mcp.server import mcp, ServerState


@mcp.tool()
async def parse_project(
    source_path: str,
    project_name: Optional[str] = None,
    language: str = "auto"
) -> dict:
    """
    解析代码项目生成CPG
    
    Args:
        source_path: 源代码路径
        project_name: 项目名称（可选，默认使用目录名）
        language: 编程语言 (auto, c, java, javascript, python, kotlin)
    
    Returns:
        解析结果，包含项目ID和状态
    
    Example:
        >>> await parse_project("/path/to/project", "my-app", "java")
        {"success": True, "project_name": "my-app", "message": "Project parsed successfully"}
    """
    logger.info(f"Parsing project: {source_path}")
    
    # 验证路径
    path = Path(source_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {source_path}"
        }
    
    # 生成项目名称
    if not project_name:
        project_name = path.name
    
    try:
        # 导入代码
        result = await asyncio.to_thread(
            ServerState.joern_server.import_code,
            str(path.absolute()),
            project_name
        )
        
        if result.get("success"):
            logger.info(f"Project {project_name} parsed successfully")
            return {
                "success": True,
                "project_name": project_name,
                "source_path": str(path.absolute()),
                "language": language,
                "message": "Project parsed successfully",
                "output": result.get("stdout", "")
            }
        else:
            logger.error(f"Failed to parse project: {result.get('stderr')}")
            return {
                "success": False,
                "error": result.get("stderr", "Unknown error")
            }
            
    except Exception as e:
        logger.exception(f"Error parsing project: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def list_projects() -> dict:
    """
    列出所有已解析的项目
    
    Returns:
        项目列表
    
    Example:
        >>> await list_projects()
        {"projects": ["project1", "project2"], "count": 2}
    """
    try:
        # 执行workspace查询
        from cpgqls_client import workspace_query
        query = workspace_query()
        result = ServerState.joern_server.execute_query(query)
        
        if result.get("success"):
            # 解析workspace输出
            stdout = result.get("stdout", "")
            # workspace输出格式通常是项目列表
            return {
                "success": True,
                "workspace_info": stdout
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to get workspace")
            }
            
    except Exception as e:
        logger.exception(f"Error listing projects: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

**测试**: `tests/test_tools/test_project.py`
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from joern_mcp.tools.project import parse_project, list_projects


@pytest.mark.asyncio
async def test_parse_project_success(tmp_path, monkeypatch):
    """测试项目解析成功"""
    # 创建测试项目
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    (test_dir / "main.c").write_text("int main() { return 0; }")
    
    # Mock ServerState
    mock_server = MagicMock()
    mock_server.import_code.return_value = {
        "success": True,
        "stdout": "CPG created"
    }
    
    from joern_mcp import server
    monkeypatch.setattr(server.ServerState, "joern_server", mock_server)
    
    # 执行解析
    result = await parse_project(str(test_dir))
    
    assert result["success"] is True
    assert result["project_name"] == "test_project"


@pytest.mark.asyncio
async def test_parse_project_path_not_exists():
    """测试路径不存在"""
    result = await parse_project("/non/existent/path")
    
    assert result["success"] is False
    assert "does not exist" in result["error"]
```

**验收标准**:
```bash
pytest tests/test_tools/test_project.py -v

# 集成测试
python -c "
import asyncio
from joern_mcp.server import mcp
from joern_mcp.tools.project import parse_project

async def test():
    result = await parse_project('/path/to/test/project', 'test-app')
    print(result)

asyncio.run(test())
"
```

**时间**: 6小时

---

### Day 8-9: 代码查询工具

#### 任务 2.3: 函数查询工具

**目标**: 实现获取函数代码和列出函数

**文件**: `src/joern_mcp/tools/query.py`

**代码**:
```python
"""代码查询MCP工具"""
import json
import asyncio
from typing import Optional, List
from loguru import logger
from joern_mcp.server import mcp, ServerState


@mcp.tool()
async def get_function_code(
    function_name: str,
    file_filter: Optional[str] = None
) -> dict:
    """
    获取指定函数的源代码
    
    Args:
        function_name: 函数名称（支持正则表达式）
        file_filter: 文件路径过滤（可选）
    
    Returns:
        函数信息，包含源代码、位置等
    
    Example:
        >>> await get_function_code("main")
        {
            "functions": [{
                "name": "main",
                "signature": "int main()",
                "filename": "main.c",
                "lineNumber": 10,
                "code": "int main() { ... }"
            }],
            "count": 1
        }
    """
    logger.info(f"Getting function code: {function_name}")
    
    try:
        # 构建查询
        if file_filter:
            query = f'''
            cpg.method.name("{function_name}")
               .filename(".*{file_filter}.*")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code
               ))
            '''
        else:
            query = f'''
            cpg.method.name("{function_name}")
               .map(m => Map(
                   "name" -> m.name,
                   "signature" -> m.signature,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1),
                   "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
                   "code" -> m.code
               ))
            '''
        
        # 执行查询
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            # 解析JSON结果
            stdout = result.get("stdout", "")
            try:
                functions = json.loads(stdout)
                return {
                    "success": True,
                    "functions": functions if isinstance(functions, list) else [functions],
                    "count": len(functions) if isinstance(functions, list) else 1
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error getting function code: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def list_functions(
    name_filter: Optional[str] = None,
    limit: int = 100
) -> dict:
    """
    列出所有函数
    
    Args:
        name_filter: 名称过滤（正则表达式，可选）
        limit: 返回数量限制
    
    Returns:
        函数列表
    
    Example:
        >>> await list_functions(name_filter=".*main.*", limit=10)
        {
            "functions": ["main", "main_helper"],
            "count": 2
        }
    """
    logger.info(f"Listing functions (filter: {name_filter}, limit: {limit})")
    
    try:
        # 构建查询
        if name_filter:
            query = f'''
            cpg.method.name(".*{name_filter}.*")
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            '''
        else:
            query = f'''
            cpg.method
               .take({limit})
               .map(m => Map(
                   "name" -> m.name,
                   "filename" -> m.filename,
                   "lineNumber" -> m.lineNumber.getOrElse(-1)
               ))
            '''
        
        # 执行查询
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            try:
                functions = json.loads(stdout)
                return {
                    "success": True,
                    "functions": functions,
                    "count": len(functions) if isinstance(functions, list) else 1
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error listing functions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_code(
    pattern: str,
    scope: str = "all"
) -> dict:
    """
    搜索代码
    
    Args:
        pattern: 搜索模式（正则表达式）
        scope: 搜索范围 (all, methods, calls, identifiers)
    
    Returns:
        匹配结果
    
    Example:
        >>> await search_code("strcpy", scope="calls")
        {
            "matches": [{
                "code": "strcpy(dst, src)",
                "filename": "main.c",
                "lineNumber": 25
            }],
            "count": 1
        }
    """
    logger.info(f"Searching code: {pattern} in {scope}")
    
    try:
        # 根据scope构建查询
        if scope == "methods":
            query = f'cpg.method.name(".*{pattern}.*")'
        elif scope == "calls":
            query = f'cpg.call.name(".*{pattern}.*")'
        elif scope == "identifiers":
            query = f'cpg.identifier.name(".*{pattern}.*")'
        else:  # all
            query = f'cpg.all.code(".*{pattern}.*")'
        
        query += '''.take(50).map(n => Map(
            "code" -> n.code,
            "type" -> n.label,
            "file" -> n.file.name.headOption.getOrElse("unknown"),
            "line" -> n.lineNumber.getOrElse(-1)
        ))'''
        
        # 执行查询
        result = await ServerState.query_executor.execute(query)
        
        if result.get("success"):
            stdout = result.get("stdout", "")
            try:
                matches = json.loads(stdout)
                return {
                    "success": True,
                    "matches": matches,
                    "count": len(matches) if isinstance(matches, list) else 1
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "raw_output": stdout
                }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Query failed")
            }
            
    except Exception as e:
        logger.exception(f"Error searching code: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

**测试**: `tests/test_tools/test_query.py`
```python
import pytest
from unittest.mock import MagicMock
from joern_mcp.tools.query import get_function_code, list_functions, search_code


@pytest.mark.asyncio
async def test_get_function_code(monkeypatch):
    """测试获取函数代码"""
    # Mock query executor
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "main", "code": "int main() {}"}]'
    })
    
    from joern_mcp import server
    monkeypatch.setattr(server.ServerState, "query_executor", mock_executor)
    
    result = await get_function_code("main")
    
    assert result["success"] is True
    assert len(result["functions"]) >= 1
    assert result["functions"][0]["name"] == "main"


@pytest.mark.asyncio
async def test_list_functions(monkeypatch):
    """测试列出函数"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "func1"}, {"name": "func2"}]'
    })
    
    from joern_mcp import server
    monkeypatch.setattr(server.ServerState, "query_executor", mock_executor)
    
    result = await list_functions(limit=10)
    
    assert result["success"] is True
    assert result["count"] == 2
```

**验收标准**:
```bash
pytest tests/test_tools/test_query.py -v

# 集成测试（需要先解析项目）
python -c "
import asyncio
from joern_mcp.tools.query import get_function_code, list_functions

async def test():
    # 列出函数
    result = await list_functions(limit=5)
    print('Functions:', result)
    
    # 获取main函数
    result = await get_function_code('main')
    print('Main function:', result)

asyncio.run(test())
"
```

**时间**: 6小时

---

### Day 10: 查询模板系统

#### 任务 2.4: 查询模板库

**目标**: 实现可重用的查询模板

**文件**: `src/joern_mcp/joern/templates.py`

**代码**:
```python
"""Joern查询模板库"""
from string import Template


class QueryTemplates:
    """查询模板集合"""
    
    # 函数查询
    GET_FUNCTION = Template('''
        cpg.method.name("$name")
           .map(m => Map(
               "name" -> m.name,
               "signature" -> m.signature,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1),
               "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
               "code" -> m.code
           ))
    ''')
    
    LIST_FUNCTIONS = Template('''
        cpg.method
           .take($limit)
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    # 调用关系查询
    GET_CALLERS = Template('''
        cpg.method.name("$name")
           .caller
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    GET_CALLEES = Template('''
        cpg.method.name("$name")
           .callee
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    GET_CALL_CHAIN = Template('''
        cpg.method.name("$name")
           .repeat(_.caller)(_.times($depth))
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "file" -> m.filename
           ))
    ''')
    
    # 数据流查询
    DATAFLOW = Template('''
        def source = cpg.method.name("$source_name").parameter
        def sink = cpg.call.name("$sink_name").argument
        
        sink.reachableBy(source).flows.map(flow => Map(
            "source" -> flow.source.code,
            "sink" -> flow.sink.code,
            "path" -> flow.elements.map(e => Map(
                "type" -> e.label,
                "code" -> e.code,
                "line" -> e.lineNumber.getOrElse(-1),
                "file" -> e.file.name.headOption.getOrElse("unknown")
            ))
        ))
    ''')
    
    # 污点分析
    TAINT_ANALYSIS = Template('''
        def sources = cpg.method.name("($source_pattern)").parameter
        def sinks = cpg.call.name("($sink_pattern)").argument
        
        sinks.reachableBy(sources).flows.map(flow => Map(
            "vulnerability" -> "Potential Taint Flow",
            "severity" -> "$severity",
            "source" -> Map(
                "method" -> flow.source.method.name,
                "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.source.lineNumber.getOrElse(-1)
            ),
            "sink" -> Map(
                "method" -> flow.sink.method.name,
                "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.sink.lineNumber.getOrElse(-1)
            ),
            "pathLength" -> flow.elements.size
        ))
    ''')
    
    @classmethod
    def build(cls, template_name: str, **kwargs) -> str:
        """构建查询"""
        template = getattr(cls, template_name, None)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        return template.substitute(**kwargs)
```

**测试**: `tests/test_joern/test_templates.py`
```python
import pytest
from joern_mcp.joern.templates import QueryTemplates


def test_build_function_query():
    """测试构建函数查询"""
    query = QueryTemplates.build("GET_FUNCTION", name="main")
    assert "cpg.method.name(\"main\")" in query
    assert "Map(" in query


def test_build_callers_query():
    """测试构建调用者查询"""
    query = QueryTemplates.build("GET_CALLERS", name="vulnerable_func")
    assert "caller" in query


def test_build_dataflow_query():
    """测试构建数据流查询"""
    query = QueryTemplates.build(
        "DATAFLOW",
        source_name="gets",
        sink_name="system"
    )
    assert "gets" in query
    assert "system" in query
    assert "reachableBy" in query


def test_invalid_template():
    """测试无效模板"""
    with pytest.raises(ValueError):
        QueryTemplates.build("NON_EXISTENT")
```

**验收标准**:
```bash
pytest tests/test_joern/test_templates.py -v
```

**时间**: 3小时

---

## 第二周总结

**已完成**:
- ✅ FastMCP服务器基础
- ✅ 项目解析工具
- ✅ 代码查询工具（函数、搜索）
- ✅ 查询模板系统

**交付物**:
- 可运行的MCP Server
- 基础的代码分析工具
- 查询模板库

**验收测试**:
```bash
# 运行所有测试
pytest tests/ -v --cov=joern_mcp

# 启动MCP Server
python -m joern_mcp.server

# 在另一个终端测试MCP工具
# （需要MCP客户端，如Claude Desktop）
```

---

## 后续周计划概览

### 第三周：分析服务实现
- 调用图分析服务
- 数据流分析服务
- 对应的MCP工具

### 第四周：污点分析
- 污点分析服务
- 漏洞检测
- 预定义污点源和汇

### 第五周：高级功能
- 控制流分析
- 批量查询
- 结果导出

### 第六周：MCP Resources和Prompts
- 项目资源
- 分析提示模板
- 完善文档

### 第七周：集成测试
- 端到端测试
- 性能测试
- 错误处理完善

### 第八周：优化和发布
- 性能优化
- 文档完善
- 发布准备

---

**待续**: 第三周到第八周的详细计划将在后续文档中提供

**文档版本**: v1.0  
**最后更新**: 2025-11-26

