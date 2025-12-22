"""测试数据流分析服务"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from joern_mcp.services.dataflow import DataFlowService


@pytest.mark.asyncio
async def test_track_dataflow():
    """测试追踪数据流"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "source": {"code": "gets(buf)", "method": "main", "file": "main.c", "line": 10},
            "sink": {"code": "system(cmd)", "method": "exec", "file": "utils.c", "line": 20},
            "pathLength": 5,
            "path": []
        }]""",
        }
    )

    service = DataFlowService(mock_executor)
    result = await service.track_dataflow("gets", "system", project_name="test")

    assert result["success"] is True
    assert result["source_method"] == "gets"
    assert result["sink_method"] == "system"
    assert len(result["flows"]) >= 1


@pytest.mark.asyncio
async def test_analyze_variable_flow():
    """测试分析变量流"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "variable": "user_input",
            "source": {"code": "user_input", "file": "main.c", "line": 5},
            "sink": {"code": "system(user_input)", "method": "system", "file": "main.c", "line": 10},
            "pathLength": 3
        }]""",
        }
    )

    service = DataFlowService(mock_executor)
    result = await service.analyze_variable_flow(
        "user_input", "system", project_name="test"
    )

    assert result["success"] is True
    assert result["variable"] == "user_input"
    assert result["sink_method"] == "system"
    assert len(result["flows"]) >= 1


@pytest.mark.asyncio
async def test_analyze_variable_flow_no_sink():
    """测试分析变量流（无特定汇）"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "variable": "buf",
            "code": "buf",
            "type": "char[]",
            "method": "main",
            "file": "main.c",
            "line": 10
        }]""",
        }
    )

    service = DataFlowService(mock_executor)
    result = await service.analyze_variable_flow("buf", project_name="test")

    assert result["success"] is True
    assert result["variable"] == "buf"
    assert result["sink_method"] is None
    assert len(result["flows"]) >= 1


@pytest.mark.asyncio
async def test_find_data_dependencies():
    """测试查找数据依赖"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "variable": "x",
            "code": "x",
            "type": "int",
            "file": "main.c",
            "line": 5
        }, {
            "variable": "y",
            "code": "y",
            "type": "int",
            "file": "main.c",
            "line": 6
        }]""",
        }
    )

    service = DataFlowService(mock_executor)
    result = await service.find_data_dependencies("compute", project_name="test")

    assert result["success"] is True
    assert result["function"] == "compute"
    assert len(result["dependencies"]) >= 2


@pytest.mark.asyncio
async def test_find_data_dependencies_specific_variable():
    """测试查找特定变量的依赖"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": """[{
            "variable": "buf",
            "code": "buf",
            "method": "main",
            "file": "main.c",
            "line": 10,
            "type": "char[]"
        }]""",
        }
    )

    service = DataFlowService(mock_executor)
    result = await service.find_data_dependencies("main", "buf", project_name="test")

    assert result["success"] is True
    assert result["function"] == "main"
    assert result["variable"] == "buf"
    assert len(result["dependencies"]) >= 1


@pytest.mark.asyncio
async def test_track_dataflow_no_results():
    """测试无数据流结果"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={"success": True, "stdout": "[]"})

    service = DataFlowService(mock_executor)
    result = await service.track_dataflow("source", "sink", project_name="test")

    assert result["success"] is True
    assert result["count"] == 0
    assert len(result["flows"]) == 0


@pytest.mark.asyncio
async def test_track_dataflow_query_failed():
    """测试查询失败"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={"success": False, "stderr": "Query error"}
    )

    service = DataFlowService(mock_executor)
    result = await service.track_dataflow("source", "sink", project_name="test")

    assert result["success"] is False
    assert "error" in result
