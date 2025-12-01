"""增强的服务层测试 - 覆盖未测试的方法"""

import sys
from pathlib import Path

import pytest

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.joern.manager import JoernManager
from joern_mcp.models.taint_rules import get_rule_by_name
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService

# 添加e2e测试目录到path以导入test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent / "e2e"))
from test_helpers import import_code_safe  # noqa: E402


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestCallGraphServiceEnhanced:
    """增强的调用图服务测试"""

    @pytest.mark.asyncio
    async def test_get_call_chain(self, joern_server, sample_c_code):
        """测试获取调用链"""
        # 导入代码（使用安全方法避免event loop冲突）
        await import_code_safe(joern_server, str(sample_c_code), "test_call_chain")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试获取调用链
        result = await service.get_call_chain("main", max_depth=3)

        # 基本验证
        assert isinstance(result, dict), f"返回类型应该是dict，实际: {type(result)}"
        assert "function" in result, "应该包含function字段"
        assert result["function"] == "main", f"函数名应该是main，实际: {result.get('function')}"
        assert "success" in result, "应该包含success字段"

        # 深度验证chain结构
        if result.get("success"):
            assert "chain" in result, "成功时应该包含chain字段"
            assert "max_depth" in result, "应该包含max_depth字段"
            assert result["max_depth"] == 3, f"max_depth应该是3，实际: {result.get('max_depth')}"

            chain = result["chain"]
            assert isinstance(chain, list), "chain应该是列表"

            # 如果chain不为空，验证每个节点的结构
            for i, node in enumerate(chain):
                assert isinstance(node, dict), f"chain[{i}]应该是dict"
                assert "name" in node, f"chain[{i}]应该包含name字段"
                assert isinstance(node["name"], str), f"chain[{i}].name应该是字符串"

                # 验证可选字段的类型
                if "filename" in node:
                    assert isinstance(node["filename"], str), \
                        f"chain[{i}].filename应该是字符串"
                if "lineNumber" in node:
                    assert isinstance(node["lineNumber"], int) or node["lineNumber"] == -1, \
                        f"chain[{i}].lineNumber应该是整数"

    @pytest.mark.asyncio
    async def test_get_call_graph(self, joern_server, sample_c_code):
        """测试获取完整调用图"""
        # 导入代码
        await import_code_safe(joern_server, str(sample_c_code), "test_call_graph")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试获取调用图（参数名是depth，不是max_depth）
        result = await service.get_call_graph(function_name="main", depth=2)

        # 严格验证
        assert isinstance(result, dict), f"返回类型应该是dict，实际: {type(result)}"
        assert "success" in result, "应该包含success字段"

        # 如果成功，验证图结构
        if result.get("success"):
            assert "nodes" in result or "edges" in result or "graph" in result, \
                "成功时应该包含图结构信息"

    @pytest.mark.asyncio
    async def test_get_callers_with_depth(self, joern_server, sample_c_code):
        """测试不同深度的调用者查询"""
        await import_code_safe(joern_server, str(sample_c_code), "test_callers_depth")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试不同深度
        for depth in [1, 2, 3]:
            result = await service.get_callers("unsafe_strcpy", depth=depth)

            assert isinstance(result, dict), f"深度{depth}应返回dict"
            assert "function" in result, f"深度{depth}应包含function字段"
            assert result["function"] == "unsafe_strcpy"


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestDataFlowServiceEnhanced:
    """增强的数据流服务测试"""

    @pytest.mark.asyncio
    async def test_analyze_variable_flow(self, joern_server, sample_c_code):
        """测试变量流分析"""
        await import_code_safe(joern_server, str(sample_c_code), "test_var_flow")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 测试变量流分析
        result = await service.analyze_variable_flow("main", "buffer")

        # 基本验证
        assert isinstance(result, dict), f"返回类型应该是dict，实际: {type(result)}"
        assert "success" in result, "应该包含success字段"
        assert "variable" in result, "应该包含variable字段"
        assert result["variable"] == "main", \
            f"变量名应该是main，实际: {result.get('variable')}"

        # 深度验证flows内容
        if result.get("success"):
            assert "flows" in result or "sink_method" in result, \
                "成功时应该包含流信息"
            assert result.get("sink_method") == "buffer", \
                f"sink_method应该是buffer，实际: {result.get('sink_method')}"

            # 如果有flows数据，验证其结构
            if "flows" in result and result["flows"]:
                flows = result["flows"]
                assert isinstance(flows, list), "flows应该是列表"

                for i, flow in enumerate(flows):
                    assert isinstance(flow, dict), f"flow[{i}]应该是dict"
                    # 验证必需字段存在
                    for field in ["source", "sink"]:
                        assert field in flow, f"flow[{i}]应该包含{field}字段"

                    # 验证source结构
                    source = flow["source"]
                    assert isinstance(source, dict), f"flow[{i}].source应该是dict"
                    assert "code" in source, f"flow[{i}].source应该包含code"
                    assert "line" in source, f"flow[{i}].source应该包含line"
                    assert isinstance(source.get("line"), int) or source.get("line") == -1, \
                        f"flow[{i}].source.line应该是整数"

                    # 验证sink结构
                    sink = flow["sink"]
                    assert isinstance(sink, dict), f"flow[{i}].sink应该是dict"
                    assert "code" in sink, f"flow[{i}].sink应该包含code"
                    assert "line" in sink, f"flow[{i}].sink应该包含line"
                    assert isinstance(sink.get("line"), int) or sink.get("line") == -1, \
                        f"flow[{i}].sink.line应该是整数"

    @pytest.mark.asyncio
    async def test_find_data_dependencies(self, joern_server, sample_c_code):
        """测试查找数据依赖"""
        await import_code_safe(joern_server, str(sample_c_code), "test_data_deps")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 测试查找数据依赖
        result = await service.find_data_dependencies("main")

        # 基本验证
        assert isinstance(result, dict), f"返回类型应该是dict，实际: {type(result)}"
        assert "function" in result, "应该包含function字段"
        assert result["function"] == "main", \
            f"函数名应该是main，实际: {result.get('function')}"
        assert "success" in result, "应该包含success字段"

        # 深度验证依赖信息
        if result.get("success"):
            assert "dependencies" in result, "成功时应该包含dependencies字段"

            dependencies = result["dependencies"]
            assert isinstance(dependencies, list), "dependencies应该是列表"

            # 如果有依赖数据，验证其结构
            if dependencies:
                for i, dep in enumerate(dependencies):
                    assert isinstance(dep, dict), f"dependency[{i}]应该是dict"
                    # 验证必需字段
                    assert "variable" in dep, f"dependency[{i}]应该包含variable"
                    assert "code" in dep, f"dependency[{i}]应该包含code"

                    # 验证数据类型
                    assert isinstance(dep.get("variable"), str), \
                        f"dependency[{i}].variable应该是字符串"
                    assert isinstance(dep.get("code"), str), \
                        f"dependency[{i}].code应该是字符串"

                    # 如果有line字段，验证其类型
                    if "line" in dep:
                        assert isinstance(dep["line"], int) or dep["line"] == -1, \
                            f"dependency[{i}].line应该是整数"

    @pytest.mark.asyncio
    async def test_track_dataflow_with_limits(self, joern_server, sample_c_code):
        """测试不同流限制的数据流追踪"""
        await import_code_safe(joern_server, str(sample_c_code), "test_flow_limits")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 测试不同的流限制
        for max_flows in [1, 5, 10]:
            result = await service.track_dataflow("gets", "strcpy", max_flows=max_flows)

            assert isinstance(result, dict), f"max_flows={max_flows}应返回dict"
            assert "success" in result, f"max_flows={max_flows}应包含success"


@pytest.mark.integration
@pytest.mark.skipif(
    not JoernManager().validate_installation(), reason="Joern not installed"
)
class TestTaintAnalysisServiceEnhanced:
    """增强的污点分析服务测试"""

    @pytest.mark.asyncio
    async def test_check_specific_flow(self, joern_server, sample_c_code):
        """测试检查特定流"""
        await import_code_safe(joern_server, str(sample_c_code), "test_specific_flow")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 测试检查特定的source->sink流
        result = await service.check_specific_flow("gets", "strcpy")

        # 严格验证
        assert isinstance(result, dict), f"返回类型应该是dict，实际: {type(result)}"
        assert "source_pattern" in result, "应该包含source_pattern字段"
        assert "sink_pattern" in result, "应该包含sink_pattern字段"
        assert result["source_pattern"] == "gets", f"source应该是gets，实际: {result.get('source_pattern')}"
        assert result["sink_pattern"] == "strcpy", f"sink应该是strcpy，实际: {result.get('sink_pattern')}"
        assert "success" in result, "应该包含success字段"
        assert "flows" in result, "应该包含flows字段"

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="某些污点规则包含ProcessBuilder等安全关键字，会被OptimizedQueryExecutor拦截"
    )
    async def test_analyze_with_all_rules(self, joern_server, sample_c_code):
        """测试使用所有规则进行分析"""
        await import_code_safe(joern_server, str(sample_c_code), "test_all_rules")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 获取所有规则
        rules_result = service.list_rules()
        assert rules_result.get("success"), "获取规则列表应该成功"

        rules = rules_result.get("rules", [])
        assert len(rules) > 0, "应该有规则"

        # 对每个规则进行测试
        for rule_dict in rules[:3]:  # 测试前3个规则，避免太慢
            rule_name = rule_dict["name"]

            # 获取实际的TaintRule对象
            rule = get_rule_by_name(rule_name)
            result = await service.analyze_with_rule(rule)

            assert isinstance(result, dict), f"规则{rule_name}应返回dict"
            assert "rule" in result, f"规则{rule_name}应包含rule字段"
            assert result["rule"] == rule_name, \
                f"规则名应该是{rule_name}，实际: {result.get('rule')}"

    @pytest.mark.asyncio
    async def test_find_vulnerabilities_with_limits(self, joern_server, sample_c_code):
        """测试不同限制的漏洞查找"""
        await import_code_safe(joern_server, str(sample_c_code), "test_vuln_limits")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 测试不同的流限制
        for max_flows in [1, 5, 10]:
            result = await service.find_vulnerabilities(max_flows=max_flows)

            assert isinstance(result, dict), f"max_flows={max_flows}应返回dict"
            assert "success" in result, f"max_flows={max_flows}应包含success"

            # 验证结构
            if result.get("success"):
                assert "vulnerabilities" in result or "summary" in result, \
                    f"max_flows={max_flows}成功时应包含vulnerabilities或summary"

    @pytest.mark.asyncio
    async def test_get_all_rule_details(self, joern_server):
        """测试获取所有规则详情"""
        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 获取规则列表
        rules_result = service.list_rules()
        rules = rules_result.get("rules", [])

        # 获取每个规则的详情
        for rule in rules:
            rule_name = rule["name"]
            details = service.get_rule_details(rule_name)

            # 严格验证
            assert isinstance(details, dict), f"规则{rule_name}详情应该是dict"
            assert details.get("success"), f"获取规则{rule_name}详情应该成功"
            assert "rule" in details, f"规则{rule_name}应该包含rule字段"

            # 验证规则结构
            rule_data = details["rule"]
            assert "name" in rule_data, f"规则{rule_name}应该有name"
            assert "severity" in rule_data, f"规则{rule_name}应该有severity"
            assert "sources" in rule_data, f"规则{rule_name}应该有sources"
            assert "sinks" in rule_data, f"规则{rule_name}应该有sinks"

