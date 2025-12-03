# 安装指南

本文档详细介绍如何安装和配置 Joern MCP Server。

---

## 📋 系统要求

### 最低要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Linux, macOS, Windows (WSL2) |
| **Python** | 3.10+ |
| **Java** | JDK 11+ (Joern依赖) |
| **内存** | 4GB+ (建议8GB+用于大型项目) |
| **磁盘** | 2GB+ (Joern安装) |

### 推荐配置

- **CPU**: 4核+
- **内存**: 16GB+
- **磁盘**: SSD，10GB+可用空间

---

## 📦 安装步骤

### 第一步：安装Java

Joern需要Java 11或更高版本。

**macOS (Homebrew)**:
```bash
brew install openjdk@11
# 或安装最新版本
brew install openjdk
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install openjdk-11-jdk
```

**验证安装**:
```bash
java -version
# 输出应显示 Java 11 或更高版本
```

---

### 第二步：安装Joern

**方式一：使用安装脚本（推荐）**

```bash
# 下载并运行安装脚本
curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" | bash

# 添加到PATH
export PATH="$HOME/bin/joern:$PATH"
echo 'export PATH="$HOME/bin/joern:$PATH"' >> ~/.bashrc  # 或 ~/.zshrc
```

**方式二：Homebrew (macOS)**

```bash
brew install joern
```

**方式三：手动下载**

1. 访问 [Joern Releases](https://github.com/joernio/joern/releases)
2. 下载最新版本的 `joern-cli-*.zip`
3. 解压并添加到PATH

**验证安装**:
```bash
joern --version
# 应输出类似: Joern Version 2.x.x
```

---

### 第三步：安装Joern MCP Server

**方式一：从源码安装（开发）**

```bash
# 克隆仓库
git clone https://github.com/yourusername/joern_mcp.git
cd joern_mcp

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装（含开发依赖）
pip install -e ".[dev]"
```

**方式二：pip安装（发布后）**

```bash
pip install joern-mcp
```

**验证安装**:
```bash
# 检查模块
python -c "import joern_mcp; print(joern_mcp.__version__)"

# 运行单元测试
pytest tests/test_services -v --timeout=60
```

---

## ⚙️ 配置

### 环境变量

创建 `.env` 文件（或设置环境变量）：

```bash
# Joern Server配置
JOERN_SERVER_HOST=localhost     # Joern服务器地址
JOERN_SERVER_PORT=8080          # Joern服务器端口
JOERN_SERVER_USERNAME=          # 可选：认证用户名
JOERN_SERVER_PASSWORD=          # 可选：认证密码

# 查询配置
MAX_QUERY_TIMEOUT=300           # 查询超时时间（秒）
ENABLE_CUSTOM_QUERIES=true      # 是否允许自定义查询

# 日志配置
LOG_LEVEL=INFO                  # 日志级别: DEBUG, INFO, WARNING, ERROR

# 性能配置
QUERY_CACHE_SIZE=1000           # 查询缓存大小
MAX_CONCURRENT_QUERIES=5        # 最大并发查询数
```

### 配置文件位置

配置文件按以下顺序加载：

1. `.env` 文件（项目根目录）
2. `~/.joern_mcp/.env`（用户目录）
3. 环境变量（优先级最高）

---

## 🚀 启动服务器

### 基本启动

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务器
python -m joern_mcp
```

### 调试模式

```bash
# 设置调试日志
LOG_LEVEL=DEBUG python -m joern_mcp
```

### 后台运行

```bash
# 使用nohup
nohup python -m joern_mcp > joern_mcp.log 2>&1 &

# 或使用systemd服务（Linux）
```

---

## 🔍 验证安装

### 1. 检查Joern连接

```bash
# 启动独立的Joern Server
joern --server --server-host localhost --server-port 8080
```

### 2. 运行测试

```bash
# 单元测试（无需Joern）
pytest tests/test_services -v

# 集成测试（需要Joern）
pytest tests/integration -v --timeout=180
```

### 3. 测试MCP工具

```python
# 使用Python测试
import asyncio
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor

async def test():
    # 启动服务器
    server = JoernServerManager()
    await server.start()
    
    # 导入测试代码
    await server.import_code("/path/to/test/code", "test-project")
    
    # 测试服务
    executor = OptimizedQueryExecutor(server)
    service = CallGraphService(executor)
    result = await service.get_callers("main")
    print(result)
    
    # 关闭
    await server.stop()

asyncio.run(test())
```

---

## 🐛 常见问题

### 问题1：Joern启动失败

**症状**: `Could not find or load main class io.joern.joerncli.JoernCli`

**解决方案**:
```bash
# 确保Java版本正确
java -version

# 重新安装Joern
rm -rf ~/bin/joern
curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" | bash
```

### 问题2：端口被占用

**症状**: `Port 8080 is already in use`

**解决方案**:
```bash
# 查找占用进程
lsof -i :8080

# 终止进程
kill -9 <PID>

# 或使用其他端口
JOERN_SERVER_PORT=9090 python -m joern_mcp
```

### 问题3：内存不足

**症状**: `java.lang.OutOfMemoryError`

**解决方案**:
```bash
# 增加Java堆内存
export JAVA_OPTS="-Xmx8g"
joern --server --server-host localhost --server-port 8080
```

### 问题4：Python依赖冲突

**症状**: `ModuleNotFoundError` 或版本冲突

**解决方案**:
```bash
# 重新创建虚拟环境
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## 📊 性能优化

### 大型项目

对于大型代码库（>100K行），建议：

```bash
# 增加内存
export JAVA_OPTS="-Xmx16g"

# 增加超时
MAX_QUERY_TIMEOUT=600 python -m joern_mcp

# 启用查询缓存
QUERY_CACHE_SIZE=2000 python -m joern_mcp
```

### 多项目分析

```bash
# 限制并发
MAX_CONCURRENT_QUERIES=3 python -m joern_mcp
```

---

## 📞 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/yourusername/joern_mcp/issues)
- **Joern文档**: [docs.joern.io](https://docs.joern.io)
- **MCP协议**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## ⏭️ 下一步

安装完成后，请阅读：

- [用户手册](./USER_GUIDE.md) - 学习如何使用各种功能
- [API参考](./API_REFERENCE.md) - 查看所有MCP工具的详细说明
- [示例项目](../examples/) - 运行真实的漏洞检测示例

