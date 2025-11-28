# Joern MCP Server 开发计划总览

## 📋 文档导航

### 核心开发文档

| 文档 | 内容 | 适用阶段 |
|------|------|---------|
| [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) | 第一周详细计划 | Week 1 |
| [DEVELOPMENT_PLAN_WEEK2-8.md](DEVELOPMENT_PLAN_WEEK2-8.md) | 第2-8周计划 | Week 2-8 |
| [TASK_TRACKER.md](TASK_TRACKER.md) | 任务跟踪表 | 全程 |

### 参考文档

| 文档 | 内容 |
|------|------|
| [DESIGN.md](DESIGN.md) | 技术设计方案 |
| [JOERN_INTEGRATION.md](JOERN_INTEGRATION.md) | Joern集成详解 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速参考手册 |

---

## 🎯 开发目标

**总目标**: 实现一个功能完整、稳定可靠的Joern MCP Server

### MVP版本 (v0.1.0) 功能清单

#### 核心功能
- ✅ Joern Server集成和管理
- ✅ 查询执行和缓存
- ✅ 37个MCP工具
- ✅ MCP Resources和Prompts
- ✅ 完整的错误处理
- ✅ 日志和监控

#### 支持的分析类型
1. **项目管理**
   - 解析项目生成CPG
   - 列出和管理项目
   
2. **代码查询**
   - 获取函数代码
   - 列出函数
   - 搜索代码
   
3. **调用图分析**
   - 获取调用者/被调用者
   - 构建调用链
   - 生成调用图
   
4. **数据流分析**
   - 追踪数据流
   - 变量流向分析
   
5. **污点分析**
   - 污点追踪
   - 漏洞检测
   - 预定义规则
   
6. **控制流分析**
   - 获取CFG
   - 路径查找

---

## 📅 时间规划

### 整体时间线

```
Week 1: 基础设施 (23h)
├── Day 1-2: 项目初始化 (9h)
├── Day 3-4: Joern集成 (10h)
└── Day 5: 查询执行器 (4h)

Week 2: MCP基础 (19h)
├── Day 6-7: FastMCP集成 (10h)
└── Day 8-10: 查询工具 (9h)

Week 3: 分析服务 (22h)
├── Day 11-12: 调用图 (11h)
└── Day 13-14: 数据流 (11h)

Week 4: 污点分析 (17h)
└── Day 15-17: 污点分析 (17h)

Week 5: 高级功能 (14h)
└── Day 18-20: 控制流、批量 (14h)

Week 6: Resources/Prompts (14h)
└── Day 21-23: Resources、Prompts (14h)

Week 7: 集成测试 (17h)
└── Day 24-27: 测试完善 (17h)

Week 8: 优化发布 (14h)
└── Day 28-30: 优化文档 (14h)

总计: 140小时 ≈ 8周（每周17.5小时）
```

### 建议工作安排

#### 全职开发（1人）
- 每天3.5小时
- 每周5天
- 8周完成

#### 兼职开发（1人）
- 每天2小时
- 每周7天
- 10周完成

#### 团队开发（2人）
- 并行开发
- 每人每天2小时
- 5周完成

---

## 🏗️ 开发流程

### 每个任务的标准流程

```
1. 理解需求
   └── 阅读设计文档相关章节
   
2. 编写代码
   ├── 创建文件
   ├── 实现功能
   └── 添加类型注解和docstring
   
3. 编写测试
   ├── 单元测试
   ├── 集成测试（如需要）
   └── 目标覆盖率 > 80%
   
4. 代码审查
   ├── 运行black格式化
   ├── 运行ruff检查
   ├── 运行mypy类型检查
   └── 通过所有检查
   
5. 测试验证
   ├── 运行单元测试
   ├── 运行集成测试
   ├── 手动测试
   └── 所有测试通过
   
6. 提交代码
   ├── Git commit
   ├── 更新TASK_TRACKER.md
   └── 更新CHANGELOG.md（如需要）
```

---

## 🔍 质量保证

### 代码质量标准

#### 1. 代码规范
```bash
# 格式化
black src/ tests/

# 检查
ruff check src/ tests/

# 类型检查
mypy src/
```

#### 2. 测试覆盖率
```bash
# 运行测试并生成覆盖率报告
pytest --cov=joern_mcp --cov-report=html --cov-report=term

# 目标: 整体覆盖率 > 85%
```

#### 3. 性能基准
- 查询响应时间 < 5秒（简单查询）
- 查询响应时间 < 30秒（复杂查询）
- 并发查询支持 >= 5
- 内存占用 < 2GB（正常运行）

#### 4. 安全检查
- 查询注入防护
- 路径遍历防护
- 资源限制

---

## 🎓 开发技能要求

### 必备技能
- ✅ Python 3.10+
- ✅ 异步编程（asyncio）
- ✅ Pydantic数据验证
- ✅ pytest测试框架

### 推荐技能
- 📚 Scala基础（理解Joern查询）
- 📚 代码分析基础
- 📚 MCP协议
- 📚 FastMCP框架

### 学习资源
- [Python Asyncio教程](https://docs.python.org/3/library/asyncio.html)
- [Pydantic文档](https://docs.pydantic.dev/)
- [Joern文档](https://docs.joern.io/)
- [MCP协议](https://modelcontextprotocol.io)

---

## 📊 进度跟踪方式

### 1. 任务级别跟踪
使用 [TASK_TRACKER.md](TASK_TRACKER.md) 跟踪每个任务的状态。

### 2. 每日站会
每天更新：
- 昨天完成了什么
- 今天计划做什么
- 遇到什么问题

### 3. 周报
每周五总结：
- 完成的任务
- 工时统计
- 下周计划
- 风险和问题

### 4. 里程碑检查
在每个里程碑（M1-M5）进行检查：
- 功能完成情况
- 测试覆盖率
- 性能指标
- 问题清单

---

## 🚀 快速开始指南

### 第一天上手步骤

#### 1. 环境准备（30分钟）
```bash
# 克隆仓库（如果还没有）
git clone <your-repo>
cd joern_mcp

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 验证环境
pytest --version
black --version
```

#### 2. 安装Joern（15分钟）
```bash
# 下载安装脚本
curl -L https://github.com/joernio/joern/releases/latest/download/joern-install.sh -o joern-install.sh
chmod +x joern-install.sh

# 安装
sudo ./joern-install.sh

# 验证
joern --version
```

#### 3. 运行第一个测试（15分钟）
```bash
# 阅读开发计划
cat doc/DEVELOPMENT_PLAN.md

# 开始第一个任务
# 创建项目结构（按照任务1.1）
mkdir -p src/joern_mcp/...

# 运行测试
pytest tests/ -v
```

### 每天的开发流程

#### 开始工作（5分钟）
```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 拉取最新代码（如果是团队开发）
git pull

# 3. 查看今天的任务
cat doc/TASK_TRACKER.md | grep "今天"
```

#### 开发过程（2-4小时）
```bash
# 1. 创建功能分支
git checkout -b feature/task-1.3

# 2. 编写代码
vim src/joern_mcp/config.py

# 3. 编写测试
vim tests/test_config.py

# 4. 运行测试
pytest tests/test_config.py -v

# 5. 代码检查
black src/ tests/
ruff check src/ tests/
```

#### 结束工作（10分钟）
```bash
# 1. 提交代码
git add .
git commit -m "feat: implement config management (task 1.3)"

# 2. 推送代码
git push origin feature/task-1.3

# 3. 更新任务状态
# 编辑 TASK_TRACKER.md，标记任务为完成

# 4. 记录今日工作
# 在TASK_TRACKER.md的"每日站会记录"中记录
```

---

## 🐛 常见问题

### Q1: Joern启动失败
```bash
# 检查Java版本
java -version  # 应该是21

# 检查端口占用
lsof -i :8080

# 查看错误日志
cat ~/.joern_mcp/logs/error_*.log
```

### Q2: 测试失败
```bash
# 清除pytest缓存
pytest --cache-clear

# 只运行失败的测试
pytest --lf

# 详细输出
pytest -vv -s
```

### Q3: 依赖问题
```bash
# 重新安装依赖
pip install --force-reinstall -r requirements.txt

# 检查依赖冲突
pip check
```

### Q4: 代码格式问题
```bash
# 自动格式化
black src/ tests/

# 自动修复可修复的问题
ruff check --fix src/ tests/
```

---

## 📚 开发资源

### 代码示例

#### 最小可运行示例
```python
# minimal_example.py
import asyncio
from joern_mcp.joern.server import JoernServerManager

async def main():
    # 启动Joern Server
    manager = JoernServerManager()
    await manager.start()
    
    # 执行查询
    result = manager.execute_query("1 + 1")
    print(result)
    
    # 停止服务器
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 测试示例
```python
# test_example.py
import pytest
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_example():
    """测试示例"""
    mock_obj = MagicMock()
    mock_obj.method.return_value = "result"
    
    result = mock_obj.method()
    assert result == "result"
```

### 调试技巧

#### 1. 使用日志调试
```python
from loguru import logger

logger.debug("调试信息")
logger.info("一般信息")
logger.error("错误信息")
```

#### 2. 使用pdb调试
```python
import pdb; pdb.set_trace()
```

#### 3. 使用pytest调试
```bash
# 在失败时进入调试器
pytest --pdb

# 显示print输出
pytest -s
```

---

## 🎯 成功标准

### MVP版本验收标准

#### 1. 功能完整性 ✅
- [ ] 所有37个MCP工具实现
- [ ] 至少支持3种分析类型
- [ ] 基础的错误处理

#### 2. 质量标准 ✅
- [ ] 测试覆盖率 > 85%
- [ ] 所有测试通过
- [ ] 代码符合规范

#### 3. 性能标准 ✅
- [ ] 简单查询 < 5秒
- [ ] 并发支持 >= 5
- [ ] 内存占用合理

#### 4. 文档标准 ✅
- [ ] API文档完整
- [ ] 使用示例充分
- [ ] README清晰

#### 5. 可用性 ✅
- [ ] 能够与Claude Desktop集成
- [ ] 能够进行真实的代码分析
- [ ] 错误消息清晰

---

## 📞 获取帮助

### 遇到技术问题

1. **查看文档**
   - 先查阅相关设计文档
   - 查看QUICK_REFERENCE.md

2. **查看代码示例**
   - examples/ 目录
   - tests/ 目录的测试代码

3. **调试**
   - 查看日志文件
   - 使用pdb调试
   - 运行单元测试

4. **提问**
   - GitHub Issues
   - 团队讨论
   - 代码审查

---

## 🎉 下一步

### 立即开始

1. **阅读文档**（1小时）
   - 通读本文档
   - 阅读DEVELOPMENT_PLAN.md

2. **环境准备**（30分钟）
   - 安装Python和依赖
   - 安装Joern
   - 运行示例

3. **开始第一个任务**（2小时）
   - 任务1.1: 创建项目骨架
   - 编写第一个测试
   - 提交第一个commit

### 保持联系

- 📧 技术问题：通过GitHub Issues
- 💬 日常讨论：团队聊天工具
- 📊 进度汇报：每周例会

---

**祝开发顺利！** 🚀

**文档版本**: v1.0  
**最后更新**: 2025-11-26  
**维护者**: Joern MCP Team

