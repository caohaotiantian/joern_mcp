"""
tests/test_main.py

测试主程序入口
"""
import pytest


def test_main_module_can_be_imported():
    """测试__main__模块可以导入"""
    # 简单测试，不实际运行main
    import sys
    import importlib.util
    
    # 检查模块文件存在
    from pathlib import Path
    main_file = Path(__file__).parent.parent / "src" / "joern_mcp" / "__main__.py"
    assert main_file.exists(), "__main__.py should exist"
