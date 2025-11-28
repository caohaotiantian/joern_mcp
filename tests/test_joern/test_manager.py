"""测试Joern管理器"""

import pytest
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
from joern_mcp.joern.manager import JoernManager, JoernNotFoundError


def test_detect_joern_from_path():
    """测试从PATH检测Joern"""
    with patch("shutil.which", return_value="/usr/local/bin/joern"):
        with patch.object(Path, "exists", return_value=True):
            manager = JoernManager()
            assert manager.joern_path is not None


def test_detect_joern_not_found(monkeypatch):
    """测试Joern未找到"""
    with patch("shutil.which", return_value=None):
        monkeypatch.setattr("joern_mcp.config.settings.joern_home", None)
        monkeypatch.delenv("JOERN_HOME", raising=False)

        with pytest.raises(JoernNotFoundError):
            JoernManager()


@pytest.mark.skipif(not shutil.which("joern"), reason="Joern not installed")
def test_get_version_real():
    """测试获取真实Joern版本"""
    manager = JoernManager()
    version = manager.get_version()
    assert version != "unknown"
    # 版本号格式应该是 x.y.z
    version_parts = version.split(".")
    assert len(version_parts) >= 2


def test_validate_installation(mock_joern_manager):
    """测试安装验证"""
    result = mock_joern_manager.validate_installation()
    assert "joern_found" in result
    assert result["joern_found"] is True


def test_ensure_directories(tmp_path, monkeypatch):
    """测试创建必要目录"""
    from joern_mcp import config

    workspace = tmp_path / "workspace"
    cpg_cache = tmp_path / "cpg_cache"

    monkeypatch.setattr(config.settings, "joern_workspace", workspace)
    monkeypatch.setattr(config.settings, "joern_cpg_cache", cpg_cache)

    with patch("shutil.which", return_value="/usr/local/bin/joern"):
        with patch.object(Path, "exists", return_value=True):
            manager = JoernManager()
            manager.ensure_directories()

    assert workspace.exists()
    assert cpg_cache.exists()
