"""端口管理工具"""

import random
import socket

from loguru import logger


def find_free_port(
    start_port: int = 20000, end_port: int = 30000, max_attempts: int = 100
) -> int:
    """查找一个可用的端口

    Args:
        start_port: 起始端口号
        end_port: 结束端口号
        max_attempts: 最大尝试次数

    Returns:
        可用的端口号

    Raises:
        RuntimeError: 如果找不到可用端口
    """
    for attempt in range(max_attempts):
        port = random.randint(start_port, end_port)

        if is_port_available(port):
            logger.debug(f"Found free port: {port} (attempt {attempt + 1})")
            return port

    raise RuntimeError(
        f"Could not find free port in range {start_port}-{end_port} "
        f"after {max_attempts} attempts"
    )


def is_port_available(port: int, host: str = "localhost") -> bool:
    """检查端口是否可用

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        True表示端口可用，False表示被占用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """检查端口是否被占用（is_port_available的反向）

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        True表示端口被占用，False表示可用
    """
    return not is_port_available(port, host)


def wait_for_port(
    port: int, host: str = "localhost", timeout: float = 30.0, interval: float = 0.5
) -> bool:
    """等待端口变为可用（被监听）

    Args:
        port: 端口号
        host: 主机地址
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）

    Returns:
        True表示端口在超时前变为可用，False表示超时
    """
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect((host, port))
                logger.debug(f"Port {port} is now in use (listening)")
                return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            time.sleep(interval)

    logger.warning(f"Port {port} did not become available within {timeout}s")
    return False


def kill_process_on_port(port: int) -> bool:
    """终止占用指定端口的进程

    Args:
        port: 端口号

    Returns:
        True表示成功，False表示失败或无进程占用

    Note:
        这个函数依赖于系统命令，可能不是跨平台的
    """
    import subprocess
    import sys

    try:
        if sys.platform == "darwin" or sys.platform == "linux":
            # macOS和Linux
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    logger.info(f"Killing process {pid} on port {port}")
                    subprocess.run(["kill", "-9", pid], timeout=5)
                return True

        elif sys.platform == "win32":
            # Windows
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    logger.info(f"Killing process {pid} on port {port}")
                    subprocess.run(["taskkill", "/F", "/PID", pid], timeout=5)
                    return True

        return False

    except Exception as e:
        logger.error(f"Failed to kill process on port {port}: {e}")
        return False


def get_port_info(port: int) -> dict | None:
    """获取端口的详细信息

    Args:
        port: 端口号

    Returns:
        包含端口信息的字典，如果端口未被占用则返回None
    """
    import subprocess
    import sys

    try:
        if sys.platform == "darwin" or sys.platform == "linux":
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-P"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    # 解析lsof输出
                    header = lines[0].split()
                    data = lines[1].split(None, len(header) - 1)

                    return {
                        "command": data[0] if len(data) > 0 else None,
                        "pid": data[1] if len(data) > 1 else None,
                        "user": data[2] if len(data) > 2 else None,
                        "name": data[8] if len(data) > 8 else None,
                    }

        return None

    except Exception as e:
        logger.error(f"Failed to get port info for {port}: {e}")
        return None
