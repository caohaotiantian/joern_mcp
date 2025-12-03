# 服务层 API 参考

本文档详细介绍了 Joern MCP Server 的三个核心服务类的 API。

## 目录

- [CallGraphService - 调用图分析服务](#callgraphservice---调用图分析服务)
- [DataFlowService - 数据流分析服务](#dataflowservice---数据流分析服务)
- [TaintAnalysisService - 污点分析服务](#taintanalysisservice---污点分析服务)

---

## CallGraphService - 调用图分析服务

调用图分析服务提供函数调用关系的分析功能，包括查找调用者、被调用者、调用链和完整调用图。

### 初始化

```python
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.joern.executor import QueryExecutor

# 初始化服务
executor = QueryExecutor(server_manager)
callgraph_service = CallGraphService(executor)
```

### 方法

#### `get_callers(function_name, depth=1)`

获取调用指定函数的所有函数（调用者）。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `function_name` | `str` | - | 目标函数名称 |
| `depth` | `int` | `1` | 调用深度，1 表示直接调用者，大于 1 表示递归查找 |

**返回值：**
```python
{
    "success": True,
    "function": "target_function",  # 目标函数名
    "depth": 1,                     # 查询深度
    "callers": [                    # 调用者列表
        {
            "name": "caller_function",
            "signature": "void caller_function(int)",
            "filename": "/path/to/file.c",
            "lineNumber": 42
        }
    ],
    "count": 1                      # 调用者数量
}
```

**示例：**
```python
# 获取直接调用者
result = await callgraph_service.get_callers("vulnerable_func")

# 获取多层调用者（最多3层）
result = await callgraph_service.get_callers("vulnerable_func", depth=3)
```

---

#### `get_callees(function_name, depth=1)`

获取指定函数调用的所有函数（被调用者）。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `function_name` | `str` | - | 目标函数名称 |
| `depth` | `int` | `1` | 调用深度 |

**返回值：**
```python
{
    "success": True,
    "function": "main",
    "depth": 1,
    "callees": [
        {
            "name": "printf",
            "signature": "int printf(const char*, ...)",
            "filename": "<includes>",
            "lineNumber": -1
        }
    ],
    "count": 1
}
```

**示例：**
```python
# 获取 main 函数调用的所有函数
result = await callgraph_service.get_callees("main")

# 递归获取所有被调用函数（最多2层）
result = await callgraph_service.get_callees("main", depth=2)
```

---

#### `get_call_chain(function_name, max_depth=5, direction="up")`

获取函数的完整调用链。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `function_name` | `str` | - | 目标函数名称 |
| `max_depth` | `int` | `5` | 最大追踪深度 |
| `direction` | `str` | `"up"` | 追踪方向：`"up"` 向上追踪调用者，`"down"` 向下追踪被调用者 |

**返回值：**
```python
{
    "success": True,
    "function": "vulnerable_func",
    "direction": "up",
    "max_depth": 5,
    "chain": [
        {
            "name": "main",
            "filename": "/path/to/main.c",
            "depth": "unknown"
        },
        {
            "name": "process_input",
            "filename": "/path/to/input.c",
            "depth": "unknown"
        }
    ],
    "count": 2
}
```

**示例：**
```python
# 向上追踪调用链（谁调用了这个函数）
result = await callgraph_service.get_call_chain("strcpy", direction="up")

# 向下追踪调用链（这个函数调用了什么）
result = await callgraph_service.get_call_chain("main", direction="down", max_depth=3)
```

---

#### `get_call_graph(function_name, include_callers=True, include_callees=True, depth=2)`

获取函数的完整调用图，包含节点和边信息，适合可视化展示。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `function_name` | `str` | - | 目标函数名称 |
| `include_callers` | `bool` | `True` | 是否包含调用者 |
| `include_callees` | `bool` | `True` | 是否包含被调用者 |
| `depth` | `int` | `2` | 分析深度 |

**返回值：**
```python
{
    "success": True,
    "function": "process_data",
    "nodes": [
        {"id": "main", "type": "caller", "filename": "main.c", "lineNumber": 10},
        {"id": "process_data", "type": "target", "filename": "", "lineNumber": -1},
        {"id": "validate", "type": "callee", "filename": "utils.c", "lineNumber": 50}
    ],
    "edges": [
        {"from": "main", "to": "process_data", "type": "calls"},
        {"from": "process_data", "to": "validate", "type": "calls"}
    ],
    "node_count": 3,
    "edge_count": 2
}
```

**示例：**
```python
# 获取完整调用图
result = await callgraph_service.get_call_graph("vulnerable_func")

# 只获取调用者图
result = await callgraph_service.get_call_graph(
    "vulnerable_func", 
    include_callers=True, 
    include_callees=False
)
```

---

## DataFlowService - 数据流分析服务

数据流分析服务提供数据在程序中流动路径的追踪功能。

### 初始化

```python
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.joern.executor import QueryExecutor

executor = QueryExecutor(server_manager)
dataflow_service = DataFlowService(executor)
```

### 方法

#### `track_dataflow(source_method, sink_method, max_flows=10)`

追踪从源方法到汇方法的数据流。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_method` | `str` | - | 源方法名称（数据起点） |
| `sink_method` | `str` | - | 汇方法名称（数据终点） |
| `max_flows` | `int` | `10` | 最大返回流数量 |

**返回值：**
```python
{
    "success": True,
    "source_method": "read_input",
    "sink_method": "system",
    "flows": [
        {
            "source": {
                "code": "char* input",
                "file": "input.c",
                "line": 15
            },
            "sink": {
                "code": "system(cmd)",
                "file": "exec.c",
                "line": 42
            },
            "pathLength": 5,
            "path": [
                {"type": "IDENTIFIER", "code": "input", "line": 15},
                {"type": "CALL", "code": "strcpy(buf, input)", "line": 20},
                {"type": "IDENTIFIER", "code": "buf", "line": 25},
                {"type": "CALL", "code": "system(cmd)", "line": 42}
            ]
        }
    ],
    "count": 1
}
```

**示例：**
```python
# 追踪从用户输入到系统调用的数据流
result = await dataflow_service.track_dataflow("gets", "system")

# 追踪从文件读取到内存拷贝的数据流
result = await dataflow_service.track_dataflow("fread", "memcpy", max_flows=20)
```

---

#### `analyze_variable_flow(variable_name, sink_method=None, max_flows=10)`

分析特定变量的数据流向。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `variable_name` | `str` | - | 变量名称 |
| `sink_method` | `str \| None` | `None` | 目标汇方法（可选） |
| `max_flows` | `int` | `10` | 最大返回流数量 |

**返回值（有 sink_method）：**
```python
{
    "success": True,
    "variable": "user_input",
    "sink_method": "printf",
    "flows": [
        {
            "variable": "user_input",
            "source": {
                "code": "user_input = argv[1]",
                "file": "main.c",
                "line": 10
            },
            "sink": {
                "code": "printf(user_input)",
                "method": "printf",
                "file": "main.c",
                "line": 25
            },
            "pathLength": 3
        }
    ],
    "count": 1
}
```

**返回值（无 sink_method，查找所有使用）：**
```python
{
    "success": True,
    "variable": "buffer",
    "sink_method": None,
    "flows": [
        {
            "variable": "buffer",
            "code": "buffer",
            "type": "char*",
            "method": "process_data",
            "file": "utils.c",
            "line": 30
        }
    ],
    "count": 1
}
```

**示例：**
```python
# 追踪变量到特定函数
result = await dataflow_service.analyze_variable_flow("password", "printf")

# 查找变量的所有使用位置
result = await dataflow_service.analyze_variable_flow("sensitive_data")
```

---

#### `find_data_dependencies(function_name, variable_name=None)`

查找函数中的数据依赖关系。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `function_name` | `str` | - | 函数名称 |
| `variable_name` | `str \| None` | `None` | 特定变量名（可选） |

**返回值：**
```python
{
    "success": True,
    "function": "process_input",
    "variable": None,
    "dependencies": [
        {
            "variable": "input",
            "code": "input",
            "type": "char*",
            "file": "process.c",
            "line": 15
        },
        {
            "variable": "output",
            "code": "output",
            "type": "char*",
            "file": "process.c",
            "line": 20
        }
    ],
    "count": 2
}
```

**示例：**
```python
# 获取函数中所有变量的使用
result = await dataflow_service.find_data_dependencies("vulnerable_func")

# 只查找特定变量
result = await dataflow_service.find_data_dependencies("vulnerable_func", "buffer")
```

---

## TaintAnalysisService - 污点分析服务

污点分析服务提供安全漏洞检测功能，追踪不可信数据从源到汇的流动。

### 初始化

```python
from joern_mcp.services.taint import TaintAnalysisService
from joern_mcp.joern.executor import QueryExecutor

executor = QueryExecutor(server_manager)
taint_service = TaintAnalysisService(executor)
```

### 方法

#### `analyze_with_rule(rule, max_flows=10)`

使用特定规则进行污点分析。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `rule` | `TaintRule` | - | 污点分析规则对象 |
| `max_flows` | `int` | `10` | 最大返回流数量 |

**返回值：**
```python
{
    "success": True,
    "rule": "Command Injection",
    "severity": "CRITICAL",
    "cwe_id": "CWE-78",
    "vulnerabilities": [
        {
            "vulnerability": "Command Injection",
            "severity": "CRITICAL",
            "cwe_id": "CWE-78",
            "description": "User input flows to command execution",
            "source": {
                "code": "char* cmd",
                "file": "input.c",
                "line": 10
            },
            "sink": {
                "code": "system(cmd)",
                "file": "exec.c",
                "line": 25
            },
            "pathLength": 4
        }
    ],
    "count": 1
}
```

**示例：**
```python
from joern_mcp.models.taint_rules import get_rule_by_name

# 使用命令注入规则分析
rule = get_rule_by_name("Command Injection")
result = await taint_service.analyze_with_rule(rule)

# 使用 SQL 注入规则分析
rule = get_rule_by_name("SQL Injection")
result = await taint_service.analyze_with_rule(rule, max_flows=20)
```

---

#### `find_vulnerabilities(rule_name=None, severity=None, max_flows=10)`

批量查找漏洞，支持按规则名或严重程度过滤。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `rule_name` | `str \| None` | `None` | 特定规则名称 |
| `severity` | `str \| None` | `None` | 严重程度：`CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `max_flows` | `int` | `10` | 每个规则的最大流数量 |

**返回值：**
```python
{
    "success": True,
    "vulnerabilities": [
        {
            "vulnerability": "Command Injection",
            "severity": "CRITICAL",
            "cwe_id": "CWE-78",
            "source": {"code": "...", "file": "...", "line": 10},
            "sink": {"code": "...", "file": "...", "line": 25},
            "pathLength": 4
        },
        {
            "vulnerability": "Buffer Overflow",
            "severity": "HIGH",
            "cwe_id": "CWE-120",
            "source": {"code": "...", "file": "...", "line": 15},
            "sink": {"code": "...", "file": "...", "line": 30},
            "pathLength": 3
        }
    ],
    "total_count": 2,
    "summary": {
        "CRITICAL": 1,
        "HIGH": 1,
        "MEDIUM": 0,
        "LOW": 0
    },
    "rules_checked": 6
}
```

**示例：**
```python
# 使用所有规则扫描
result = await taint_service.find_vulnerabilities()

# 只扫描特定规则
result = await taint_service.find_vulnerabilities(rule_name="SQL Injection")

# 只扫描高危漏洞
result = await taint_service.find_vulnerabilities(severity="CRITICAL")
```

---

#### `check_specific_flow(source_pattern, sink_pattern, max_flows=10)`

检查自定义的污点流，使用正则表达式匹配源和汇。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_pattern` | `str` | - | 源模式（正则表达式） |
| `sink_pattern` | `str` | - | 汇模式（正则表达式） |
| `max_flows` | `int` | `10` | 最大返回流数量 |

**返回值：**
```python
{
    "success": True,
    "source_pattern": "read.*|gets|scanf",
    "sink_pattern": "system|exec.*|popen",
    "flows": [
        {
            "source": {
                "code": "fgets(buf, size, stdin)",
                "file": "input.c",
                "line": 12
            },
            "sink": {
                "code": "system(cmd)",
                "file": "exec.c",
                "line": 45
            },
            "pathLength": 6,
            "path": [
                {"type": "CALL", "code": "fgets(...)", "line": 12},
                {"type": "IDENTIFIER", "code": "buf", "line": 15},
                {"type": "CALL", "code": "system(cmd)", "line": 45}
            ]
        }
    ],
    "count": 1
}
```

**示例：**
```python
# 检查从任何读取函数到命令执行的流
result = await taint_service.check_specific_flow(
    source_pattern="read.*|gets|fgets|scanf",
    sink_pattern="system|execve|popen"
)

# 检查从网络输入到文件操作的流
result = await taint_service.check_specific_flow(
    source_pattern="recv|recvfrom|read",
    sink_pattern="fopen|fwrite|fprintf"
)
```

---

#### `list_rules()`

列出所有可用的漏洞检测规则。

**返回值：**
```python
{
    "success": True,
    "rules": [
        {"name": "Command Injection", "severity": "CRITICAL", "cwe_id": "CWE-78"},
        {"name": "SQL Injection", "severity": "CRITICAL", "cwe_id": "CWE-89"},
        {"name": "Path Traversal", "severity": "HIGH", "cwe_id": "CWE-22"},
        {"name": "XSS", "severity": "MEDIUM", "cwe_id": "CWE-79"},
        {"name": "Buffer Overflow", "severity": "HIGH", "cwe_id": "CWE-120"},
        {"name": "Format String", "severity": "HIGH", "cwe_id": "CWE-134"}
    ],
    "count": 6
}
```

**示例：**
```python
# 获取所有规则
rules = taint_service.list_rules()
for rule in rules["rules"]:
    print(f"{rule['name']} ({rule['severity']})")
```

---

#### `get_rule_details(rule_name)`

获取特定规则的详细信息。

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `rule_name` | `str` | 规则名称 |

**返回值：**
```python
{
    "success": True,
    "rule": {
        "name": "Command Injection",
        "description": "User input flows to command execution",
        "severity": "CRITICAL",
        "cwe_id": "CWE-78",
        "sources": ["main", "read.*", "gets", "fgets", "scanf", "recv"],
        "sinks": ["system", "exec.*", "popen", "ShellExecute"],
        "source_count": 6,
        "sink_count": 4
    }
}
```

**示例：**
```python
# 获取命令注入规则详情
details = taint_service.get_rule_details("Command Injection")
print(f"Sources: {details['rule']['sources']}")
print(f"Sinks: {details['rule']['sinks']}")
```

---

## 内置漏洞检测规则

| 规则名称 | 严重程度 | CWE ID | 描述 |
|---------|---------|--------|------|
| Command Injection | CRITICAL | CWE-78 | 命令注入漏洞 |
| SQL Injection | CRITICAL | CWE-89 | SQL 注入漏洞 |
| Path Traversal | HIGH | CWE-22 | 路径遍历漏洞 |
| XSS | MEDIUM | CWE-79 | 跨站脚本攻击 |
| Buffer Overflow | HIGH | CWE-120 | 缓冲区溢出 |
| Format String | HIGH | CWE-134 | 格式化字符串漏洞 |

---

## 错误处理

所有服务方法都返回统一的结果格式：

**成功：**
```python
{
    "success": True,
    # ... 具体结果数据
}
```

**失败：**
```python
{
    "success": False,
    "error": "错误描述信息"
}
```

**常见错误类型：**
- 查询执行失败
- 函数/变量不存在
- 规则名称无效
- 连接超时

---

## 完整使用示例

```python
import asyncio
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService

async def analyze_project():
    # 初始化 Joern 服务器
    server = JoernServerManager()
    await server.start()
    
    try:
        # 导入代码
        await server.import_code("/path/to/project", "my_project")
        
        # 初始化服务
        executor = QueryExecutor(server)
        callgraph = CallGraphService(executor)
        dataflow = DataFlowService(executor)
        taint = TaintAnalysisService(executor)
        
        # 1. 调用图分析
        callers = await callgraph.get_callers("vulnerable_func")
        print(f"调用者: {callers['callers']}")
        
        # 2. 数据流分析
        flows = await dataflow.track_dataflow("gets", "strcpy")
        print(f"数据流: {flows['flows']}")
        
        # 3. 漏洞检测
        vulns = await taint.find_vulnerabilities(severity="CRITICAL")
        print(f"发现 {vulns['total_count']} 个高危漏洞")
        
    finally:
        await server.stop()

# 运行分析
asyncio.run(analyze_project())
```

