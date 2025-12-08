"""测试调用图分析服务"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from joern_mcp.services.callgraph import CallGraphService


@pytest.mark.asyncio
async def test_get_callers():
    """测试获取调用者

    注意：使用 .callIn 获取调用节点，而非 .caller 获取方法定义。
    .callIn 返回调用点信息，包含文件名、行号、代码等。
    """
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": '[{"name": "main", "methodFullName": "main", "filename": "main.c", "lineNumber": 10, "signature": "int()", "code": "vulnerable_func()"}]',
        }
    )

    service = CallGraphService(mock_executor)
    result = await service.get_callers("vulnerable_func", depth=1, project_name="test")

    # 验证返回结果
    assert result["success"] is True
    assert result["function"] == "vulnerable_func"
    assert result["depth"] == 1
    assert len(result["callers"]) >= 1
    assert result["callers"][0]["name"] == "main"

    # 验证Mock被正确调用
    mock_executor.execute.assert_called_once()

    # 验证查询参数 - 使用 .callIn 而非 .caller
    call_args = mock_executor.execute.call_args[0][0]
    assert isinstance(call_args, str), "查询应该是字符串"
    assert "vulnerable_func" in call_args, "查询应该包含函数名"
    assert ".callIn" in call_args, "查询应该使用 .callIn 获取调用节点"


@pytest.mark.asyncio
async def test_get_callees():
    """测试获取被调用者

    注意：使用 .call 获取调用节点，而非 .callee 获取方法定义。
    .call 返回调用点信息，包含文件名、行号、代码等。
    """
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": '[{"name": "strcpy", "methodFullName": "strcpy", "filename": "main.c", "lineNumber": 20, "signature": "char*()", "code": "strcpy(buf, input)"}]',
        }
    )

    service = CallGraphService(mock_executor)
    result = await service.get_callees("main", depth=1, project_name="test")

    # 验证返回结果
    assert result["success"] is True
    assert result["function"] == "main"
    assert result["depth"] == 1
    assert len(result["callees"]) >= 1
    assert result["callees"][0]["name"] == "strcpy"

    # 验证Mock被正确调用
    mock_executor.execute.assert_called_once()

    # 验证查询参数 - 使用 .call 而非 .callee
    call_args = mock_executor.execute.call_args[0][0]
    assert isinstance(call_args, str), "查询应该是字符串"
    assert "main" in call_args, "查询应该包含函数名"
    assert ".call" in call_args, "查询应该使用 .call 获取调用节点"


@pytest.mark.asyncio
async def test_get_call_chain():
    """测试获取调用链"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": '[{"name": "func1", "filename": "main.c"}, {"name": "func2", "filename": "main.c"}]',
        }
    )

    service = CallGraphService(mock_executor)
    result = await service.get_call_chain("target_func", max_depth=5, direction="up", project_name="test")

    assert result["success"] is True
    assert result["function"] == "target_func"
    assert result["direction"] == "up"
    assert len(result["chain"]) >= 1


@pytest.mark.asyncio
async def test_get_call_graph():
    """测试获取调用图"""
    mock_executor = MagicMock()

    # Mock多次调用
    call_count = 0

    async def mock_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # callers
            return {
                "success": True,
                "stdout": '[{"name": "caller1", "filename": "main.c", "lineNumber": 10, "signature": "int()"}]',
            }
        else:
            # callees
            return {
                "success": True,
                "stdout": '[{"name": "callee1", "filename": "utils.c", "lineNumber": 20, "signature": "void()"}]',
            }

    mock_executor.execute = mock_execute

    service = CallGraphService(mock_executor)
    result = await service.get_call_graph("main", depth=2, project_name="test")

    assert result["success"] is True
    assert result["function"] == "main"
    assert "nodes" in result
    assert "edges" in result
    assert result["node_count"] >= 1


@pytest.mark.asyncio
async def test_get_callers_query_failed():
    """测试查询失败"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={"success": False, "stderr": "Query error"}
    )

    service = CallGraphService(mock_executor)
    result = await service.get_callers("nonexistent", project_name="test")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_get_callers_with_depth():
    """测试多层调用者"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "success": True,
            "stdout": '[{"name": "func1", "signature": "int()", "filename": "a.c", "lineNumber": 1}, {"name": "func2", "signature": "void()", "filename": "b.c", "lineNumber": 2}]',
        }
    )

    service = CallGraphService(mock_executor)
    result = await service.get_callers("target", depth=3, project_name="test")

    assert result["success"] is True
    assert result["depth"] == 3
    assert result["count"] == 2
