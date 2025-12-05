"""
共享测试fixtures和utilities
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# 全局 mock for get_safe_cpg_prefix
async def mock_get_safe_cpg_prefix(executor, project_name):
    """返回简单的 cpg 前缀，跳过项目验证"""
    return "cpg", None


@pytest.fixture(autouse=True)
def mock_project_validation():
    """自动 mock 所有服务的 get_safe_cpg_prefix"""
    with patch("joern_mcp.services.callgraph.get_safe_cpg_prefix", mock_get_safe_cpg_prefix), \
         patch("joern_mcp.services.dataflow.get_safe_cpg_prefix", mock_get_safe_cpg_prefix), \
         patch("joern_mcp.services.taint.get_safe_cpg_prefix", mock_get_safe_cpg_prefix):
        yield


@pytest.fixture
def mock_joern_server():
    """Mock Joern Server Manager"""
    server = MagicMock()
    server.execute_query.return_value = {"success": True, "stdout": "[]"}
    server.execute_query_async = AsyncMock(
        return_value={"success": True, "stdout": "[]"}
    )
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
        "stdout": '[{"name": "main", "filename": "test.c", "lineNumber": 10}]',
    }


@pytest.fixture
def sample_function_code():
    """示例函数代码"""
    return """
void main() {
    printf("Hello, World!");
}
"""
