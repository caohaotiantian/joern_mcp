"""测试调用图分析服务"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from joern_mcp.services.callgraph import CallGraphService


@pytest.mark.asyncio
async def test_get_callers():
    """测试获取调用者"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "main", "filename": "main.c", "lineNumber": 10}]'
    })
    
    service = CallGraphService(mock_executor)
    result = await service.get_callers("vulnerable_func")
    
    assert result["success"] is True
    assert result["function"] == "vulnerable_func"
    assert len(result["callers"]) >= 1
    assert result["callers"][0]["name"] == "main"


@pytest.mark.asyncio
async def test_get_callees():
    """测试获取被调用者"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "strcpy", "filename": "string.h", "lineNumber": 20}]'
    })
    
    service = CallGraphService(mock_executor)
    result = await service.get_callees("main")
    
    assert result["success"] is True
    assert result["function"] == "main"
    assert len(result["callees"]) >= 1


@pytest.mark.asyncio
async def test_get_call_chain():
    """测试获取调用链"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "func1", "filename": "main.c"}, {"name": "func2", "filename": "main.c"}]'
    })
    
    service = CallGraphService(mock_executor)
    result = await service.get_call_chain("target_func", max_depth=5, direction="up")
    
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
                "stdout": '[{"name": "caller1", "filename": "main.c", "lineNumber": 10}]'
            }
        else:
            # callees
            return {
                "success": True,
                "stdout": '[{"name": "callee1", "filename": "utils.c", "lineNumber": 20}]'
            }
    
    mock_executor.execute = mock_execute
    
    service = CallGraphService(mock_executor)
    result = await service.get_call_graph("main", depth=2)
    
    assert result["success"] is True
    assert result["function"] == "main"
    assert "nodes" in result
    assert "edges" in result
    assert result["node_count"] >= 1


@pytest.mark.asyncio
async def test_get_callers_query_failed():
    """测试查询失败"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": False,
        "stderr": "Query error"
    })
    
    service = CallGraphService(mock_executor)
    result = await service.get_callers("nonexistent")
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_get_callers_with_depth():
    """测试多层调用者"""
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={
        "success": True,
        "stdout": '[{"name": "func1"}, {"name": "func2"}]'
    })
    
    service = CallGraphService(mock_executor)
    result = await service.get_callers("target", depth=3)
    
    assert result["success"] is True
    assert result["depth"] == 3
    assert result["count"] == 2

