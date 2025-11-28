"""Pytest配置和共享fixtures"""
import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """创建临时项目目录"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # 创建一个简单的C文件
    (project_dir / "main.c").write_text(
        "int main() { return 0; }"
    )
    
    return project_dir


@pytest.fixture
def mock_joern_manager():
    """Mock JoernManager"""
    manager = MagicMock()
    manager.joern_path = Path("/usr/local/bin/joern")
    manager.get_version.return_value = "2.0.1"
    manager.validate_installation.return_value = {
        "joern_found": True,
        "joern_executable": True,
        "version_retrieved": True,
    }
    return manager


@pytest.fixture
def mock_joern_server():
    """Mock JoernServerManager"""
    server = MagicMock()
    server.endpoint = "localhost:8080"
    server.execute_query.return_value = {
        "success": True,
        "stdout": '["result"]',
        "stderr": ""
    }
    return server


@pytest.fixture
async def mock_async_server():
    """Mock async JoernServerManager"""
    server = MagicMock()
    server.start = AsyncMock()
    server.stop = AsyncMock()
    server.health_check = AsyncMock(return_value=True)
    server.execute_query.return_value = {
        "success": True,
        "stdout": '["result"]'
    }
    return server

