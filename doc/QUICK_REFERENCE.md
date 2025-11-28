# Joern MCP Server 快速参考

## Joern Server 快速命令

### 启动服务器

```bash
# 基本启动
joern --server

# 带认证启动
joern --server \
  --server-auth-username admin \
  --server-auth-password secret123

# 自定义主机和端口
joern --server \
  --server-host 0.0.0.0 \
  --server-port 8888
```

### 测试连接

```bash
# 测试服务器是否运行
curl http://localhost:8080/

# 执行同步查询
curl -X POST http://localhost:8080/query-sync \
  -H "Content-Type: application/json" \
  -d '{"query": "1 + 1"}'

# 带认证的查询
curl -X POST http://localhost:8080/query-sync \
  -u admin:secret123 \
  -H "Content-Type: application/json" \
  -d '{"query": "cpg.method.name.l"}'
```

## Python 快速代码片段

### 安装依赖

```bash
pip install cpgqls-client httpx
```

### 基础使用

```python
from cpgqls_client import CPGQLSClient, import_code_query

# 创建客户端
client = CPGQLSClient("localhost:8080")

# 导入代码
query = import_code_query("/path/to/code", "project-name")
result = client.execute(query)
print(result['stdout'])

# 执行查询
result = client.execute("cpg.method.name.l")
print(result)
```

### 异步使用

```python
import asyncio
import httpx

async def execute_async_query(query: str):
    # 提交查询
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/query",
            json={"query": query}
        )
        uuid = response.json()["uuid"]
    
    # 轮询结果
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/result/{uuid}"
            )
            result = response.json()
            
            if result["success"]:
                return result
        
        await asyncio.sleep(0.5)

# 使用
result = asyncio.run(execute_async_query("cpg.method.name.l"))
print(result)
```

## 常用查询模板

### 列出所有方法

```scala
cpg.method.name.l
```

### 获取方法详情

```scala
cpg.method.name("main")
   .map(m => Map(
       "name" -> m.name,
       "signature" -> m.signature,
       "filename" -> m.filename,
       "lineNumber" -> m.lineNumber.getOrElse(-1),
       "code" -> m.code
   )).toJson
```

### 查找调用者

```scala
cpg.method.name("vulnerable_function")
   .caller
   .map(m => Map(
       "name" -> m.name,
       "file" -> m.filename
   )).dedup.toJson
```

### 数据流分析

```scala
def source = cpg.method.name("gets").parameter
def sink = cpg.call.name("system").argument

sink.reachableBy(source).flows.map(flow => Map(
    "source" -> flow.source.code,
    "sink" -> flow.sink.code,
    "pathLength" -> flow.elements.size
)).toJson
```

### 污点分析

```scala
def sources = cpg.method.name("(gets|scanf)").parameter
def sinks = cpg.call.name("(system|exec)").argument

sinks.reachableBy(sources).flows.map(flow => Map(
    "vulnerability" -> "Command Injection",
    "source" -> Map(
        "method" -> flow.source.method.name,
        "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
        "line" -> flow.source.lineNumber.getOrElse(-1)
    ),
    "sink" -> Map(
        "method" -> flow.sink.method.name,
        "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
        "line" -> flow.sink.lineNumber.getOrElse(-1)
    )
)).toJson
```

## API 端点速查

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/query` | 提交异步查询，返回UUID |
| GET | `/result/{uuid}` | 获取查询结果 |
| POST | `/query-sync` | 同步查询（推荐） |
| WebSocket | `/connect` | 订阅查询完成通知 |

## 配置速查

### 环境变量

```bash
# Joern Server
JOERN_SERVER_HOST=localhost
JOERN_SERVER_PORT=8080
JOERN_SERVER_USERNAME=admin
JOERN_SERVER_PASSWORD=secret

# MCP Server
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO

# 性能
MAX_CONCURRENT_QUERIES=5
QUERY_TIMEOUT=300
QUERY_CACHE_SIZE=1000
QUERY_CACHE_TTL=3600
```

### Python 配置

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Joern配置
    joern_server_host: str = "localhost"
    joern_server_port: int = 8080
    joern_server_username: Optional[str] = None
    joern_server_password: Optional[str] = None
    
    # 性能配置
    max_concurrent_queries: int = 5
    query_timeout: int = 300
    query_cache_size: int = 1000
    query_cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
```

## 故障排除

### 服务器无法启动

```bash
# 检查端口是否被占用
lsof -i :8080

# 使用其他端口
joern --server --server-port 8888

# 检查Joern是否安装
joern --version

# 查看详细日志
joern --server 2>&1 | tee joern-server.log
```

### 查询超时

```python
# 增加超时时间
result = client.execute(query)  # 默认300秒

# 优化查询
query = "cpg.method.name.take(10).l"  # 限制结果数量
```

### 连接被拒绝

```bash
# 检查服务器是否运行
ps aux | grep joern

# 检查防火墙
sudo ufw status

# 测试连接
curl http://localhost:8080/
```

## 性能优化技巧

### 1. 使用缓存

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)

def execute_cached(query: str):
    key = hash(query)
    if key in cache:
        return cache[key]
    
    result = client.execute(query)
    cache[key] = result
    return result
```

### 2. 限制结果数量

```scala
// 限制返回10个结果
cpg.method.name.take(10).l

// 使用过滤条件
cpg.method.name.filter(_.contains("main")).l
```

### 3. 并发查询

```python
import asyncio

async def batch_queries(queries: List[str]):
    tasks = [execute_async_query(q) for q in queries]
    return await asyncio.gather(*tasks)
```

### 4. 索引优化

```scala
// 使用索引查询更快
cpg.method.name("exact_name").l  // 精确匹配
// 而不是
cpg.method.filter(_.name.contains("name")).l  // 全扫描
```

## 监控和日志

### 健康检查

```python
async def health_check():
    try:
        result = client.execute("1 + 1")
        return result.get("success", False)
    except:
        return False
```

### 查询日志

```python
from loguru import logger

logger.add("joern_queries.log", rotation="500 MB")

def execute_with_logging(query: str):
    logger.info(f"Executing query: {query[:100]}...")
    start = time.time()
    
    try:
        result = client.execute(query)
        duration = time.time() - start
        logger.info(f"Query completed in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise
```

### 性能指标

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QueryMetrics:
    query: str
    duration: float
    success: bool
    timestamp: datetime
    result_size: int

metrics: List[QueryMetrics] = []

def track_metrics(query: str, result: Dict, duration: float):
    metrics.append(QueryMetrics(
        query=query[:100],
        duration=duration,
        success=result.get("success", False),
        timestamp=datetime.now(),
        result_size=len(str(result))
    ))
```

## 安全最佳实践

### 1. 启用认证

```bash
joern --server \
  --server-auth-username $(openssl rand -base64 12) \
  --server-auth-password $(openssl rand -base64 32)
```

### 2. 查询验证

```python
FORBIDDEN_PATTERNS = [
    r"System\.exit",
    r"Runtime\.getRuntime",
    r"ProcessBuilder",
    r"File\.delete",
]

def validate_query(query: str) -> bool:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, query):
            return False
    return True
```

### 3. 资源限制

```python
MAX_QUERY_LENGTH = 10000
MAX_RESULT_SIZE = 100 * 1024 * 1024  # 100MB

def check_limits(query: str, result: Dict):
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Query too long")
    
    result_size = len(str(result))
    if result_size > MAX_RESULT_SIZE:
        raise ValueError("Result too large")
```

## 相关链接

- 📘 [完整设计文档](DESIGN.md)
- 🔧 [集成详解](JOERN_INTEGRATION.md)
- 📝 [更新说明](UPDATES.md)
- 🌐 [Joern官网](https://joern.io)
- 📚 [Joern文档](https://docs.joern.io)
- 🐙 [GitHub](https://github.com/joernio/joern)

---

**版本**: v1.0  
**更新**: 2025-11-26

