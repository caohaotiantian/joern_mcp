# 示例项目

本目录包含Joern MCP Server的演示示例。

## 📁 目录结构

```
examples/
├── README.md                  # 本文件
├── demo.py                    # 直接 API 调用演示
├── mcp_client_example.py      # MCP 客户端使用示例
├── scripts/                   # 安全分析脚本
│   ├── README.md              # 脚本说明
│   ├── analyze_command_injection.py   # 命令注入检测
│   ├── analyze_buffer_overflow.py     # 缓冲区溢出检测
│   └── analyze_all_vulnerabilities.py # 综合安全扫描
└── vulnerable_c/              # 示例漏洞C代码
    └── vulnerable.c           # 包含多种漏洞的C代码
```

## 🚀 快速开始

### 运行演示

```bash
# 进入项目根目录
cd joern_mcp

# 激活虚拟环境
source .venv/bin/activate

# 运行演示脚本
python examples/demo.py
```

### 演示内容

演示脚本将展示以下功能：

1. **项目管理** - 解析C代码生成CPG
2. **调用图分析** - 分析函数调用关系
3. **数据流分析** - 追踪数据流向
4. **漏洞检测** - 自动检测安全漏洞
5. **自定义查询** - 执行CPGQL查询

## 🔒 示例漏洞代码

`vulnerable_c/vulnerable.c` 包含以下漏洞示例：

| 漏洞类型 | 函数名 | CWE编号 |
|---------|--------|---------|
| 命令注入 | `command_injection` | CWE-78 |
| 缓冲区溢出 | `buffer_overflow` | CWE-120 |
| 格式化字符串 | `format_string` | CWE-134 |
| 不安全的gets | `unsafe_gets` | CWE-120 |
| SQL注入模拟 | `sql_query` | CWE-89 |
| 路径遍历 | `path_traversal` | CWE-22 |

⚠️ **警告**: 这些代码仅用于演示目的，请勿在实际项目中使用！

## 📊 预期输出

运行演示后，您将看到类似以下的输出：

```
🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒
     Joern MCP Server 演示
🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒

示例代码路径: /path/to/examples/vulnerable_c

启动Joern服务器...
✅ Joern服务器已启动: localhost:8080

============================================================
 📂 项目管理演示
============================================================

1. 解析项目...
   ✅ 项目解析成功

============================================================
 🛡️ 漏洞检测演示
============================================================

2. 扫描所有漏洞:
   发现 8 个潜在漏洞
   - CRITICAL: 5 个
   - HIGH: 3 个
...
```

## 🔌 MCP 客户端示例

`mcp_client_example.py` 演示如何通过 MCP 协议与 Joern MCP Server 交互：

### 使用 stdio 传输（自动启动服务器）

```bash
python examples/mcp_client_example.py
```

### 使用 HTTP 传输（需要先启动服务器）

```bash
# 终端 1: 启动服务器
python -m joern_mcp

# 终端 2: 运行客户端
python examples/mcp_client_example.py http
```

该示例演示完整的分析流程：
1. 健康检查
2. 解析项目（构建 CPG）
3. 列出函数
4. 搜索危险函数
5. 漏洞检测
6. 污点流分析
7. 自定义查询

详细使用指南请参阅 [MCP 使用指南](../docs/MCP_USAGE_GUIDE.md)。

## 🔍 安全分析脚本

`scripts/` 目录包含独立的安全分析脚本：

### 命令注入检测

```bash
python examples/scripts/analyze_command_injection.py examples/vulnerable_c
```

### 缓冲区溢出检测

```bash
python examples/scripts/analyze_buffer_overflow.py examples/vulnerable_c
```

### 综合安全扫描

```bash
python examples/scripts/analyze_all_vulnerabilities.py examples/vulnerable_c
```

综合扫描会生成 JSON 格式的详细报告。

详细说明请参阅 [scripts/README.md](scripts/README.md)。

## 🛠️ 自定义演示

您可以修改`demo.py`来测试不同的功能：

```python
# 修改目标函数
callers = await service.get_callers("your_function", depth=3)

# 修改污点源和汇
flows = await service.check_specific_flow("your_source", "your_sink")

# 添加自定义查询
result = await executor.execute("your_cpgql_query")
```

## 📚 更多信息

- [用户手册](../docs/USER_GUIDE.md)
- [API参考](../docs/API_REFERENCE.md)
- [安装指南](../docs/INSTALLATION.md)

