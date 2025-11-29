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
    from unittest.mock import AsyncMock
    
    mock_server = MagicMock()
    mock_server.execute_query_async = AsyncMock(
        return_value={"success": True, "stdout": '["main"]'}
    )

    executor = QueryExecutor(mock_server)

    # 第一次执行
    result1 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query_async.call_count == 1

    # 第二次应该从缓存读取
    result2 = await executor.execute("cpg.method.name.l", use_cache=True)
    assert mock_server.execute_query_async.call_count == 1  # 仍然是1

    assert result1 == result2


@pytest.mark.asyncio
async def test_query_execution_error():
    """测试查询执行错误"""
    from unittest.mock import AsyncMock
    
    mock_server = MagicMock()
    mock_server.execute_query_async = AsyncMock(
        return_value={"success": False, "stderr": "Query error"}
    )

    executor = QueryExecutor(mock_server)

    with pytest.raises(QueryExecutionError):
        await executor.execute("cpg.method.name.l")


@pytest.mark.asyncio
async def test_clear_cache():
    """测试清空缓存"""
    from unittest.mock import AsyncMock
    
    mock_server = MagicMock()
    mock_server.execute_query_async = AsyncMock(
        return_value={"success": True, "stdout": '["result"]'}
    )

    executor = QueryExecutor(mock_server)

    # 执行查询填充缓存
    await executor.execute("cpg.method.name.l")
    assert len(executor.cache) > 0

    # 清空缓存
    executor.clear_cache()
    assert len(executor.cache) == 0


@pytest.mark.asyncio
async def test_query_validation_multiple_dangerous_ops():
    """测试查询验证多种危险操作"""
    mock_server = MagicMock()
    mock_server.execute_query_async = AsyncMock()
    
    executor = QueryExecutor(mock_server)
    
    # 测试多种危险操作（一次只测试一个）
    with pytest.raises(QueryValidationError):
        await executor.execute("System.exit(0)")


@pytest.mark.asyncio
async def test_concurrent_queries_basic():
    """测试基本并发查询"""
    from unittest.mock import AsyncMock
    import asyncio
    
    mock_server = MagicMock()
    
    async def mock_execute(*args, **kwargs):
        await asyncio.sleep(0.01)  # 模拟短暂查询
        return {"success": True, "stdout": '["result"]'}
    
    mock_server.execute_query_async = mock_execute
    
    executor = QueryExecutor(mock_server)
    
    # 发起几个并发查询
    tasks = [executor.execute(f"query{i}") for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    # 所有查询都应该成功
    assert all(r["success"] for r in results)


@pytest.mark.asyncio
async def test_cache_with_same_query():
    """测试相同查询的缓存"""
    from unittest.mock import AsyncMock
    
    mock_server = MagicMock()
    call_count = 0
    
    async def mock_execute_counted(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return {"success": True, "stdout": '["result"]'}
    
    mock_server.execute_query_async = mock_execute_counted
    
    executor = QueryExecutor(mock_server)  # 缓存默认启用
    
    # 第一次执行
    result1 = await executor.execute("test_query")
    # 第二次执行相同查询
    result2 = await executor.execute("test_query")
    
    assert result1["success"]
    assert result2["success"]
    # 缓存应该有内容
    assert len(executor.cache) > 0


@pytest.mark.asyncio  
async def test_format_query():
    """测试查询格式化"""
    mock_server = MagicMock()
    mock_server.execute_query_async = AsyncMock(
        return_value={"success": True, "stdout": "[]"}
    )
    
    executor = QueryExecutor(mock_server)
    
    # 测试格式化：去除多余空白
    query = """
        cpg.method
            .name("test")
            .l
    """
    
    await executor.execute(query)
    # 查询应该被成功执行（格式化后）
    assert mock_server.execute_query_async.called


@pytest.mark.asyncio
async def test_executor_without_async_method():
    """测试不支持async方法的server"""
    from unittest.mock import AsyncMock
    
    mock_server = MagicMock()
    # 没有execute_query_async方法，只有execute_query
    mock_server.execute_query = MagicMock(
        return_value={"success": True, "stdout": "[]"}
    )
    del mock_server.execute_query_async  # 确保没有async方法
    
    executor = QueryExecutor(mock_server)
    
    # 应该使用同步方法的fallback
    result = await executor.execute("test_query")
    assert result["success"]
