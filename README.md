# Joern MCP Server

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Development Status](https://img.shields.io/badge/status-Week%201%20Complete-success.svg)]()

将强大的Joern代码分析平台封装为MCP Server，让LLM能够对代码进行深度静态分析。

## 🎉 项目状态

**当前进度**: ✅ Week 1-6 完成（MCP三大能力全部实现）  
**完成度**: 75% (Week 6 of 8)  
**代码行数**: ~4230行  
**测试用例**: 48个  
**MCP Tools**: 26个  
**MCP Resources**: 4个  
**MCP Prompts**: 5个  
**分析服务**: 3个  
**漏洞规则**: 6个

查看详细进度：
- [Week 1 进度](PROGRESS_WEEK1.md)
- [Week 2 进度](PROGRESS_WEEK2.md)
- [Week 3 进度](PROGRESS_WEEK3.md)
- [Week 4-5 进度](PROGRESS_WEEK4-5.md)
- [Week 6 进度](PROGRESS_WEEK6.md)
- [📊 项目状态](PROJECT_STATUS.md)
- [✅ 验证报告](VALIDATION_REPORT.md)

## ✨ 已实现功能

### Week 1: 基础设施 ✅
- ✅ 配置管理系统
- ✅ 日志系统
- ✅ Joern安装检测和管理
- ✅ Joern Server启动和管理
- ✅ 查询执行器（缓存、验证、并发控制）

### Week 2: MCP基础 ✅
- ✅ FastMCP服务器（生命周期管理）
- ✅ 8个MCP工具（项目管理、代码查询）
- ✅ 15+个查询模板
- ✅ 健康检查和自定义查询

### Week 3: 分析服务 ✅
- ✅ CallGraphService（调用图分析）
- ✅ DataFlowService（数据流分析）
- ✅ 7个新MCP工具（调用图、数据流）
- ✅ 13个新测试用例

### Week 4: 污点分析 ✅
- ✅ TaintAnalysisService（污点分析服务）
- ✅ 6个预定义漏洞检测规则
- ✅ 4个新MCP工具（漏洞检测）
- ✅ 11个新测试用例

### Week 5: 高级功能 ✅
- ✅ CFG控制流分析（3个工具）
- ✅ 批量查询功能（2个工具）
- ✅ 结果导出功能（2个工具）
- ✅ 多格式支持（JSON, Markdown, CSV）

### Week 6: MCP Resources和Prompts ✅
- ✅ 4个MCP Resources（项目数据暴露）
- ✅ 5个MCP Prompts（分析提示模板）
- ✅ 完整的用户指南（1300+行）
- ✅ 详细的API参考（700+行）

## 🚀 快速开始

### 前置要求

- Python 3.10+
- JDK 21
- Joern（可选，用于集成测试）

### 安装

```bash
# 1. 克隆仓库（如果还没有）
cd /Users/caohaotian/Documents/joern_mcp

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 安装Joern（可选）
curl -L https://github.com/joernio/joern/releases/latest/download/joern-install.sh | sudo bash

# 5. 运行测试
pytest tests/ -v
```

### 验证安装

```bash
# 测试配置系统
python3 -c "from joern_mcp.config import settings; print(settings.joern_server_host)"

# 测试Joern检测（需要安装Joern）
python3 -c "from joern_mcp.joern.manager import JoernManager; m = JoernManager(); print(f'Joern version: {m.get_version()}')"

# 运行所有测试
pytest tests/ -v --cov=joern_mcp
```

## 📖 文档

### 核心文档

- 📘 [开发就绪指南](DEVELOPMENT_READY.md) - **从这里开始！**
- 📋 [第一周进度报告](PROGRESS_WEEK1.md) - 查看已完成的工作
- 📚 [完整设计方案](doc/DESIGN.md) - 技术设计（15,000字）
- 🔧 [Joern集成详解](doc/JOERN_INTEGRATION.md) - Joern Server模式
- 📖 [快速参考手册](doc/QUICK_REFERENCE.md) - 日常开发速查
- 📊 [任务跟踪表](doc/TASK_TRACKER.md) - 开发进度跟踪

### 开发文档

- 🎯 [开发计划总览](doc/DEVELOPMENT_OVERVIEW.md)
- 📅 [第一周详细计划](doc/DEVELOPMENT_PLAN.md)
- 📅 [第2-8周计划](doc/DEVELOPMENT_PLAN_WEEK2-8.md)

## 🏗️ 项目结构

```
joern_mcp/
├── src/joern_mcp/          # 源代码
│   ├── config.py           # ✅ 配置管理
│   ├── joern/              # ✅ Joern集成
│   │   ├── manager.py      # ✅ Joern管理器
│   │   ├── server.py       # ✅ Server管理
│   │   └── executor.py     # ✅ 查询执行器
│   ├── utils/              # ✅ 工具函数
│   │   └── logger.py       # ✅ 日志系统
│   ├── services/           # ⏳ 分析服务（Week 3-4）
│   ├── tools/              # ⏳ MCP工具（Week 2）
│   ├── resources/          # ⏳ MCP资源（Week 6）
│   └── prompts/            # ⏳ MCP提示（Week 6）
│
├── tests/                  # ✅ 测试代码
│   ├── conftest.py         # ✅ Pytest配置
│   ├── test_config.py      # ✅ 配置测试
│   ├── test_joern/         # ✅ Joern集成测试
│   └── test_utils/         # ✅ 工具测试
│
└── doc/                    # 📚 完整文档
```

## 🎓 开发路线图

### ✅ Week 1: 基础设施（已完成）
- 项目初始化
- 配置和日志系统
- Joern集成
- 查询执行器

### ⏳ Week 2: MCP基础设施（进行中）
- FastMCP服务器
- 项目管理工具
- 代码查询工具

### 📅 Week 3-8: 核心功能
- Week 3: 调用图和数据流分析
- Week 4: 污点分析
- Week 5: 高级功能
- Week 6: Resources和Prompts
- Week 7: 集成测试
- Week 8: 优化和发布

详见：[开发路线图](doc/ROADMAP.md)

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 查看覆盖率
pytest --cov=joern_mcp --cov-report=html tests/
open htmlcov/index.html

# 跳过需要Joern的测试
pytest -m "not requires_joern" tests/
```

## 🛠️ 开发工具

### 代码格式化

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/

# 类型检查
mypy src/
```

### 开发环境

推荐使用VS Code或PyCharm，配置已包含在项目中。

## 🤝 贡献指南

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 提交Pull Request

详见：[开发指南](doc/DEVELOPMENT.md)

## 📊 当前进度

| 模块 | 状态 | 完成度 |
|------|------|--------|
| 基础设施 | ✅ | 100% |
| Joern集成 | ✅ | 100% |
| MCP基础 | ⏳ | 0% |
| 分析服务 | ⏳ | 0% |
| 测试 | ✅ | Week 1完成 |
| 文档 | ✅ | 100% |

## 🔗 相关链接

- [Joern官网](https://joern.io)
- [Joern文档](https://docs.joern.io)
- [MCP协议](https://modelcontextprotocol.io)
- [cpgqls-client](https://github.com/joernio/cpgqls-client-python)

## 📝 许可证

本项目采用 Apache 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Joern](https://joern.io) - 强大的代码分析平台
- [FastMCP](https://github.com/jlowin/fastmcp) - 优秀的MCP框架
- [Anthropic](https://www.anthropic.com) - MCP协议和Claude

## 📞 联系方式

- 项目主页: https://github.com/yourusername/joern_mcp
- 问题反馈: https://github.com/yourusername/joern_mcp/issues
- 讨论区: https://github.com/yourusername/joern_mcp/discussions

---

**当前版本**: 0.1.0-dev  
**开发状态**: Week 1 完成，准备进入 Week 2  
**最后更新**: 2025-11-26

**下一步**: 安装依赖并运行测试，然后开始 Week 2 的MCP基础设施开发。

查看 [DEVELOPMENT_READY.md](DEVELOPMENT_READY.md) 了解如何开始！

