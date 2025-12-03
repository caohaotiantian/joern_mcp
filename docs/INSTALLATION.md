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

### 快速配置

复制示例配置文件：

```bash
cp env.example .env
```

### 配置项说明

创建 `.env` 文件并根据需要修改：

```bash
# ============================================
# Joern 服务器配置（必需）
# ============================================
JOERN_SERVER_HOST=localhost     # Joern 服务器地址
JOERN_SERVER_PORT=8080          # Joern 服务器端口

# 如果 Joern 服务器启用了认证（可选）
# JOERN_SERVER_USERNAME=admin
# JOERN_SERVER_PASSWORD=secret

# ============================================
# Joern 路径配置（可选）
# ============================================
# Joern 安装路径（默认从 PATH 查找）
# JOERN_HOME=/usr/local/lib/joern

# 工作空间路径（存放临时文件）
# JOERN_WORKSPACE=~/.joern_mcp/workspace

# CPG 缓存路径（存放生成的 CPG 文件）
# JOERN_CPG_CACHE=~/.joern_mcp/cpg_cache

# ============================================
# 性能配置
# ============================================
MAX_CONCURRENT_QUERIES=5        # 最大并发查询数
QUERY_TIMEOUT=300               # 查询超时时间（秒）
QUERY_CACHE_SIZE=1000           # 查询结果缓存大小（条目数）
QUERY_CACHE_TTL=3600            # 查询缓存 TTL（秒）

# ============================================
# 安全配置
# ============================================
ENABLE_CUSTOM_QUERIES=true      # 是否允许执行自定义 CPGQL 查询

# ============================================
# 日志配置
# ============================================
LOG_LEVEL=INFO                  # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
# LOG_FILE_PATH=~/.joern_mcp/logs  # 日志文件路径
LOG_FILE_SIZE=500               # 日志文件大小限制（MB）
LOG_RETENTION_DAYS=10           # 日志文件保留天数

# ============================================
# JVM 配置（可选，影响 Joern 性能）
# ============================================
# _JAVA_OPTIONS=-Xmx8G -Xms2G
```

### 配置项详解

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `JOERN_SERVER_HOST` | string | `localhost` | Joern 服务器地址 |
| `JOERN_SERVER_PORT` | int | `8080` | Joern 服务器端口 |
| `JOERN_SERVER_USERNAME` | string | - | 认证用户名（可选） |
| `JOERN_SERVER_PASSWORD` | string | - | 认证密码（可选） |
| `JOERN_HOME` | path | - | Joern 安装路径 |
| `JOERN_WORKSPACE` | path | `~/.joern_mcp/workspace` | 工作空间路径 |
| `JOERN_CPG_CACHE` | path | `~/.joern_mcp/cpg_cache` | CPG 缓存路径 |
| `MAX_CONCURRENT_QUERIES` | int | `5` | 最大并发查询数 |
| `QUERY_TIMEOUT` | int | `300` | 查询超时（秒） |
| `QUERY_CACHE_SIZE` | int | `1000` | 查询缓存大小 |
| `QUERY_CACHE_TTL` | int | `3600` | 缓存 TTL（秒） |
| `ENABLE_CUSTOM_QUERIES` | bool | `true` | 允许自定义查询 |
| `LOG_LEVEL` | string | `INFO` | 日志级别 |
| `LOG_FILE_PATH` | path | `~/.joern_mcp/logs` | 日志文件路径 |
| `LOG_FILE_SIZE` | int | `500` | 日志文件大小（MB） |
| `LOG_RETENTION_DAYS` | int | `10` | 日志保留天数 |

### 配置文件位置

配置按以下优先级加载（后者覆盖前者）：

1. 默认值（代码中定义）
2. `.env` 文件（项目根目录）
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
# 增加 JVM 内存
export _JAVA_OPTIONS="-Xmx16g -Xms4g"

# 增加查询超时时间
QUERY_TIMEOUT=600 python -m joern_mcp

# 增大查询缓存
QUERY_CACHE_SIZE=2000 python -m joern_mcp

# 或组合配置
QUERY_TIMEOUT=600 QUERY_CACHE_SIZE=2000 python -m joern_mcp
```

### 多项目分析

```bash
# 限制并发数以避免资源竞争
MAX_CONCURRENT_QUERIES=3 python -m joern_mcp
```

### 调试模式

```bash
# 启用详细日志
LOG_LEVEL=DEBUG python -m joern_mcp
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

