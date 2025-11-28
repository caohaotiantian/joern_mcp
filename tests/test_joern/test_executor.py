"""测试查询执行器"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from joern_mcp.joern.executor import (
    QueryExecutor,
    QueryValidationError,
    QueryExecutionError,
)


@pytest.mark.asyncio
async def test_query_validation():
    """测试查询验证"""
    mock_server = MagicMock()
    executor = QueryExecutor(mock_server)

    # 合法查询
    is_valid, _ = executor._validate_query("cpg.method.name.l")
    assert is_valid

    # 非法查询 - System.exit
    is_valid, msg = executor._validate_query("System.exit(0)")
    assert not is_valid
    assert "System" in msg and "exit" in msg

    # 非法查询 - 太长
    is_valid, msg = executor._validate_query("a" * 10001)
    assert not is_valid
    assert "too long" in msg


@pytest.mark.asyncio
async def test_query_format():
    """测试查询格式化"""
    mock_server = MagicMock()
    executor = QueryExecutor(mock_server)

    # JSON格式
    formatted = executor._format_query("cpg.method.name.l", "json")
    assert formatted.endswith(".toJson")

    # 已经有.toJson
    formatted = executor._format_query("cpg.method.name.l.toJson", "json")
    assert formatted.count(".toJson") == 1

    # DOT格式
    formatted = executor._format_query("cpg.method.name.l", "dot")
    assert formatted.endswith(".toDot")


@pytest.mark.asyncio
async def test_cache():
    """测试缓存"""
    mock_server = MagicMock()
    mock_server.execute_query.return_value = {"success": True, "stdout": '["main"]'}

    executor = QueryExecutor(mock_server)

    # 第一次执行
    result1 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query.call_count == 1

    # 第二次应该从缓存读取
    result2 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query.call_count == 1  # 仍然是1

    assert result1 == result2


@pytest.mark.asyncio
async def test_query_execution_error():
    """测试查询执行错误"""
    mock_server = MagicMock()
    mock_server.execute_query.return_value = {"success": False, "stderr": "Query error"}

    executor = QueryExecutor(mock_server)

    with pytest.raises(QueryExecutionError):
        await executor.execute("invalid query")


@pytest.mark.asyncio
async def test_clear_cache():
    """测试清空缓存"""
    mock_server = MagicMock()
    mock_server.execute_query.return_value = {"success": True, "stdout": '["result"]'}

    executor = QueryExecutor(mock_server)

    # 执行查询填充缓存
    await executor.execute("cpg.method.name.l")
    assert len(executor.cache) > 0

    # 清空缓存
    executor.clear_cache()
    assert len(executor.cache) == 0
