# Joern MCP Server 文档中心

欢迎来到 Joern MCP Server 的文档中心！这里包含了项目的完整技术文档。

## 📚 文档导航

### 核心设计文档

#### 1. [DESIGN.md](DESIGN.md) - 技术设计方案 ⭐
**完整的技术设计文档，必读！**

- 系统架构设计（4层架构）
- 核心功能设计（37个MCP工具）
- Joern集成方案
- 数据模型定义
- 实施步骤规划
- 技术难点和解决方案

**适合**: 开发者、架构师、技术决策者

**字数**: ~15,000字  
**章节**: 12章

---

#### 2. [JOERN_INTEGRATION.md](JOERN_INTEGRATION.md) - Joern集成详解 🔧
**深入讲解如何集成Joern Server**

- REPL模式 vs Server模式对比
- Server模式完整API文档
- Python客户端使用指南
- 架构设计和代码示例
- 配置建议和最佳实践

**适合**: 开发者、集成工程师

**字数**: ~6,000字

---

#### 3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考手册 📖
**日常开发必备的速查手册**

- Joern Server快速命令
- Python代码片段
- 常用查询模板
- API端点速查
- 故障排除指南
- 性能优化技巧

**适合**: 所有开发者

**字数**: ~4,000字

---

#### 4. [UPDATES.md](UPDATES.md) - 变更说明 📝
**记录重要的设计变更**

- 2025-11-26: REPL模式 → Server模式
- 技术栈更新
- 代码架构调整
- 迁移指南
- 风险评估

**适合**: 项目跟踪者、开发者

**字数**: ~3,000字

---

## 🎯 快速开始

### 新用户入门路线

```
1️⃣ 阅读 QUICK_REFERENCE.md (10分钟)
   ↓
2️⃣ 浏览 JOERN_INTEGRATION.md (20分钟)
   ↓
3️⃣ 深入 DESIGN.md (60分钟)
   ↓
4️⃣ 开始编码！
```

### 开发者路线

```
1️⃣ 精读 DESIGN.md 第1-7章 (核心设计)
   ↓
2️⃣ 实现 JoernServerManager (参考 JOERN_INTEGRATION.md)
   ↓
3️⃣ 实现 QueryExecutor
   ↓
4️⃣ 实现 MCP Tools
   ↓
5️⃣ 集成测试
```

### 架构师路线

```
1️⃣ 通读 DESIGN.md (完整设计)
   ↓
2️⃣ 评审技术选型
   ↓
3️⃣ 审查架构设计
   ↓
4️⃣ 提出改进建议
```

## 📊 文档统计

| 文档 | 字数 | 章节 | 代码示例 | 更新日期 |
|------|------|------|----------|---------|
| DESIGN.md | ~15,000 | 12 | 20+ | 2025-11-26 |
| JOERN_INTEGRATION.md | ~6,000 | 8 | 15+ | 2025-11-26 |
| QUICK_REFERENCE.md | ~4,000 | 11 | 25+ | 2025-11-26 |
| UPDATES.md | ~3,000 | 9 | 10+ | 2025-11-26 |
| **总计** | **~28,000** | **40** | **70+** | - |

## 🔍 按主题查找

### Joern集成
- [JOERN_INTEGRATION.md](JOERN_INTEGRATION.md) - 完整集成方案
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速命令和API
- [DESIGN.md](DESIGN.md) 第3节 - 集成设计
- [DESIGN.md](DESIGN.md) 第8.1节 - Server模式实现

### MCP工具设计
- [DESIGN.md](DESIGN.md) 第2.2节 - 完整工具列表
- [DESIGN.md](DESIGN.md) 第6节 - 工具实现详解

### 架构设计
- [DESIGN.md](DESIGN.md) 第1节 - 系统架构
- [DESIGN.md](DESIGN.md) 第4节 - 项目结构

### 数据模型
- [DESIGN.md](DESIGN.md) 第5节 - 数据模型定义

### 查询模板
- [DESIGN.md](DESIGN.md) 第3.4节 - Scala查询模板
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 常用查询

### 安全和性能
- [DESIGN.md](DESIGN.md) 第9节 - 安全考虑
- [DESIGN.md](DESIGN.md) 第8.4节 - 性能优化
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 性能优化技巧

### 配置管理
- [DESIGN.md](DESIGN.md) 第11节 - 配置管理
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 配置速查

### 测试
- [DESIGN.md](DESIGN.md) 第12节 - 测试策略

## 💡 关键概念

### CPG (Code Property Graph)
代码属性图，Joern的核心数据结构。参见：
- [Joern文档](https://docs.joern.io/)
- [CPG规范](https://cpg.joern.io)

### MCP (Model Context Protocol)
模型上下文协议，用于LLM工具集成。参见：
- [MCP协议](https://modelcontextprotocol.io)

### Joern Server模式
通过HTTP API访问Joern的方式。参见：
- [JOERN_INTEGRATION.md](JOERN_INTEGRATION.md)

### 污点分析
追踪数据从源到汇的流动。参见：
- [DESIGN.md](DESIGN.md) 第6.4节

## 🛠️ 代码示例索引

### Python示例

#### 启动Joern Server
```python
# 见 JOERN_INTEGRATION.md 第8节
```

#### 执行查询
```python
# 见 QUICK_REFERENCE.md - Python快速代码片段
```

#### 污点分析
```python
# 见 DESIGN.md 第6.4节
```

### Scala查询示例

#### 获取函数代码
```scala
# 见 DESIGN.md 第3.4节 - GET_FUNCTION_CODE
```

#### 数据流分析
```scala
# 见 DESIGN.md 第3.4节 - DATAFLOW_PATHS
```

#### 污点分析
```scala
# 见 DESIGN.md 第3.4节 - TAINT_ANALYSIS
```

### Bash命令示例

#### 启动服务器
```bash
# 见 QUICK_REFERENCE.md - Joern Server快速命令
```

#### 测试连接
```bash
# 见 QUICK_REFERENCE.md - 测试连接
```

## 🔗 外部资源

### Joern官方
- 🌐 [Joern主页](https://joern.io)
- 📚 [Joern文档](https://docs.joern.io)
- 🐙 [Joern GitHub](https://github.com/joernio/joern)
- 🔧 [集成指南](https://joern.io/integrate/)
- 📡 [Server文档](https://docs.joern.io/server/)
- 🐍 [Python客户端](https://github.com/joernio/cpgqls-client-python)

### MCP协议
- 📖 [MCP规范](https://modelcontextprotocol.io)
- 🚀 [FastMCP](https://github.com/jlowin/fastmcp)

### 技术栈
- 🐍 [Python官网](https://www.python.org/)
- ⚡ [Pydantic](https://docs.pydantic.dev/)
- 📝 [Loguru](https://github.com/Delgan/loguru)
- 🌐 [HTTPX](https://www.python-httpx.org/)

## 📝 文档贡献

### 如何改进文档

1. **发现错误**
   - 在GitHub上提交Issue
   - 标注文档名称和章节

2. **提出改进**
   - 在Discussions中讨论
   - 提供具体建议

3. **提交PR**
   - Fork仓库
   - 修改文档
   - 提交Pull Request

### 文档规范

- 使用Markdown格式
- 代码示例要完整可运行
- 添加适当的图表和示例
- 保持更新日期

## 🎓 学习路径

### 初级（1-2周）
- [ ] 阅读QUICK_REFERENCE.md
- [ ] 理解基本概念（CPG、MCP、Server模式）
- [ ] 运行示例代码
- [ ] 尝试基本查询

### 中级（3-4周）
- [ ] 深入DESIGN.md核心章节
- [ ] 理解系统架构
- [ ] 学习数据流分析
- [ ] 实现简单工具

### 高级（5-8周）
- [ ] 完整阅读所有文档
- [ ] 实现完整的MCP Server
- [ ] 编写自定义查询
- [ ] 贡献代码和文档

## 🔄 文档更新历史

| 日期 | 文档 | 变更 |
|------|------|------|
| 2025-11-26 | DESIGN.md | 更新Joern集成方式为Server模式 |
| 2025-11-26 | JOERN_INTEGRATION.md | 新增 |
| 2025-11-26 | QUICK_REFERENCE.md | 新增 |
| 2025-11-26 | UPDATES.md | 新增 |
| 2025-11-26 | README.md (本文档) | 新增 |

## 📞 获取帮助

### 遇到问题？

1. **查阅文档**
   - 先搜索相关文档
   - 查看QUICK_REFERENCE.md

2. **查看示例**
   - 参考代码示例
   - 运行测试代码

3. **提问**
   - GitHub Issues (bug报告)
   - GitHub Discussions (一般讨论)
   - 社区论坛

### 文档反馈

文档有问题或需要改进？
- 📧 提交Issue
- 💬 参与Discussions
- 📝 提交PR

---

## 📄 文档许可

所有文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。

---

**文档维护**: Joern MCP Team  
**最后更新**: 2025-11-26  
**文档版本**: v1.0

---

## 下一步

根据你的角色选择：

- 👨‍💻 **开发者**: 开始阅读 [DESIGN.md](DESIGN.md)
- 🏗️ **架构师**: 查看 [JOERN_INTEGRATION.md](JOERN_INTEGRATION.md)
- 🚀 **快速开始**: 参考 [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 📝 **了解变更**: 阅读 [UPDATES.md](UPDATES.md)

祝你学习愉快！🎉

