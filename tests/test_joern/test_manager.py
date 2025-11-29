"""测试Joern管理器"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from joern_mcp.joern.manager import JoernManager, JoernNotFoundError


def test_detect_joern_from_path():
    """测试从PATH检测Joern"""
    with (
        patch("shutil.which", return_value="/usr/local/bin/joern"),
        patch.object(Path, "exists", return_value=True),
    ):
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
    # 版本号格式可能是 x.y.z 或 HEAD+日期
    assert len(version) > 0
    # 验证版本号是合法格式（数字.数字.数字 或 HEAD+日期）
    import re

    assert re.match(r"(\d+\.\d+\.\d+)|(HEAD\+\d{8}-\d{4})", version)


def test_validate_installation():
    """测试安装验证"""
    manager = JoernManager()
    result = manager.validate_installation()
    assert "joern_found" in result
    # 如果Joern未安装，joern_found可能为False
    assert isinstance(result["joern_found"], bool)


def test_ensure_directories(tmp_path, monkeypatch):
    """测试创建必要目录"""
    from joern_mcp import config

    workspace = tmp_path / "workspace"
    cpg_cache = tmp_path / "cpg_cache"

    monkeypatch.setattr(config.settings, "joern_workspace", workspace)
    monkeypatch.setattr(config.settings, "joern_cpg_cache", cpg_cache)

    with (
        patch("shutil.which", return_value="/usr/local/bin/joern"),
        patch.object(Path, "exists", return_value=True),
    ):
        manager = JoernManager()
        manager.ensure_directories()

    assert workspace.exists()
    assert cpg_cache.exists()


def test_detect_joern_from_config(monkeypatch, tmp_path):
    """测试从配置检测Joern"""
    from joern_mcp import config

    joern_home = tmp_path / "joern"
    joern_home.mkdir()
    joern_bin = joern_home / "joern"
    joern_bin.touch()
    joern_bin.chmod(0o755)

    monkeypatch.setattr(config.settings, "joern_home", joern_home)

    with patch("shutil.which", return_value=None):
        manager = JoernManager()
        assert manager.joern_path is not None


def test_get_version_with_error():
    """测试获取版本出错时返回unknown"""
    with (
        patch("shutil.which", return_value="/usr/local/bin/joern"),
        patch.object(Path, "exists", return_value=True),
        patch("subprocess.run", side_effect=Exception("Test error")),
    ):
        manager = JoernManager()
        version = manager.get_version()
        assert version == "unknown"


def test_validate_installation_structure():
    """测试验证安装返回结构"""
    try:
        manager = JoernManager()
        result = manager.validate_installation()
        # 验证返回结构
        assert isinstance(result, dict)
        assert "joern_found" in result
        assert isinstance(result["joern_found"], bool)
    except JoernNotFoundError:
        # 如果Joern未安装，跳过测试
        pytest.skip("Joern not installed")
