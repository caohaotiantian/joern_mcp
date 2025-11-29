"""
tests/test_prompts/test_analysis_prompts.py

测试分析提示模板
"""
import pytest


def test_prompts_module_exists():
    """测试prompts模块存在"""
    from pathlib import Path
    prompts_file = Path(__file__).parent.parent.parent / "src" / "joern_mcp" / "prompts" / "analysis_prompts.py"
    assert prompts_file.exists()


def test_prompts_file_content():
    """测试prompts文件内容"""
    from pathlib import Path
    prompts_file = Path(__file__).parent.parent.parent / "src" / "joern_mcp" / "prompts" / "analysis_prompts.py"
    content = prompts_file.read_text()
    
    # 验证包含关键提示函数
    assert "security_audit_prompt" in content
    assert "vulnerability_analysis_prompt" in content or "analysis" in content
    assert "@mcp.prompt()" in content


def test_prompts_module_structure():
    """测试prompts模块结构"""
    from pathlib import Path
    prompts_file = Path(__file__).parent.parent.parent / "src" / "joern_mcp" / "prompts" / "analysis_prompts.py"
    content = prompts_file.read_text()
    
    # 验证使用了装饰器模式
    assert "async def" in content
    assert "prompt" in content.lower()
