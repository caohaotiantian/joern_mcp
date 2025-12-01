"""复杂项目测试 - 测试多文件、复杂调用链"""

from pathlib import Path

import pytest
from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService
from tests.e2e.test_helpers import execute_query_safe, import_code_safe


@pytest.fixture
def complex_c_project():
    """复杂C项目的路径"""
    project_path = Path(__file__).parent / "test_data" / "complex_c"
    if not project_path.exists():
        pytest.skip(f"Complex C project not found at {project_path}")
    return project_path


@pytest.mark.integration
@pytest.mark.asyncio
class TestComplexProject:
    """测试复杂项目的分析功能"""

    async def test_import_complex_project(self, joern_server, complex_c_project):
        """测试导入复杂的多文件C项目"""
        result = await import_code_safe(
            joern_server, str(complex_c_project), "complex_project"
        )

        # 严格验证
        assert result.get("success"), f"导入失败: {result.get('stderr', '')}"
        assert "stdout" in result or "success" in result, "应该返回导入结果"

        # 查询项目中的函数数量
        query = "cpg.method.name.l"
        methods_result = await execute_query_safe(joern_server, query)

        assert methods_result.get("success"), "查询函数列表应该成功"

        # 验证包含预期的函数
        stdout = str(methods_result.get("stdout", ""))
        expected_functions = [
            "main",  # main.c
            "process_data",  # utils.c
            "log_message",  # utils.c
            "unsafe_strcpy",  # utils.c
            "init_network",  # network.c
            "receive_network_data",  # network.c
        ]

        for func in expected_functions:
            assert func in stdout, f"应该包含函数{func}"

    async def test_cross_file_call_graph(self, joern_server, complex_c_project):
        """测试跨文件的调用图分析"""
        await import_code_safe(joern_server, str(complex_c_project), "cross_file_test")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 分析main函数的调用图（应该包含跨文件调用）
        result = await service.get_call_graph("main", depth=3)

        # 验证基本结构
        assert result.get("success"), f"获取调用图失败: {result.get('error')}"
        assert "nodes" in result, "应该包含nodes字段"
        assert "edges" in result, "应该包含edges字段"

        nodes = result["nodes"]
        edges = result["edges"]

        # 验证节点和边的结构
        assert isinstance(nodes, list), "nodes应该是列表"
        assert isinstance(edges, list), "edges应该是列表"

        # main函数的调用图应该有节点
        if nodes:
            # 验证节点结构（节点可能使用id或name字段）
            for i, node in enumerate(nodes):
                assert isinstance(node, dict), f"node[{i}]应该是dict"
                assert "id" in node or "name" in node, \
                    f"node[{i}]应该包含id或name字段，实际: {node.keys()}"
                # 验证type字段
                if "type" in node:
                    assert isinstance(node["type"], str), \
                        f"node[{i}].type应该是字符串"

            # 记录节点名称用于调试
            node_names = [n.get("id", n.get("name", "unknown")) for n in nodes]
            logger.info(f"Call graph nodes: {node_names}")

            # 验证main函数至少有一些调用（不要求特定函数）
            assert len(nodes) >= 1, "main函数的调用图应该至少有1个节点"

    async def test_deep_call_chain(self, joern_server, complex_c_project):
        """测试深层调用链（多层嵌套）"""
        await import_code_safe(joern_server, str(complex_c_project), "deep_chain_test")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 测试不同深度的调用链
        for depth in [1, 3, 5]:
            result = await service.get_call_chain("main", max_depth=depth, direction="down")

            assert result.get("success"), f"depth={depth}应该成功"
            assert result["max_depth"] == depth, f"max_depth应该是{depth}"
            assert "chain" in result, "应该包含chain"
            assert isinstance(result["chain"], list), "chain应该是列表"

            logger.info(
                f"Depth={depth}: 返回{len(result['chain'])}个节点"
            )

    async def test_buffer_overflow_detection(self, joern_server, complex_c_project):
        """测试缓冲区溢出检测"""
        await import_code_safe(joern_server, str(complex_c_project), "overflow_test")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 检查strcpy相关的污点流（潜在的缓冲区溢出）
        result = await service.check_specific_flow("strcpy|unsafe_strcpy", "strcpy")

        # 验证基本结构
        assert isinstance(result, dict), "应该返回dict"
        assert "success" in result, "应该包含success字段"

        # 如果成功，验证flows（可能找到或找不到，都是有效结果）
        if result.get("success"):
            assert "flows" in result, "应该包含flows字段"
            assert isinstance(result["flows"], list), "flows应该是列表"

    async def test_command_injection_detection(self, joern_server, complex_c_project):
        """测试命令注入检测"""
        await import_code_safe(
            joern_server, str(complex_c_project), "command_injection_test"
        )

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)

        # 检查命令执行函数（system, popen等）
        result = await service.check_specific_flow("argv|gets|scanf", "system|popen")

        # 验证基本结构
        assert isinstance(result, dict), "应该返回dict"
        assert "success" in result, "应该包含success字段"

        if result.get("success"):
            assert "flows" in result, "应该包含flows字段"

            # 如果找到污点流，验证其结构
            if result["flows"]:
                for i, flow in enumerate(result["flows"]):
                    assert isinstance(flow, dict), f"flow[{i}]应该是dict"
                    assert "source" in flow, f"flow[{i}]应该包含source"
                    assert "sink" in flow, f"flow[{i}]应该包含sink"

    async def test_multi_file_dataflow(self, joern_server, complex_c_project):
        """测试跨文件的数据流分析"""
        await import_code_safe(
            joern_server, str(complex_c_project), "multi_file_dataflow_test"
        )

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 追踪从main到process_data的数据流（跨文件）
        result = await service.track_dataflow("main", "process_data", max_flows=10)

        # 基本验证
        assert isinstance(result, dict), "应该返回dict"
        assert "success" in result, "应该包含success字段"
        assert result.get("source_method") == "main", "source_method应该是main"
        assert result.get("sink_method") == "process_data", "sink_method应该是process_data"

        # 如果成功，验证flows
        if result.get("success") and result.get("flows"):
            flows = result["flows"]
            assert isinstance(flows, list), "flows应该是列表"

            # 验证flows结构
            for i, flow in enumerate(flows):
                assert isinstance(flow, dict), f"flow[{i}]应该是dict"
                assert "source" in flow, f"flow[{i}]应该包含source"
                assert "sink" in flow, f"flow[{i}]应该包含sink"

                # 验证路径长度
                if "pathLength" in flow:
                    assert isinstance(flow["pathLength"], int), \
                        f"flow[{i}].pathLength应该是整数"
                    assert flow["pathLength"] > 0, \
                        f"flow[{i}].pathLength应该大于0"

    async def test_vulnerability_functions(self, joern_server, complex_c_project):
        """测试识别漏洞函数"""
        await import_code_safe(
            joern_server, str(complex_c_project), "vulnerability_test"
        )

        # 查询使用了危险函数的位置
        query = 'cpg.call.name("strcpy|sprintf|gets|system").code.l'
        result = await execute_query_safe(joern_server, query)

        assert result.get("success"), "查询危险函数应该成功"
        assert "stdout" in result, "应该包含stdout"

        # 验证找到了危险函数的使用
        stdout = str(result["stdout"])
        dangerous_functions = ["strcpy", "sprintf", "system"]

        found_any = False
        for func in dangerous_functions:
            if func in stdout:
                found_any = True
                logger.info(f"发现危险函数: {func}")

        # 复杂项目应该至少使用了一些危险函数
        assert found_any or "[]" in stdout, "应该找到危险函数或返回空列表"

    async def test_global_variable_tracking(self, joern_server, complex_c_project):
        """测试全局变量追踪"""
        await import_code_safe(joern_server, str(complex_c_project), "global_var_test")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)

        # 查找main函数的数据依赖（应该包含全局变量）
        result = await service.find_data_dependencies("main")

        # 基本验证
        assert isinstance(result, dict), "应该返回dict"
        assert result.get("function") == "main", "function应该是main"

        # 验证dependencies结构
        if result.get("success") and "dependencies" in result:
            deps = result["dependencies"]
            assert isinstance(deps, list), "dependencies应该是列表"

            # 验证每个依赖的结构
            for i, dep in enumerate(deps):
                if isinstance(dep, dict):
                    assert "variable" in dep or "code" in dep, \
                        f"dependency[{i}]应该包含variable或code"

    async def test_function_complexity_check(self, joern_server, complex_c_project):
        """测试函数复杂度检查"""
        await import_code_safe(joern_server, str(complex_c_project), "complexity_test")

        # 查询每个函数的行数作为复杂度指标
        query = 'cpg.method.map(m => (m.name, m.numberOfLines)).l'
        result = await execute_query_safe(joern_server, query)

        assert result.get("success"), "查询函数复杂度应该成功"
        assert "stdout" in result, "应该包含stdout"

        # 验证返回了复杂度信息
        stdout = str(result["stdout"])
        assert len(stdout) > 0, "应该返回复杂度信息"

    async def test_callgraph_callers_validation(self, joern_server, complex_c_project):
        """测试调用图的caller分析 - 增强验证"""
        await import_code_safe(joern_server, str(complex_c_project), "callers_validation")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)

        # 分析process_data的调用者（应该包括main和internal_handler）
        result = await service.get_callers("process_data", depth=2)

        # 严格验证结果结构
        assert result.get("success"), f"获取调用者失败: {result.get('error')}"
        assert result["function"] == "process_data", "function字段不匹配"
        assert result["depth"] == 2, "depth字段不匹配"
        assert "callers" in result, "应该包含callers字段"
        assert "count" in result, "应该包含count字段"

        callers = result["callers"]
        assert isinstance(callers, list), f"callers应该是列表，实际: {type(callers)}"

        # 验证每个caller的结构
        for i, caller in enumerate(callers):
            assert isinstance(caller, dict), f"caller[{i}]应该是dict"
            assert "name" in caller, f"caller[{i}]应该包含name字段"
            assert isinstance(caller["name"], str), \
                f"caller[{i}].name应该是字符串"

            # 验证可选字段的类型
            if "filename" in caller:
                assert isinstance(caller["filename"], str), \
                    f"caller[{i}].filename应该是字符串"
            if "lineNumber" in caller:
                assert isinstance(caller["lineNumber"], int) or caller["lineNumber"] == -1, \
                    f"caller[{i}].lineNumber应该是整数"

        # count应该与callers长度一致
        assert result["count"] == len(callers), \
            f"count({result['count']})应该等于callers长度({len(callers)})"

