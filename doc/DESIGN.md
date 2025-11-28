# Joern MCP Server 技术设计方案

## 项目概述

**项目名称**: Joern MCP Server  
**项目目标**: 将 Joern 代码分析平台封装为 MCP Server，使 LLM 能够通过标准化接口进行代码静态分析  
**开发语言**: Python 3.10+  
**核心框架**: FastMCP  
**集成平台**: Joern (https://joern.io)

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         LLM Client                          │
│                    (Claude, GPT, etc.)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
                         │ (stdio/HTTP)
┌────────────────────────┴────────────────────────────────────┐
│                   MCP Server (Python)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastMCP Application Layer                  │  │
│  │  - Resource Management (代码项目资源)                │  │
│  │  - Tool Registry (分析工具注册)                      │  │
│  │  - Prompt Templates (分析提示模板)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Joern Integration Layer                      │  │
│  │  - Joern CLI Wrapper (命令行封装)                    │  │
│  │  - CPG Manager (代码属性图管理)                      │  │
│  │  - Query Executor (查询执行器)                       │  │
│  │  - Result Parser (结果解析器)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Analysis Service Layer                      │  │
│  │  - Code Extraction Service                           │  │
│  │  - Call Graph Service                                │  │
│  │  - Data Flow Service                                 │  │
│  │  - Taint Analysis Service                            │  │
│  │  - Control Flow Service                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ Process/API
┌────────────────────────┴────────────────────────────────────┐
│                    Joern Platform                           │
│  - joern (CLI)                                              │
│  - joern-parse (代码解析)                                   │
│  - joern-export (结果导出)                                  │
│  - CPG Database (图数据库)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级        | 技术选型                | 说明                  |
| ----------- | ----------------------- | --------------------- |
| MCP 框架    | FastMCP 0.1.0+          | MCP 协议实现          |
| 异步处理    | asyncio                 | 异步 IO 和并发        |
| Joern 客户端 | cpgqls-client           | Joern 官方 Python 客户端 |
| HTTP 客户端 | httpx                   | 异步 HTTP 请求        |
| 数据验证    | Pydantic 2.0+           | 数据模型和验证        |
| JSON 处理   | orjson                  | 高性能 JSON           |
| 缓存        | cachetools 5.0+         | 结果缓存              |
| 日志        | loguru 0.7+             | 结构化日志            |
| 测试        | pytest + pytest-asyncio | 单元和集成测试        |

## 2. 核心功能设计

### 2.1 MCP Resources（资源）

Resources 提供代码项目和 CPG 的只读访问：

| Resource URI             | 描述           | 返回内容                   |
| ------------------------ | -------------- | -------------------------- |
| `project://list`         | 已解析项目列表 | 项目名称、路径、CPG 状态   |
| `project://{name}/info`  | 项目详细信息   | 元数据、文件列表、统计信息 |
| `cpg://{project}/stats`  | CPG 统计信息   | 节点数、边数、支持查询类型 |
| `cpg://{project}/schema` | CPG Schema     | 节点类型、边类型、属性定义 |

### 2.2 MCP Tools（工具）

#### 2.2.1 项目管理类

| 工具名           | 功能             | 参数                           | 返回              |
| ---------------- | ---------------- | ------------------------------ | ----------------- |
| `parse_project`  | 解析代码生成 CPG | source_path, language, options | 项目 ID, CPG 路径 |
| `list_projects`  | 列出已解析项目   | -                              | 项目列表          |
| `load_project`   | 加载项目 CPG     | project_id                     | 加载状态          |
| `delete_project` | 删除项目 CPG     | project_id                     | 删除状态          |

#### 2.2.2 代码查询类

| 工具名              | 功能         | 参数                | 返回         |
| ------------------- | ------------ | ------------------- | ------------ |
| `get_function_code` | 获取函数源码 | function_name, file | 函数完整代码 |
| `list_functions`    | 列出所有函数 | filter, limit       | 函数列表     |
| `search_by_name`    | 按名称搜索   | name, type          | 匹配结果     |
| `search_by_pattern` | 按模式搜索   | pattern, scope      | 匹配结果     |
| `get_file_code`     | 获取文件源码 | file_path           | 文件内容     |

#### 2.2.3 调用链分析类

| 工具名           | 功能           | 参数                                | 返回         |
| ---------------- | -------------- | ----------------------------------- | ------------ |
| `get_callers`    | 获取调用者     | function_name, depth                | 调用者列表   |
| `get_callees`    | 获取被调用者   | function_name, depth                | 被调用者列表 |
| `get_call_chain` | 获取完整调用链 | function_name, direction, max_depth | 调用链图     |
| `get_call_graph` | 获取调用图     | entry_points, max_depth             | 调用图 JSON  |

#### 2.2.4 数据流分析类

| 工具名                  | 功能         | 参数                 | 返回       |
| ----------------------- | ------------ | -------------------- | ---------- |
| `track_dataflow`        | 数据流追踪   | source, sink, type   | 数据流路径 |
| `find_flows_to`         | 查找流向目标 | target, max_paths    | 流向路径   |
| `find_flows_from`       | 查找从源流出 | source, max_paths    | 流出路径   |
| `analyze_variable_flow` | 变量流分析   | variable_name, scope | 变量流向   |

#### 2.2.5 污点分析类

| 工具名                 | 功能         | 参数                       | 返回       |
| ---------------------- | ------------ | -------------------------- | ---------- |
| `taint_analysis`       | 污点追踪     | sources, sinks, sanitizers | 污点路径   |
| `find_sources`         | 查找污点源   | category                   | 污点源列表 |
| `find_sinks`           | 查找污点汇   | category                   | 污点汇列表 |
| `find_vulnerabilities` | 查找潜在漏洞 | vuln_type                  | 漏洞列表   |

#### 2.2.6 控制流分析类

| 工具名               | 功能         | 参数               | 返回     |
| -------------------- | ------------ | ------------------ | -------- |
| `get_cfg`            | 获取控制流图 | function_name      | CFG JSON |
| `find_paths`         | 查找执行路径 | from_line, to_line | 路径列表 |
| `analyze_dominators` | 支配节点分析 | function_name      | 支配树   |

#### 2.2.7 高级查询类

| 工具名           | 功能           | 参数                | 返回     |
| ---------------- | -------------- | ------------------- | -------- |
| `execute_query`  | 执行自定义查询 | query_code, timeout | 查询结果 |
| `export_results` | 导出分析结果   | format, output_path | 导出状态 |
| `batch_query`    | 批量查询       | queries             | 批量结果 |

### 2.3 MCP Prompts（提示模板）

| Prompt 名称           | 场景          | 参数              | 输出         |
| --------------------- | ------------- | ----------------- | ------------ |
| `analyze_security`    | 安全分析向导  | entry_function    | 分析步骤建议 |
| `trace_vulnerability` | 漏洞追踪向导  | vuln_type, target | 追踪策略     |
| `understand_function` | 函数理解向导  | function_name     | 理解问题列表 |
| `review_code_quality` | 代码质量审查  | scope             | 审查清单     |
| `find_bug_pattern`    | 查找 bug 模式 | pattern_type      | 检查建议     |

## 3. Joern 集成设计

### 3.1 Joern 管理器

```python
class JoernManager:
    """Joern安装和生命周期管理"""

    def __init__(self):
        self.joern_path: Path = None
        self.workspace: Path = Path.home() / ".joern_mcp" / "workspace"
        self.cpg_cache: Path = Path.home() / ".joern_mcp" / "cpg_cache"
        self.joern_version: str = None

    def detect_joern(self) -> Path:
        """
        检测Joern安装
        优先级：
        1. 环境变量 JOERN_HOME
        2. 系统PATH中的joern命令
        3. 默认安装路径 /usr/local/bin/joern
        """

    def ensure_joern(self) -> bool:
        """确保Joern已安装并可用"""

    def get_version(self) -> str:
        """获取Joern版本"""

    def validate_installation(self) -> Dict[str, bool]:
        """验证Joern安装完整性"""
```

### 3.2 CPG 管理器

```python
class CPGManager:
    """代码属性图生成和管理"""

    async def parse_project(
        self,
        source_path: str,
        language: str = "auto",
        output_path: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> str:
        """
        解析代码生成CPG

        支持的语言：
        - c/cpp: C/C++代码
        - java: Java字节码和源码
        - javascript: JavaScript/TypeScript
        - python: Python代码
        - kotlin: Kotlin代码
        - binary: 二进制文件

        返回：项目ID（CPG标识符）
        """

    async def load_cpg(self, cpg_path: str) -> bool:
        """加载已有CPG到内存"""

    async def get_cpg_stats(self, project_id: str) -> Dict:
        """获取CPG统计信息"""

    def get_cpg_path(self, source_path: str) -> Path:
        """计算CPG存储路径"""

    async def incremental_parse(
        self,
        project_id: str,
        changed_files: List[str]
    ) -> bool:
        """增量解析（仅更新变更文件）"""
```

### 3.3 查询执行器

```python
from cpgqls_client import CPGQLSClient
from typing import Optional, Dict, Tuple

class QueryExecutor:
    """Joern查询执行引擎"""

    def __init__(self, server_manager: JoernServerManager):
        self.server_manager = server_manager
        self.query_templates: Dict[str, str] = {}
        self.result_cache: Cache = Cache(maxsize=1000)

    async def execute_query(
        self,
        query: str,
        format: str = "json",
        timeout: int = 300,
        use_cache: bool = True
    ) -> Dict:
        """
        执行Joern查询

        支持的格式：
        - json: JSON输出（通过.toJson）
        - dot: Graphviz DOT格式（通过.toDot）
        - 其他自定义格式

        Args:
            query: Scala查询语句
            format: 输出格式
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存

        Returns:
            查询结果字典，包含stdout、stderr等信息
        """
        # 1. 验证查询安全性
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            raise QueryValidationError(error_msg)

        # 2. 检查缓存
        cache_key = self._get_cache_key(query)
        if use_cache and cache_key in self.result_cache:
            return self.result_cache[cache_key]

        # 3. 确保查询返回JSON格式
        if format == "json" and not query.strip().endswith(".toJson"):
            query = f"({query}).toJson"

        # 4. 执行查询
        try:
            result = await asyncio.wait_for(
                self.server_manager.execute_query(query),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise QueryTimeoutError(f"Query timeout after {timeout}s")

        # 5. 缓存结果
        if use_cache:
            self.result_cache[cache_key] = result

        return result

    def build_query(self, query_type: str, **params) -> str:
        """使用模板构建查询语句"""
        template = self.query_templates.get(query_type)
        if not template:
            raise ValueError(f"Unknown query type: {query_type}")

        # 使用字符串模板替换参数
        from string import Template
        return Template(template).substitute(**params)

    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        验证查询安全性

        检查项：
        1. 禁止执行系统命令
        2. 禁止文件操作
        3. 限制查询长度
        """
        # 在QueryValidator中实现详细检查
        pass

    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()
```

### 3.4 查询模板库

```scala
// 函数查询模板
val GET_FUNCTION_CODE = """
cpg.method.name("${name}")
   .map(m => Map(
       "name" -> m.name,
       "signature" -> m.signature,
       "filename" -> m.filename,
       "lineNumber" -> m.lineNumber.getOrElse(-1),
       "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
       "code" -> m.code
   )).toJson
"""

// 调用者查询模板
val GET_CALLERS = """
cpg.method.name("${name}")
   .caller
   .map(m => Map(
       "name" -> m.name,
       "filename" -> m.filename,
       "lineNumber" -> m.lineNumber.getOrElse(-1)
   )).dedup.toJson
"""

// 数据流查询模板
val DATAFLOW_PATHS = """
def source = cpg.method.name("${source}").parameter
def sink = cpg.call.name("${sink}").argument

sink.reachableBy(source).flows.map(flow => Map(
    "source" -> flow.source.code,
    "sink" -> flow.sink.code,
    "path" -> flow.elements.map(e => Map(
        "type" -> e.label,
        "code" -> e.code,
        "line" -> e.lineNumber.getOrElse(-1),
        "file" -> e.file.name.headOption.getOrElse("unknown")
    ))
)).toJson
"""

// 污点分析模板
val TAINT_ANALYSIS = """
def sources = cpg.method.name("${sources}").parameter
def sinks = cpg.call.name("${sinks}").argument

sinks.reachableBy(sources).flows.map(flow => Map(
    "vulnerability" -> "Potential Taint Flow",
    "severity" -> "${severity}",
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
)).toJson
"""

// 调用图模板
val CALL_GRAPH = """
cpg.method.name("${entryPoint}")
   .repeat(_.callee)(_.times(${maxDepth}))
   .dedup
   .map(m => Map(
       "name" -> m.fullName,
       "file" -> m.filename,
       "callers" -> m.caller.name.l,
       "callees" -> m.callee.name.l
   )).toJson
"""

// 控制流图模板
val CONTROL_FLOW = """
cpg.method.name("${name}")
   .controlFlow
   .map(node => Map(
       "id" -> node.id,
       "type" -> node.label,
       "code" -> node.code,
       "line" -> node.lineNumber.getOrElse(-1),
       "successors" -> node.cfgNext.id.l
   )).toJson
"""
```

## 4. 项目结构

```
joern_mcp/
├── pyproject.toml              # 项目配置
├── README.md                   # 项目文档
├── DESIGN.md                   # 设计方案（本文档）
├── ARCHITECTURE.md             # 架构详细说明
├── DEVELOPMENT.md              # 开发指南
├── requirements.txt            # 依赖列表
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略文件
│
├── src/
│   └── joern_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP服务器主入口
│       ├── config.py          # 配置管理
│       │
│       ├── joern/             # Joern集成层
│       │   ├── __init__.py
│       │   ├── manager.py     # Joern管理器
│       │   ├── cpg.py         # CPG管理
│       │   ├── executor.py    # 查询执行器
│       │   ├── parser.py      # 结果解析器
│       │   └── templates.py   # 查询模板
│       │
│       ├── services/          # 分析服务层
│       │   ├── __init__.py
│       │   ├── code.py        # 代码提取服务
│       │   ├── callgraph.py   # 调用图服务
│       │   ├── dataflow.py    # 数据流服务
│       │   ├── taint.py       # 污点分析服务
│       │   └── cfg.py         # 控制流服务
│       │
│       ├── tools/             # MCP工具定义
│       │   ├── __init__.py
│       │   ├── project.py     # 项目管理工具
│       │   ├── query.py       # 查询工具
│       │   ├── analysis.py    # 分析工具
│       │   └── export.py      # 导出工具
│       │
│       ├── resources/         # MCP资源定义
│       │   ├── __init__.py
│       │   └── project.py     # 项目资源
│       │
│       ├── prompts/           # MCP提示模板
│       │   ├── __init__.py
│       │   └── templates.py   # 分析模板
│       │
│       ├── models/            # 数据模型
│       │   ├── __init__.py
│       │   ├── project.py     # 项目模型
│       │   ├── cpg.py         # CPG模型
│       │   └── analysis.py    # 分析结果模型
│       │
│       └── utils/             # 工具函数
│           ├── __init__.py
│           ├── cache.py       # 缓存管理
│           ├── logger.py      # 日志管理
│           ├── validators.py  # 数据验证
│           └── format.py      # 格式化工具
│
├── scripts/                   # 脚本工具
│   ├── install_joern.sh      # Joern安装脚本
│   ├── setup.sh              # 环境设置脚本
│   └── test_integration.py   # 集成测试脚本
│
├── tests/                     # 测试
│   ├── __init__.py
│   ├── conftest.py           # pytest配置
│   ├── test_joern/           # Joern集成测试
│   │   ├── test_manager.py
│   │   ├── test_cpg.py
│   │   └── test_executor.py
│   ├── test_services/        # 服务层测试
│   │   ├── test_code.py
│   │   ├── test_callgraph.py
│   │   ├── test_dataflow.py
│   │   └── test_taint.py
│   ├── test_tools/           # 工具测试
│   │   └── test_mcp_tools.py
│   └── fixtures/             # 测试fixtures
│       └── sample_projects/  # 示例项目
│
├── docs/                      # 文档
│   ├── api/                  # API文档
│   │   ├── tools.md
│   │   ├── resources.md
│   │   └── prompts.md
│   ├── guides/               # 使用指南
│   │   ├── quickstart.md
│   │   ├── security_analysis.md
│   │   └── custom_queries.md
│   └── examples/             # 示例
│       ├── basic_usage.md
│       └── advanced_analysis.md
│
└── examples/                  # 代码示例
    ├── analyze_project.py    # 项目分析示例
    ├── find_vulnerabilities.py  # 漏洞查找示例
    └── custom_queries.py     # 自定义查询示例
```

## 5. 数据模型

### 5.1 项目模型

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

class ProjectInfo(BaseModel):
    """项目信息模型"""
    id: str = Field(description="项目唯一标识符")
    name: str = Field(description="项目名称")
    source_path: Path = Field(description="源代码路径")
    cpg_path: Path = Field(description="CPG存储路径")
    language: str = Field(description="项目语言")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    size_bytes: int = Field(description="项目大小（字节）")
    file_count: int = Field(description="文件数量")
    status: str = Field(description="状态: parsed, loading, loaded, error")
    metadata: Dict = Field(default_factory=dict, description="额外元数据")

class CPGStats(BaseModel):
    """CPG统计信息"""
    node_count: int = Field(description="节点总数")
    edge_count: int = Field(description="边总数")
    method_count: int = Field(description="方法数量")
    file_count: int = Field(description="文件数量")
    type_count: int = Field(description="类型数量")
    node_types: Dict[str, int] = Field(description="节点类型分布")
    edge_types: Dict[str, int] = Field(description="边类型分布")
```

### 5.2 分析结果模型

```python
class FunctionInfo(BaseModel):
    """函数信息"""
    name: str
    full_name: str
    signature: str
    filename: str
    line_number: int
    line_number_end: int
    code: str
    parameters: List[str]
    return_type: Optional[str]
    complexity: Optional[int]

class CallChain(BaseModel):
    """调用链"""
    entry_point: str
    depth: int
    nodes: List[FunctionInfo]
    edges: List[Dict[str, str]]  # {"from": "func1", "to": "func2"}

class DataFlow(BaseModel):
    """数据流"""
    source: Dict[str, any]
    sink: Dict[str, any]
    path: List[Dict[str, any]]
    path_length: int

class TaintFlow(BaseModel):
    """污点流"""
    vulnerability: str
    severity: str  # low, medium, high, critical
    source: Dict[str, any]
    sink: Dict[str, any]
    path_length: int
    sanitizers: List[str]
    confidence: float  # 0.0-1.0
```

## 6. 工具实现详细设计

### 6.1 代码查询工具

```python
@mcp.tool()
async def get_function_code(
    function_name: str,
    file_filter: Optional[str] = None
) -> Dict:
    """
    获取指定函数的源代码

    Args:
        function_name: 函数名称（支持正则表达式）
        file_filter: 文件过滤器（可选）

    Returns:
        {
            "functions": [
                {
                    "name": "main",
                    "signature": "int main(int argc, char** argv)",
                    "filename": "/path/to/file.c",
                    "lineNumber": 10,
                    "lineNumberEnd": 25,
                    "code": "int main() { ... }"
                }
            ],
            "count": 1
        }
    """
    query = build_function_query(function_name, file_filter)
    result = await executor.execute_query(query)
    return parse_function_result(result)
```

### 6.2 调用链分析工具

```python
@mcp.tool()
async def get_call_chain(
    function_name: str,
    direction: str = "both",  # "callers", "callees", "both"
    max_depth: int = 3,
    include_external: bool = False
) -> Dict:
    """
    获取函数的调用链

    Args:
        function_name: 函数名称
        direction: 调用方向
        max_depth: 最大深度
        include_external: 是否包含外部库调用

    Returns:
        {
            "entry_point": "main",
            "depth": 3,
            "nodes": [...],
            "edges": [...],
            "graph_viz": "digraph { ... }"
        }
    """
    result = {}

    if direction in ["callers", "both"]:
        result["callers"] = await get_callers_recursive(
            function_name, max_depth, include_external
        )

    if direction in ["callees", "both"]:
        result["callees"] = await get_callees_recursive(
            function_name, max_depth, include_external
        )

    return result
```

### 6.3 数据流分析工具

```python
@mcp.tool()
async def track_dataflow(
    source: str,
    sink: str,
    source_type: str = "parameter",
    sink_type: str = "call",
    max_paths: int = 10
) -> Dict:
    """
    追踪从源到汇的数据流

    Args:
        source: 源函数/变量名
        sink: 汇函数/变量名
        source_type: 源类型 (parameter, literal, call, identifier)
        sink_type: 汇类型 (parameter, call, return)
        max_paths: 最大路径数

    Returns:
        {
            "paths": [
                {
                    "source": {...},
                    "sink": {...},
                    "path": [
                        {
                            "type": "IDENTIFIER",
                            "code": "userInput",
                            "line": 10,
                            "file": "main.c"
                        },
                        ...
                    ],
                    "pathLength": 5
                }
            ],
            "totalPaths": 3
        }
    """
    query = build_dataflow_query(
        source, sink, source_type, sink_type, max_paths
    )
    result = await executor.execute_query(query)
    return parse_dataflow_result(result)
```

### 6.4 污点分析工具

```python
@mcp.tool()
async def taint_analysis(
    sources: List[str],
    sinks: List[str],
    sanitizers: Optional[List[str]] = None,
    vulnerability_type: str = "all"
) -> Dict:
    """
    执行污点分析

    Args:
        sources: 污点源列表（如：["gets", "scanf", "recv"]）
        sinks: 污点汇列表（如：["system", "exec", "strcpy"]）
        sanitizers: 净化函数列表（如：["sanitize", "escape"]）
        vulnerability_type: 漏洞类型 (sqli, xss, command_injection, all)

    Returns:
        {
            "vulnerabilities": [
                {
                    "type": "Command Injection",
                    "severity": "high",
                    "confidence": 0.85,
                    "source": {...},
                    "sink": {...},
                    "pathLength": 4,
                    "hasSanitizer": false,
                    "description": "User input flows to system() call"
                }
            ],
            "summary": {
                "total": 5,
                "high": 2,
                "medium": 2,
                "low": 1
            }
        }
    """
    # 根据漏洞类型预定义污点源和汇
    if vulnerability_type != "all":
        sources, sinks = get_predefined_sources_sinks(vulnerability_type)

    query = build_taint_query(sources, sinks, sanitizers)
    result = await executor.execute_query(query)

    # 分析结果并评估严重程度
    vulnerabilities = parse_taint_result(result)
    vulnerabilities = assess_severity(vulnerabilities)

    return {
        "vulnerabilities": vulnerabilities,
        "summary": summarize_vulnerabilities(vulnerabilities)
    }
```

## 7. 实现步骤规划

### 阶段 1: 基础设施（第 1-2 周）

**Week 1: 项目初始化**

- [x] 创建项目结构
- [ ] 配置开发环境
- [ ] 实现配置管理系统
- [ ] 实现日志系统
- [ ] 编写 Joern 安装检测逻辑

**Week 2: Joern 集成**

- [ ] 实现 JoernManager
- [ ] 实现 CPG 生成功能
- [ ] 实现 Joern 进程管理
- [ ] 测试基本的 Joern 调用

### 阶段 2: 核心查询功能（第 3-4 周）

**Week 3: 查询执行器**

- [ ] 实现 QueryExecutor
- [ ] 实现查询模板系统
- [ ] 实现结果解析器
- [ ] 实现查询缓存

**Week 4: 基础查询工具**

- [ ] 实现函数查询工具
- [ ] 实现代码搜索工具
- [ ] 实现项目管理工具
- [ ] 单元测试

### 阶段 3: 高级分析功能（第 5-6 周）

**Week 5: 调用图和数据流**

- [ ] 实现调用图分析服务
- [ ] 实现数据流追踪服务
- [ ] 实现相关 MCP 工具
- [ ] 集成测试

**Week 6: 污点分析和控制流**

- [ ] 实现污点分析服务
- [ ] 实现控制流分析服务
- [ ] 实现漏洞检测规则
- [ ] 集成测试

### 阶段 4: MCP 集成（第 7 周）

**Week 7: MCP 接口**

- [ ] 实现 MCP Resources
- [ ] 注册所有 MCP Tools
- [ ] 实现 MCP Prompts
- [ ] MCP 协议测试

### 阶段 5: 优化和文档（第 8 周）

**Week 8: 完善和发布**

- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 编写完整文档
- [ ] 编写使用示例
- [ ] 发布 v0.1.0

## 8. 技术难点与解决方案

### 8.1 Joern Server 集成

**技术方案**:

使用 Joern 的 Server 模式而非 REPL 模式，通过 HTTP API 进行交互。

参考资料：
- Joern 集成文档: https://joern.io/integrate/
- Server 文档: https://docs.joern.io/server/
- Python 客户端: https://github.com/joernio/cpgqls-client-python

**优势**:

- 标准的 HTTP REST API，无需处理 REPL 提示符
- 官方提供 Python 客户端库 `cpgqls-client`
- 支持异步查询和 WebSocket 通知
- 可配置认证和访问控制
- 更稳定可靠的进程管理

**解决方案**:

```python
from cpgqls_client import CPGQLSClient, import_code_query, workspace_query
import httpx
import asyncio

class JoernServerManager:
    """Joern Server管理器"""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.endpoint = f"{host}:{port}"
        self.client: Optional[CPGQLSClient] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.auth_credentials: Optional[Tuple[str, str]] = None

    async def start_server(
        self, 
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """启动Joern Server"""
        cmd = [
            "joern",
            "--server",
            "--server-host", self.host,
            "--server-port", str(self.port)
        ]
        
        # 添加认证参数
        if username and password:
            cmd.extend([
                "--server-auth-username", username,
                "--server-auth-password", password
            ])
            self.auth_credentials = (username, password)
        
        # 启动服务器进程
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 等待服务器启动
        await self._wait_for_server()
        
        # 初始化客户端
        self.client = CPGQLSClient(
            self.endpoint,
            auth_credentials=self.auth_credentials
        )

    async def _wait_for_server(self, timeout: int = 30):
        """等待服务器就绪"""
        start_time = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"http://{self.endpoint}/",
                        timeout=1.0
                    )
                    if response.status_code in [200, 404]:
                        return
                except:
                    pass
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Joern server failed to start")
                
                await asyncio.sleep(0.5)

    async def execute_query(
        self, 
        query: str, 
        timeout: int = 300
    ) -> Dict:
        """执行查询（同步方式）"""
        if not self.client:
            raise RuntimeError("Joern server not started")
        
        # 使用官方客户端执行查询
        result = self.client.execute(query)
        return result

    async def execute_query_async(
        self, 
        query: str
    ) -> str:
        """执行查询（异步方式）"""
        if not self.client:
            raise RuntimeError("Joern server not started")
        
        # 提交查询获取UUID
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{self.endpoint}/query",
                json={"query": query},
                auth=self.auth_credentials
            )
            uuid = response.json()["uuid"]
        
        # 轮询结果
        while True:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.endpoint}/result/{uuid}",
                    auth=self.auth_credentials
                )
                result = response.json()
                
                if result["success"]:
                    return result
                
                await asyncio.sleep(0.5)

    async def import_code(
        self, 
        source_path: str, 
        project_name: str
    ) -> Dict:
        """导入代码生成CPG"""
        query = import_code_query(source_path, project_name)
        result = self.client.execute(query)
        return result

    async def get_workspace(self) -> Dict:
        """获取工作空间信息"""
        query = workspace_query()
        result = self.client.execute(query)
        return result

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.endpoint}/",
                    timeout=5.0
                )
                return response.status_code in [200, 404]
        except:
            return False

    async def stop_server(self):
        """停止服务器"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.client = None

    async def restart_server(self):
        """重启服务器"""
        await self.stop_server()
        await self.start_server()
```

### 8.2 大型 CPG 处理

**难点**:

- 大型项目的 CPG 可能达到几 GB
- 加载时间长，内存占用大
- 查询可能很慢

**解决方案**:

```python
class CPGManager:
    """CPG管理策略"""

    # 1. 分片处理
    async def parse_in_chunks(self, source_path: Path):
        """分模块解析"""
        modules = self.detect_modules(source_path)
        for module in modules:
            cpg = await self.parse_module(module)
            await self.merge_cpg(cpg)

    # 2. 懒加载
    async def lazy_load_cpg(self, project_id: str):
        """仅加载元数据，按需加载详细数据"""
        metadata = await self.load_metadata(project_id)
        return PartialCPG(metadata, loader=self)

    # 3. 查询优化
    def optimize_query(self, query: str) -> str:
        """查询优化提示"""
        # 添加过滤条件
        # 限制结果数量
        # 使用索引
        return optimized_query

    # 4. 缓存策略
    @cache(ttl=3600)
    async def execute_cached(self, query: str):
        """缓存常见查询结果"""
        return await self.execute(query)
```

### 8.3 查询结果解析

**难点**:

- Joern 输出格式多样（JSON、文本、DOT 等）
- 可能包含 Scala 错误信息
- 大结果集处理

**解决方案**:

```python
class ResultParser:
    """结果解析器"""

    def parse(self, raw_output: str, format: str = "json") -> Dict:
        """智能解析输出"""
        # 1. 清理输出
        cleaned = self.clean_output(raw_output)

        # 2. 检测错误
        if self.is_error(cleaned):
            raise JoernQueryError(self.extract_error(cleaned))

        # 3. 解析JSON
        if format == "json":
            return self.parse_json(cleaned)

        # 4. 解析其他格式
        return self.parse_custom(cleaned, format)

    def clean_output(self, output: str) -> str:
        """清理REPL提示符和ANSI代码"""
        # 移除 "joern>" 提示符
        # 移除颜色代码
        # 移除多余空白
        return cleaned

    def parse_json(self, output: str) -> Dict:
        """解析JSON输出"""
        try:
            return orjson.loads(output)
        except orjson.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}|\[.*\]', output, re.DOTALL)
            if json_match:
                return orjson.loads(json_match.group())
            raise ParseError("No valid JSON found")
```

### 8.4 性能优化

**难点**:

- 某些查询非常耗时
- 并发查询管理
- 资源限制

**解决方案**:

```python
class PerformanceOptimizer:
    """性能优化器"""

    # 1. 查询超时
    @timeout(300)
    async def execute_with_timeout(self, query: str):
        """带超时的查询执行"""
        return await self.execute(query)

    # 2. 并发控制
    semaphore = asyncio.Semaphore(5)

    async def execute_concurrent(self, query: str):
        """并发控制的查询"""
        async with self.semaphore:
            return await self.execute(query)

    # 3. 批量查询
    async def batch_execute(self, queries: List[str]):
        """批量执行查询"""
        tasks = [self.execute(q) for q in queries]
        return await asyncio.gather(*tasks)

    # 4. 结果流式返回
    async def execute_streaming(self, query: str):
        """流式返回大结果集"""
        async for chunk in self.execute_generator(query):
            yield chunk
```

## 9. 安全考虑

### 9.1 访问控制

```python
class SecurityConfig:
    """安全配置"""

    # 限制可访问的代码路径
    ALLOWED_PATHS = [
        "/tmp/code_analysis",
        str(Path.home() / "projects"),
    ]

    # 路径白名单验证
    def validate_path(self, path: Path) -> bool:
        """验证路径是否在白名单内"""
        resolved = path.resolve()
        return any(
            resolved.is_relative_to(allowed)
            for allowed in self.ALLOWED_PATHS
        )
```

### 9.2 查询安全

```python
class QueryValidator:
    """查询验证器"""

    # 禁止的操作
    FORBIDDEN_PATTERNS = [
        r"System\.exit",
        r"Runtime\.getRuntime",
        r"ProcessBuilder",
        r"File\.delete",
        r"os\.",
        r"sys\.",
    ]

    def validate(self, query: str) -> Tuple[bool, str]:
        """验证查询安全性"""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, query):
                return False, f"Forbidden operation: {pattern}"

        # 验证查询长度
        if len(query) > 10000:
            return False, "Query too long"

        return True, "OK"
```

### 9.3 资源限制

```python
class ResourceLimiter:
    """资源限制器"""

    # 限制
    MAX_CPG_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
    MAX_CONCURRENT_QUERIES = 5
    MAX_QUERY_TIME = 300  # 5分钟
    MAX_RESULT_SIZE = 100 * 1024 * 1024  # 100MB

    def check_cpg_size(self, path: Path) -> bool:
        """检查CPG大小"""
        size = path.stat().st_size
        return size <= self.MAX_CPG_SIZE

    def check_result_size(self, result: str) -> bool:
        """检查结果大小"""
        size = len(result.encode('utf-8'))
        return size <= self.MAX_RESULT_SIZE
```

## 10. 监控和日志

### 10.1 日志系统

```python
from loguru import logger

# 配置日志
logger.add(
    "logs/joern_mcp_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# 日志使用
logger.info("CPG parsed successfully", project=project_id, size=cpg_size)
logger.error("Query execution failed", query=query, error=str(e))
logger.debug("Query result", result=result[:100])
```

### 10.2 指标收集

```python
class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics = {
            "queries": [],
            "parse_times": [],
            "errors": [],
        }

    def track_query(self, query_type: str, duration: float, success: bool):
        """记录查询指标"""
        self.metrics["queries"].append({
            "type": query_type,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now()
        })

    def track_parse(self, language: str, duration: float, size: int):
        """记录解析指标"""
        self.metrics["parse_times"].append({
            "language": language,
            "duration": duration,
            "size": size,
            "timestamp": datetime.now()
        })

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_queries": len(self.metrics["queries"]),
            "avg_query_time": self._avg_duration("queries"),
            "success_rate": self._success_rate(),
            "total_errors": len(self.metrics["errors"]),
        }
```

## 11. 配置管理

### 11.1 环境变量

```bash
# .env.example

# Joern配置
JOERN_HOME=/usr/local/lib/joern
JOERN_WORKSPACE=/Users/user/.joern_mcp/workspace
JOERN_CPG_CACHE=/Users/user/.joern_mcp/cpg_cache

# MCP配置
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
MCP_LOG_LEVEL=INFO

# 性能配置
MAX_CONCURRENT_QUERIES=5
QUERY_TIMEOUT=300
CPG_CACHE_SIZE=10737418240  # 10GB

# 安全配置
ALLOWED_PATHS=/tmp/code_analysis,~/projects
ENABLE_CUSTOM_QUERIES=true
```

### 11.2 配置类

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""

    # Joern配置
    joern_home: Path = Path("/usr/local/lib/joern")
    joern_workspace: Path = Path.home() / ".joern_mcp" / "workspace"
    joern_cpg_cache: Path = Path.home() / ".joern_mcp" / "cpg_cache"

    # MCP配置
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 3000
    mcp_log_level: str = "INFO"

    # 性能配置
    max_concurrent_queries: int = 5
    query_timeout: int = 300
    cpg_cache_size: int = 10 * 1024 * 1024 * 1024

    # 安全配置
    allowed_paths: List[Path] = []
    enable_custom_queries: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

## 12. 测试策略

### 12.1 单元测试

```python
# tests/test_joern/test_manager.py

import pytest
from joern_mcp.joern.manager import JoernManager

@pytest.fixture
def joern_manager():
    return JoernManager()

def test_detect_joern(joern_manager):
    """测试Joern检测"""
    path = joern_manager.detect_joern()
    assert path is not None
    assert path.exists()

def test_get_version(joern_manager):
    """测试版本获取"""
    version = joern_manager.get_version()
    assert version is not None
    assert re.match(r'\d+\.\d+\.\d+', version)
```

### 12.2 集成测试

```python
# tests/test_integration.py

@pytest.mark.integration
async def test_full_analysis_pipeline():
    """测试完整分析流程"""
    # 1. 解析项目
    project_id = await parse_project("tests/fixtures/sample_c_project")

    # 2. 获取函数列表
    functions = await list_functions(project_id)
    assert len(functions) > 0

    # 3. 执行数据流分析
    flows = await track_dataflow(
        source="gets",
        sink="system"
    )

    # 4. 执行污点分析
    vulns = await taint_analysis(
        sources=["gets", "scanf"],
        sinks=["system", "exec"]
    )

    assert len(vulns) > 0
```

### 12.3 性能测试

```python
# tests/test_performance.py

@pytest.mark.performance
async def test_query_performance():
    """测试查询性能"""
    start = time.time()
    result = await execute_query(large_project_query)
    duration = time.time() - start

    assert duration < 10.0  # 应在10秒内完成
```
