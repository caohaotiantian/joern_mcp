# Joern 集成方案详解

## 集成方式对比

### 方式一：REPL 模式（不推荐）

**运行方式**:
```bash
joern
# 或
joern --script <script.sc>
```

**特点**:
- ❌ 交互式命令行界面
- ❌ 需要解析提示符（`joern>`）
- ❌ 需要处理 ANSI 颜色代码
- ❌ 输出格式不统一
- ❌ 进程管理复杂
- ❌ 错误处理困难

**适用场景**:
- 手动交互式分析
- 脚本执行
- 调试和测试

### 方式二：Server 模式（推荐✅）

**运行方式**:
```bash
joern --server
# 或带认证
joern --server --server-auth-username admin --server-auth-password secret
# 或指定主机和端口
joern --server --server-host localhost --server-port 8080
```

**特点**:
- ✅ 标准 HTTP REST API
- ✅ 官方 Python 客户端库（`cpgqls-client`）
- ✅ 支持同步和异步查询
- ✅ WebSocket 通知支持
- ✅ 可配置认证
- ✅ 稳定可靠
- ✅ 易于集成

**适用场景**:
- 自动化代码分析
- 集成到其他工具
- 远程代码分析
- **我们的 MCP Server** ⭐

## Server 模式详解

### API 端点

#### 1. 提交查询（异步）

**POST** `/query`

请求体:
```json
{
  "query": "cpg.method.name.l"
}
```

响应:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. 获取结果

**GET** `/result/{uuid}`

响应（查询进行中）:
```json
{
  "success": false,
  "stdout": "",
  "stderr": ""
}
```

响应（查询完成）:
```json
{
  "success": true,
  "stdout": "[\"main\", \"foo\", \"bar\"]",
  "stderr": ""
}
```

#### 3. 同步查询（推荐）

**POST** `/query-sync`

请求体:
```json
{
  "query": "cpg.method.name.l"
}
```

响应:
```json
{
  "success": true,
  "stdout": "[\"main\", \"foo\", \"bar\"]",
  "stderr": ""
}
```

#### 4. WebSocket 通知

**WebSocket** `ws://localhost:8080/connect`

订阅后会收到查询完成的 UUID 通知。

### Python 客户端使用

#### 安装

```bash
pip install cpgqls-client
```

#### 基础使用

```python
from cpgqls_client import CPGQLSClient, import_code_query

# 创建客户端
server_endpoint = "localhost:8080"
client = CPGQLSClient(server_endpoint)

# 带认证
auth_credentials = ("username", "password")
client = CPGQLSClient(server_endpoint, auth_credentials=auth_credentials)

# 导入代码
query = import_code_query("/path/to/code", "project-name")
result = client.execute(query)
print(result['stdout'])

# 执行查询
query = "cpg.method.name.l"
result = client.execute(query)
print(result)  # {'success': True, 'stdout': '...', 'stderr': ''}
```

#### 高级用法

```python
# 复杂查询示例
query = """
cpg.method.name("main")
   .map(m => Map(
       "name" -> m.name,
       "signature" -> m.signature,
       "filename" -> m.filename,
       "lineNumber" -> m.lineNumber.getOrElse(-1)
   )).toJson
"""
result = client.execute(query)

# 解析 JSON 结果
import json
data = json.loads(result['stdout'])
print(data)
```

## 我们的集成方案

### 架构设计

```
┌────────────────────────────────────────────┐
│         Joern MCP Server (Python)          │
│                                            │
│  ┌──────────────────────────────────┐    │
│  │    JoernServerManager            │    │
│  │  - 启动/停止 Joern Server        │    │
│  │  - 进程生命周期管理              │    │
│  │  - 健康检查                      │    │
│  └──────────────────────────────────┘    │
│                 │                         │
│                 │ 使用                    │
│                 ↓                         │
│  ┌──────────────────────────────────┐    │
│  │    QueryExecutor                 │    │
│  │  - 查询执行                      │    │
│  │  - 结果缓存                      │    │
│  │  - 查询验证                      │    │
│  └──────────────────────────────────┘    │
│                 │                         │
│                 │ 依赖                    │
│                 ↓                         │
│  ┌──────────────────────────────────┐    │
│  │    cpgqls_client.CPGQLSClient    │    │
│  │    (官方 Python 库)               │    │
│  └──────────────────────────────────┘    │
└────────────────────────────────────────────┘
                 │
                 │ HTTP/WebSocket
                 ↓
┌────────────────────────────────────────────┐
│         Joern Server (Scala/JVM)           │
│                                            │
│  - HTTP API (:8080)                        │
│  - WebSocket (:8080/connect)               │
│  - CPG 查询引擎                            │
└────────────────────────────────────────────┘
```

### 核心代码示例

#### JoernServerManager

```python
from cpgqls_client import CPGQLSClient, import_code_query
import asyncio
import httpx

class JoernServerManager:
    """Joern Server 管理器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.endpoint = f"{host}:{port}"
        self.client: Optional[CPGQLSClient] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        
    async def start_server(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """启动 Joern Server"""
        cmd = [
            "joern",
            "--server",
            "--server-host", self.host,
            "--server-port", str(self.port)
        ]
        
        if username and password:
            cmd.extend([
                "--server-auth-username", username,
                "--server-auth-password", password
            ])
            self.auth_credentials = (username, password)
        
        # 启动服务器
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 等待服务器就绪
        await self._wait_for_server()
        
        # 初始化客户端
        self.client = CPGQLSClient(
            self.endpoint,
            auth_credentials=self.auth_credentials if username else None
        )
    
    async def _wait_for_server(self, timeout: int = 30):
        """等待服务器启动"""
        start_time = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"http://{self.endpoint}/",
                        timeout=1.0
                    )
                    if response.status_code in [200, 404]:
                        logger.info("Joern server is ready")
                        return
                except Exception as e:
                    logger.debug(f"Waiting for server: {e}")
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Joern server failed to start")
                
                await asyncio.sleep(0.5)
    
    async def execute_query(self, query: str) -> Dict:
        """执行查询（同步）"""
        if not self.client:
            raise RuntimeError("Joern server not started")
        
        result = self.client.execute(query)
        return result
    
    async def import_code(self, source_path: str, project_name: str) -> Dict:
        """导入代码生成 CPG"""
        query = import_code_query(source_path, project_name)
        result = self.client.execute(query)
        return result
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            result = self.client.execute("1 + 1")
            return result.get("success", False)
        except:
            return False
    
    async def stop_server(self):
        """停止服务器"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.client = None
```

#### QueryExecutor

```python
from typing import Dict, Optional
from cachetools import TTLCache
import hashlib

class QueryExecutor:
    """查询执行器"""
    
    def __init__(self, server_manager: JoernServerManager):
        self.server_manager = server_manager
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        
    async def execute(
        self,
        query: str,
        format: str = "json",
        use_cache: bool = True
    ) -> Dict:
        """执行查询"""
        # 1. 验证查询
        self._validate_query(query)
        
        # 2. 检查缓存
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if use_cache and cache_key in self.cache:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.cache[cache_key]
        
        # 3. 确保返回 JSON
        if format == "json" and not query.strip().endswith(".toJson"):
            query = f"({query}).toJson"
        
        # 4. 执行查询
        result = await self.server_manager.execute_query(query)
        
        # 5. 解析结果
        if result.get("success"):
            parsed = self._parse_result(result)
            
            # 6. 缓存结果
            if use_cache:
                self.cache[cache_key] = parsed
            
            return parsed
        else:
            raise QueryExecutionError(result.get("stderr", "Unknown error"))
    
    def _validate_query(self, query: str):
        """验证查询安全性"""
        forbidden = [
            "System.exit",
            "Runtime.getRuntime",
            "ProcessBuilder",
        ]
        for pattern in forbidden:
            if pattern in query:
                raise SecurityError(f"Forbidden operation: {pattern}")
    
    def _parse_result(self, result: Dict) -> Dict:
        """解析查询结果"""
        stdout = result.get("stdout", "")
        
        # 尝试解析 JSON
        import json
        try:
            return {"data": json.loads(stdout), "raw": stdout}
        except json.JSONDecodeError:
            return {"raw": stdout}
```

### 使用示例

```python
import asyncio
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor

async def main():
    # 1. 启动 Joern Server
    manager = JoernServerManager()
    await manager.start_server()
    
    # 2. 创建查询执行器
    executor = QueryExecutor(manager)
    
    # 3. 导入代码
    await manager.import_code("/path/to/code", "my-project")
    
    # 4. 执行查询
    result = await executor.execute("cpg.method.name.l")
    print(result)
    
    # 5. 复杂查询
    query = """
    cpg.method.name("main")
       .map(m => Map(
           "name" -> m.name,
           "file" -> m.filename
       )).toJson
    """
    result = await executor.execute(query)
    print(result['data'])
    
    # 6. 停止服务器
    await manager.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置建议

### 环境变量

```bash
# Joern Server 配置
JOERN_SERVER_HOST=localhost
JOERN_SERVER_PORT=8080
JOERN_SERVER_USERNAME=admin
JOERN_SERVER_PASSWORD=secret

# 性能配置
JOERN_SERVER_TIMEOUT=30
QUERY_CACHE_SIZE=1000
QUERY_CACHE_TTL=3600
```

### 生产环境建议

1. **启用认证**
   ```bash
   joern --server \
     --server-auth-username $USERNAME \
     --server-auth-password $PASSWORD
   ```

2. **使用专用端口**
   ```bash
   joern --server --server-port 8888
   ```

3. **监控健康状态**
   - 定期调用 `health_check()`
   - 设置自动重启机制

4. **日志管理**
   - 捕获服务器输出
   - 记录查询日志
   - 监控性能指标

5. **资源限制**
   - 限制并发查询数量
   - 设置查询超时
   - 控制缓存大小

## 优势总结

使用 Joern Server 模式相比 REPL 模式的优势：

1. **开发体验** ⭐⭐⭐⭐⭐
   - 官方 Python 库，开箱即用
   - API 清晰，易于理解
   - 无需处理 REPL 复杂性

2. **稳定性** ⭐⭐⭐⭐⭐
   - HTTP 协议成熟可靠
   - 标准化的错误处理
   - 进程管理简单

3. **性能** ⭐⭐⭐⭐
   - 支持异步查询
   - WebSocket 实时通知
   - 可配置缓存

4. **安全性** ⭐⭐⭐⭐⭐
   - 内置认证机制
   - 可配置访问控制
   - 网络隔离

5. **可维护性** ⭐⭐⭐⭐⭐
   - 代码简洁清晰
   - 易于测试
   - 便于调试

## 参考资料

- [Joern 集成指南](https://joern.io/integrate/)
- [Joern Server 文档](https://docs.joern.io/server/)
- [cpgqls-client Python 库](https://github.com/joernio/cpgqls-client-python)
- [Joern 主页](https://joern.io)
- [Joern GitHub](https://github.com/joernio/joern)

---

**最后更新**: 2025-11-26  
**文档版本**: v1.0

