# Joern MCP Server

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple.svg" alt="MCP Compatible">
  <img src="https://img.shields.io/badge/Tests-93%25-brightgreen.svg" alt="Test Coverage">
</p>

**Joern MCP Server** 是一个将 [Joern](https://joern.io/) 代码分析平台与 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 集成的服务器，让大语言模型（LLM）能够直接执行代码安全分析任务。

---

## ✨ 核心功能

| 功能类别 | 描述 | MCP工具 |
|---------|------|---------|
| 🔍 **项目管理** | 解析代码、生成CPG、管理项目 | `parse_project`, `list_projects`, `delete_project` |
| 📞 **调用图分析** | 函数调用关系追踪、调用链分析 | `get_callers`, `get_callees`, `get_call_chain`, `get_call_graph` |
| 🌊 **数据流分析** | 变量流向追踪、数据依赖分析 | `track_dataflow`, `analyze_variable_flow`, `find_data_dependencies` |
| 🛡️ **漏洞检测** | 内置6种漏洞规则、自定义污点分析 | `find_vulnerabilities`, `check_taint_flow`, `list_vulnerability_rules` |
| ⚙️ **自定义查询** | 执行任意CPGQL查询 | `execute_query`, `health_check` |

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/joern_mcp.git
cd joern_mcp

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 2. 安装Joern

```bash
# macOS (Homebrew)
brew install joern

# Linux/Windows
curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" | bash
```

### 3. 验证安装

```bash
# 检查Joern
joern --version

# 运行单元测试
pytest tests/test_services -v
```

### 4. 启动服务器

```bash
# 启动MCP服务器
python -m joern_mcp
```

---

## 📖 使用示例

### 示例1：检测C代码漏洞

```python
# 1. 解析项目
await parse_project("/path/to/c_project", "my-c-app")

# 2. 查找所有漏洞
result = await find_vulnerabilities(severity="CRITICAL")
print(f"发现 {result['total_count']} 个严重漏洞")

# 3. 追踪特定漏洞流
flows = await check_taint_flow("gets", "system")
for flow in flows['flows']:
    print(f"污点从 {flow['source']} 流向 {flow['sink']}")
```

### 示例2：分析函数调用关系

```python
# 获取函数的调用者
callers = await get_callers("vulnerable_function", depth=3)
for caller in callers['callers']:
    print(f"{caller['name']} 在 {caller['filename']} 调用了目标函数")

# 生成完整调用图
graph = await get_call_graph("main", depth=2)
print(f"调用图包含 {graph['node_count']} 个节点, {graph['edge_count']} 条边")
```

### 示例3：追踪数据流

```python
# 追踪用户输入到危险函数的流向
flows = await track_dataflow("scanf", "strcpy")

# 分析特定变量
var_flow = await analyze_variable_flow("user_input", sink_method="system")
```

---

## 🔧 配置

创建 `.env` 文件配置服务器：

```bash
# Joern Server配置
JOERN_SERVER_HOST=localhost
JOERN_SERVER_PORT=8080

# 安全设置
ENABLE_CUSTOM_QUERIES=true
MAX_QUERY_TIMEOUT=300

# 日志级别
LOG_LEVEL=INFO
```

---

## 📚 文档

| 文档 | 描述 |
|------|------|
| [安装指南](./docs/INSTALLATION.md) | 详细安装步骤和系统要求 |
| [用户手册](./docs/USER_GUIDE.md) | 完整使用教程和最佳实践 |
| [API参考](./docs/API_REFERENCE.md) | MCP工具完整API文档 |
| [示例项目](./examples/) | 真实漏洞检测示例 |

---

## 🛡️ 内置漏洞规则

| 规则名称 | 严重级别 | CWE编号 | 描述 |
|---------|---------|---------|------|
| Command Injection | CRITICAL | CWE-78 | 命令注入漏洞检测 |
| SQL Injection | CRITICAL | CWE-89 | SQL注入漏洞检测 |
| Buffer Overflow | CRITICAL | CWE-120 | 缓冲区溢出检测 |
| Path Traversal | HIGH | CWE-22 | 路径遍历漏洞检测 |
| Format String | HIGH | CWE-134 | 格式化字符串漏洞 |
| Use After Free | CRITICAL | CWE-416 | 释放后使用检测 |

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM / AI Agent                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ MCP Protocol (stdio)
┌─────────────────────────────────────────────────────────────┐
│                    Joern MCP Server                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Tools     │  │  Services   │  │  Query Executor     │ │
│  │ ─ project   │  │ ─ callgraph │  │ ─ Caching           │ │
│  │ ─ callgraph │  │ ─ dataflow  │  │ ─ Concurrency       │ │
│  │ ─ dataflow  │  │ ─ taint     │  │ ─ Validation        │ │
│  │ ─ taint     │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP + WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      Joern Server                           │
│                   (Code Property Graph)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 只运行单元测试
pytest tests/test_services -v

# 运行集成测试（需要Joern）
pytest tests/integration -v --timeout=180

# 查看测试覆盖率
pytest --cov=joern_mcp --cov-report=html
```

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

---

## 📄 许可证

本项目采用 Apache 2.0 许可证。详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

- [Joern](https://joern.io/) - 强大的代码分析平台
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP服务器框架
- [Model Context Protocol](https://modelcontextprotocol.io/) - LLM工具协议

---

<p align="center">
  <b>🔒 让AI成为你的代码安全专家</b>
</p>
