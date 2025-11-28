# Joern MCP Server 集成测试指南

## 📚 目录

1. [概述](#概述)
2. [环境准备](#环境准备)
3. [运行集成测试](#运行集成测试)
4. [测试类型](#测试类型)
5. [测试详情](#测试详情)
6. [故障排除](#故障排除)

---

## 概述

集成测试验证Joern MCP Server在真实环境中的功能和性能。

### 测试范围

- ✅ 服务器生命周期管理
- ✅ MCP Tools功能集成
- ✅ 项目管理流程
- ✅ 查询执行和缓存
- ✅ 并发和性能
- ✅ 错误处理和边界条件

### 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.performance` | 性能测试 |
| `@pytest.mark.stress` | 压力测试 |
| `@pytest.mark.skipif` | 条件跳过 |

---

## 环境准备

### 1. 安装Joern

集成测试需要真实的Joern环境。

**下载Joern**:
```bash
# 访问 https://joern.io 下载最新版本
# 或使用以下命令:
cd /tmp
wget https://github.com/joernio/joern/releases/latest/download/joern-cli.zip
unzip joern-cli.zip
sudo mv joern-cli /opt/joern
```

**添加到PATH**:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PATH="/opt/joern/joern-cli:$PATH"

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

**验证安装**:
```bash
joern --version
```

### 2. 安装Python依赖

```bash
cd /path/to/joern_mcp

# 激活虚拟环境
source .venv/bin/activate

# 安装集成测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock psutil
```

### 3. 配置环境

创建 `.env` 文件（可选）:

```bash
# Joern Server配置
JOERN_SERVER_HOST=localhost
JOERN_SERVER_PORT=8080
JOERN_SERVER_TIMEOUT=300

# 测试配置
JOERN_INSTALL_PATH=/opt/joern/joern-cli
```

---

## 运行集成测试

### 使用便捷脚本（推荐）

```bash
cd /path/to/joern_mcp

# 查看帮助
./run_integration_tests.sh --help

# 快速测试（跳过性能测试）
./run_integration_tests.sh

# 运行所有测试
./run_integration_tests.sh --all

# 只测试生命周期
./run_integration_tests.sh --lifecycle

# 只测试工具集成
./run_integration_tests.sh --tools

# 性能测试
./run_integration_tests.sh --performance

# 压力测试
./run_integration_tests.sh --stress

# 错误处理测试
./run_integration_tests.sh --error
```

### 使用pytest直接运行

```bash
cd /path/to/joern_mcp
source .venv/bin/activate

# 运行所有集成测试
PYTHONPATH=src pytest tests/integration/ -m integration -v

# 运行特定测试文件
PYTHONPATH=src pytest tests/integration/test_server_lifecycle.py -v

# 运行性能测试
PYTHONPATH=src pytest tests/integration/ -m performance -v

# 运行压力测试
PYTHONPATH=src pytest tests/integration/ -m stress -v

# 跳过需要Joern的测试
PYTHONPATH=src pytest tests/integration/ -v
```

---

## 测试类型

### 1. 生命周期测试

**文件**: `tests/integration/test_server_lifecycle.py`

**测试内容**:
- Joern管理器初始化
- Joern Server启动和停止
- 查询执行器初始化
- 服务器重启
- 并发查询

**运行**:
```bash
./run_integration_tests.sh --lifecycle
```

### 2. 工具集成测试

**文件**: `tests/integration/test_tools_integration.py`

**测试内容**:
- 项目管理流程（导入、列出、删除）
- 查询工具（函数查询、详情、列表）
- 调用图工具（callers、callees、call graph）
- 污点分析工具（漏洞检测、规则查询）
- 批量操作（批量查询、批量分析）

**运行**:
```bash
./run_integration_tests.sh --tools
```

### 3. 性能测试

**文件**: `tests/integration/test_performance.py`

**测试内容**:
- 查询响应时间
- 并发查询性能
- 缓存性能
- 内存使用

**运行**:
```bash
./run_integration_tests.sh --performance
```

### 4. 压力测试

**文件**: `tests/integration/test_performance.py`

**测试内容**:
- 高并发测试（50+并发查询）
- 长时间运行查询

**运行**:
```bash
./run_integration_tests.sh --stress
```

### 5. 错误处理测试

**文件**: `tests/integration/test_error_handling.py`

**测试内容**:
- 无效查询处理
- 查询超时
- 不存在的项目
- 无效文件路径
- 空查询
- 危险查询阻止
- 参数边界条件

**运行**:
```bash
./run_integration_tests.sh --error
```

---

## 测试详情

### 测试数据

集成测试使用自动生成的示例代码：

**C代码示例** (`tests/integration/test_data/sample_c/vulnerable.c`):
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[100];
    strcpy(buffer, input);  // Buffer overflow
    system(buffer);         // Command injection
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0
}
```

**Java代码示例** (`tests/integration/test_data/sample_java/Vulnerable.java`):
```java
public class Vulnerable {
    public void sqlInjection(String userInput) {
        String query = "SELECT * FROM users WHERE name = '" + userInput + "'";
        executeQuery(query);  // SQL Injection
    }
}
```

### 预期结果

#### 快速测试

```
运行测试...
======================================
============================= test session starts ==============================
collected X items

tests/integration/test_server_lifecycle.py::TestServerLifecycle::test_joern_manager_initialization PASSED
tests/integration/test_server_lifecycle.py::TestServerLifecycle::test_query_executor_initialization PASSED
...

✅ 集成测试完成！
```

#### 完整测试

所有测试应该通过，除非：
- Joern未安装（自动跳过）
- 系统资源不足（性能测试可能失败）
- Joern Server端口被占用

---

## 故障排除

### 问题1: Joern未安装

**错误**:
```
⚠️  警告：Joern未安装或不在PATH中
```

**解决**:
1. 下载并安装Joern: https://joern.io
2. 添加到PATH
3. 验证: `joern --version`

### 问题2: 端口被占用

**错误**:
```
OSError: [Errno 48] Address already in use
```

**解决**:
```bash
# 查找占用8080端口的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或修改端口
export JOERN_SERVER_PORT=8081
```

### 问题3: 测试超时

**错误**:
```
TimeoutError: Joern server did not become ready in time
```

**解决**:
1. 增加超时时间:
```bash
export JOERN_SERVER_TIMEOUT=600
```

2. 检查Joern是否正确启动:
```bash
joern --server --server-host localhost --server-port 8080
```

### 问题4: 内存不足

**错误**:
```
MemoryError or OutOfMemoryError
```

**解决**:
1. 增加JVM内存（Joern配置）
2. 减少并发测试数量
3. 跳过压力测试:
```bash
./run_integration_tests.sh --quick
```

### 问题5: 测试数据创建失败

**错误**:
```
FileNotFoundError: test_data directory
```

**解决**:
```bash
# 手动创建测试数据目录
mkdir -p tests/integration/test_data
```

---

## 性能基准

### 预期性能指标

| 测试类型 | 预期时间 | 内存使用 |
|---------|---------|---------|
| 简单查询 | < 5秒 | < 100MB |
| 并发查询(10) | < 30秒 | < 200MB |
| 缓存查询 | < 1秒 | 最小 |
| 批量操作 | < 60秒 | < 300MB |

### 系统要求

**最低配置**:
- CPU: 2核心
- 内存: 4GB
- 磁盘: 5GB

**推荐配置**:
- CPU: 4核心+
- 内存: 8GB+
- 磁盘: 10GB+

---

## CI/CD集成

### GitHub Actions示例

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Joern
        run: |
          wget https://github.com/joernio/joern/releases/latest/download/joern-cli.zip
          unzip joern-cli.zip
          echo "$PWD/joern-cli" >> $GITHUB_PATH
          
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
          
      - name: Install Dependencies
        run: pip install -r requirements.txt
        
      - name: Run Integration Tests
        run: ./run_integration_tests.sh --quick
```

---

## 最佳实践

### 1. 运行顺序

建议按以下顺序运行测试：

```bash
# 1. 快速验证
./run_integration_tests.sh --quick

# 2. 完整测试
./run_integration_tests.sh --all

# 3. 性能测试
./run_integration_tests.sh --performance

# 4. 压力测试
./run_integration_tests.sh --stress
```

### 2. 调试测试

```bash
# 显示详细输出
PYTHONPATH=src pytest tests/integration/ -v -s

# 只运行失败的测试
PYTHONPATH=src pytest tests/integration/ --lf

# 调试模式
PYTHONPATH=src pytest tests/integration/ --pdb
```

### 3. 测试隔离

- 每个测试使用独立的项目名称
- 使用`cleanup_projects` fixture清理
- 避免测试间的状态共享

### 4. 性能优化

- 使用缓存减少重复查询
- 批量操作优于循环单次操作
- 合理设置并发限制

---

## 更多信息

- [用户指南](USER_GUIDE.md)
- [API参考](API_REFERENCE.md)
- [开发计划](DEVELOPMENT_PLAN.md)
- [验证报告](../VALIDATION_REPORT.md)

---

**版本**: 0.7.0-dev  
**最后更新**: 2025-11-27

