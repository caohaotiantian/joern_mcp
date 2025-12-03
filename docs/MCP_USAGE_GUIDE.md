# MCP 完整使用指南

本指南详细介绍如何通过 MCP (Model Context Protocol) 使用 Joern MCP Server 进行代码分析。

---

## 📋 目录

- [服务器启动](#服务器启动)
- [MCP 客户端连接](#mcp-客户端连接)
- [完整分析流程](#完整分析流程)
- [工具详解](#工具详解)
- [实际案例](#实际案例)

---

## 🚀 服务器启动

### 1. 启动 MCP 服务器

```bash
# 进入项目目录
cd /path/to/joern_mcp

# 激活虚拟环境
source .venv/bin/activate

# 启动服务器（HTTP 模式）
python -m joern_mcp
```

服务器默认启动在 `http://localhost:8000`（streamable-http 模式）。

### 2. 确认服务状态

服务器启动后会显示：
```
============================================================
Joern MCP Server
============================================================
Joern Server: localhost:8080
Log level: INFO
============================================================
```

---

## 🔌 MCP 客户端连接

### 方式一：使用 Claude Desktop

在 Claude Desktop 配置文件中添加：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "joern": {
      "command": "python",
      "args": ["-m", "joern_mcp"],
      "cwd": "/path/to/joern_mcp",
      "env": {
        "VIRTUAL_ENV": "/path/to/joern_mcp/.venv",
        "PATH": "/path/to/joern_mcp/.venv/bin:$PATH"
      }
    }
  }
}
```

### 方式二：使用 Cursor IDE

在 Cursor 设置中配置 MCP 服务器，指向 Joern MCP Server。

### 方式三：使用 Python MCP 客户端

```python
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def connect_to_server():
    async with stdio_client(
        command="python",
        args=["-m", "joern_mcp"],
        cwd="/path/to/joern_mcp"
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 列出可用工具
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])
            
            # 调用工具
            result = await session.call_tool("health_check", {})
            print("Health check:", result)

asyncio.run(connect_to_server())
```

---

## 🔄 完整分析流程

以下是一个完整的代码安全分析流程：

### 步骤 1：解析项目（构建 CPG）

```
工具: parse_project
参数:
  - source_path: "/path/to/your/code"  # 源代码路径
  - project_name: "my-project"          # 项目名称（可选）
  - language: "auto"                    # 语言（可选：auto, c, java, javascript, python）
```

**示例请求（通过 Claude）：**
```
请解析位于 /Users/me/projects/vulnerable_app 的代码项目
```

**预期响应：**
```json
{
  "success": true,
  "project_name": "vulnerable_app",
  "source_path": "/Users/me/projects/vulnerable_app",
  "language": "auto",
  "message": "Project parsed successfully"
}
```

### 步骤 2：列出项目中的函数

```
工具: list_functions
参数:
  - name_filter: null  # 可选，正则表达式过滤
  - limit: 100         # 返回数量限制
```

**示例请求：**
```
列出项目中所有包含 "main" 的函数
```

**预期响应：**
```json
{
  "success": true,
  "functions": [
    {"name": "main", "filename": "main.c", "lineNumber": 10},
    {"name": "main_helper", "filename": "utils.c", "lineNumber": 25}
  ],
  "count": 2
}
```

### 步骤 3：搜索危险函数调用

```
工具: search_code
参数:
  - pattern: "strcpy|gets|sprintf"  # 搜索模式
  - scope: "calls"                   # 搜索范围
```

**示例请求：**
```
搜索代码中所有对 strcpy、gets、sprintf 的调用
```

**预期响应：**
```json
{
  "success": true,
  "matches": [
    {"code": "strcpy(buf, input)", "type": "CALL", "file": "main.c", "line": 42},
    {"code": "gets(buffer)", "type": "CALL", "file": "input.c", "line": 15}
  ],
  "count": 2,
  "scope": "calls"
}
```

### 步骤 4：执行漏洞检测

```
工具: find_vulnerabilities
参数:
  - rule_name: null      # 可选，指定规则名称
  - severity: "CRITICAL" # 可选，按严重程度过滤
  - max_flows: 10        # 每个规则最大流数量
```

**示例请求：**
```
扫描项目中所有高危和严重漏洞
```

**预期响应：**
```json
{
  "success": true,
  "vulnerabilities": [
    {
      "vulnerability": "Command Injection",
      "severity": "CRITICAL",
      "cwe_id": "CWE-78",
      "source": {"code": "char* cmd", "file": "main.c", "line": 10},
      "sink": {"code": "system(cmd)", "file": "main.c", "line": 25},
      "pathLength": 4
    }
  ],
  "total_count": 1,
  "summary": {"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
}
```

### 步骤 5：检查特定污点流

```
工具: check_taint_flow
参数:
  - source_pattern: "gets|fgets|scanf"  # 源函数模式
  - sink_pattern: "system|exec|popen"   # 汇函数模式
  - max_flows: 20                        # 最大流数量
```

**示例请求：**
```
检查从用户输入函数到系统命令执行的数据流
```

### 步骤 6：获取函数详细代码

```
工具: get_function_code
参数:
  - function_name: "vulnerable_func"  # 函数名
  - file_filter: null                  # 可选，文件过滤
```

**示例请求：**
```
获取 vulnerable_func 函数的完整源代码
```

### 步骤 7：执行自定义查询

```
工具: execute_query
参数:
  - query: "cpg.method.name.l"  # Joern CPGQL 查询
  - format: "json"               # 输出格式
  - timeout: null                # 超时时间（可选）
```

**示例请求：**
```
执行自定义查询：获取所有方法名
```

---

## 🛠️ 工具详解

### 项目管理工具

| 工具 | 功能 | 必需参数 |
|------|------|---------|
| `parse_project` | 解析代码生成 CPG | `source_path` |
| `list_projects` | 列出已解析项目 | 无 |
| `delete_project` | 删除项目 CPG | `project_name` |

### 代码查询工具

| 工具 | 功能 | 必需参数 |
|------|------|---------|
| `get_function_code` | 获取函数源代码 | `function_name` |
| `list_functions` | 列出所有函数 | 无 |
| `search_code` | 搜索代码 | `pattern` |

### 安全分析工具

| 工具 | 功能 | 必需参数 |
|------|------|---------|
| `find_vulnerabilities` | 查找安全漏洞 | 无 |
| `check_taint_flow` | 检查污点流 | `source_pattern`, `sink_pattern` |
| `list_vulnerability_rules` | 列出检测规则 | 无 |
| `get_rule_details` | 获取规则详情 | `rule_name` |

### 通用工具

| 工具 | 功能 | 必需参数 |
|------|------|---------|
| `health_check` | 检查服务器状态 | 无 |
| `execute_query` | 执行自定义查询 | `query` |

---

## 💡 实际案例

### 案例 1：分析 C 项目的缓冲区溢出

**对话示例：**

```
用户: 请分析 /home/user/vulnerable_app 项目的安全性

AI: 我来帮你分析这个项目。首先解析代码...
    [调用 parse_project]
    
    项目解析成功！接下来扫描安全漏洞...
    [调用 find_vulnerabilities]
    
    发现以下安全问题：
    
    🔴 严重漏洞 (2个):
    1. 命令注入 - main.c:25
       从 gets() 到 system() 的数据流
       
    2. 缓冲区溢出 - input.c:42
       使用了不安全的 strcpy()
    
    🟠 高危漏洞 (1个):
    1. 格式化字符串 - print.c:18
       printf() 直接使用用户输入
    
    建议修复顺序：先处理命令注入，再处理缓冲区溢出...
```

### 案例 2：追踪敏感数据流

**对话示例：**

```
用户: 检查项目中密码数据是否安全处理

AI: 让我追踪密码相关的数据流...
    [调用 search_code pattern="password" scope="identifiers"]
    
    找到 5 处密码相关标识符。
    
    [调用 check_taint_flow source_pattern="password" sink_pattern="printf|log|write"]
    
    ⚠️ 发现敏感数据泄露风险：
    
    1. auth.c:35 - 密码被写入日志
       password -> sprintf -> fprintf(log_file)
    
    建议：使用掩码处理敏感信息再记录日志
```

### 案例 3：代码理解

**对话示例：**

```
用户: 解释 process_request 函数的作用

AI: 让我获取这个函数的代码...
    [调用 get_function_code function_name="process_request"]
    
    [调用 search_code pattern="process_request" scope="calls"]
    
    这个函数位于 server.c:120，主要功能是：
    
    1. 接收 HTTP 请求
    2. 解析请求头和请求体
    3. 调用对应的处理器
    4. 返回响应
    
    该函数被以下位置调用：
    - main.c:55 (主循环中)
    - worker.c:30 (工作线程中)
    
    潜在问题：第 135 行未验证请求长度...
```

---

## 📝 最佳实践

1. **先解析后分析**：始终先调用 `parse_project` 构建 CPG
2. **增量分析**：对大型项目，可以按目录分批解析
3. **组合使用工具**：结合多个工具获得全面视图
4. **保存结果**：重要分析结果应导出保存
5. **定期重新解析**：代码更新后需要重新解析 CPG

---

## ❓ 常见问题

### Q: 解析大型项目很慢怎么办？

增加 JVM 内存：
```bash
export _JAVA_OPTIONS="-Xmx16g"
python -m joern_mcp
```

### Q: 如何只分析特定文件？

在 `search_code` 或 `get_function_code` 中使用 `file_filter` 参数。

### Q: 自定义查询语法在哪里学习？

参考 [Joern 文档](https://docs.joern.io/cpgql/reference-card/)

---

## 🔗 相关文档

- [API 参考](./API_REFERENCE.md)
- [服务层 API](./SERVICE_API.md)
- [安装指南](./INSTALLATION.md)
- [示例项目](../examples/)

