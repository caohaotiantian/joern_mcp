# Joern MCP Server 详细开发计划

## 项目概述

**目标**: 实现一个功能完整的Joern MCP Server，使LLM能够通过MCP协议进行代码静态分析

**开发周期**: 8周（MVP版本）

**团队规模**: 建议1-2名开发者

## 开发原则

1. **迭代开发**: 每个阶段都产出可运行的版本
2. **测试驱动**: 每个功能都有对应的测试
3. **持续集成**: 每次提交都要通过测试
4. **文档同步**: 代码和文档同步更新

---

## 第一周：基础设施搭建

### Day 1-2: 项目初始化

#### 任务 1.1: 创建项目骨架

**目标**: 搭建完整的项目目录结构

**步骤**:
```bash
# 1. 创建目录结构
mkdir -p src/joern_mcp/{joern,services,tools,resources,prompts,models,utils}
mkdir -p tests/{test_joern,test_services,test_tools,fixtures/sample_projects}
mkdir -p scripts docs/api

# 2. 创建 __init__.py 文件
touch src/joern_mcp/__init__.py
touch src/joern_mcp/{joern,services,tools,resources,prompts,models,utils}/__init__.py
touch tests/__init__.py
```

**交付物**:
- ✅ 完整的目录结构
- ✅ 所有必要的 `__init__.py` 文件

**验收标准**:
```bash
# 能够导入包
python -c "import joern_mcp"  # 应该成功
```

**时间**: 2小时

---

#### 任务 1.2: 配置开发环境

**目标**: 设置开发工具和依赖管理

**步骤**:

1. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate
```

2. **安装依赖**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **配置开发工具**
```bash
# 配置 pre-commit
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
EOF

pre-commit install
```

4. **配置 pytest**
```bash
# pytest.ini 已在 pyproject.toml 中配置
pytest --version  # 验证安装
```

**交付物**:
- ✅ 虚拟环境
- ✅ 已安装所有依赖
- ✅ 配置好的开发工具

**验收标准**:
```bash
# 所有工具能正常运行
black --version
ruff --version
pytest --version
mypy --version
```

**时间**: 2小时

---

#### 任务 1.3: 实现配置管理

**目标**: 实现应用配置加载和管理

**文件**: `src/joern_mcp/config.py`

**代码**:
```python
"""应用配置管理"""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # Joern Server配置
    joern_server_host: str = Field(default="localhost", description="Joern服务器地址")
    joern_server_port: int = Field(default=8080, description="Joern服务器端口")
    joern_server_username: Optional[str] = Field(default=None, description="认证用户名")
    joern_server_password: Optional[str] = Field(default=None, description="认证密码")
    
    # Joern路径配置
    joern_home: Optional[Path] = Field(default=None, description="Joern安装路径")
    joern_workspace: Path = Field(
        default=Path.home() / ".joern_mcp" / "workspace",
        description="工作空间路径"
    )
    joern_cpg_cache: Path = Field(
        default=Path.home() / ".joern_mcp" / "cpg_cache",
        description="CPG缓存路径"
    )
    
    # MCP配置
    mcp_server_host: str = Field(default="localhost", description="MCP服务器地址")
    mcp_server_port: int = Field(default=3000, description="MCP服务器端口")
    
    # 性能配置
    max_concurrent_queries: int = Field(default=5, description="最大并发查询数")
    query_timeout: int = Field(default=300, description="查询超时时间(秒)")
    query_cache_size: int = Field(default=1000, description="查询缓存大小")
    query_cache_ttl: int = Field(default=3600, description="缓存TTL(秒)")
    
    # 安全配置
    allowed_paths: List[Path] = Field(default_factory=list, description="允许访问的路径")
    enable_custom_queries: bool = Field(default=True, description="是否允许自定义查询")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file_path: Path = Field(
        default=Path.home() / ".joern_mcp" / "logs",
        description="日志文件路径"
    )
    log_file_size: int = Field(default=500, description="日志文件大小限制(MB)")
    log_retention_days: int = Field(default=10, description="日志保留天数")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
```

**测试**: `tests/test_config.py`
```python
import pytest
from joern_mcp.config import Settings


def test_default_settings():
    """测试默认配置"""
    settings = Settings()
    assert settings.joern_server_host == "localhost"
    assert settings.joern_server_port == 8080
    assert settings.max_concurrent_queries == 5


def test_custom_settings():
    """测试自定义配置"""
    settings = Settings(
        joern_server_port=8888,
        max_concurrent_queries=10
    )
    assert settings.joern_server_port == 8888
    assert settings.max_concurrent_queries == 10


def test_settings_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("JOERN_SERVER_PORT", "9000")
    settings = Settings()
    assert settings.joern_server_port == 9000
```

**验收标准**:
```bash
# 测试通过
pytest tests/test_config.py -v

# 能够加载配置
python -c "from joern_mcp.config import settings; print(settings.joern_server_host)"
```

**时间**: 3小时

---

#### 任务 1.4: 实现日志系统

**目标**: 配置和初始化日志系统

**文件**: `src/joern_mcp/utils/logger.py`

**代码**:
```python
"""日志配置"""
import sys
from pathlib import Path
from loguru import logger
from joern_mcp.config import settings


def setup_logging():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 确保日志目录存在
    settings.log_file_path.mkdir(parents=True, exist_ok=True)
    
    # 文件输出 - 所有日志
    logger.add(
        settings.log_file_path / "joern_mcp_{time}.log",
        rotation=f"{settings.log_file_size} MB",
        retention=f"{settings.log_retention_days} days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # 错误日志单独文件
    logger.add(
        settings.log_file_path / "error_{time}.log",
        rotation=f"{settings.log_file_size} MB",
        retention=f"{settings.log_retention_days} days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    logger.info("Logging system initialized")


# 自动初始化
setup_logging()
```

**测试**: `tests/test_utils/test_logger.py`
```python
import pytest
from loguru import logger
from joern_mcp.utils.logger import setup_logging


def test_logger_works():
    """测试日志功能"""
    setup_logging()
    
    # 这些应该不抛出异常
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")


def test_log_file_created(tmp_path, monkeypatch):
    """测试日志文件创建"""
    monkeypatch.setattr("joern_mcp.config.settings.log_file_path", tmp_path)
    setup_logging()
    
    logger.info("Test message")
    
    # 检查日志文件是否创建
    log_files = list(tmp_path.glob("*.log"))
    assert len(log_files) > 0
```

**验收标准**:
```bash
pytest tests/test_utils/test_logger.py -v

# 手动测试
python -c "from joern_mcp.utils.logger import logger; logger.info('Test')"
# 应该在控制台看到彩色日志
```

**时间**: 2小时

---

### Day 3-4: Joern Server集成

#### 任务 1.5: 实现 JoernManager

**目标**: Joern安装检测和版本管理

**文件**: `src/joern_mcp/joern/manager.py`

**代码**:
```python
"""Joern管理器"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from joern_mcp.config import settings


class JoernNotFoundError(Exception):
    """Joern未找到异常"""
    pass


class JoernManager:
    """Joern安装和版本管理"""
    
    def __init__(self):
        self.joern_path: Optional[Path] = None
        self.version: Optional[str] = None
        self._detect_joern()
    
    def _detect_joern(self) -> None:
        """检测Joern安装"""
        # 1. 检查配置的路径
        if settings.joern_home and (settings.joern_home / "joern").exists():
            self.joern_path = settings.joern_home / "joern"
            logger.info(f"Found Joern at configured path: {self.joern_path}")
            return
        
        # 2. 检查环境变量
        if joern_home := os.getenv("JOERN_HOME"):
            path = Path(joern_home) / "joern"
            if path.exists():
                self.joern_path = path
                logger.info(f"Found Joern from JOERN_HOME: {self.joern_path}")
                return
        
        # 3. 检查PATH
        if joern_path := shutil.which("joern"):
            self.joern_path = Path(joern_path)
            logger.info(f"Found Joern in PATH: {self.joern_path}")
            return
        
        # 4. 检查默认安装路径
        default_paths = [
            Path("/usr/local/bin/joern"),
            Path("/opt/joern/joern"),
            Path.home() / ".local/bin/joern",
        ]
        for path in default_paths:
            if path.exists():
                self.joern_path = path
                logger.info(f"Found Joern at default path: {self.joern_path}")
                return
        
        logger.error("Joern not found")
        raise JoernNotFoundError(
            "Joern not found. Please install Joern or set JOERN_HOME environment variable."
        )
    
    def get_version(self) -> str:
        """获取Joern版本"""
        if self.version:
            return self.version
        
        if not self.joern_path:
            raise JoernNotFoundError("Joern not found")
        
        try:
            result = subprocess.run(
                [str(self.joern_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析版本号
            output = result.stdout.strip()
            # 版本号通常在输出中，格式如 "Joern 2.0.1" 或 "2.0.1"
            version_line = output.split('\n')[0]
            # 提取版本号
            import re
            match = re.search(r'(\d+\.\d+\.\d+)', version_line)
            if match:
                self.version = match.group(1)
                logger.info(f"Joern version: {self.version}")
                return self.version
            
            logger.warning(f"Could not parse version from: {output}")
            return "unknown"
            
        except Exception as e:
            logger.error(f"Failed to get Joern version: {e}")
            return "unknown"
    
    def validate_installation(self) -> Dict[str, bool]:
        """验证Joern安装完整性"""
        result = {
            "joern_found": self.joern_path is not None,
            "joern_executable": False,
            "version_retrieved": False,
        }
        
        if not self.joern_path:
            return result
        
        # 检查可执行权限
        result["joern_executable"] = os.access(self.joern_path, os.X_OK)
        
        # 检查版本
        version = self.get_version()
        result["version_retrieved"] = version != "unknown"
        
        return result
    
    def ensure_directories(self) -> None:
        """确保必要的目录存在"""
        settings.joern_workspace.mkdir(parents=True, exist_ok=True)
        settings.joern_cpg_cache.mkdir(parents=True, exist_ok=True)
        logger.info("Joern directories created")
```

**测试**: `tests/test_joern/test_manager.py`
```python
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from joern_mcp.joern.manager import JoernManager, JoernNotFoundError


def test_detect_joern_from_path(monkeypatch):
    """测试从PATH检测Joern"""
    with patch('shutil.which', return_value='/usr/local/bin/joern'):
        manager = JoernManager()
        assert manager.joern_path == Path('/usr/local/bin/joern')


def test_detect_joern_not_found(monkeypatch):
    """测试Joern未找到"""
    with patch('shutil.which', return_value=None):
        monkeypatch.setattr('joern_mcp.config.settings.joern_home', None)
        monkeypatch.delenv('JOERN_HOME', raising=False)
        
        with pytest.raises(JoernNotFoundError):
            JoernManager()


@pytest.mark.skipif(not shutil.which('joern'), reason="Joern not installed")
def test_get_version_real():
    """测试获取真实Joern版本"""
    manager = JoernManager()
    version = manager.get_version()
    assert version != "unknown"
    assert len(version.split('.')) == 3  # x.y.z格式


def test_validate_installation():
    """测试安装验证"""
    with patch('shutil.which', return_value='/usr/local/bin/joern'):
        manager = JoernManager()
        result = manager.validate_installation()
        assert "joern_found" in result
        assert result["joern_found"] is True
```

**验收标准**:
```bash
# 测试通过
pytest tests/test_joern/test_manager.py -v

# 手动测试
python -c "from joern_mcp.joern.manager import JoernManager; m = JoernManager(); print(m.get_version())"
```

**时间**: 4小时

---

#### 任务 1.6: 实现 JoernServerManager

**目标**: Joern Server启动、停止和管理

**文件**: `src/joern_mcp/joern/server.py`

**代码**:
```python
"""Joern Server管理"""
import asyncio
from typing import Optional, Tuple, Dict
import httpx
from loguru import logger
from cpgqls_client import CPGQLSClient, import_code_query
from joern_mcp.config import settings
from joern_mcp.joern.manager import JoernManager


class JoernServerError(Exception):
    """Joern Server错误"""
    pass


class JoernServerManager:
    """Joern Server生命周期管理"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        joern_manager: Optional[JoernManager] = None
    ):
        self.host = host or settings.joern_server_host
        self.port = port or settings.joern_server_port
        self.endpoint = f"{self.host}:{self.port}"
        self.joern_manager = joern_manager or JoernManager()
        
        self.process: Optional[asyncio.subprocess.Process] = None
        self.client: Optional[CPGQLSClient] = None
        self.auth_credentials: Optional[Tuple[str, str]] = None
    
    async def start(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ) -> None:
        """启动Joern Server"""
        if self.process:
            logger.warning("Joern server already running")
            return
        
        logger.info(f"Starting Joern server at {self.endpoint}")
        
        # 构建命令
        cmd = [
            str(self.joern_manager.joern_path),
            "--server",
            "--server-host", self.host,
            "--server-port", str(self.port)
        ]
        
        # 添加认证
        username = username or settings.joern_server_username
        password = password or settings.joern_server_password
        
        if username and password:
            cmd.extend([
                "--server-auth-username", username,
                "--server-auth-password", password
            ])
            self.auth_credentials = (username, password)
            logger.info("Authentication enabled")
        
        # 启动进程
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Joern server process started (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start Joern server: {e}")
            raise JoernServerError(f"Failed to start server: {e}")
        
        # 等待服务器就绪
        try:
            await self._wait_for_ready(timeout)
            logger.info("Joern server is ready")
        except TimeoutError as e:
            await self.stop()
            raise e
        
        # 初始化客户端
        self.client = CPGQLSClient(
            self.endpoint,
            auth_credentials=self.auth_credentials
        )
        logger.info("Joern client initialized")
    
    async def _wait_for_ready(self, timeout: int = 30) -> None:
        """等待服务器就绪"""
        logger.info(f"Waiting for server to be ready (timeout: {timeout}s)")
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"http://{self.endpoint}/",
                        timeout=2.0
                    )
                    # 服务器返回任何响应都表示已启动
                    if response.status_code in [200, 404]:
                        return
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                except Exception as e:
                    logger.debug(f"Waiting for server: {e}")
                
                # 检查超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Joern server failed to start within {timeout}s")
                
                # 检查进程是否已退出
                if self.process.returncode is not None:
                    stderr = await self.process.stderr.read()
                    raise JoernServerError(f"Server process exited: {stderr.decode()}")
                
                await asyncio.sleep(0.5)
    
    async def stop(self) -> None:
        """停止Joern Server"""
        if not self.process:
            logger.warning("Joern server not running")
            return
        
        logger.info("Stopping Joern server")
        
        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=10)
            logger.info("Joern server stopped gracefully")
        except asyncio.TimeoutError:
            logger.warning("Server did not stop gracefully, killing...")
            self.process.kill()
            await self.process.wait()
            logger.info("Joern server killed")
        finally:
            self.process = None
            self.client = None
    
    async def restart(self) -> None:
        """重启Joern Server"""
        logger.info("Restarting Joern server")
        await self.stop()
        await self.start()
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.client:
            return False
        
        try:
            result = self.client.execute("1 + 1")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def execute_query(self, query: str) -> Dict:
        """执行查询（同步）"""
        if not self.client:
            raise JoernServerError("Server not started")
        
        logger.debug(f"Executing query: {query[:100]}...")
        try:
            result = self.client.execute(query)
            logger.debug(f"Query completed: success={result.get('success')}")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise JoernServerError(f"Query failed: {e}")
    
    async def import_code(
        self,
        source_path: str,
        project_name: str
    ) -> Dict:
        """导入代码生成CPG"""
        logger.info(f"Importing code from {source_path} as {project_name}")
        query = import_code_query(source_path, project_name)
        result = self.execute_query(query)
        
        if result.get("success"):
            logger.info(f"Code imported successfully: {project_name}")
        else:
            logger.error(f"Code import failed: {result.get('stderr')}")
        
        return result
```

**测试**: `tests/test_joern/test_server.py`
```python
import pytest
import asyncio
from joern_mcp.joern.server import JoernServerManager


@pytest.mark.asyncio
@pytest.mark.skipif(not shutil.which('joern'), reason="Joern not installed")
async def test_server_start_stop():
    """测试服务器启动和停止"""
    manager = JoernServerManager()
    
    # 启动
    await manager.start()
    assert manager.process is not None
    assert manager.client is not None
    
    # 健康检查
    is_healthy = await manager.health_check()
    assert is_healthy is True
    
    # 停止
    await manager.stop()
    assert manager.process is None


@pytest.mark.asyncio
async def test_server_timeout(monkeypatch):
    """测试启动超时"""
    # Mock一个永远不会ready的服务器
    async def mock_wait(*args, **kwargs):
        await asyncio.sleep(100)
    
    manager = JoernServerManager()
    monkeypatch.setattr(manager, '_wait_for_ready', mock_wait)
    
    with pytest.raises(asyncio.TimeoutError):
        await manager.start(timeout=1)
```

**验收标准**:
```bash
pytest tests/test_joern/test_server.py -v

# 手动测试
python -c "
import asyncio
from joern_mcp.joern.server import JoernServerManager

async def test():
    m = JoernServerManager()
    await m.start()
    print('Server started')
    result = m.execute_query('1+1')
    print('Query result:', result)
    await m.stop()
    print('Server stopped')

asyncio.run(test())
"
```

**时间**: 6小时

---

### Day 5: 查询执行器

#### 任务 1.7: 实现 QueryExecutor

**目标**: 查询执行、缓存和验证

**文件**: `src/joern_mcp/joern/executor.py`

**代码**:
```python
"""查询执行器"""
import hashlib
import asyncio
from typing import Dict, Optional, Tuple
from cachetools import TTLCache
from loguru import logger
from joern_mcp.config import settings
from joern_mcp.joern.server import JoernServerManager


class QueryExecutionError(Exception):
    """查询执行错误"""
    pass


class QueryValidationError(Exception):
    """查询验证错误"""
    pass


class QueryExecutor:
    """查询执行引擎"""
    
    def __init__(self, server_manager: JoernServerManager):
        self.server_manager = server_manager
        self.cache = TTLCache(
            maxsize=settings.query_cache_size,
            ttl=settings.query_cache_ttl
        )
        self.query_semaphore = asyncio.Semaphore(settings.max_concurrent_queries)
        
        # 禁止的查询模式
        self.forbidden_patterns = [
            r"System\.exit",
            r"Runtime\.getRuntime",
            r"ProcessBuilder",
            r"File\.delete",
            r"Files\.delete",
            r"scala\.sys\.process",
        ]
    
    async def execute(
        self,
        query: str,
        format: str = "json",
        timeout: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        执行查询
        
        Args:
            query: Scala查询语句
            format: 输出格式 (json, dot等)
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存
            
        Returns:
            查询结果字典
        """
        # 1. 验证查询
        is_valid, error_msg = self._validate_query(query)
        if not is_valid:
            logger.warning(f"Query validation failed: {error_msg}")
            raise QueryValidationError(error_msg)
        
        # 2. 确保查询返回正确格式
        query = self._format_query(query, format)
        
        # 3. 检查缓存
        cache_key = self._get_cache_key(query)
        if use_cache and cache_key in self.cache:
            logger.debug("Cache hit")
            return self.cache[cache_key]
        
        # 4. 执行查询（并发控制）
        async with self.query_semaphore:
            try:
                timeout = timeout or settings.query_timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.server_manager.execute_query, query),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Query timeout after {timeout}s")
                raise QueryExecutionError(f"Query timeout after {timeout}s")
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise QueryExecutionError(str(e))
        
        # 5. 处理结果
        if not result.get("success"):
            stderr = result.get("stderr", "Unknown error")
            logger.error(f"Query failed: {stderr}")
            raise QueryExecutionError(stderr)
        
        # 6. 缓存结果
        if use_cache:
            self.cache[cache_key] = result
        
        logger.debug("Query completed successfully")
        return result
    
    def _validate_query(self, query: str) -> Tuple[bool, str]:
        """验证查询安全性"""
        # 检查长度
        if len(query) > 10000:
            return False, "Query too long (max 10000 characters)"
        
        # 检查禁止的模式
        import re
        for pattern in self.forbidden_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Forbidden operation: {pattern}"
        
        return True, ""
    
    def _format_query(self, query: str, format: str) -> str:
        """格式化查询以返回指定格式"""
        query = query.strip()
        
        if format == "json":
            if not query.endswith(".toJson"):
                # 如果查询是一个语句块，需要用括号包裹
                if '\n' in query or query.count(';') > 0:
                    query = f"({query}).toJson"
                else:
                    query = f"{query}.toJson"
        elif format == "dot":
            if not query.endswith(".toDot"):
                query = f"{query}.toDot"
        
        return query
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("Query cache cleared")
```

**测试**: `tests/test_joern/test_executor.py`
```python
import pytest
from joern_mcp.joern.executor import QueryExecutor, QueryValidationError


@pytest.mark.asyncio
async def test_query_validation():
    """测试查询验证"""
    executor = QueryExecutor(None)
    
    # 合法查询
    is_valid, _ = executor._validate_query("cpg.method.name.l")
    assert is_valid
    
    # 非法查询 - System.exit
    is_valid, msg = executor._validate_query("System.exit(0)")
    assert not is_valid
    assert "System.exit" in msg
    
    # 非法查询 - 太长
    is_valid, msg = executor._validate_query("a" * 10001)
    assert not is_valid
    assert "too long" in msg


@pytest.mark.asyncio
async def test_query_format():
    """测试查询格式化"""
    executor = QueryExecutor(None)
    
    # JSON格式
    formatted = executor._format_query("cpg.method.name.l", "json")
    assert formatted.endswith(".toJson")
    
    # 已经有.toJson
    formatted = executor._format_query("cpg.method.name.l.toJson", "json")
    assert formatted.count(".toJson") == 1


@pytest.mark.asyncio
async def test_cache():
    """测试缓存"""
    # 使用mock server
    from unittest.mock import MagicMock, AsyncMock
    
    mock_server = MagicMock()
    mock_server.execute_query.return_value = {
        "success": True,
        "stdout": "[\"main\"]"
    }
    
    executor = QueryExecutor(mock_server)
    
    # 第一次执行
    result1 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query.call_count == 1
    
    # 第二次应该从缓存读取
    result2 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query.call_count == 1  # 仍然是1
    
    assert result1 == result2
```

**验收标准**:
```bash
pytest tests/test_joern/test_executor.py -v
```

**时间**: 4小时

---

## 第一周总结

**已完成**:
- ✅ 项目结构搭建
- ✅ 开发环境配置
- ✅ 配置管理系统
- ✅ 日志系统
- ✅ Joern检测和管理
- ✅ Joern Server启动和管理
- ✅ 查询执行器

**交付物**:
- 完整的项目骨架
- 可运行的Joern Server管理
- 查询执行基础设施

**验收测试**:
```bash
# 运行所有测试
pytest tests/ -v

# 集成测试
python -c "
import asyncio
from joern_mcp.joern.server import JoernServerManager
from joern_mcp.joern.executor import QueryExecutor

async def test():
    # 启动服务器
    server = JoernServerManager()
    await server.start()
    
    # 创建执行器
    executor = QueryExecutor(server)
    
    # 执行查询
    result = await executor.execute('cpg.method.name.take(5).l')
    print('Query result:', result)
    
    # 停止服务器
    await server.stop()
    print('Integration test passed!')

asyncio.run(test())
"
```

---

## 下一步预告

**第二周**: MCP Tools实现
- 项目管理工具
- 代码查询工具
- 基础MCP服务器

---

**继续阅读**: 
- 第二周计划将在下一部分详细说明
- 建议先完成第一周任务并通过所有测试

**文档版本**: v1.0  
**最后更新**: 2025-11-26

