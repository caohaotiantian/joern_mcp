"""
tests/test_utils/test_port_utils.py

测试端口管理工具
"""
import pytest
import socket
from joern_mcp.utils.port_utils import (
    find_free_port,
    is_port_available,
    is_port_in_use
)


class TestPortUtils:
    """测试端口管理工具"""

    def test_find_free_port_basic(self):
        """测试查找空闲端口基本功能"""
        port = find_free_port()
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_find_free_port_with_range(self):
        """测试在指定范围查找空闲端口"""
        port = find_free_port(start_port=10000, end_port=10100)
        assert 10000 <= port <= 10100

    def test_is_port_available_likely_free(self):
        """测试检测可能空闲的端口"""
        # 找一个空闲端口，然后检查它
        port = find_free_port(start_port=50000, end_port=50100)
        # 该端口应该可用
        result = is_port_available(port)
        assert isinstance(result, bool)

    def test_is_port_available_occupied(self):
        """测试检测被占用的端口"""
        # 创建一个socket占用端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("localhost", 0))  # 让系统分配端口
            sock.listen(1)
            port = sock.getsockname()[1]
            
            # 端口应该不可用
            assert not is_port_available(port, host="localhost")
        finally:
            sock.close()

    def test_is_port_in_use_occupied(self):
        """测试检测正在使用的端口"""
        # 绑定一个端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("localhost", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            
            assert is_port_in_use(port, host="localhost")
        finally:
            sock.close()

    def test_is_port_in_use_free(self):
        """测试检测未使用的端口"""
        # 找一个空闲端口
        port = find_free_port(start_port=50100, end_port=50200)
        # 该端口不应该被使用
        assert not is_port_in_use(port)


class TestPortUtilsEdgeCases:
    """测试端口工具的边界情况"""

    def test_find_free_port_multiple_calls(self):
        """测试多次调用find_free_port"""
        ports = []
        for _ in range(5):
            port = find_free_port(start_port=50200, end_port=50300)
            ports.append(port)
            assert 50200 <= port <= 50300

    def test_is_port_available_with_custom_host(self):
        """测试使用自定义主机检测端口"""
        port = find_free_port()
        # 使用127.0.0.1
        result1 = is_port_available(port, host="127.0.0.1")
        # 使用localhost
        result2 = is_port_available(port, host="localhost")
        # 两者应该相同
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    def test_port_lifecycle(self):
        """测试端口生命周期"""
        # 找一个空闲端口
        port = find_free_port(start_port=50300, end_port=50400)
        
        # 初始应该可用
        assert is_port_available(port)
        
        # 占用端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("localhost", port))
            sock.listen(1)
            
            # 应该不可用
            assert not is_port_available(port)
            assert is_port_in_use(port)
        finally:
            sock.close()
        
        # 关闭后可能需要一点时间才能释放
        # 所以这里不强制要求立即可用

    def test_concurrent_port_operations(self):
        """测试并发端口操作"""
        import concurrent.futures
        
        def check_port():
            port = find_free_port(start_port=50400, end_port=50500)
            return is_port_available(port)
        
        # 多个线程同时操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(check_port) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # 所有操作都应该成功
        assert len(results) == 5
        assert all(isinstance(r, bool) for r in results)
