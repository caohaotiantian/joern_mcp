"""测试查询模板"""

import pytest

from joern_mcp.joern.templates import QueryTemplates


def test_build_function_query():
    """测试构建函数查询"""
    query = QueryTemplates.build("GET_FUNCTION", name="main")
    assert 'cpg.method.name("main")' in query
    assert "Map(" in query


def test_build_callers_query():
    """测试构建调用者查询"""
    query = QueryTemplates.build("GET_CALLERS", name="vulnerable_func")
    assert "caller" in query
    assert 'name("vulnerable_func")' in query


def test_build_dataflow_query():
    """测试构建数据流查询"""
    query = QueryTemplates.build("DATAFLOW", source_name="gets", sink_name="system")
    assert "gets" in query
    assert "system" in query
    assert "reachableBy" in query


def test_build_taint_analysis():
    """测试构建污点分析查询"""
    query = QueryTemplates.build(
        "TAINT_ANALYSIS",
        source_pattern="get.*",
        sink_pattern="system|exec",
        severity="HIGH",
    )
    assert "get.*" in query
    assert "system|exec" in query
    assert "HIGH" in query


def test_invalid_template():
    """测试无效模板"""
    with pytest.raises(ValueError):
        QueryTemplates.build("NON_EXISTENT")


def test_list_templates():
    """测试列出所有模板"""
    templates = QueryTemplates.list_templates()
    assert len(templates) > 0
    assert "GET_FUNCTION" in templates
    assert "GET_CALLERS" in templates
    assert "DATAFLOW" in templates
    assert "TAINT_ANALYSIS" in templates


def test_search_calls_pattern():
    """测试搜索调用模式查询"""
    query = QueryTemplates.build("SEARCH_CALLS_BY_PATTERN", pattern="strcpy", limit=50)
    assert "strcpy" in query
    assert "take(50)" in query
    assert "CALL" in query


def test_search_identifiers_pattern():
    """测试搜索标识符模式查询"""
    query = QueryTemplates.build("SEARCH_IDENTIFIERS_BY_PATTERN", pattern="user", limit=25)
    assert "user" in query
    assert "take(25)" in query
    assert "IDENTIFIER" in query
