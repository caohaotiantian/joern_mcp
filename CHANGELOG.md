# Changelog

本文档记录了 Joern MCP Server 的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-12-03

### 🎉 首次发布

基于 Joern 代码分析引擎的 MCP (Model Context Protocol) 服务器，为 AI 助手提供强大的代码分析能力。

### ✨ 核心功能

**Joern 集成**
- 通过 Web Server API 与 Joern 服务器通信
- 异步查询执行，支持并发控制
- 查询缓存机制，提升性能
- 代码导入和项目管理

**MCP Tools (9个工具)**
- `parse_project` - 解析代码项目生成CPG
- `list_projects` / `delete_project` - 项目管理
- `get_function_code` / `list_functions` / `search_code` - 代码查询
- `find_vulnerabilities` / `check_taint_flow` - 漏洞检测
- `batch_query` / `batch_function_analysis` - 批量操作

**MCP Resources (4个资源)**
- `project://list` - 项目列表
- `project://{name}/info` - 项目信息
- `project://{name}/functions` - 函数列表
- `project://{name}/vulnerabilities` - 漏洞列表

**MCP Prompts (5个提示模板)**
- `security_audit_prompt` - 安全审计
- `code_understanding_prompt` - 代码理解
- `refactoring_analysis_prompt` - 重构分析
- `vulnerability_investigation_prompt` - 漏洞调查
- `batch_analysis_prompt` - 批量分析

**分析服务**
- 调用图分析 (CallGraphService)
- 数据流分析 (DataFlowService)
- 污点分析 (TaintAnalysisService)

**漏洞检测规则**
- Command Injection
- SQL Injection
- Path Traversal
- XSS
- Buffer Overflow
- Format String

### 📊 技术指标

- 源代码: ~4000行
- 测试覆盖: 85+ 测试用例
- 支持语言: C/C++, Java, JavaScript, Python 等

### 📦 依赖

- Python >= 3.11
- Joern >= 2.0.0
- mcp >= 1.0.0
- pydantic >= 2.0.0
- httpx >= 0.27.0
- websockets >= 12.0

---

## 版本说明

### 版本号规则

版本号格式：`主版本号.次版本号.修订号`

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修正

### 变更类型

- **新增**：新功能
- **变更**：已有功能的变更
- **修复**：Bug修复
- **移除**：已移除的功能

---

[0.1.0]: https://github.com/yourusername/joern_mcp/releases/tag/v0.1.0
