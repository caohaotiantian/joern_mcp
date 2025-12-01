"""测试MCP Tools集成"""

import pytest

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.joern.manager import JoernManager
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestToolsIntegration:
    """测试工具集成"""

    @pytest.mark.asyncio
    async def test_query_execution_flow(self, joern_server):
        """测试查询执行流程"""
        executor = QueryExecutor(joern_server)

        # 测试基本查询
        result = await executor.execute("cpg.method.name.l")
        assert result is not None

    @pytest.mark.asyncio
    async def test_callgraph_service_flow(self, joern_server):
        """测试调用图服务流程"""
        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试获取调用者
        result = await service.get_callers("main", depth=1)
        assert result is not None

        # 测试获取被调用者
        result = await service.get_callees("main", depth=1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_dataflow_service_flow(self, joern_server):
        """测试数据流服务流程"""
        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 测试追踪数据流
        result = await service.track_dataflow("gets", "system", max_flows=5)
        assert result is not None

    @pytest.mark.asyncio
    async def test_taint_analysis_flow(self, joern_server):
        """测试污点分析流程"""
        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 列出规则
        result = service.list_rules()
        assert result.get("success") is True
        assert len(result.get("rules", [])) >= 6

        # 获取规则详情
        result = service.get_rule_details("Command Injection")
        assert result.get("success") is True
        assert result["rule"]["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_concurrent_service_calls(self, joern_server):
        """测试并发服务调用"""
        import asyncio
        import warnings

        executor = QueryExecutor(joern_server)
        callgraph_service = CallGraphService(executor)
        dataflow_service = DataFlowService(executor)

        # 并发调用多个服务
        tasks = [
            callgraph_service.get_callers("main", depth=1),
            callgraph_service.get_callees("main", depth=1),
            dataflow_service.track_dataflow("gets", "system", max_flows=5),
        ]

        # 使用warnings过滤器抑制CPGQLSClient的协程警告
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证至少大部分成功
        success_count = sum(1 for r in results if isinstance(r, dict) and r is not None)
        assert success_count >= 2  # 至少2个成功
