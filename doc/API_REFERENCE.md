# Joern MCP Server API参考

## 📚 目录

1. [项目管理工具](#项目管理工具)
2. [基础查询工具](#基础查询工具)
3. [调用图分析工具](#调用图分析工具)
4. [数据流分析工具](#数据流分析工具)
5. [污点分析工具](#污点分析工具)
6. [控制流分析工具](#控制流分析工具)
7. [批量操作工具](#批量操作工具)
8. [导出工具](#导出工具)
9. [MCP Resources](#mcp-resources)
10. [MCP Prompts](#mcp-prompts)

---

## 项目管理工具

### parse_project

导入代码项目到Joern进行分析。

**参数**:
- `source_path` (str): 源代码路径
- `project_name` (str): 项目名称

**返回**: Dict[str, Any]

**示例**:
```python
result = await parse_project("/path/to/code", "my-project")
```

**返回值**:
```json
{
  "success": true,
  "project": "my-project",
  "message": "Project imported successfully"
}
```

---

### list_projects

列出所有已加载的项目。

**参数**: 无

**返回**: List[str]

**示例**:
```python
projects = await list_projects()
```

**返回值**:
```json
["project1", "project2", "project3"]
```

---

### delete_project

删除指定项目。

**参数**:
- `project_name` (str): 项目名称

**返回**: Dict[str, Any]

**示例**:
```python
result = await delete_project("my-project")
```

---

## 基础查询工具

### get_function_code

获取函数的源代码。

**参数**:
- `function_name` (str): 函数名称
- `file_path` (Optional[str]): 文件路径过滤

**返回**: List[str]

**示例**:
```python
code = await get_function_code("main", file_path="main.c")
```

**返回值**:
```json
[
  "int main() {\n    printf(\"Hello\");\n    return 0;\n}"
]
```

---

### get_function_details

获取函数的详细信息。

**参数**:
- `function_name` (str): 函数名称
- `file_path` (Optional[str]): 文件路径过滤

**返回**: List[Dict[str, Any]]

**示例**:
```python
details = await get_function_details("main")
```

**返回值**:
```json
[
  {
    "name": "main",
    "signature": "int main()",
    "fullName": "main:int()",
    "filename": "main.c",
    "lineNumber": 10,
    "code": "..."
  }
]
```

---

### list_all_functions

列出所有函数。

**参数**:
- `file_path` (Optional[str]): 文件路径过滤

**返回**: List[str]

**示例**:
```python
functions = await list_all_functions(file_path="utils.c")
```

---

### search_code_pattern

搜索代码模式。

**参数**:
- `pattern` (str): 搜索模式（正则表达式）
- `file_path` (Optional[str]): 文件路径过滤

**返回**: List[Dict[str, Any]]

**示例**:
```python
results = await search_code_pattern("strcpy")
```

**返回值**:
```json
[
  {
    "name": "process",
    "fullName": "process:void(char*)",
    "filename": "main.c",
    "lineNumber": 15,
    "code": "strcpy(dest, src);"
  }
]
```

---

## 调用图分析工具

### get_callers

获取函数的调用者。

**参数**:
- `function_name` (str): 函数名称
- `depth` (int): 深度（默认1，最大10）

**返回**: Dict[str, Any]

**示例**:
```python
callers = await get_callers("vulnerable_func", depth=2)
```

**返回值**:
```json
{
  "success": true,
  "function": "vulnerable_func",
  "depth": 2,
  "callers": [
    {
      "name": "main",
      "filename": "main.c",
      "lineNumber": 10
    }
  ],
  "count": 1
}
```

---

### get_callees

获取函数调用的其他函数。

**参数**:
- `function_name` (str): 函数名称
- `depth` (int): 深度（默认1，最大10）

**返回**: Dict[str, Any]

**示例**:
```python
callees = await get_callees("main", depth=2)
```

---

### get_call_chain

获取函数的调用链。

**参数**:
- `function_name` (str): 函数名称
- `max_depth` (int): 最大深度（默认5，最大10）
- `direction` (str): 方向 ("up"或"down")

**返回**: Dict[str, Any]

**示例**:
```python
chain = await get_call_chain("process", max_depth=5, direction="up")
```

---

### get_call_graph

获取完整的调用图。

**参数**:
- `function_name` (str): 函数名称
- `include_callers` (bool): 包含调用者（默认True）
- `include_callees` (bool): 包含被调用者（默认True）
- `depth` (int): 深度（默认2，最大5）

**返回**: Dict[str, Any]

**示例**:
```python
graph = await get_call_graph("main", depth=2)
```

**返回值**:
```json
{
  "success": true,
  "function": "main",
  "nodes": [
    {"id": "main", "type": "target"},
    {"id": "init", "type": "callee"},
    {"id": "process", "type": "callee"}
  ],
  "edges": [
    {"from": "main", "to": "init", "type": "calls"},
    {"from": "main", "to": "process", "type": "calls"}
  ],
  "node_count": 3,
  "edge_count": 2
}
```

---

## 数据流分析工具

### track_dataflow

追踪方法间的数据流。

**参数**:
- `source_method` (str): 源方法名称
- `sink_method` (str): 汇方法名称
- `max_flows` (int): 最大流数量（默认10，最大50）

**返回**: Dict[str, Any]

**示例**:
```python
flows = await track_dataflow("gets", "system", max_flows=5)
```

**返回值**:
```json
{
  "success": true,
  "source_method": "gets",
  "sink_method": "system",
  "flows": [
    {
      "source": {
        "code": "gets(buf)",
        "method": "main",
        "file": "main.c",
        "line": 10
      },
      "sink": {
        "code": "system(cmd)",
        "method": "execute",
        "file": "main.c",
        "line": 20
      },
      "pathLength": 5
    }
  ],
  "count": 1
}
```

---

### analyze_variable_flow

分析变量的数据流。

**参数**:
- `variable_name` (str): 变量名称
- `sink_method` (Optional[str]): 目标汇方法
- `max_flows` (int): 最大流数量（默认10，最大50）

**返回**: Dict[str, Any]

**示例**:
```python
flows = await analyze_variable_flow("user_input", sink_method="system")
```

---

### find_data_dependencies

查找函数中的数据依赖。

**参数**:
- `function_name` (str): 函数名称
- `variable_name` (Optional[str]): 变量名称

**返回**: Dict[str, Any]

**示例**:
```python
deps = await find_data_dependencies("main", variable_name="buf")
```

---

## 污点分析工具

### find_vulnerabilities

查找代码中的安全漏洞。

**参数**:
- `rule_name` (Optional[str]): 规则名称
- `severity` (Optional[str]): 严重程度 ("CRITICAL", "HIGH", "MEDIUM", "LOW")
- `max_flows` (int): 每个规则的最大流数量（默认10，最大50）

**返回**: Dict[str, Any]

**示例**:
```python
vulns = await find_vulnerabilities(severity="CRITICAL")
```

**返回值**:
```json
{
  "success": true,
  "vulnerabilities": [
    {
      "vulnerability": "Command Injection",
      "severity": "CRITICAL",
      "cwe_id": "CWE-78",
      "description": "...",
      "source": {...},
      "sink": {...},
      "pathLength": 5
    }
  ],
  "total_count": 1,
  "summary": {
    "CRITICAL": 1,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0
  },
  "rules_checked": 6
}
```

---

### check_taint_flow

检查特定的污点流。

**参数**:
- `source_pattern` (str): 源模式（正则表达式）
- `sink_pattern` (str): 汇模式（正则表达式）
- `max_flows` (int): 最大流数量（默认10，最大50）

**返回**: Dict[str, Any]

**示例**:
```python
flow = await check_taint_flow("gets", "system")
```

---

### list_vulnerability_rules

列出所有可用的漏洞检测规则。

**参数**: 无

**返回**: Dict[str, Any]

**示例**:
```python
rules = await list_vulnerability_rules()
```

**返回值**:
```json
{
  "success": true,
  "rules": [
    {
      "name": "Command Injection",
      "severity": "CRITICAL",
      "cwe_id": "CWE-78",
      "description": "...",
      "source_count": 10,
      "sink_count": 8
    }
  ],
  "count": 6
}
```

---

### get_rule_details

获取特定规则的详细信息。

**参数**:
- `rule_name` (str): 规则名称

**返回**: Dict[str, Any]

**示例**:
```python
rule = await get_rule_details("Command Injection")
```

**返回值**:
```json
{
  "success": true,
  "rule": {
    "name": "Command Injection",
    "description": "...",
    "severity": "CRITICAL",
    "cwe_id": "CWE-78",
    "sources": ["gets", "scanf", ...],
    "sinks": ["system", "exec", ...],
    "source_count": 10,
    "sink_count": 8
  }
}
```

---

## 控制流分析工具

### get_control_flow_graph

获取函数的控制流图。

**参数**:
- `function_name` (str): 函数名称
- `format` (str): 输出格式 ("dot"或"json")

**返回**: Dict[str, Any]

**示例**:
```python
cfg = await get_control_flow_graph("main", format="dot")
```

**返回值**:
```json
{
  "success": true,
  "function": "main",
  "cfg": "digraph CFG { ... }",
  "format": "dot"
}
```

---

### get_dominators

获取函数的支配树。

**参数**:
- `function_name` (str): 函数名称
- `format` (str): 输出格式 ("dot"或"json")

**返回**: Dict[str, Any]

**示例**:
```python
dom = await get_dominators("main")
```

---

### analyze_control_structures

分析函数中的控制结构。

**参数**:
- `function_name` (str): 函数名称

**返回**: Dict[str, Any]

**示例**:
```python
structures = await analyze_control_structures("main")
```

**返回值**:
```json
{
  "success": true,
  "function": "main",
  "structures": [
    {
      "type": "IF",
      "code": "if (x > 0)",
      "line": 10,
      "file": "main.c"
    },
    {
      "type": "FOR",
      "code": "for (i = 0; i < n; i++)",
      "line": 15,
      "file": "main.c"
    }
  ],
  "count": 2
}
```

---

## 批量操作工具

### batch_query

批量执行多个查询。

**参数**:
- `queries` (List[str]): 查询列表（最多20个）
- `timeout` (int): 超时时间（秒）

**返回**: Dict[str, Any]

**示例**:
```python
queries = [
    "cpg.method.name.l",
    "cpg.call.name.l"
]
results = await batch_query(queries, timeout=300)
```

**返回值**:
```json
{
  "success": true,
  "results": [
    {
      "query_index": 0,
      "success": true,
      "result": "[...]"
    },
    {
      "query_index": 1,
      "success": true,
      "result": "[...]"
    }
  ],
  "total": 2,
  "succeeded": 2,
  "failed": 0
}
```

---

### batch_function_analysis

批量分析多个函数。

**参数**:
- `function_names` (List[str]): 函数名称列表（最多10个）

**返回**: Dict[str, Any]

**示例**:
```python
functions = ["main", "init", "cleanup"]
analysis = await batch_function_analysis(functions)
```

**返回值**:
```json
{
  "success": true,
  "analyses": {
    "main": {
      "name": "main",
      "signature": "int main()",
      "filename": "main.c",
      "lineNumber": 10,
      "lineNumberEnd": 50,
      "code": "...",
      "parameterCount": 0,
      "complexity": 5
    },
    "init": {...},
    "cleanup": {...}
  },
  "count": 3,
  "analyzed": 3
}
```

---

## 导出工具

### export_cpg

导出CPG到文件。

**参数**:
- `project_name` (str): 项目名称
- `output_path` (str): 输出文件路径
- `format` (str): 导出格式 ("bin", "json", "dot")

**返回**: Dict[str, Any]

**示例**:
```python
result = await export_cpg("my-project", "/tmp/cpg.bin", "bin")
```

---

### export_analysis_results

导出分析结果到文件。

**参数**:
- `results` (Dict[str, Any]): 分析结果数据
- `output_path` (str): 输出文件路径
- `format` (str): 导出格式 ("json", "markdown", "csv")

**返回**: Dict[str, Any]

**示例**:
```python
await export_analysis_results(
    results,
    "/reports/analysis.json",
    "json"
)
```

**返回值**:
```json
{
  "success": true,
  "output_path": "/reports/analysis.json",
  "format": "json",
  "size_bytes": 1024
}
```

---

## MCP Resources

### project://list

返回所有已加载项目列表。

**URI**: `project://list`

**示例**:
```
访问: project://list
```

---

### project://{project_name}/info

返回项目详细信息。

**URI**: `project://{project_name}/info`

**示例**:
```
访问: project://my-project/info
```

---

### project://{project_name}/functions

返回项目中的所有函数。

**URI**: `project://{project_name}/functions`

**示例**:
```
访问: project://my-project/functions
```

---

### project://{project_name}/vulnerabilities

返回项目中发现的漏洞。

**URI**: `project://{project_name}/vulnerabilities`

**示例**:
```
访问: project://my-project/vulnerabilities
```

---

## MCP Prompts

### security_audit_prompt

安全审计提示模板。

**参数**:
- `project_name` (str): 项目名称（默认"unknown"）

**示例**:
```python
prompt = await security_audit_prompt("my-project")
```

---

### code_understanding_prompt

代码理解提示模板。

**参数**:
- `function_name` (str): 函数名称（默认"unknown"）

**示例**:
```python
prompt = await code_understanding_prompt("main")
```

---

### refactoring_analysis_prompt

重构分析提示模板。

**参数**:
- `function_name` (str): 函数名称（默认"unknown"）

**示例**:
```python
prompt = await refactoring_analysis_prompt("complex_function")
```

---

### vulnerability_investigation_prompt

漏洞调查提示模板。

**参数**:
- `vulnerability_type` (str): 漏洞类型（默认"Command Injection"）

**示例**:
```python
prompt = await vulnerability_investigation_prompt("SQL Injection")
```

---

### batch_analysis_prompt

批量分析提示模板。

**参数**:
- `function_list` (str): 函数列表，逗号分隔（默认"main,init,process"）

**示例**:
```python
prompt = await batch_analysis_prompt("main,init,cleanup")
```

---

## 错误处理

所有API调用的返回值都包含`success`字段：

```json
{
  "success": true,  // 或 false
  "error": "错误信息"  // 仅在失败时存在
}
```

**错误类型**:
- `Query executor not initialized`: Joern未初始化
- `Query timeout`: 查询超时
- `Invalid parameter`: 参数错误
- `Query failed`: 查询执行失败

---

**版本**: 0.5.0-dev  
**最后更新**: 2025-11-27

