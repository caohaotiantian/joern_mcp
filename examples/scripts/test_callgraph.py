#!/usr/bin/env python3
"""
调用图工具测试脚本

测试 get_callers、get_callees、get_call_chain 和 get_call_graph 工具
使用 multi_file_project 作为测试项目
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


async def main():
    """运行调用图测试"""
    from joern_mcp.joern.executor_optimized import OptimizedQueryExecutor
    from joern_mcp.joern.server import JoernServerManager
    from joern_mcp.services.callgraph import CallGraphService

    # 测试项目路径
    test_project = project_root / "examples" / "multi_file_project"
    project_name = "callgraph_test"

    logger.info(f"测试项目路径: {test_project}")

    # 启动 Joern 服务器
    logger.info("启动 Joern 服务器...")
    server = JoernServerManager()

    try:
        await server.start(timeout=120)
        logger.info(f"Joern 服务器已启动: {server.endpoint}")

        # 创建查询执行器和服务
        executor = OptimizedQueryExecutor(server)
        callgraph_service = CallGraphService(executor)

        # 导入测试项目
        logger.info(f"导入项目: {project_name}")
        import_result = await server.execute_query_async(
            f'importCode(inputPath="{test_project}", projectName="{project_name}")'
        )

        if not import_result.get("success"):
            logger.error(f"导入失败: {import_result.get('stderr')}")
            return

        logger.info("项目导入成功")

        # 等待 CPG 生成完成
        await asyncio.sleep(2)

        # ========== 测试 1: get_callers ==========
        logger.info("\n" + "="*60)
        logger.info("测试 1: get_callers - 查找谁调用了指定函数")
        logger.info("="*60)

        test_functions = ["log_message", "query_user", "exec_query"]

        for func in test_functions:
            logger.info(f"\n查找 {func} 的调用者 (depth=1):")
            result = await callgraph_service.get_callers(func, depth=1, project_name=project_name)

            if result.get("success"):
                callers = result.get("callers", [])
                logger.info(f"  找到 {len(callers)} 个调用者:")
                for caller in callers[:5]:  # 最多显示5个
                    name = caller.get("name", "unknown")
                    filename = caller.get("filename", "").split("/")[-1]
                    logger.info(f"    - {name} ({filename})")
                if len(callers) > 5:
                    logger.info(f"    ... 还有 {len(callers) - 5} 个")
            else:
                logger.warning(f"  查询失败: {result.get('error')}")

        # ========== 测试 2: get_callees ==========
        logger.info("\n" + "="*60)
        logger.info("测试 2: get_callees - 查找函数调用了哪些其他函数")
        logger.info("="*60)

        test_functions = ["main", "authenticate", "check_password", "init_app"]

        for func in test_functions:
            logger.info(f"\n查找 {func} 调用的函数 (depth=1):")
            result = await callgraph_service.get_callees(func, depth=1, project_name=project_name)

            if result.get("success"):
                callees = result.get("callees", [])
                logger.info(f"  找到 {len(callees)} 个被调用函数:")
                for callee in callees[:8]:  # 最多显示8个
                    name = callee.get("name", "unknown")
                    logger.info(f"    - {name}")
                if len(callees) > 8:
                    logger.info(f"    ... 还有 {len(callees) - 8} 个")
            else:
                logger.warning(f"  查询失败: {result.get('error')}")

        # ========== 测试 3: get_call_chain ==========
        logger.info("\n" + "="*60)
        logger.info("测试 3: get_call_chain - 追溯调用链")
        logger.info("="*60)

        # 向上追溯
        logger.info("\n从 log_message 向上追溯 (direction='up', max_depth=3):")
        result = await callgraph_service.get_call_chain(
            "log_message", max_depth=3, direction="up", project_name=project_name
        )

        if result.get("success"):
            chain = result.get("chain", [])
            logger.info(f"  调用链长度: {len(chain)}")
            for item in chain[:10]:
                name = item.get("name", "unknown")
                filename = item.get("filename", "").split("/")[-1]
                logger.info(f"    <- {name} ({filename})")
        else:
            logger.warning(f"  查询失败: {result.get('error')}")

        # 向下追溯
        logger.info("\n从 main 向下追溯 (direction='down', max_depth=3):")
        result = await callgraph_service.get_call_chain(
            "main", max_depth=3, direction="down", project_name=project_name
        )

        if result.get("success"):
            chain = result.get("chain", [])
            logger.info(f"  调用链长度: {len(chain)}")
            for item in chain[:10]:
                name = item.get("name", "unknown")
                filename = item.get("filename", "").split("/")[-1]
                logger.info(f"    -> {name} ({filename})")
        else:
            logger.warning(f"  查询失败: {result.get('error')}")

        # ========== 测试 4: get_call_graph ==========
        logger.info("\n" + "="*60)
        logger.info("测试 4: get_call_graph - 获取完整调用图")
        logger.info("="*60)

        test_functions = ["authenticate", "process_request"]

        for func in test_functions:
            logger.info(f"\n{func} 的调用图 (depth=2):")
            result = await callgraph_service.get_call_graph(
                func,
                include_callers=True,
                include_callees=True,
                depth=2,
                project_name=project_name
            )

            if result.get("success"):
                nodes = result.get("nodes", [])
                edges = result.get("edges", [])
                logger.info(f"  节点数: {len(nodes)}, 边数: {len(edges)}")

                logger.info("  节点:")
                for node in nodes[:8]:
                    logger.info(f"    - {node}")
                if len(nodes) > 8:
                    logger.info(f"    ... 还有 {len(nodes) - 8} 个")

                logger.info("  边 (调用关系):")
                for edge in edges[:5]:
                    if isinstance(edge, dict):
                        logger.info(f"    {edge.get('from', '?')} -> {edge.get('to', '?')}")
                    else:
                        logger.info(f"    {edge[0]} -> {edge[1]}")
                if len(edges) > 5:
                    logger.info(f"    ... 还有 {len(edges) - 5} 条")
            else:
                logger.warning(f"  查询失败: {result.get('error')}")

        # ========== 测试完成 ==========
        logger.info("\n" + "="*60)
        logger.info("所有调用图测试完成!")
        logger.info("="*60)

    except Exception as e:
        logger.exception(f"测试失败: {e}")
    finally:
        logger.info("停止 Joern 服务器...")
        await server.stop()
        logger.info("测试结束")


if __name__ == "__main__":
    asyncio.run(main())

