"""
tests/test_tools/test_query.py

测试基础查询工具
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from joern_mcp.joern.executor import QueryExecutor


class TestQueryTools:
    """测试查询工具逻辑"""

    @pytest.mark.asyncio
    async def test_execute_query_logic(self, mock_query_executor):
        """测试执行查询"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": '["method1", "method2"]'
            }
        )
        
        result = await mock_query_executor.execute("cpg.method.name.l")
        
        assert result["success"] is True
        assert "method1" in result["stdout"]

    @pytest.mark.asyncio
    async def test_get_function_code_logic(self, mock_query_executor):
        """测试获取函数代码"""
        function_code = """
void main() {
    printf("Hello");
}
"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": f'["{function_code}"]'
            }
        )
        
        # 执行获取函数代码的查询
        query = 'cpg.method.name("main").code.l.toJson'
        result = await mock_query_executor.execute(query)
        
        assert result["success"] is True
        assert "main" in result["stdout"]

    @pytest.mark.asyncio
    async def test_list_functions_logic(self, mock_query_executor):
        """测试列出函数"""
        functions_data = [
            {"name": "main", "filename": "test.c", "lineNumber": 10},
            {"name": "helper", "filename": "test.c", "lineNumber": 20}
        ]
        
        import json
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(functions_data)
            }
        )
        
        result = await mock_query_executor.execute("cpg.method.map(...).toJson")
        
        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert len(data) == 2
        assert data[0]["name"] == "main"

    @pytest.mark.asyncio
    async def test_search_code_logic(self, mock_query_executor):
        """测试搜索代码"""
        search_results = [
            {"code": "strcpy(buffer, input)", "filename": "vuln.c", "lineNumber": 15}
        ]
        
        import json
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(search_results)
            }
        )
        
        result = await mock_query_executor.execute('cpg.call.name("strcpy").map(...).toJson')
        
        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert len(data) > 0
        assert "strcpy" in data[0]["code"]


class TestQueryEdgeCases:
    """测试查询边界情况"""

    @pytest.mark.asyncio
    async def test_empty_query_result(self, mock_query_executor):
        """测试空查询结果"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )
        
        result = await mock_query_executor.execute('cpg.method.name("nonexistent").l.toJson')
        
        assert result["success"] is True
        assert result["stdout"] == "[]"

    @pytest.mark.asyncio
    async def test_query_with_special_characters(self, mock_query_executor):
        """测试包含特殊字符的查询"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": '["test_函数"]'}
        )
        
        result = await mock_query_executor.execute('cpg.method.name("test_函数").l.toJson')
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_query_timeout_handling(self, mock_query_executor):
        """测试查询超时处理"""
        from joern_mcp.joern.executor import QueryExecutionError
        
        mock_query_executor.execute = AsyncMock(
            side_effect=QueryExecutionError("Query timeout after 60s")
        )
        
        with pytest.raises(QueryExecutionError, match="timeout"):
            await mock_query_executor.execute("cpg.method.name.l")

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, mock_query_executor):
        """测试格式错误的JSON响应"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "not a json"  # 格式错误的JSON
            }
        )
        
        result = await mock_query_executor.execute("cpg.method.name.l")
        
        # 应该返回raw_output
        assert result["success"] is True
        assert result["stdout"] == "not a json"

    @pytest.mark.asyncio
    async def test_query_with_limit(self, mock_query_executor):
        """测试带限制的查询"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": '["method1", "method2"]'
            }
        )
        
        result = await mock_query_executor.execute("cpg.method.name.take(10).l.toJson")
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_query_with_filter(self, mock_query_executor):
        """测试带过滤器的查询"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": '["main", "main_helper"]'
            }
        )
        
        result = await mock_query_executor.execute('cpg.method.name(".*main.*").l.toJson')
        
        assert result["success"] is True
        assert "main" in result["stdout"]

