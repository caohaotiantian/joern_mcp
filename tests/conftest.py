"""
共享测试fixtures和utilities
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_joern_server():
    """Mock Joern Server Manager"""
    server = MagicMock()
    server.execute_query.return_value = {"success": True, "stdout": '[]'}
    server.execute_query_async = AsyncMock(return_value={"success": True, "stdout": '[]'})
    server.is_running.return_value = True
    return server


@pytest.fixture
def mock_query_executor(mock_joern_server):
    """Mock Query Executor"""
    from joern_mcp.joern.executor import QueryExecutor
    
    executor = QueryExecutor(mock_joern_server)
    return executor


@pytest.fixture
def sample_query_result():
    """示例查询结果"""
    return {
        "success": True,
        "stdout": '[{"name": "main", "filename": "test.c", "lineNumber": 10}]'
    }


@pytest.fixture
def sample_function_code():
    """示例函数代码"""
    return """
void main() {
    printf("Hello, World!");
}
"""
