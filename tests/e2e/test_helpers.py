"""
E2E测试辅助函数

提供用于解决event loop冲突的工具函数
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


async def run_sync_in_executor(func: Callable, *args, **kwargs) -> Any:
    """在线程池中运行同步函数，避免event loop冲突
    
    Args:
        func: 要执行的同步函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果
    """
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    try:
        result = await loop.run_in_executor(
            executor,
            lambda: func(*args, **kwargs)
        )
        return result
    finally:
        executor.shutdown(wait=True)


async def import_code_safe(joern_server, code_path: str, project_name: str) -> dict:
    """安全地导入代码，避免event loop冲突
    
    Args:
        joern_server: JoernServerManager实例
        code_path: 代码路径
        project_name: 项目名称
        
    Returns:
        导入结果字典
    """
    from cpgqls_client import import_code_query
    
    # 构建查询
    query = import_code_query(code_path, project_name)
    
    # 在线程池中执行同步查询
    result = await run_sync_in_executor(
        joern_server.execute_query,
        query
    )
    
    return result


async def execute_query_safe(joern_server, query: str) -> dict:
    """安全地执行查询，避免event loop冲突
    
    Args:
        joern_server: JoernServerManager实例
        query: Joern查询字符串
        
    Returns:
        查询结果字典
    """
    result = await run_sync_in_executor(
        joern_server.execute_query,
        query
    )
    
    return result


async def health_check_safe(joern_server) -> bool:
    """安全地执行健康检查，避免event loop冲突
    
    Args:
        joern_server: JoernServerManager实例
        
    Returns:
        True表示健康，False表示不健康
    """
    if not joern_server.client:
        return False
    
    try:
        # 使用简单查询进行健康检查
        result = await execute_query_safe(joern_server, "1 + 1")
        return result.get("success", False)
    except Exception:
        return False

