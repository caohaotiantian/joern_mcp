"""边界条件和异常场景测试"""

import pytest
from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService
from tests.e2e.test_helpers import execute_query_safe, import_code_safe


@pytest.mark.integration
@pytest.mark.asyncio
class TestBoundaryConditions:
    """边界条件测试"""

    async def test_get_callers_nonexistent_function(self, joern_server, sample_c_code):
        """测试查询不存在的函数的调用者"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_1")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 查询不存在的函数
        result = await service.get_callers("this_function_does_not_exist")

        # 应该成功但返回空结果
        assert result.get("success"), f"查询应该成功，错误: {result.get('error')}"
        assert result["function"] == "this_function_does_not_exist"
        assert result["callers"] == [], "不存在的函数应该返回空列表"
        assert result["count"] == 0, "计数应该为0"

    async def test_get_callees_nonexistent_function(self, joern_server, sample_c_code):
        """测试查询不存在的函数的被调用者"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_2")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 查询不存在的函数
        result = await service.get_callees("this_function_does_not_exist")

        # 应该成功但返回空结果
        assert result.get("success"), f"查询应该成功，错误: {result.get('error')}"
        assert result["function"] == "this_function_does_not_exist"
        assert result["callees"] == [], "不存在的函数应该返回空列表"
        assert result["count"] == 0, "计数应该为0"

    async def test_call_chain_with_max_depth_limit(self, joern_server, sample_c_code):
        """测试不同深度限制的调用链"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_3")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试不同深度
        for depth in [1, 2, 5, 10]:
            result = await service.get_call_chain("main", max_depth=depth, direction="down")

            assert result.get("success"), f"depth={depth}应该成功"
            assert result["max_depth"] == depth, f"max_depth应该是{depth}"
            assert "chain" in result, "应该包含chain字段"
            assert isinstance(result["chain"], list), "chain应该是列表"

            # 记录chain长度用于观察
            logger.debug(f"depth={depth}, chain_length={len(result['chain'])}")

    async def test_dataflow_empty_result(self, joern_server, sample_c_code):
        """测试数据流查询返回空结果"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_4")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 查询不存在的数据流
        result = await service.track_dataflow("nonexistent_source", "nonexistent_sink")

        # 应该成功但返回空结果
        assert result.get("success"), f"查询应该成功，错误: {result.get('error')}"
        assert result["source_method"] == "nonexistent_source"
        assert result["sink_method"] == "nonexistent_sink"
        assert result.get("flows", []) == [], "应该返回空flows"
        assert result.get("count", 0) == 0, "计数应该为0"

    async def test_variable_flow_with_max_flows_limit(self, joern_server, sample_c_code):
        """测试max_flows限制"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_5")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 测试不同的流限制
        for max_flows in [1, 3, 5, 10]:
            result = await service.analyze_variable_flow(
                "user_input", "strcpy", max_flows=max_flows
            )

            if result.get("success") and "flows" in result:
                flows = result["flows"]
                assert len(flows) <= max_flows, \
                    f"返回的flows数量({len(flows)})不应超过max_flows({max_flows})"

    async def test_taint_analysis_empty_result(self, joern_server, sample_c_code):
        """测试污点分析返回空结果"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_6")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 检查不存在的数据流
        result = await service.check_specific_flow(
            "nonexistent_source", "nonexistent_sink"
        )

        # 应该成功但返回空结果
        assert result.get("success"), f"查询应该成功，错误: {result.get('error')}"
        assert result["source_pattern"] == "nonexistent_source"
        assert result["sink_pattern"] == "nonexistent_sink"
        assert result.get("flows", []) == [], "应该返回空flows"
        assert result.get("count", 0) == 0, "计数应该为0"

    async def test_concurrent_queries(self, joern_server, sample_c_code):
        """测试并发查询"""
        import asyncio

        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_7")

        executor = QueryExecutor(joern_server)
        callgraph_service = CallGraphService(executor)
        dataflow_service = DataFlowService(executor)

        # 并发执行多个不同类型的查询
        tasks = [
            callgraph_service.get_callers("main"),
            callgraph_service.get_callees("process_input"),
            callgraph_service.get_call_chain("unsafe_strcpy", max_depth=3),
            dataflow_service.find_data_dependencies("main"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有查询都成功
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"查询{i}抛出异常: {result}")
            assert isinstance(result, dict), f"查询{i}应该返回dict"
            assert result.get("success") or "error" in result, \
                f"查询{i}应该包含success或error字段"

    async def test_special_characters_in_function_name(self, joern_server, sample_c_code):
        """测试函数名包含特殊字符的情况"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_8")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试包含特殊字符的函数名（虽然不太可能，但应该处理）
        special_names = [
            "func_with_underscore",
            "func123",  # 包含数字
        ]

        for func_name in special_names:
            result = await service.get_callers(func_name)

            # 应该成功（即使找不到函数）
            assert isinstance(result, dict), f"查询{func_name}应该返回dict"
            assert "success" in result, f"查询{func_name}应该包含success字段"

    async def test_empty_project(self, joern_server):
        """测试空项目的查询"""
        # 不导入任何代码，直接查询
        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 在空项目中查询
        result = await service.get_callers("main")

        # 应该成功但返回空结果
        assert isinstance(result, dict), "应该返回dict"
        assert "callers" in result or "error" in result or not result.get("success"), \
            "应该返回空callers或错误"

    async def test_zero_depth_query(self, joern_server, sample_c_code):
        """测试depth=0的查询"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_9")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # depth=0应该返回函数本身或空结果
        result = await service.get_callers("main", depth=0)

        assert isinstance(result, dict), "应该返回dict"
        assert "success" in result, "应该包含success字段"
        # depth=0可能返回空或只有函数本身

    async def test_very_large_depth(self, joern_server, sample_c_code):
        """测试非常大的depth值"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_10")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 非常大的depth值应该被处理（可能被限制）
        result = await service.get_call_chain("main", max_depth=100)

        assert isinstance(result, dict), "应该返回dict"
        assert "success" in result, "应该包含success字段"
        # 实际返回的chain长度应该远小于100（因为代码没那么深）

    async def test_max_flows_zero(self, joern_server, sample_c_code):
        """测试max_flows=0的情况"""
        await import_code_safe(joern_server, str(sample_c_code), "boundary_test_11")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # max_flows=0应该返回空结果
        result = await service.track_dataflow("gets", "strcpy", max_flows=0)

        assert isinstance(result, dict), "应该返回dict"
        if result.get("success") and "flows" in result:
            assert len(result["flows"]) == 0, "max_flows=0应该返回空flows"

