# API 参考

本文档提供 Joern MCP Server 所有工具的完整API说明。

---

## 📋 工具列表

| 类别 | 工具名称 | 描述 |
|------|---------|------|
| 系统 | `health_check` | 检查服务器健康状态 |
| 项目 | `parse_project` | 解析代码项目生成CPG |
| 项目 | `list_projects` | 列出所有已解析的项目 |
| 项目 | `delete_project` | 删除指定项目 |
| 调用图 | `get_callers` | 获取函数的调用者 |
| 调用图 | `get_callees` | 获取函数调用的其他函数 |
| 调用图 | `get_call_chain` | 获取函数的调用链 |
| 调用图 | `get_call_graph` | 获取函数的完整调用图 |
| 数据流 | `track_dataflow` | 追踪数据流路径 |
| 数据流 | `analyze_variable_flow` | 分析变量的数据流 |
| 数据流 | `find_data_dependencies` | 查找数据依赖关系 |
| 漏洞检测 | `find_vulnerabilities` | 查找代码中的安全漏洞 |
| 漏洞检测 | `check_taint_flow` | 检查特定的污点流 |
| 漏洞检测 | `list_vulnerability_rules` | 列出所有漏洞检测规则 |
| 漏洞检测 | `get_rule_details` | 获取规则详细信息 |
| 查询 | `execute_query` | 执行自定义CPGQL查询 |

---

## 🔧 系统工具

### health_check

检查服务器健康状态。

**参数**: 无

**返回值**:
```json
{
    "status": "healthy",
    "joern_endpoint": "localhost:8080"
}
```

**示例**:
```python
result = await health_check()
if result["status"] == "healthy":
    print("服务器正常运行")
```

---

## 📂 项目管理工具

### parse_project

解析代码项目生成CPG。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `source_path` | string | ✅ | - | 源代码路径 |
| `project_name` | string | ❌ | 目录名 | 项目名称 |
| `language` | string | ❌ | "auto" | 编程语言 |

**支持的语言**: `auto`, `c`, `java`, `javascript`, `python`, `kotlin`

**返回值**:
```json
{
    "success": true,
    "project_name": "my-project",
    "source_path": "/path/to/project",
    "language": "c",
    "message": "Project parsed successfully",
    "output": "..."
}
```

**示例**:
```python
# 自动检测语言
result = await parse_project("/path/to/project")

# 指定语言
result = await parse_project("/path/to/java", "my-java-app", language="java")
```

---

### list_projects

列出所有已解析的项目。

**参数**: 无

**返回值**:
```json
{
    "success": true,
    "workspace_info": "...",
    "raw_output": {...}
}
```

---

### delete_project

删除指定项目的CPG。

**参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `project_name` | string | ✅ | 要删除的项目名称 |

**返回值**:
```json
{
    "success": true,
    "project_name": "my-project",
    "message": "Project deleted successfully"
}
```

---

## 📞 调用图工具

### get_callers

获取调用目标函数的函数列表。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `function_name` | string | ✅ | - | - | 目标函数名称 |
| `depth` | int | ❌ | 1 | 1-10 | 调用深度 |

**返回值**:
```json
{
    "success": true,
    "function": "vulnerable_function",
    "depth": 2,
    "callers": [
        {
            "name": "main",
            "filename": "main.c",
            "lineNumber": 42
        }
    ],
    "count": 1
}
```

**示例**:
```python
# 获取直接调用者
callers = await get_callers("strcpy")

# 获取多层调用者
callers = await get_callers("strcpy", depth=3)
```

---

### get_callees

获取目标函数调用的其他函数。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `function_name` | string | ✅ | - | - | 目标函数名称 |
| `depth` | int | ❌ | 1 | 1-10 | 调用深度 |

**返回值**:
```json
{
    "success": true,
    "function": "main",
    "depth": 1,
    "callees": [
        {
            "name": "printf",
            "filename": "stdio.h",
            "lineNumber": 0
        }
    ],
    "count": 5
}
```

---

### get_call_chain

获取函数的完整调用链。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `function_name` | string | ✅ | - | - | 目标函数名称 |
| `max_depth` | int | ❌ | 5 | 1-10 | 最大深度 |
| `direction` | string | ❌ | "up" | up/down | 追踪方向 |

**方向说明**:
- `up`: 向上追踪调用者链（谁调用了这个函数）
- `down`: 向下追踪被调用者链（这个函数调用了谁）

**返回值**:
```json
{
    "success": true,
    "function": "process_input",
    "direction": "up",
    "max_depth": 5,
    "chain": [
        {"name": "handle_request", "filename": "server.c", "depth": 1},
        {"name": "main", "filename": "main.c", "depth": 2}
    ],
    "count": 2
}
```

---

### get_call_graph

获取函数的完整调用图（包含节点和边）。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `function_name` | string | ✅ | - | - | 中心函数名称 |
| `include_callers` | bool | ❌ | true | - | 包含调用者 |
| `include_callees` | bool | ❌ | true | - | 包含被调用者 |
| `depth` | int | ❌ | 2 | 1-5 | 深度 |

**返回值**:
```json
{
    "success": true,
    "function": "main",
    "nodes": [
        {"id": "main", "name": "main", "type": "center"},
        {"id": "printf", "name": "printf", "type": "callee"}
    ],
    "edges": [
        {"from": "main", "to": "printf", "type": "calls"}
    ],
    "node_count": 10,
    "edge_count": 12
}
```

---

## 🌊 数据流工具

### track_dataflow

追踪从源方法到汇方法的数据流。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `source_method` | string | ✅ | - | - | 源方法名称 |
| `sink_method` | string | ✅ | - | - | 汇方法名称 |
| `max_flows` | int | ❌ | 10 | 1-50 | 最大流数量 |

**返回值**:
```json
{
    "success": true,
    "source_method": "gets",
    "sink_method": "system",
    "flows": [
        {
            "source": {"code": "gets(buf)", "file": "main.c", "line": 10},
            "sink": {"code": "system(cmd)", "file": "main.c", "line": 20},
            "pathLength": 5
        }
    ],
    "count": 1
}
```

---

### analyze_variable_flow

分析特定变量的数据流向。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `variable_name` | string | ✅ | - | - | 变量名称 |
| `sink_method` | string | ❌ | null | - | 目标汇方法 |
| `max_flows` | int | ❌ | 10 | 1-50 | 最大流数量 |

**返回值**:
```json
{
    "success": true,
    "variable": "user_input",
    "sink_method": "system",
    "flows": [
        {
            "variable": "user_input",
            "source": {"code": "...", "file": "...", "line": 10},
            "sink": {"code": "...", "method": "system", "file": "...", "line": 20},
            "pathLength": 3
        }
    ],
    "count": 1
}
```

---

### find_data_dependencies

查找函数中的数据依赖关系。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `function_name` | string | ✅ | - | 函数名称 |
| `variable_name` | string | ❌ | null | 特定变量 |

**返回值**:
```json
{
    "success": true,
    "function": "main",
    "variable": "buf",
    "dependencies": [
        {
            "variable": "buf",
            "source": "gets",
            "type": "input"
        }
    ],
    "count": 3
}
```

---

## 🛡️ 漏洞检测工具

### find_vulnerabilities

使用内置规则查找安全漏洞。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `rule_name` | string | ❌ | null | - | 规则名称 |
| `severity` | string | ❌ | null | CRITICAL/HIGH/MEDIUM/LOW | 严重级别 |
| `max_flows` | int | ❌ | 10 | 1-50 | 每规则最大流数 |

**内置规则**:
- `Command Injection` (CRITICAL, CWE-78)
- `SQL Injection` (CRITICAL, CWE-89)
- `Buffer Overflow` (CRITICAL, CWE-120)
- `Path Traversal` (HIGH, CWE-22)
- `Format String` (HIGH, CWE-134)
- `Use After Free` (CRITICAL, CWE-416)

**返回值**:
```json
{
    "success": true,
    "vulnerabilities": [
        {
            "vulnerability": "Command Injection",
            "severity": "CRITICAL",
            "cwe_id": "CWE-78",
            "source": {"code": "...", "file": "...", "line": 10},
            "sink": {"code": "...", "file": "...", "line": 20}
        }
    ],
    "total_count": 5,
    "summary": {"CRITICAL": 3, "HIGH": 2},
    "rules_checked": 6
}
```

---

### check_taint_flow

检查自定义的污点流（源-汇对）。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 范围 | 描述 |
|------|------|------|--------|------|------|
| `source_pattern` | string | ✅ | - | 正则 | 源模式 |
| `sink_pattern` | string | ✅ | - | 正则 | 汇模式 |
| `max_flows` | int | ❌ | 10 | 1-50 | 最大流数量 |

**示例模式**:
- 源: `"gets|scanf|fgets|read"`
- 汇: `"system|exec|popen|eval"`

**返回值**:
```json
{
    "success": true,
    "source_pattern": "gets|scanf",
    "sink_pattern": "system|exec",
    "flows": [...],
    "count": 3
}
```

---

### list_vulnerability_rules

列出所有可用的漏洞检测规则。

**参数**: 无

**返回值**:
```json
{
    "success": true,
    "rules": [
        {
            "name": "Command Injection",
            "severity": "CRITICAL",
            "cwe_id": "CWE-78",
            "description": "检测命令注入漏洞"
        }
    ],
    "count": 6
}
```

---

### get_rule_details

获取特定规则的详细信息。

**参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `rule_name` | string | ✅ | 规则名称 |

**返回值**:
```json
{
    "success": true,
    "rule": {
        "name": "Command Injection",
        "description": "检测从用户输入到命令执行的数据流",
        "severity": "CRITICAL",
        "cwe_id": "CWE-78",
        "sources": ["gets", "scanf", "fgets", "read", "recv"],
        "sinks": ["system", "popen", "exec", "execve"]
    }
}
```

---

## ⚙️ 查询工具

### execute_query

执行自定义CPGQL查询。

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | CPGQL查询语句 |
| `format` | string | ❌ | "json" | 输出格式 (json/dot) |
| `timeout` | int | ❌ | null | 超时时间（秒） |

**返回值**:
```json
{
    "success": true,
    "result": "...",
    "raw": {...}
}
```

**示例查询**:
```python
# 获取所有方法名
await execute_query("cpg.method.name.l")

# 查找特定调用
await execute_query('cpg.call.name("strcpy").l')

# 导出DOT格式
await execute_query("cpg.method.name('main').dotAst.head", format="dot")
```

---

## ❌ 错误处理

所有工具在失败时返回统一格式：

```json
{
    "success": false,
    "error": "错误描述"
}
```

**常见错误**:
| 错误 | 描述 | 解决方案 |
|------|------|---------|
| `Query executor not initialized` | 服务器未初始化 | 重启服务器 |
| `Depth must be between 1 and 10` | 参数超出范围 | 调整参数值 |
| `Path does not exist` | 路径不存在 | 检查路径 |
| `Query timeout` | 查询超时 | 增加超时或简化查询 |

---

## 📊 性能建议

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `depth` | 1-3 | 深度越大性能越差 |
| `max_flows` | 10-20 | 过多会增加处理时间 |
| `timeout` | 60-300 | 根据项目大小调整 |

