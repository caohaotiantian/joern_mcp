# Joern MCP Server 使用指南

## 📚 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [工具使用](#工具使用)
4. [资源访问](#资源访问)
5. [提示模板](#提示模板)
6. [实战场景](#实战场景)
7. [最佳实践](#最佳实践)

---

## 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd joern_mcp

# 安装依赖
pip install -r requirements.txt

# 或使用 poetry
poetry install
```

### 启动服务

```bash
# 启动Joern MCP Server
python -m joern_mcp

# 或使用配置文件
python -m joern_mcp --config .env
```

### 配置Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "joern": {
      "command": "python",
      "args": ["-m", "joern_mcp"],
      "env": {
        "JOERN_SERVER_HOST": "localhost",
        "JOERN_SERVER_PORT": "8080"
      }
    }
  }
}
```

---

## 核心概念

### 1. 代码属性图 (CPG)

Joern使用代码属性图来表示代码结构：
- **节点**: 代码元素（函数、变量、调用等）
- **边**: 元素之间的关系（调用、数据流等）

### 2. 静态分析

支持的分析类型：
- **调用图分析**: 函数间的调用关系
- **数据流分析**: 数据在代码中的流动
- **控制流分析**: 程序的执行路径
- **污点分析**: 从输入到输出的数据传播

### 3. MCP协议

Model Context Protocol提供三种核心能力：
- **Tools**: 可调用的分析功能
- **Resources**: 暴露的项目数据
- **Prompts**: 预定义的分析模板

---

## 工具使用

### 项目管理

#### 导入项目

```python
# 导入C/C++项目
await parse_project("/path/to/code", "my-project")

# 列出所有项目
projects = await list_projects()

# 删除项目
await delete_project("my-project")
```

### 基础查询

#### 获取函数信息

```python
# 获取函数代码
code = await get_function_code("main")

# 获取函数详情
details = await get_function_details("main")

# 列出所有函数
functions = await list_all_functions()

# 搜索代码模式
results = await search_code_pattern("strcpy")
```

### 调用图分析

#### 调用关系

```python
# 找出调用者
callers = await get_callers("vulnerable_func", depth=2)

# 找出被调用者
callees = await get_callees("main", depth=2)

# 获取调用链
chain = await get_call_chain("process", max_depth=5, direction="up")

# 完整调用图
graph = await get_call_graph("main", depth=2)
```

**输出示例**:
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

### 数据流分析

#### 追踪数据流

```python
# 方法间数据流
flows = await track_dataflow("gets", "system")

# 变量流向
var_flows = await analyze_variable_flow("user_input", "system")

# 数据依赖
deps = await find_data_dependencies("main", "buf")
```

**输出示例**:
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

### 污点分析

#### 漏洞检测

```python
# 查找所有CRITICAL漏洞
vulns = await find_vulnerabilities(severity="CRITICAL")

# 查找特定类型漏洞
sql_vulns = await find_vulnerabilities(rule_name="SQL Injection")

# 检查特定污点流
flow = await check_taint_flow("gets", "system")

# 列出所有规则
rules = await list_vulnerability_rules()

# 获取规则详情
rule = await get_rule_details("Command Injection")
```

**输出示例**:
```json
{
  "success": true,
  "vulnerabilities": [
    {
      "vulnerability": "Command Injection",
      "severity": "CRITICAL",
      "cwe_id": "CWE-78",
      "description": "用户输入未经验证直接传递到命令执行函数",
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
  "total_count": 1,
  "summary": {
    "CRITICAL": 1,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0
  }
}
```

### 控制流分析

#### CFG和控制结构

```python
# 获取控制流图
cfg = await get_control_flow_graph("main", format="dot")

# 获取支配树
dom = await get_dominators("main")

# 分析控制结构
structures = await analyze_control_structures("main")
```

**输出示例**:
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

### 批量操作

#### 批量查询

```python
# 批量执行查询
queries = [
    "cpg.method.name.l",
    "cpg.call.name.l"
]
results = await batch_query(queries, timeout=300)

# 批量分析函数
functions = ["main", "init", "cleanup"]
analysis = await batch_function_analysis(functions)
```

### 结果导出

#### 多格式导出

```python
# 导出为JSON
await export_analysis_results(
    results,
    "/reports/analysis.json",
    "json"
)

# 导出为Markdown
await export_analysis_results(
    results,
    "/reports/report.md",
    "markdown"
)

# 导出为CSV
await export_analysis_results(
    results,
    "/reports/data.csv",
    "csv"
)

# 导出CPG
await export_cpg("my-project", "/data/cpg.bin", "bin")
```

---

## 资源访问

### 项目资源

MCP Resources允许LLM直接访问项目数据：

#### 1. 项目列表

```
project://list
```

返回所有已加载的项目列表。

#### 2. 项目信息

```
project://{project_name}/info
```

返回项目的详细信息（方法数、文件数等）。

#### 3. 项目函数

```
project://{project_name}/functions
```

返回项目中的所有函数列表。

#### 4. 项目漏洞

```
project://{project_name}/vulnerabilities
```

返回项目中发现的漏洞列表。

---

## 提示模板

### 使用提示模板

MCP Prompts提供预定义的分析模板：

#### 1. 安全审计

```python
# 使用安全审计提示
prompt = await security_audit_prompt("my-project")
```

提供完整的安全审计流程指导。

#### 2. 代码理解

```python
# 使用代码理解提示
prompt = await code_understanding_prompt("main")
```

提供深入的代码理解分析步骤。

#### 3. 重构分析

```python
# 使用重构分析提示
prompt = await refactoring_analysis_prompt("complex_function")
```

提供重构影响分析和建议。

#### 4. 漏洞调查

```python
# 使用漏洞调查提示
prompt = await vulnerability_investigation_prompt("SQL Injection")
```

提供漏洞深入调查步骤。

#### 5. 批量分析

```python
# 使用批量分析提示
prompt = await batch_analysis_prompt("main,init,process")
```

提供批量代码分析策略。

---

## 实战场景

### 场景1: 自动化安全审计

**目标**: 对项目进行全面的安全审计

**步骤**:

1. **导入项目**
```python
await parse_project("/path/to/code", "audit-project")
```

2. **使用安全审计提示**
```python
prompt = await security_audit_prompt("audit-project")
# LLM会根据提示进行系统化审计
```

3. **扫描漏洞**
```python
vulns = await find_vulnerabilities(severity="CRITICAL")
```

4. **详细分析**
```python
for vuln in vulns["vulnerabilities"]:
    # 获取规则详情
    rule = await get_rule_details(vuln["vulnerability"])
    
    # 追踪污点流
    flow = await check_taint_flow(
        vuln["source"]["code"],
        vuln["sink"]["code"]
    )
```

5. **生成报告**
```python
await export_analysis_results(
    vulns,
    "/reports/security-audit.md",
    "markdown"
)
```

### 场景2: 代码重构前的影响分析

**目标**: 评估重构某个函数的影响

**步骤**:

1. **使用重构提示**
```python
prompt = await refactoring_analysis_prompt("old_function")
```

2. **分析调用者**
```python
callers = await get_callers("old_function", depth=3)
affected_count = callers["count"]
```

3. **分析数据依赖**
```python
deps = await find_data_dependencies("old_function")
```

4. **分析控制流**
```python
structures = await analyze_control_structures("old_function")
complexity = structures["count"]
```

5. **生成完整调用图**
```python
graph = await get_call_graph("old_function", depth=2)
```

6. **评估风险**
```python
if affected_count > 10:
    print("高风险：影响超过10个调用者")
elif complexity > 5:
    print("中风险：控制结构复杂")
else:
    print("低风险：可以安全重构")
```

### 场景3: CI/CD集成

**目标**: 在CI/CD中集成自动化安全检查

**GitHub Actions示例**:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Joern
        run: |
          wget https://github.com/joernio/joern/releases/latest/download/joern-cli.zip
          unzip joern-cli.zip
          
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
          
      - name: Install Joern MCP
        run: pip install -r requirements.txt
        
      - name: Run Security Scan
        run: |
          python -m joern_mcp scan \
            --project ${{ github.repository }} \
            --severity CRITICAL \
            --output security-report.md
            
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: security-report.md
          
      - name: Fail on Critical Vulnerabilities
        run: |
          if grep -q "CRITICAL" security-report.md; then
            exit 1
          fi
```

---

## 最佳实践

### 1. 性能优化

#### 使用批量操作

```python
# ❌ 不好：逐个查询
for func in functions:
    result = await get_function_code(func)

# ✅ 好：批量查询
results = await batch_function_analysis(functions)
```

#### 限制查询深度

```python
# ❌ 不好：深度太大
callers = await get_callers("func", depth=10)

# ✅ 好：合理深度
callers = await get_callers("func", depth=3)
```

### 2. 漏洞检测

#### 按严重程度扫描

```python
# 先扫描CRITICAL
critical = await find_vulnerabilities(severity="CRITICAL")

# 如果没有CRITICAL，再扫描HIGH
if critical["total_count"] == 0:
    high = await find_vulnerabilities(severity="HIGH")
```

#### 使用具体规则

```python
# ❌ 不好：扫描所有
all_vulns = await find_vulnerabilities()

# ✅ 好：针对性扫描
sql_vulns = await find_vulnerabilities(rule_name="SQL Injection")
cmd_vulns = await find_vulnerabilities(rule_name="Command Injection")
```

### 3. 结果导出

#### 选择合适的格式

```python
# JSON：用于程序处理
await export_analysis_results(data, "results.json", "json")

# Markdown：用于人工审查
await export_analysis_results(data, "report.md", "markdown")

# CSV：用于数据分析
await export_analysis_results(data, "data.csv", "csv")
```

### 4. 资源管理

#### 及时删除项目

```python
# 分析完成后删除
await delete_project("temp-project")
```

### 5. 错误处理

#### 检查返回值

```python
result = await find_vulnerabilities()

if not result.get("success"):
    error = result.get("error", "Unknown error")
    logger.error(f"Analysis failed: {error}")
    return

# 处理成功结果
vulnerabilities = result["vulnerabilities"]
```

---

## 故障排除

### 常见问题

#### 1. Joern Server无法启动

**症状**: "Joern server not initialized"

**解决**:
- 检查Joern是否正确安装
- 检查端口8080是否被占用
- 查看日志文件 `logs/file_*.log`

#### 2. 查询超时

**症状**: "Query timeout"

**解决**:
- 减少查询深度
- 增加超时时间（配置`max_query_timeout`）
- 使用更具体的查询条件

#### 3. 内存不足

**症状**: "Out of memory"

**解决**:
- 减少并发查询数量
- 使用分批处理
- 增加JVM内存（Joern配置）

---

## 配置参考

### 环境变量

```bash
# Joern Server
JOERN_SERVER_HOST=localhost
JOERN_SERVER_PORT=8080
JOERN_SERVER_TIMEOUT=300

# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_DEBUG=false

# 路径
JOERN_INSTALL_PATH=/path/to/joern
JOERN_PROJECTS_ROOT=./joern_projects
LOG_DIR=./logs
CACHE_DIR=./cache

# 安全
ALLOW_DANGEROUS_QUERIES=false
MAX_QUERY_TIMEOUT=600

# 性能
QUERY_CACHE_MAXSIZE=128
QUERY_CACHE_TTL=300
MAX_CONCURRENT_JOERN_QUERIES=5
```

---

## 进阶主题

### 自定义漏洞规则

```python
from joern_mcp.models.taint_rules import TaintRule

# 定义自定义规则
custom_rule = TaintRule(
    name="Custom Vulnerability",
    description="自定义漏洞描述",
    severity="HIGH",
    sources=["custom_source"],
    sinks=["custom_sink"],
    cwe_id="CWE-XXX"
)

# 使用自定义规则
service = TaintAnalysisService(executor)
result = await service.analyze_with_rule(custom_rule)
```

### 扩展MCP工具

```python
from joern_mcp.mcp_server import mcp

@mcp.tool()
async def custom_analysis() -> dict:
    """自定义分析工具"""
    # 实现自定义分析逻辑
    pass
```

---

## 更多资源

- [技术设计文档](DESIGN.md)
- [Joern集成说明](JOERN_INTEGRATION.md)
- [快速参考](QUICK_REFERENCE.md)
- [开发计划](DEVELOPMENT_PLAN.md)
- [Joern官方文档](https://docs.joern.io)

---

**版本**: 0.5.0-dev  
**最后更新**: 2025-11-27

