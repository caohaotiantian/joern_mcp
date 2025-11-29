"""分析提示模板"""

from loguru import logger

from joern_mcp.mcp_server import mcp


@mcp.prompt()
async def security_audit_prompt(project_name: str = "unknown") -> str:
    """
    安全审计提示模板

    Args:
        project_name: 项目名称

    Returns:
        str: 提示内容
    """
    logger.info(f"Generating security audit prompt for: {project_name}")

    return f"""# 安全审计分析

你是一个专业的代码安全审计员，正在分析项目：**{project_name}**

## 审计目标

1. 识别潜在的安全漏洞
2. 分析数据流和污点传播
3. 检查危险函数的使用
4. 评估输入验证机制

## 分析步骤

### 第一步：概览扫描
使用 `find_vulnerabilities(severity="CRITICAL")` 快速扫描CRITICAL级别漏洞。

### 第二步：详细分析
针对每个发现的漏洞：
- 使用 `get_rule_details()` 了解漏洞详情
- 使用 `check_taint_flow()` 追踪污点流路径
- 使用 `get_call_chain()` 分析调用链

### 第三步：上下文理解
- 使用 `get_function_code()` 查看相关函数代码
- 使用 `get_callers()` 找出调用来源
- 使用 `find_data_dependencies()` 分析数据依赖

### 第四步：生成报告
使用 `export_analysis_results()` 生成详细的审计报告。

## OWASP Top 10 检查清单

- [ ] A01: 权限控制失效
- [ ] A02: 加密机制失效
- [ ] A03: 注入攻击 (使用 find_vulnerabilities 检测)
- [ ] A04: 不安全设计
- [ ] A05: 安全配置错误
- [ ] A06: 易受攻击和过时的组件
- [ ] A07: 认证和授权失败
- [ ] A08: 软件和数据完整性失败
- [ ] A09: 安全日志和监控失效
- [ ] A10: 服务端请求伪造

## 建议的MCP工具

- `find_vulnerabilities()` - 自动漏洞检测
- `check_taint_flow()` - 污点流追踪
- `get_call_graph()` - 调用关系分析
- `analyze_control_structures()` - 控制流分析
- `export_analysis_results()` - 导出报告

开始你的安全审计吧！
"""


@mcp.prompt()
async def code_understanding_prompt(function_name: str = "unknown") -> str:
    """
    代码理解提示模板

    Args:
        function_name: 函数名称

    Returns:
        str: 提示内容
    """
    logger.info(f"Generating code understanding prompt for: {function_name}")

    return f"""# 代码理解分析

你正在分析函数：**{function_name}**

## 分析目标

1. 理解函数的功能和逻辑
2. 识别函数的依赖关系
3. 分析数据流和控制流
4. 评估代码质量和复杂度

## 分析步骤

### 第一步：基本信息
```
# 获取函数详情
await get_function_details("{function_name}")

# 获取函数代码
await get_function_code("{function_name}")
```

### 第二步：调用关系
```
# 谁调用了这个函数？
await get_callers("{function_name}", depth=2)

# 这个函数调用了什么？
await get_callees("{function_name}", depth=2)

# 完整调用图
await get_call_graph("{function_name}", depth=2)
```

### 第三步：控制流分析
```
# 获取控制流图
await get_control_flow_graph("{function_name}", format="dot")

# 分析控制结构
await analyze_control_structures("{function_name}")
```

### 第四步：数据流分析
```
# 查找数据依赖
await find_data_dependencies("{function_name}")

# 追踪变量流向
await analyze_variable_flow("variable_name")
```

## 理解框架

### 功能分析
- **输入**: 函数参数和全局状态
- **处理**: 核心业务逻辑
- **输出**: 返回值和副作用

### 质量评估
- **复杂度**: 控制结构数量和嵌套层次
- **耦合度**: 调用关系的复杂程度
- **可维护性**: 代码清晰度和组织结构

### 潜在问题
- **性能**: 是否有性能瓶颈
- **安全**: 是否有安全隐患
- **设计**: 是否符合最佳实践

开始深入理解代码吧！
"""


@mcp.prompt()
async def refactoring_analysis_prompt(function_name: str = "unknown") -> str:
    """
    重构分析提示模板

    Args:
        function_name: 函数名称

    Returns:
        str: 提示内容
    """
    logger.info(f"Generating refactoring prompt for: {function_name}")

    return f"""# 重构影响分析

你正在评估重构函数：**{function_name}** 的影响

## 重构前评估

### 第一步：依赖分析
```
# 找出所有调用者（影响范围）
await get_callers("{function_name}", depth=3)

# 找出所有被调用函数（内部依赖）
await get_callees("{function_name}", depth=2)
```

### 第二步：数据流分析
```
# 分析数据依赖
await find_data_dependencies("{function_name}")

# 追踪关键变量
await analyze_variable_flow("critical_var")
```

### 第三步：控制流分析
```
# 评估复杂度
await analyze_control_structures("{function_name}")

# 可视化控制流
await get_control_flow_graph("{function_name}")
```

## 重构策略

### 提取函数
如果函数过于复杂：
1. 识别可独立的代码块
2. 评估提取后的影响范围
3. 确保数据流正确性

### 简化条件
如果条件语句复杂：
1. 分析控制结构
2. 识别可合并的条件
3. 考虑使用策略模式

### 消除重复
如果存在代码重复：
1. 使用 `search_code_pattern()` 找到重复代码
2. 评估提取公共函数的可行性
3. 分析调用者的影响

## 风险评估

### 高风险因素
- [ ] 调用者数量 > 10
- [ ] 调用深度 > 5
- [ ] 复杂的数据依赖
- [ ] 外部API依赖

### 测试策略
1. 识别所有调用路径
2. 为每个路径创建测试用例
3. 重点测试边界条件

## 验证步骤

重构后：
```
# 验证调用关系未变
await get_call_graph("{function_name}", depth=2)

# 验证数据流正确
await track_dataflow("source", "sink")

# 确保没有引入新漏洞
await find_vulnerabilities()
```

安全地进行重构吧！
"""


@mcp.prompt()
async def vulnerability_investigation_prompt(
    vulnerability_type: str = "Command Injection",
) -> str:
    """
    漏洞调查提示模板

    Args:
        vulnerability_type: 漏洞类型

    Returns:
        str: 提示内容
    """
    logger.info(
        f"Generating vulnerability investigation prompt for: {vulnerability_type}"
    )

    return f"""# 漏洞深入调查

你正在调查：**{vulnerability_type}** 漏洞

## 调查步骤

### 第一步：了解漏洞
```
# 获取规则详情
await get_rule_details("{vulnerability_type}")

# 列出所有相关规则
await list_vulnerability_rules()
```

### 第二步：定位漏洞
```
# 查找该类型的所有漏洞
await find_vulnerabilities(rule_name="{vulnerability_type}")
```

### 第三步：分析每个漏洞实例

针对每个发现的漏洞：

```
# 追踪污点流
await check_taint_flow("source_pattern", "sink_pattern")

# 分析调用链
await get_call_chain("vulnerable_function", direction="up")

# 查看函数代码
await get_function_code("vulnerable_function")
```

### 第四步：评估影响

```
# 找出谁调用了有漏洞的函数
await get_callers("vulnerable_function", depth=3)

# 分析数据流
await track_dataflow("user_input", "dangerous_function")
```

## 漏洞分类

### {vulnerability_type} 的特征

根据漏洞类型，关注：

**Command Injection (CWE-78)**
- 源: 用户输入 (gets, scanf, getParameter)
- 汇: 命令执行 (system, exec, popen)
- 风险: 远程代码执行

**SQL Injection (CWE-89)**
- 源: 用户输入
- 汇: SQL查询 (executeQuery, prepareStatement)
- 风险: 数据泄露、篡改

**Path Traversal (CWE-22)**
- 源: 用户输入
- 汇: 文件操作 (fopen, readFile)
- 风险: 任意文件读取/写入

## 修复建议框架

### 输入验证
- 白名单验证
- 输入净化
- 类型检查

### 安全编码
- 使用参数化查询（SQL）
- 避免动态命令构造
- 使用安全的API

### 防御措施
- 最小权限原则
- 输入输出编码
- 错误处理

## 生成报告

```
# 导出详细报告
await export_analysis_results(
    results,
    "vulnerability-report.md",
    "markdown"
)
```

开始你的漏洞调查吧！
"""


@mcp.prompt()
async def batch_analysis_prompt(function_list: str = "main,init,process") -> str:
    """
    批量分析提示模板

    Args:
        function_list: 函数列表（逗号分隔）

    Returns:
        str: 提示内容
    """
    logger.info(f"Generating batch analysis prompt for: {function_list}")

    functions = [f.strip() for f in function_list.split(",")]

    return f"""# 批量代码分析

你正在批量分析以下函数：**{", ".join(functions)}**

## 批量分析策略

### 第一步：概览分析
```
# 批量获取函数信息
await batch_function_analysis({functions})

# 批量执行查询
# 示例：查询特定函数的代码
queries = [
    'cpg.method.name("<function_name>").code.l'
]
await batch_query(queries)
```

### 第二步：对比分析

为每个函数生成以下信息：
- 函数签名和参数
- 代码行数和复杂度
- 调用关系
- 潜在问题

### 第三步：关系分析

```
# 分析函数间的调用关系
for func in {functions}:
    await get_call_graph(func, depth=2)
```

### 第四步：质量评估

生成对比表格：

| 函数 | 行数 | 复杂度 | 调用者数 | 被调用数 | 问题 |
|------|------|--------|----------|----------|------|
| ... | ... | ... | ... | ... | ... |

## 分析维度

### 代码质量
- **简洁性**: 代码行数
- **复杂度**: 控制结构数量
- **可读性**: 命名和组织

### 架构设计
- **耦合度**: 调用关系复杂度
- **内聚性**: 功能单一性
- **可测试性**: 依赖数量

### 安全性
- **输入验证**: 是否验证输入
- **错误处理**: 是否正确处理错误
- **权限检查**: 是否检查权限

## 优化建议

基于分析结果，提供：
1. 需要重构的函数列表
2. 需要添加测试的函数
3. 需要安全加固的函数
4. 优化优先级排序

## 导出结果

```
# 生成对比报告
await export_analysis_results(
    comparison_results,
    "batch-analysis.md",
    "markdown"
)
```

开始批量分析吧！
"""
