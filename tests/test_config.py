"""测试配置管理"""
import pytest
from pathlib import Path
from joern_mcp.config import Settings


def test_default_settings():
    """测试默认配置"""
    settings = Settings()
    assert settings.joern_server_host == "localhost"
    assert settings.joern_server_port == 8080
    assert settings.max_concurrent_queries == 5
    assert settings.query_timeout == 300


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
    monkeypatch.setenv("MAX_CONCURRENT_QUERIES", "15")
    
    settings = Settings()
    assert settings.joern_server_port == 9000
    assert settings.max_concurrent_queries == 15


def test_path_settings():
    """测试路径配置"""
    settings = Settings()
    assert isinstance(settings.joern_workspace, Path)
    assert isinstance(settings.joern_cpg_cache, Path)
    assert isinstance(settings.log_file_path, Path)


def test_security_settings():
    """测试安全配置"""
    settings = Settings()
    assert isinstance(settings.allowed_paths, list)
    assert isinstance(settings.enable_custom_queries, bool)

