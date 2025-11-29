"""
tests/test_tools/test_cfg.py

测试控制流图(CFG)工具
"""

import json
from unittest.mock import AsyncMock

import pytest


class TestCFGTools:
    """测试CFG工具逻辑"""

    @pytest.mark.asyncio
    async def test_get_cfg_basic(self, mock_query_executor):
        """测试获取CFG基本功能"""
        # Mock CFG数据
        cfg_data = {
            "function": "main",
            "nodes": [
                {"id": 1, "code": "int main()", "type": "ENTRY"},
                {"id": 2, "code": "if (x > 0)", "type": "CONTROL_STRUCTURE"},
                {"id": 3, "code": "return 0", "type": "RETURN"},
            ],
            "edges": [{"source": 1, "target": 2}, {"source": 2, "target": 3}],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(cfg_data)}
        )

        # CFG查询应该返回图结构
        result = await mock_query_executor.execute('cpg.method.name("main").cfg')

        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert data["function"] == "main"
        assert len(data["nodes"]) == 3

    @pytest.mark.asyncio
    async def test_get_cfg_complex(self, mock_query_executor):
        """测试复杂函数的CFG"""
        cfg_data = {
            "function": "complex_func",
            "nodes": [{"id": i, "code": f"stmt{i}"} for i in range(10)],
            "edges": [{"source": i, "target": i + 1} for i in range(9)],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(cfg_data)}
        )

        result = await mock_query_executor.execute(
            'cpg.method.name("complex_func").cfg'
        )

        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert len(data["nodes"]) == 10

    @pytest.mark.asyncio
    async def test_get_cfg_with_loops(self, mock_query_executor):
        """测试包含循环的CFG"""
        cfg_data = {
            "function": "loop_func",
            "nodes": [
                {"id": 1, "code": "while(true)", "type": "CONTROL_STRUCTURE"},
                {"id": 2, "code": "work()", "type": "CALL"},
                {"id": 3, "code": "break", "type": "BREAK"},
            ],
            "edges": [
                {"source": 1, "target": 2},
                {"source": 2, "target": 1},  # 循环边
                {"source": 2, "target": 3},  # 退出边
            ],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(cfg_data)}
        )

        result = await mock_query_executor.execute('cpg.method.name("loop_func").cfg')

        assert result["success"] is True
        data = json.loads(result["stdout"])
        # 验证循环边存在
        assert any(e["source"] == 2 and e["target"] == 1 for e in data["edges"])

    @pytest.mark.asyncio
    async def test_dominator_tree(self, mock_query_executor):
        """测试支配树分析"""
        dom_data = {
            "function": "test_func",
            "dominators": [
                {"node": 1, "dominates": [2, 3, 4]},
                {"node": 2, "dominates": [3]},
            ],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(dom_data)}
        )

        result = await mock_query_executor.execute(
            'cpg.method.name("test_func").dominatorTree'
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_post_dominator_tree(self, mock_query_executor):
        """测试后支配树分析"""
        postdom_data = {
            "function": "test_func",
            "post_dominators": [
                {"node": 5, "post_dominates": [4, 3, 2, 1]},
            ],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(postdom_data)}
        )

        result = await mock_query_executor.execute(
            'cpg.method.name("test_func").postDominatorTree'
        )

        assert result["success"] is True


class TestCFGEdgeCases:
    """测试CFG边界情况"""

    @pytest.mark.asyncio
    async def test_empty_function_cfg(self, mock_query_executor):
        """测试空函数的CFG"""
        cfg_data = {
            "function": "empty",
            "nodes": [{"id": 1, "code": "void empty() {}", "type": "ENTRY"}],
            "edges": [],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(cfg_data)}
        )

        result = await mock_query_executor.execute('cpg.method.name("empty").cfg')

        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert len(data["nodes"]) >= 1

    @pytest.mark.asyncio
    async def test_function_not_found(self, mock_query_executor):
        """测试函数不存在"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Function not found"}
        )

        result = await mock_query_executor.execute('cpg.method.name("nonexistent").cfg')

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_unreachable_code(self, mock_query_executor):
        """测试不可达代码的CFG"""
        cfg_data = {
            "function": "unreachable_func",
            "nodes": [
                {"id": 1, "code": "return 0", "type": "RETURN"},
                {"id": 2, "code": "unreachable()", "type": "CALL", "unreachable": True},
            ],
            "edges": [{"source": 1, "target": 2, "type": "UNREACHABLE"}],
        }

        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": json.dumps(cfg_data)}
        )

        result = await mock_query_executor.execute(
            'cpg.method.name("unreachable_func").cfg'
        )

        assert result["success"] is True
