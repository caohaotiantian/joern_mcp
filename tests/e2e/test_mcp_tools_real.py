"""
MCP工具真实端到端测试

实际运行 MCP Server 并测试每个工具的调用结果。
这些测试使用真实的 Joern Server，验证工具的完整功能。

注意：MCP 工具函数被 @mcp.tool() 装饰后变成 FunctionTool 对象，
需要通过 .fn 属性获取原始函数来调用。

更新：所有查询工具现在要求 project_name 作为第一个必填参数。
"""

import pytest
from loguru import logger

from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor as QueryExecutor
from joern_mcp.mcp_server import server_state


def get_tool_fn(tool):
    """获取 MCP 工具的原始函数

    MCP 工具被 @mcp.tool() 装饰后变成 FunctionTool 对象，
    需要通过 .fn 属性获取原始函数。
    """
    if hasattr(tool, "fn"):
        return tool.fn
    return tool


# 测试项目名称常量
TEST_PROJECT = "e2e_test_project"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPToolsReal:
    """测试 MCP 工具的真实调用

    这些测试使用真实的 Joern Server，验证工具的完整功能。
    """

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state，模拟 MCP Server 环境"""
        # 设置全局状态
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        # 导入测试代码
        from tests.e2e.test_helpers import import_code_safe

        result = await import_code_safe(joern_server, str(sample_c_code), TEST_PROJECT)
        logger.info(f"Import result: {result}")

        yield

        # 清理
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_health_check(self):
        """测试 health_check 工具"""
        from joern_mcp.server import health_check

        result = await get_tool_fn(health_check)()

        logger.info(f"health_check result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "status" in result, "缺少 status 字段"
        assert result["status"] == "healthy", f"服务器状态异常: {result}"
        assert "joern_endpoint" in result, "缺少 joern_endpoint 字段"

    async def test_execute_query(self):
        """测试 execute_query 工具"""
        from joern_mcp.server import execute_query

        # 测试简单查询
        result = await get_tool_fn(execute_query)("cpg.method.name.l")

        logger.info(f"execute_query result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"查询失败: {result.get('error')}"
        assert "result" in result, "缺少 result 字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestProjectToolsReal:
    """测试项目管理工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server):
        """设置 server_state"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_parse_project(self, sample_c_code):
        """测试 parse_project 工具"""
        from joern_mcp.tools.project import parse_project

        result = await get_tool_fn(parse_project)(
            str(sample_c_code), "test_parse_project"
        )

        logger.info(f"parse_project result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"解析失败: {result.get('error')}"
        assert result["project_name"] == "test_parse_project"

    async def test_list_projects(self, sample_c_code):
        """测试 list_projects 工具 - 诊断解析问题"""
        from joern_mcp.tools.project import list_projects, parse_project

        # 先导入一个项目
        await get_tool_fn(parse_project)(str(sample_c_code), "test_list_project")

        result = await get_tool_fn(list_projects)()

        logger.info(f"list_projects result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"

        # 如果失败，输出详细错误信息用于诊断
        if not result.get("success"):
            logger.error(f"list_projects 失败: {result}")
            # 尝试直接查询以诊断问题
            raw_result = await server_state.joern_server.execute_query_async(
                "workspace.projects.name.l"
            )
            logger.info(f"原始 workspace 查询结果: {raw_result}")

        assert result["success"], f"列出项目失败: {result.get('error')}"
        assert "projects" in result, "缺少 projects 字段"
        assert "count" in result, "缺少 count 字段"
        assert isinstance(result["projects"], list), "projects 应该是列表"

    async def test_list_projects_raw_response(self, sample_c_code):
        """验证 list_projects 使用的查询格式能正确解析"""
        from joern_mcp.tools.project import parse_project

        # 先导入一个项目
        await get_tool_fn(parse_project)(str(sample_c_code), "test_raw_response")

        # 执行新的简化查询（与 list_projects 实现一致）
        query = 'workspace.projects.map(p => s"${p.name}:::${p.inputPath}").l'

        result = await server_state.joern_server.execute_query_async(query)
        logger.info(f"原始 Joern 响应 - success: {result.get('success')}")
        logger.info(f"原始 Joern 响应 - stdout: {result.get('stdout')[:200]}...")
        logger.info(f"原始 Joern 响应 - stderr: {result.get('stderr')}")

        # 验证原始响应
        assert result.get("success"), f"查询失败: {result.get('stderr')}"

        # 尝试解析响应
        from joern_mcp.utils.response_parser import (
            safe_parse_joern_response,
        )

        stdout = result.get("stdout", "")

        # 测试安全解析
        parsed = safe_parse_joern_response(stdout, default=[])
        logger.info(f"safe_parse_joern_response 结果: {len(parsed)} 项目")

        # 验证解析结果
        assert isinstance(parsed, list), f"解析结果应该是列表: {type(parsed)}"
        assert len(parsed) > 0, "应该至少有一个项目"

        # 验证格式（每个项目应该包含 ::: 分隔符）
        for item in parsed:
            assert isinstance(item, str), f"每个项目应该是字符串: {type(item)}"
            assert ":::" in item, f"项目格式应该包含 :::, 实际: {item}"

    async def test_switch_project(self, sample_c_code):
        """测试 switch_project 工具"""
        from joern_mcp.tools.project import parse_project, switch_project

        # 先创建项目
        await get_tool_fn(parse_project)(str(sample_c_code), "test_switch_project")

        result = await get_tool_fn(switch_project)("test_switch_project")

        logger.info(f"switch_project result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"切换项目失败: {result.get('error')}"

    async def test_get_current_project(self, sample_c_code):
        """测试 get_current_project 工具"""
        from joern_mcp.tools.project import get_current_project, parse_project

        # 先创建项目
        await get_tool_fn(parse_project)(str(sample_c_code), "test_current_project")

        result = await get_tool_fn(get_current_project)()

        logger.info(f"get_current_project result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"

        # 如果失败，输出诊断信息
        if not result.get("success"):
            logger.warning(f"get_current_project 失败: {result}")

    async def test_delete_project(self, sample_c_code):
        """测试 delete_project 工具"""
        from joern_mcp.tools.project import delete_project, parse_project

        # 先创建项目
        await get_tool_fn(parse_project)(str(sample_c_code), "test_delete_project")

        result = await get_tool_fn(delete_project)("test_delete_project")

        logger.info(f"delete_project result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"删除项目失败: {result.get('error')}"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestQueryToolsReal:
    """测试查询工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "query_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_list_functions(self):
        """测试 list_functions 工具"""
        from joern_mcp.tools.query import list_functions

        # project_name 现在是必填参数
        result = await get_tool_fn(list_functions)("query_tools_test")

        logger.info(f"list_functions result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"列出函数失败: {result.get('error')}"
        assert "functions" in result, "缺少 functions 字段"
        assert result.get("project") == "query_tools_test", "返回的项目名称不匹配"

    async def test_get_function_code(self):
        """测试 get_function_code 工具"""
        from joern_mcp.tools.query import get_function_code

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_function_code)("query_tools_test", "main")

        logger.info(f"get_function_code result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result["success"], f"获取函数代码失败: {result.get('error')}"
        assert result.get("project") == "query_tools_test", "返回的项目名称不匹配"

    async def test_search_code(self):
        """测试 search_code 工具"""
        from joern_mcp.tools.query import search_code

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(search_code)(
            "query_tools_test", "main", scope="methods"
        )

        logger.info(f"search_code result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "query_tools_test", "返回的项目名称不匹配"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCallgraphToolsReal:
    """测试调用图工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "callgraph_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_get_callers(self):
        """测试 get_callers 工具"""
        from joern_mcp.tools.callgraph import get_callers

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_callers)(
            "callgraph_tools_test", "vulnerable_function"
        )

        logger.info(f"get_callers result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "callgraph_tools_test", "返回的项目名称不匹配"

    async def test_get_callees(self):
        """测试 get_callees 工具"""
        from joern_mcp.tools.callgraph import get_callees

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_callees)("callgraph_tools_test", "main")

        logger.info(f"get_callees result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "callgraph_tools_test", "返回的项目名称不匹配"

    async def test_get_call_chain(self):
        """测试 get_call_chain 工具"""
        from joern_mcp.tools.callgraph import get_call_chain

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_call_chain)(
            "callgraph_tools_test", "main", max_depth=3
        )

        logger.info(f"get_call_chain result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "callgraph_tools_test", "返回的项目名称不匹配"

    async def test_get_call_graph(self):
        """测试 get_call_graph 工具"""
        from joern_mcp.tools.callgraph import get_call_graph

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_call_graph)(
            "callgraph_tools_test", "main", depth=1
        )

        logger.info(f"get_call_graph result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "callgraph_tools_test", "返回的项目名称不匹配"
        # 验证调用图结构
        if result.get("success"):
            assert "nodes" in result, "缺少 nodes 字段"
            assert "edges" in result, "缺少 edges 字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDataflowToolsReal:
    """测试数据流工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "dataflow_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_track_dataflow(self):
        """测试 track_dataflow 工具"""
        from joern_mcp.tools.dataflow import track_dataflow

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(track_dataflow)(
            "dataflow_tools_test", "gets", "strcpy"
        )

        logger.info(f"track_dataflow result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "dataflow_tools_test", "返回的项目名称不匹配"

    async def test_find_data_dependencies(self):
        """测试 find_data_dependencies 工具"""
        from joern_mcp.tools.dataflow import find_data_dependencies

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(find_data_dependencies)(
            "dataflow_tools_test", "main"
        )

        logger.info(f"find_data_dependencies result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "dataflow_tools_test", "返回的项目名称不匹配"

    async def test_analyze_variable_flow(self):
        """测试 analyze_variable_flow 工具"""
        from joern_mcp.tools.dataflow import analyze_variable_flow

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(analyze_variable_flow)(
            "dataflow_tools_test", "buffer"
        )

        logger.info(f"analyze_variable_flow result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "dataflow_tools_test", "返回的项目名称不匹配"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestTaintToolsReal:
    """测试污点分析工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "taint_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_find_vulnerabilities(self):
        """测试 find_vulnerabilities 工具"""
        from joern_mcp.tools.taint import find_vulnerabilities

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(find_vulnerabilities)("taint_tools_test")

        logger.info(f"find_vulnerabilities result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "taint_tools_test", "返回的项目名称不匹配"

    async def test_check_taint_flow(self):
        """测试 check_taint_flow 工具"""
        from joern_mcp.tools.taint import check_taint_flow

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(check_taint_flow)(
            "taint_tools_test", "gets", "strcpy"
        )

        logger.info(f"check_taint_flow result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "taint_tools_test", "返回的项目名称不匹配"

    async def test_list_vulnerability_rules(self):
        """测试 list_vulnerability_rules 工具"""
        from joern_mcp.tools.taint import list_vulnerability_rules

        result = await get_tool_fn(list_vulnerability_rules)()

        logger.info(f"list_vulnerability_rules result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        if result.get("success"):
            assert "rules" in result, "缺少 rules 字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCFGToolsReal:
    """测试控制流图工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "cfg_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_get_control_flow_graph(self):
        """测试 get_control_flow_graph 工具"""
        from joern_mcp.tools.cfg import get_control_flow_graph

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_control_flow_graph)("cfg_tools_test", "main")

        logger.info(f"get_control_flow_graph result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "cfg_tools_test", "返回的项目名称不匹配"

    async def test_analyze_control_structures(self):
        """测试 analyze_control_structures 工具"""
        from joern_mcp.tools.cfg import analyze_control_structures

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(analyze_control_structures)("cfg_tools_test", "main")

        logger.info(f"analyze_control_structures result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "cfg_tools_test", "返回的项目名称不匹配"

    async def test_get_dominators(self):
        """测试 get_dominators 工具"""
        from joern_mcp.tools.cfg import get_dominators

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(get_dominators)("cfg_tools_test", "main")

        logger.info(f"get_dominators result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "cfg_tools_test", "返回的项目名称不匹配"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestBatchToolsReal:
    """测试批量操作工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "batch_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_batch_query(self):
        """测试 batch_query 工具"""
        from joern_mcp.tools.batch import batch_query

        # 查询需要指定项目前缀
        queries = [
            'workspace.project("batch_tools_test").get.cpg.get.method.name.l',
            'workspace.project("batch_tools_test").get.cpg.get.call.name.l',
        ]
        result = await get_tool_fn(batch_query)(queries)

        logger.info(f"batch_query result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        if result.get("success"):
            assert "results" in result, "缺少 results 字段"

    async def test_batch_function_analysis(self):
        """测试 batch_function_analysis 工具"""
        from joern_mcp.tools.batch import batch_function_analysis

        # project_name 现在是第一个必填参数
        result = await get_tool_fn(batch_function_analysis)(
            "batch_tools_test", ["main"]
        )

        logger.info(f"batch_function_analysis result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"
        assert result.get("project") == "batch_tools_test", "返回的项目名称不匹配"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExportToolsReal:
    """测试导出工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "export_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_export_cpg(self, tmp_path):
        """测试 export_cpg 工具"""
        from joern_mcp.tools.export import export_cpg

        output_path = str(tmp_path / "exported_cpg")
        result = await get_tool_fn(export_cpg)(
            "export_tools_test", output_path, format="bin"
        )

        logger.info(f"export_cpg result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"

    async def test_export_analysis_results(self, tmp_path):
        """测试 export_analysis_results 工具"""
        from joern_mcp.tools.export import export_analysis_results

        output_path = str(tmp_path / "results.json")
        test_data = {"vulnerabilities": [{"name": "test_vuln", "severity": "HIGH"}]}
        result = await get_tool_fn(export_analysis_results)(
            test_data, output_path, format="json"
        )

        logger.info(f"export_analysis_results result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestPerformanceToolsReal:
    """测试性能工具的真实调用"""

    @pytest.fixture(autouse=True)
    async def setup_server_state(self, joern_server, sample_c_code):
        """设置 server_state 并导入测试代码"""
        server_state.joern_server = joern_server
        server_state.query_executor = QueryExecutor(joern_server)

        from tests.e2e.test_helpers import import_code_safe

        await import_code_safe(joern_server, str(sample_c_code), "perf_tools_test")
        yield
        server_state.joern_server = None
        server_state.query_executor = None

    async def test_get_performance_stats(self):
        """测试 get_performance_stats 工具"""
        from joern_mcp.tools.performance import get_performance_stats

        result = await get_tool_fn(get_performance_stats)()

        logger.info(f"get_performance_stats result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        # 验证有数据返回
        assert result is not None

    async def test_clear_query_cache(self):
        """测试 clear_query_cache 工具"""
        from joern_mcp.tools.performance import clear_query_cache

        result = await get_tool_fn(clear_query_cache)()

        logger.info(f"clear_query_cache result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
        assert "success" in result, "缺少 success 字段"

    async def test_get_cache_stats(self):
        """测试 get_cache_stats 工具"""
        from joern_mcp.tools.performance import get_cache_stats

        result = await get_tool_fn(get_cache_stats)()

        logger.info(f"get_cache_stats result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"

    async def test_get_system_health(self):
        """测试 get_system_health 工具"""
        from joern_mcp.tools.performance import get_system_health

        result = await get_tool_fn(get_system_health)()

        logger.info(f"get_system_health result: {result}")

        assert isinstance(result, dict), f"返回类型错误: {type(result)}"
