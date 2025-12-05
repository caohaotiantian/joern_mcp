"""
共享测试fixtures和utilities
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# 全局 mock for get_safe_cpg_prefix
async def mock_get_safe_cpg_prefix(executor, project_name):
    """返回简单的 cpg 前缀，跳过项目验证"""
    return "cpg", None


@pytest.fixture
def mock_project_validation():
    """Mock 所有服务的 get_safe_cpg_prefix

    注意：此 fixture 不再是 autouse，需要在测试中显式使用。
    单元测试目录会自动使用此 fixture（见下方的 autouse fixture）。
    集成测试和 e2e 测试不会自动使用此 fixture。
    """
    with patch("joern_mcp.services.callgraph.get_safe_cpg_prefix", mock_get_safe_cpg_prefix), \
         patch("joern_mcp.services.dataflow.get_safe_cpg_prefix", mock_get_safe_cpg_prefix), \
         patch("joern_mcp.services.taint.get_safe_cpg_prefix", mock_get_safe_cpg_prefix):
        yield


@pytest.fixture(autouse=True)
def auto_mock_for_unit_tests(request, mock_project_validation):
    """
    仅对单元测试自动应用 mock_project_validation。
    集成测试和 e2e 测试不会自动 mock。
    """
    # 检查测试文件路径，只对单元测试目录自动 mock
    test_path = str(request.fspath)
    unit_test_dirs = [
        "test_services",
        "test_tools",
        "test_joern",
        "test_utils",
        "test_prompts",
    ]

    # 如果是单元测试目录，使用 mock
    if any(d in test_path for d in unit_test_dirs):
        # mock 已经在 mock_project_validation fixture 中应用了
        yield
    else:
        # 集成测试和 e2e 测试不 mock
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
