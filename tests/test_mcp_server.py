"""
tests/test_mcp_server.py

测试MCP服务器模块
"""
import pytest


def test_mcp_server_module_exists():
    """测试MCP服务器模块存在"""
    from pathlib import Path
    mcp_server_file = Path(__file__).parent.parent / "src" / "joern_mcp" / "mcp_server.py"
    assert mcp_server_file.exists()


def test_server_state_class_definition():
    """测试ServerState类定义存在"""
    # 读取文件内容检查
    from pathlib import Path
    mcp_server_file = Path(__file__).parent.parent / "src" / "joern_mcp" / "mcp_server.py"
    content = mcp_server_file.read_text()
    assert "ServerState" in content or "server_state" in content
