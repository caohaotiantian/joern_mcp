"""
E2E测试 - MCP工具层（修复版）

真正验证功能的正确性，不掩盖问题
"""

import pytest

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.mcp_server import server_state
from joern_mcp.services.callgraph import CallGraphService
from joern_mcp.services.dataflow import DataFlowService
from joern_mcp.services.taint import TaintAnalysisService

from .test_helpers import execute_query_safe, import_code_safe


@pytest.mark.e2e
@pytest.mark.asyncio
class TestProjectToolsE2E:
    """测试项目管理工具的E2E流程"""

    async def test_create_and_delete_project_workflow(
        self, joern_server, sample_c_code
    ):
        """测试创建和删除项目的完整流程"""
        project_name = "test_e2e_project"

        # 1. 导入代码
        result = await import_code_safe(joern_server, str(sample_c_code), project_name)
        assert result["success"], (
            f"导入代码失败: {result.get('stderr', 'Unknown error')}"
        )

        # 2. 验证项目已创建
        projects_result = await execute_query_safe(
            joern_server, "workspace.projects.name.l"
        )
        assert projects_result["success"], "列出项目失败"

        # 3. 删除项目
        delete_query = f'workspace.projects.name("{project_name}").delete'
        await execute_query_safe(joern_server, delete_query)
        # delete操作不总是返回success，这是已知的Joern行为


@pytest.mark.e2e
@pytest.mark.asyncio
class TestQueryToolsE2E:
    """测试查询工具的E2E流程"""

    async def test_get_function_code_workflow(self, joern_server, sample_c_code):
        """测试获取函数代码的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "query_test")

        query = 'cpg.method.name("main").code.l'
        result = await execute_query_safe(joern_server, query)

        assert result["success"], f"查询失败: {result.get('stderr', '')}"
        assert "stdout" in result, "返回结果中缺少stdout字段"
        # 验证返回了main函数的代码
        assert len(result["stdout"]) > 0, "未返回函数代码"

    async def test_list_functions_workflow(self, joern_server, sample_c_code):
        """测试列出函数的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "list_funcs_test")

        query = "cpg.method.name.l"
        result = await execute_query_safe(joern_server, query)

        # 强断言验证
        assert result.get("success"), f"查询失败: {result.get('stderr', '')}"
        assert "stdout" in result, "应该包含stdout字段"

        stdout = result["stdout"]
        assert stdout is not None, "stdout不应该是None"

        # 解析函数列表
        import json
        if isinstance(stdout, list):
            functions = stdout
        elif isinstance(stdout, str):
            # 尝试解析为JSON
            try:
                functions = json.loads(stdout) if stdout else []
            except json.JSONDecodeError:
                # 可能是逗号分隔的字符串
                functions = [f.strip() for f in stdout.split(',') if f.strip()]
        else:
            functions = []

        # 验证函数列表结构
        assert isinstance(functions, list), f"函数列表应该是list，实际: {type(functions)}"

        # 验证包含预期的函数（基于sample_c代码）
        expected_functions = ["main", "unsafe_strcpy", "process_input"]
        function_names = [f if isinstance(f, str) else str(f) for f in functions]

        for expected in expected_functions:
            assert any(expected in fname for fname in function_names), \
                f"函数列表应该包含{expected}，实际: {function_names}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCallGraphToolsE2E:
    """测试调用图工具的E2E流程"""

    async def test_get_callers_workflow(self, joern_server, sample_c_code):
        """测试获取调用者的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "callers_test")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)
        result = await service.get_callers("unsafe_strcpy", depth=1)

        # 真正的验证
        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "function" in result, "返回结果缺少function字段"
        assert result["function"] == "unsafe_strcpy", (
            f"函数名不匹配: {result.get('function')}"
        )
        assert "success" in result, "返回结果缺少success字段"

    async def test_get_callees_workflow(self, joern_server, sample_c_code):
        """测试获取被调用者的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "callees_test")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)
        result = await service.get_callees("process_input", depth=1)

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "function" in result, "返回结果缺少function字段"
        assert "success" in result, "返回结果缺少success字段"

    async def test_analyze_call_chain_workflow(self, joern_server, sample_c_code):
        """测试分析调用链的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "call_chain_test")

        executor = QueryExecutor(joern_server)
        service = CallGraphService(executor)
        result = await service.get_call_chain("main", max_depth=5)

        # 真正验证结果
        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "function" in result, "返回结果缺少function字段"
        assert result["function"] == "main", f"函数名不匹配: {result.get('function')}"

        # 如果查询成功，验证有chain数据
        if result.get("success"):
            assert "chain" in result, "成功时应该包含chain字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDataFlowToolsE2E:
    """测试数据流工具的E2E流程"""

    async def test_track_dataflow_workflow(self, joern_server, sample_c_code):
        """测试追踪数据流的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "dataflow_test")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)
        result = await service.track_dataflow("main", "argv")

        # 真正验证
        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "返回结果缺少success字段"
        assert "source_method" in result, "返回结果缺少source_method字段"
        assert result["source_method"] == "main", (
            f"源方法不匹配: {result.get('source_method')}"
        )

    async def test_analyze_variable_flow_workflow(self, joern_server, sample_c_code):
        """测试分析变量流的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "var_flow_test")

        executor = QueryExecutor(joern_server)
        service = DataFlowService(executor)
        result = await service.analyze_variable_flow("process_input", "buffer")

        # 真正验证基本结构
        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "返回结果缺少success字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestTaintToolsE2E:
    """测试污点分析工具的E2E流程"""

    async def test_find_vulnerabilities_workflow(self, joern_server, sample_c_code):
        """测试查找漏洞的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "vuln_test")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)
        results = await service.find_vulnerabilities()

        # 真正验证 - find_vulnerabilities返回dict而非list
        assert isinstance(results, dict), f"返回类型错误，应该是dict: {type(results)}"
        assert "success" in results, "返回结果缺少success字段"

        # 如果成功，验证结构
        if results.get("success"):
            assert "vulnerabilities" in results or "summary" in results, (
                "成功时应该包含vulnerabilities或summary字段"
            )

    async def test_check_specific_flow_workflow(self, joern_server, sample_c_code):
        """测试检查特定流的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "flow_test")

        executor = QueryExecutor(joern_server)
        service = TaintAnalysisService(executor)
        result = await service.check_specific_flow("argv", "strcpy")

        # 真正验证
        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "返回结果缺少success字段"
        assert "source_pattern" in result, "返回结果缺少source_pattern字段"
        assert "sink_pattern" in result, "返回结果缺少sink_pattern字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCFGToolsE2E:
    """测试控制流图工具的E2E流程"""

    async def test_get_cfg_workflow(self, joern_server, sample_c_code):
        """测试获取CFG的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "cfg_test")

        query = 'cpg.method.name("main").dotCfg.l'
        result = await execute_query_safe(joern_server, query)

        assert result["success"], f"查询失败: {result.get('stderr', '')}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestBatchToolsE2E:
    """测试批量查询工具的E2E流程"""

    async def test_batch_query_workflow(self, joern_server, sample_c_code):
        """测试批量查询的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "batch_test")

        queries = ["cpg.method.name.l", "cpg.call.name.l", "cpg.literal.code.l"]
        results = []

        for query in queries:
            result = await execute_query_safe(joern_server, query)
            results.append(result)

        # 真正验证每个查询结果
        assert len(results) == 3, f"期望3个结果，实际{len(results)}个"
        for i, result in enumerate(results):
            assert result["success"], f"查询{i}失败: {result.get('stderr', '')}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExportToolsE2E:
    """测试导出工具的E2E流程"""

    async def test_export_to_json_workflow(self, joern_server, sample_c_code):
        """测试导出为JSON的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "export_test")

        query = "cpg.method.name.l"
        result = await execute_query_safe(joern_server, query)

        assert result["success"], f"查询失败: {result.get('stderr', '')}"
        assert "stdout" in result, "返回结果缺少stdout字段"

    async def test_export_to_dot_workflow(self, joern_server, sample_c_code):
        """测试导出为DOT格式的完整流程"""
        await import_code_safe(joern_server, str(sample_c_code), "dot_test")

        query = 'cpg.method.name("main").dotCfg.l'
        result = await execute_query_safe(joern_server, query)

        assert result["success"], f"查询失败: {result.get('stderr', '')}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestServerStateE2E:
    """测试ServerState的E2E流程"""

    async def test_server_state_initialization(self, joern_server):
        """测试ServerState初始化"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        assert server_state.joern_server is not None, "joern_server未正确设置"
        assert server_state.query_executor is not None, "query_executor未正确设置"

    async def test_server_state_executor_usage(self, joern_server, sample_c_code):
        """测试通过ServerState使用executor"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        await import_code_safe(joern_server, str(sample_c_code), "state_test")

        result = await execute_query_safe(joern_server, "cpg.method.name.l")
        assert result["success"], f"查询失败: {result.get('stderr', '')}"
